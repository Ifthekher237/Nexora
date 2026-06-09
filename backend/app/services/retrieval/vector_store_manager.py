"""Coordinator for FAISS and optional Chroma vector stores."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from backend.app.core.config import PROJECT_ROOT, get_retrieval_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ingestion.storage_service import project_relative_path, safe_filename
from backend.app.services.retrieval import chroma_store, embedding_service, faiss_store
from backend.app.services.retrieval.retrieval_metadata_service import (
    append_vector_metadata,
    is_chunk_indexed,
    read_vector_metadata,
    vector_metadata_status,
)


logger = logging.getLogger(__name__)


class VectorStoreManagerError(RuntimeError):
    """Raised when vector index operations fail."""


def validate_vector_store(vector_store: str) -> str:
    normalized = vector_store.strip().lower()
    config = get_retrieval_config().get("retrieval", {})
    if normalized == "faiss" and config.get("enable_faiss", True):
        return normalized
    if normalized == "chroma" and config.get("enable_chroma", True):
        return normalized
    raise VectorStoreManagerError(f"Unsupported or disabled vector store: {vector_store}")


def chunks_dir() -> Path:
    configured = get_retrieval_config().get("indexing", {}).get(
        "chunks_dir", "data/processed/chunks"
    )
    return PROJECT_ROOT / configured


def vector_id_for_chunk(chunk_id: str, vector_store: str, embedding_model: str) -> str:
    model_hash = hashlib.sha1(embedding_model.encode("utf-8")).hexdigest()[:6]
    return safe_filename(f"{vector_store.upper()}_{chunk_id}_{model_hash}")


def _load_processed_chunks(limit: int) -> tuple[list[dict[str, Any]], list[str]]:
    loaded: list[dict[str, Any]] = []
    errors: list[str] = []
    directory = chunks_dir()
    if not directory.exists():
        return loaded, [f"Chunks directory does not exist: {directory}"]

    for path in sorted(directory.glob("*_chunks.json")):
        if len(loaded) >= limit:
            break
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Malformed chunk JSON {path}: {exc}")
            continue
        if not isinstance(data, list):
            errors.append(f"Chunk file is not a JSON list: {path}")
            continue
        for chunk in data:
            if len(loaded) >= limit:
                break
            if not isinstance(chunk, dict) or not chunk.get("chunk_id") or not chunk.get("chunk_text"):
                errors.append(f"Invalid chunk record in {path}")
                continue
            enriched = dict(chunk)
            enriched["source_chunk_file"] = project_relative_path(path)
            loaded.append(enriched)

    return loaded, errors


def vector_store_availability() -> dict[str, object]:
    return {
        "default": get_retrieval_config().get("retrieval", {}).get("default_vector_store", "faiss"),
        "faiss": faiss_store.faiss_status(),
        "chroma": chroma_store.chroma_status(),
    }


def build_vector_index(limit: int, vector_store: str, rebuild: bool = False) -> dict[str, Any]:
    store = validate_vector_store(vector_store)
    embedding_model = embedding_service.default_embedding_model()
    chunks, load_errors = _load_processed_chunks(limit)
    logger.info(
        "Vector indexing started | store=%s | chunks_found=%s | rebuild=%s | model=%s",
        store,
        len(chunks),
        rebuild,
        embedding_model,
    )

    selected_chunks: list[dict[str, Any]] = []
    duplicates = 0
    for chunk in chunks:
        chunk_id = str(chunk["chunk_id"])
        if not rebuild and is_chunk_indexed(chunk_id, store, embedding_model):
            duplicates += 1
            continue
        selected_chunks.append(chunk)

    if not selected_chunks:
        return {
            "status": "success" if not load_errors else "partial_success",
            "vector_store": store,
            "embedding_model": embedding_model,
            "chunks_found": len(chunks),
            "chunks_indexed": 0,
            "duplicates_skipped": duplicates,
            "errors": load_errors,
        }

    texts = [str(chunk["chunk_text"]) for chunk in selected_chunks]
    vectors = embedding_service.embed_texts(texts, model_name=embedding_model)
    dimension = int(vectors.shape[1])

    records: list[dict[str, Any]] = []
    vector_ids: list[str] = []
    for chunk in selected_chunks:
        vector_id = vector_id_for_chunk(str(chunk["chunk_id"]), store, embedding_model)
        vector_ids.append(vector_id)
        records.append(
            {
                "vector_id": vector_id,
                "chunk_id": chunk.get("chunk_id", ""),
                "processed_document_id": chunk.get("processed_document_id", ""),
                "source_document_id": chunk.get("source_document_id", ""),
                "chunk_index": chunk.get("chunk_index", ""),
                "company_name": chunk.get("company_name", ""),
                "ticker": chunk.get("ticker", ""),
                "market": chunk.get("market", ""),
                "document_type": chunk.get("document_type", ""),
                "source_type": chunk.get("source_type", ""),
                "published_at": chunk.get("published_at", ""),
                "period": chunk.get("period", ""),
                "section_hint": chunk.get("section_hint", ""),
                "embedding_model": embedding_model,
                "embedding_dimension": dimension,
                "vector_store": store,
                "indexed_at": utc_now_iso(),
                "chunk_word_count": chunk.get("chunk_word_count", ""),
                "chunk_char_count": chunk.get("chunk_char_count", ""),
                "source_chunk_file": chunk.get("source_chunk_file", ""),
                "status": "indexed",
                "error_message": "",
            }
        )

    if store == "faiss":
        faiss_store.add_vectors(vectors, vector_ids, rebuild=rebuild)
    elif store == "chroma":
        chroma_metadatas = [
            {key: value for key, value in record.items() if key != "error_message"}
            for record in records
        ]
        chroma_store.add_vectors(
            vectors,
            vector_ids,
            texts,
            chroma_metadatas,
            rebuild=rebuild,
        )

    append_vector_metadata(records, rebuild_store=store if rebuild else None)
    logger.info(
        "Vector indexing finished | store=%s | indexed=%s | duplicates=%s",
        store,
        len(records),
        duplicates,
    )
    return {
        "status": "success" if not load_errors else "partial_success",
        "vector_store": store,
        "embedding_model": embedding_model,
        "chunks_found": len(chunks),
        "chunks_indexed": len(records),
        "duplicates_skipped": duplicates,
        "errors": load_errors,
    }


def search_vector_store(
    query_vector: np.ndarray,
    vector_store: str,
    top_k: int,
    allowed_vector_ids: set[str] | None = None,
    filters: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    store = validate_vector_store(vector_store)
    if store == "faiss":
        raw_results = faiss_store.search_all_vectors(query_vector)
        if allowed_vector_ids is not None:
            raw_results = [
                result
                for result in raw_results
                if str(result["vector_id"]) in allowed_vector_ids
            ]
        return raw_results[:top_k]

    return chroma_store.search_vectors(query_vector, top_k=top_k, filters=filters)


def retrieval_system_status() -> dict[str, object]:
    metadata_status = vector_metadata_status()
    return {
        "status": "ready",
        "embedding_model_status": embedding_service.embedding_status(),
        "vector_store_availability": vector_store_availability(),
        "indexed_chunks": metadata_status["indexed_chunks"],
        "faiss_index_status": faiss_store.faiss_status(),
        "chroma_status": chroma_store.chroma_status(),
        "metadata_index_status": metadata_status,
    }
