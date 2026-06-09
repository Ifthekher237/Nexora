"""TTL and mtime-aware caches for repeated local metadata/history reads."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from backend.app.services.agents import agent_output_service
from backend.app.services.explainability import explainability_output_service
from backend.app.services.ingestion import metadata_service
from backend.app.services.performance import cache_service
from backend.app.services.processing import processing_metadata_service
from backend.app.services.rag import rag_response_service
from backend.app.services.reasoning import reasoning_output_service
from backend.app.services.retrieval import retrieval_metadata_service
from backend.app.services.risk import risk_output_service


logger = logging.getLogger(__name__)


def _file_signature(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
        return {"path": str(path), "mtime": stat.st_mtime, "size": stat.st_size}
    except OSError:
        return {"path": str(path), "mtime": 0.0, "size": 0}


def _records_from_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return frame.fillna("").to_dict(orient="records")


def _cached_records(name: str, path: Path, reader: Callable[[], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    key = cache_service.make_cache_key({"name": name, "signature": _file_signature(path)}, prefix="metadata")
    cached = cache_service.get("metadata", key)
    if isinstance(cached, list):
        return cached
    records = reader()
    cache_service.set("metadata", key, records, ttl_seconds=cache_service.namespace_ttl("metadata"))
    logger.debug("Metadata cache refreshed | name=%s | rows=%s", name, len(records))
    return records


def ingestion_records() -> list[dict[str, Any]]:
    return _cached_records(
        "ingestion_index",
        metadata_service.csv_index_path(),
        lambda: _records_from_frame(metadata_service.read_metadata()),
    )


def processing_records() -> list[dict[str, Any]]:
    return _cached_records(
        "processing_index",
        processing_metadata_service.processing_csv_path(),
        lambda: _records_from_frame(processing_metadata_service.read_processing_metadata()),
    )


def vector_records() -> list[dict[str, Any]]:
    return _cached_records(
        "vector_index",
        retrieval_metadata_service.vector_csv_path(),
        lambda: _records_from_frame(retrieval_metadata_service.read_vector_metadata()),
    )


def rag_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    return _cached_records(
        f"rag_history:{filters}",
        rag_response_service.response_index_json_path(),
        lambda: rag_response_service.read_history(filters),
    )


def reasoning_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    return _cached_records(
        f"reasoning_history:{filters}",
        reasoning_output_service.index_json_path(),
        lambda: reasoning_output_service.read_history(filters),
    )


def risk_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    return _cached_records(
        f"risk_history:{filters}",
        risk_output_service.index_json_path(),
        lambda: risk_output_service.read_history(filters),
    )


def explainability_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    return _cached_records(
        f"explainability_history:{filters}",
        explainability_output_service.index_json_path(),
        lambda: explainability_output_service.read_history(filters),
    )


def agent_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    return _cached_records(
        f"agent_history:{filters}",
        agent_output_service.index_json_path(),
        lambda: agent_output_service.read_history(filters),
    )
