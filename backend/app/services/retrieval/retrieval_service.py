"""Semantic retrieval coordination for Nexora."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_retrieval_config
from backend.app.services.retrieval import embedding_service, vector_store_manager
from backend.app.services.retrieval.retrieval_metadata_service import (
    filter_vector_metadata,
    read_vector_metadata,
    vector_summary,
)
from backend.app.services.retrieval.search_filter_service import normalize_filters
from backend.app.services.performance import response_cache_service


logger = logging.getLogger(__name__)


class RetrievalServiceError(RuntimeError):
    """Raised when semantic retrieval cannot be completed."""


def _top_k(value: int) -> int:
    config = get_retrieval_config().get("retrieval", {})
    top_k_max = int(config.get("top_k_max", 20))
    if value < 1:
        raise RetrievalServiceError("top_k must be at least 1.")
    if value > top_k_max:
        raise RetrievalServiceError(f"top_k cannot exceed {top_k_max}.")
    return value


def _metadata_by_vector_id() -> dict[str, dict[str, str]]:
    frame = read_vector_metadata()
    if frame.empty:
        return {}
    return {
        row["vector_id"]: row
        for row in frame.fillna("").to_dict(orient="records")
        if row.get("status") == "indexed"
    }


def _load_chunk_text(metadata: dict[str, str]) -> str:
    source_file = metadata.get("source_chunk_file", "")
    if not source_file:
        return ""
    path = Path(source_file)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        return ""
    try:
        chunks = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""

    for chunk in chunks:
        if chunk.get("chunk_id") == metadata.get("chunk_id"):
            return str(chunk.get("chunk_text", ""))
    return ""


def search(
    query: str,
    top_k: int,
    vector_store: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_query = query.strip()
    if not clean_query:
        raise RetrievalServiceError("Search query cannot be empty.")

    requested_top_k = _top_k(top_k)
    normalized_filters = normalize_filters(filters)
    normalized_filters["status"] = "indexed"
    cached = response_cache_service.get_retrieval_result(
        clean_query,
        requested_top_k,
        vector_store,
        normalized_filters,
    )
    if cached is not None:
        logger.info(
            "Retrieval cache hit | query=%s | top_k=%s | filters=%s",
            clean_query,
            requested_top_k,
            normalized_filters,
        )
        return cached

    candidate_metadata = filter_vector_metadata(normalized_filters)
    candidate_metadata = [
        record
        for record in candidate_metadata
        if record.get("vector_store", "").lower() == vector_store.lower()
    ]
    if not candidate_metadata:
        result = {"query": clean_query, "top_k": requested_top_k, "results": []}
        response_cache_service.set_retrieval_result(clean_query, requested_top_k, vector_store, normalized_filters, result)
        return result

    allowed_ids = {record["vector_id"] for record in candidate_metadata}
    metadata_map = _metadata_by_vector_id()
    query_vector = embedding_service.embed_query(clean_query)
    raw_results = vector_store_manager.search_vector_store(
        query_vector,
        vector_store=vector_store,
        top_k=requested_top_k,
        allowed_vector_ids=allowed_ids,
        filters={key: value for key, value in normalized_filters.items() if key != "status"},
    )

    results: list[dict[str, Any]] = []
    for rank, result in enumerate(raw_results, start=1):
        vector_id = str(result["vector_id"])
        metadata = metadata_map.get(vector_id, {})
        chunk_text = str(result.get("chunk_text") or _load_chunk_text(metadata))
        results.append(
            {
                "rank": rank,
                "score": float(result["score"]),
                "chunk_id": metadata.get("chunk_id", ""),
                "chunk_text": chunk_text,
                "metadata": metadata,
            }
        )

    logger.info(
        "Retrieval search completed | query=%s | top_k=%s | filters=%s | results=%s",
        clean_query,
        requested_top_k,
        normalized_filters,
        len(results),
    )
    payload = {"query": clean_query, "top_k": requested_top_k, "results": results}
    response_cache_service.set_retrieval_result(clean_query, requested_top_k, vector_store, normalized_filters, payload)
    return payload


def summary() -> dict[str, Any]:
    return vector_summary()


def index_metadata(filters: dict[str, str | None]) -> list[dict[str, str]]:
    return filter_vector_metadata(filters)
