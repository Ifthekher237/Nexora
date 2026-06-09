"""Persistent storage for Phase 6 reasoning outputs."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_reasoning_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ingestion.storage_service import project_relative_path, safe_filename


INDEX_FIELDS = [
    "reasoning_id",
    "created_at",
    "scenario",
    "company_name",
    "ticker",
    "market",
    "scenario_type",
    "model",
    "confidence_level",
    "confidence_score",
    "status",
    "response_path",
    "error_message",
]


class ReasoningOutputStorageError(RuntimeError):
    """Raised when reasoning outputs cannot be stored or loaded."""


def _config() -> dict[str, Any]:
    return get_reasoning_config().get("reasoning", {})


def save_enabled() -> bool:
    return bool(_config().get("save_reasoning_outputs", True))


def output_dir() -> Path:
    return PROJECT_ROOT / _config().get("output_dir", "data/reasoning_outputs/responses")


def index_csv_path() -> Path:
    return PROJECT_ROOT / _config().get("index_csv", "data/reasoning_outputs/reasoning_index.csv")


def index_json_path() -> Path:
    return PROJECT_ROOT / _config().get("index_json", "data/reasoning_outputs/reasoning_index.json")


def ensure_storage() -> None:
    output_dir().mkdir(parents=True, exist_ok=True)
    index_csv_path().parent.mkdir(parents=True, exist_ok=True)
    if not index_csv_path().exists():
        with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
            writer.writeheader()
    if not index_json_path().exists():
        index_json_path().write_text("[]", encoding="utf-8")


def generate_reasoning_id(scenario: str) -> str:
    timestamp = utc_now_iso().replace(":", "").replace("+", "Z").replace("-", "")
    digest = hashlib.sha1(scenario.encode("utf-8")).hexdigest()[:8]
    return safe_filename(f"REASON_{timestamp}_{digest}")


def _read_index() -> list[dict[str, Any]]:
    ensure_storage()
    try:
        data = json.loads(index_json_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReasoningOutputStorageError(f"Reasoning index JSON is malformed: {exc}") from exc
    if not isinstance(data, list):
        raise ReasoningOutputStorageError("Reasoning index JSON must contain a list.")
    return [record for record in data if isinstance(record, dict)]


def _coerce_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    if normalized.get("confidence_score") in {None, ""}:
        normalized["confidence_score"] = 0.0
    for field in ["company_name", "ticker", "market", "error_message"]:
        if normalized.get(field) is None:
            normalized[field] = ""
    return normalized


def _write_index(records: list[dict[str, Any]]) -> None:
    normalized_records = [
        {
            field: "" if record.get(field) is None else str(record.get(field, ""))
            for field in INDEX_FIELDS
        }
        for record in records
    ]
    with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(normalized_records)
    index_json_path().write_text(json.dumps(normalized_records, indent=2), encoding="utf-8")


def _index_record(output: dict[str, Any], response_path: Path) -> dict[str, Any]:
    confidence = output.get("confidence") or {}
    return {
        "reasoning_id": output.get("reasoning_id", ""),
        "created_at": output.get("created_at", ""),
        "scenario": output.get("scenario", ""),
        "company_name": output.get("company_name", ""),
        "ticker": output.get("ticker", ""),
        "market": output.get("market", ""),
        "scenario_type": output.get("scenario_type", ""),
        "model": output.get("model", ""),
        "confidence_level": confidence.get("level", ""),
        "confidence_score": confidence.get("score", 0.0),
        "status": output.get("status", ""),
        "response_path": project_relative_path(response_path),
        "error_message": output.get("error_message", ""),
    }


def save_output(output: dict[str, Any]) -> dict[str, Any]:
    if not save_enabled():
        return {"saved": False, "response_path": ""}
    ensure_storage()
    reasoning_id = str(output.get("reasoning_id") or generate_reasoning_id(output.get("scenario", "")))
    output["reasoning_id"] = reasoning_id
    response_path = output_dir() / f"{safe_filename(reasoning_id)}.json"
    try:
        response_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
        records = [record for record in _read_index() if record.get("reasoning_id") != reasoning_id]
        records.append(_index_record(output, response_path))
        _write_index(records)
    except OSError as exc:
        raise ReasoningOutputStorageError(f"Could not save reasoning output: {exc}") from exc
    return {"saved": True, "response_path": project_relative_path(response_path)}


def read_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    records = [_coerce_record(record) for record in _read_index()]
    filters = filters or {}
    for key in ["ticker", "market", "scenario_type", "confidence_level", "status"]:
        value = filters.get(key)
        if value:
            records = [
                record
                for record in records
                if str(record.get(key, "")).lower() == str(value).lower()
            ]
    return sorted(records, key=lambda item: item.get("created_at", ""), reverse=True)


def read_output(reasoning_id: str) -> dict[str, Any] | None:
    clean_id = reasoning_id.strip()
    for record in _read_index():
        if record.get("reasoning_id") != clean_id:
            continue
        response_path = PROJECT_ROOT / str(record.get("response_path", ""))
        if not response_path.exists():
            raise ReasoningOutputStorageError(f"Reasoning output body is missing for {clean_id}.")
        try:
            data = json.loads(response_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ReasoningOutputStorageError(f"Reasoning output file is malformed: {exc}") from exc
        return data if isinstance(data, dict) else None
    return None


def output_count() -> int:
    return len(_read_index())
