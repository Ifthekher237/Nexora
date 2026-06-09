"""Safe response caches for retrieval, status summaries, and history tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.services.performance import cache_service
from backend.app.services.retrieval import retrieval_metadata_service


def _file_signature(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
        return {"path": str(path), "mtime": stat.st_mtime, "size": stat.st_size}
    except OSError:
        return {"path": str(path), "mtime": 0.0, "size": 0}


def retrieval_key(query: str, top_k: int, vector_store: str, filters: dict[str, Any] | None) -> str:
    return cache_service.make_cache_key(
        {
            "query": query.strip(),
            "top_k": int(top_k),
            "vector_store": vector_store.lower(),
            "filters": filters or {},
            "vector_index": _file_signature(retrieval_metadata_service.vector_csv_path()),
        },
        prefix="retrieval",
    )


def get_retrieval_result(query: str, top_k: int, vector_store: str, filters: dict[str, Any] | None) -> dict[str, Any] | None:
    cached = cache_service.get("retrieval", retrieval_key(query, top_k, vector_store, filters))
    return cached if isinstance(cached, dict) else None


def set_retrieval_result(query: str, top_k: int, vector_store: str, filters: dict[str, Any] | None, result: dict[str, Any]) -> bool:
    if result.get("status") == "error":
        return False
    return cache_service.set(
        "retrieval",
        retrieval_key(query, top_k, vector_store, filters),
        result,
        ttl_seconds=cache_service.namespace_ttl("retrieval"),
    )


def status_key(name: str, payload: dict[str, Any] | None = None) -> str:
    return cache_service.make_cache_key({"name": name, "payload": payload or {}}, prefix="status")


def get_status(name: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    cached = cache_service.get("status", status_key(name, payload))
    return cached if isinstance(cached, dict) else None


def set_status(name: str, value: dict[str, Any], payload: dict[str, Any] | None = None, ttl_seconds: int = 15) -> bool:
    if value.get("status") == "error":
        return False
    return cache_service.set("status", status_key(name, payload), value, ttl_seconds=ttl_seconds)


def history_key(name: str, filters: dict[str, Any] | None = None) -> str:
    return cache_service.make_cache_key({"name": name, "filters": filters or {}}, prefix="history")


def get_history(name: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]] | None:
    cached = cache_service.get("response", history_key(name, filters))
    return cached if isinstance(cached, list) else None


def set_history(name: str, rows: list[dict[str, Any]], filters: dict[str, Any] | None = None, ttl_seconds: int = 30) -> bool:
    return cache_service.set("response", history_key(name, filters), rows, ttl_seconds=ttl_seconds)
