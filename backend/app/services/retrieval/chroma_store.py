"""Optional local ChromaDB vector store adapter."""

from __future__ import annotations

from typing import Any

import numpy as np

from backend.app.services.retrieval.retrieval_metadata_service import chroma_dir


class ChromaStoreError(RuntimeError):
    """Raised when ChromaDB cannot complete an operation."""


COLLECTION_NAME = "nexora_chunks"


def _load_chroma_client():
    try:
        import chromadb

        return chromadb.PersistentClient(path=str(chroma_dir()))
    except Exception as exc:
        raise ChromaStoreError("chromadb is not installed or could not be initialized.") from exc


def chroma_status() -> dict[str, object]:
    try:
        client = _load_chroma_client()
        collection = client.get_or_create_collection(COLLECTION_NAME)
        return {
            "available": True,
            "path": str(chroma_dir()),
            "collection": COLLECTION_NAME,
            "count": collection.count(),
            "error": "",
        }
    except ChromaStoreError as exc:
        return {
            "available": False,
            "path": str(chroma_dir()),
            "collection": COLLECTION_NAME,
            "count": 0,
            "error": str(exc),
        }


def add_vectors(
    vectors: np.ndarray,
    vector_ids: list[str],
    texts: list[str],
    metadatas: list[dict[str, Any]],
    rebuild: bool = False,
) -> None:
    client = _load_chroma_client()
    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(COLLECTION_NAME)
    if not vector_ids:
        return

    collection.add(
        ids=vector_ids,
        embeddings=np.asarray(vectors, dtype=float).tolist(),
        documents=texts,
        metadatas=metadatas,
    )


def search_vectors(
    query_vector: np.ndarray,
    top_k: int,
    filters: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    client = _load_chroma_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    if collection.count() == 0:
        return []

    where = filters or None
    result = collection.query(
        query_embeddings=np.asarray(query_vector, dtype=float).tolist(),
        n_results=top_k,
        where=where,
    )
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    rows: list[dict[str, object]] = []
    for vector_id, distance, document, metadata in zip(ids, distances, documents, metadatas, strict=False):
        rows.append(
            {
                "vector_id": vector_id,
                "score": float(1 - distance),
                "chunk_text": document,
                "metadata": metadata,
            }
        )
    return rows
