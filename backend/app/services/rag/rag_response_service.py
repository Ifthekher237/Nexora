"""Persistent storage for RAG responses and response history."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_rag_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ingestion.storage_service import project_relative_path, safe_filename


INDEX_FIELDS = [
    "response_id",
    "created_at",
    "question",
    "model",
    "ticker",
    "confidence_level",
    "confidence_score",
    "source_count",
    "status",
    "response_path",
    "error_message",
]


class RAGResponseStorageError(RuntimeError):
    """Raised when RAG output persistence fails."""


def _rag_config() -> dict[str, Any]:
    return get_rag_config().get("rag", {})


def save_enabled() -> bool:
    return bool(_rag_config().get("save_rag_outputs", True))


def response_output_dir() -> Path:
    return PROJECT_ROOT / _rag_config().get(
        "response_output_dir",
        "data/rag_outputs/responses",
    )


def response_index_csv_path() -> Path:
    return PROJECT_ROOT / _rag_config().get(
        "response_index_csv",
        "data/rag_outputs/rag_response_index.csv",
    )


def response_index_json_path() -> Path:
    return PROJECT_ROOT / _rag_config().get(
        "response_index_json",
        "data/rag_outputs/rag_response_index.json",
    )


def ensure_response_storage() -> None:
    response_output_dir().mkdir(parents=True, exist_ok=True)
    response_index_csv_path().parent.mkdir(parents=True, exist_ok=True)
    response_index_json_path().parent.mkdir(parents=True, exist_ok=True)
    if not response_index_csv_path().exists():
        with response_index_csv_path().open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
            writer.writeheader()
    if not response_index_json_path().exists():
        response_index_json_path().write_text("[]", encoding="utf-8")


def generate_response_id(question: str) -> str:
    timestamp = utc_now_iso().replace(":", "").replace("+", "Z").replace("-", "")
    digest = hashlib.sha1(question.encode("utf-8")).hexdigest()[:8]
    return safe_filename(f"RAG_{timestamp}_{digest}")


def _read_json_index() -> list[dict[str, Any]]:
    ensure_response_storage()
    try:
        data = json.loads(response_index_json_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RAGResponseStorageError(f"RAG response index is malformed: {exc}") from exc
    if not isinstance(data, list):
        raise RAGResponseStorageError("RAG response index JSON must contain a list.")
    return [record for record in data if isinstance(record, dict)]


def _write_indexes(records: list[dict[str, Any]]) -> None:
    ensure_response_storage()
    normalized_records = [
        {
            field: "" if record.get(field) is None else str(record.get(field, ""))
            for field in INDEX_FIELDS
        }
        for record in records
    ]
    with response_index_csv_path().open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(normalized_records)
    response_index_json_path().write_text(
        json.dumps(normalized_records, indent=2),
        encoding="utf-8",
    )


def _index_record(response: dict[str, Any], response_path: Path) -> dict[str, Any]:
    confidence = response.get("confidence") or {}
    filters = response.get("filters") or {}
    if not isinstance(filters, dict):
        filters = {}
    sources = response.get("sources") or []
    return {
        "response_id": response.get("response_id", ""),
        "created_at": response.get("created_at", ""),
        "question": response.get("question", ""),
        "model": response.get("model", ""),
        "ticker": filters.get("ticker", ""),
        "confidence_level": confidence.get("level", ""),
        "confidence_score": confidence.get("score", 0.0),
        "source_count": len(sources) if isinstance(sources, list) else 0,
        "status": response.get("status", ""),
        "response_path": project_relative_path(response_path),
        "error_message": response.get("error_message", ""),
    }


def _coerce_history_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    if normalized.get("confidence_score") in {None, ""}:
        normalized["confidence_score"] = 0.0
    if normalized.get("source_count") in {None, ""}:
        normalized["source_count"] = 0
    if normalized.get("ticker") is None:
        normalized["ticker"] = ""
    return normalized


def save_response(response: dict[str, Any]) -> dict[str, Any]:
    if not save_enabled():
        return {"saved": False, "response_path": ""}

    ensure_response_storage()
    response_id = str(response.get("response_id") or generate_response_id(response.get("question", "")))
    response["response_id"] = response_id
    response_path = response_output_dir() / f"{safe_filename(response_id)}.json"

    try:
        response_path.write_text(
            json.dumps(response, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        records = _read_json_index()
        new_record = _index_record(response, response_path)
        records = [record for record in records if record.get("response_id") != response_id]
        records.append(new_record)
        _write_indexes(records)
    except OSError as exc:
        raise RAGResponseStorageError(f"Could not save RAG response: {exc}") from exc

    return {"saved": True, "response_path": project_relative_path(response_path)}


def read_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    records = [_coerce_history_record(record) for record in _read_json_index()]
    filters = filters or {}
    filtered = records
    for key in ["ticker", "model", "confidence_level", "status"]:
        value = filters.get(key)
        if value:
            filtered = [
                record
                for record in filtered
                if str(record.get(key, "")).lower() == str(value).lower()
            ]
    return sorted(filtered, key=lambda item: item.get("created_at", ""), reverse=True)


def read_response(response_id: str) -> dict[str, Any] | None:
    clean_id = response_id.strip()
    if not clean_id:
        return None
    for record in _read_json_index():
        if record.get("response_id") != clean_id:
            continue
        response_path = PROJECT_ROOT / str(record.get("response_path", ""))
        if not response_path.exists():
            raise RAGResponseStorageError(
                f"RAG response body is missing for response_id={clean_id}."
            )
        try:
            data = json.loads(response_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RAGResponseStorageError(f"RAG response file is malformed: {exc}") from exc
        return data if isinstance(data, dict) else None
    return None
