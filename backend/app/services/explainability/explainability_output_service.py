"""Persistent storage for Phase 8 explainability reports."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_explainability_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ingestion.storage_service import project_relative_path, safe_filename


INDEX_FIELDS = [
    "explainability_id",
    "created_at",
    "target_type",
    "target_id",
    "coverage_level",
    "coverage_score",
    "explainability_score",
    "status",
    "report_path",
    "error_message",
]


class ExplainabilityOutputStorageError(RuntimeError):
    """Raised when explainability report persistence fails."""


def _config() -> dict[str, Any]:
    return get_explainability_config().get("explainability", {})


def save_enabled() -> bool:
    return bool(_config().get("save_reports", True))


def output_dir() -> Path:
    return PROJECT_ROOT / _config().get("output_dir", "data/explainability_outputs/reports")


def index_csv_path() -> Path:
    return PROJECT_ROOT / _config().get("index_csv", "data/explainability_outputs/explainability_index.csv")


def index_json_path() -> Path:
    return PROJECT_ROOT / _config().get("index_json", "data/explainability_outputs/explainability_index.json")


def ensure_storage() -> None:
    output_dir().mkdir(parents=True, exist_ok=True)
    index_csv_path().parent.mkdir(parents=True, exist_ok=True)
    if not index_csv_path().exists():
        with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
            writer.writeheader()
    if not index_json_path().exists():
        index_json_path().write_text("[]", encoding="utf-8")


def generate_explainability_id(target_type: str, target_id: str) -> str:
    timestamp = utc_now_iso().replace(":", "").replace("+", "Z").replace("-", "")
    digest = hashlib.sha1(f"{target_type}:{target_id}".encode("utf-8")).hexdigest()[:8]
    return safe_filename(f"EXPLAIN_{timestamp}_{target_type}_{digest}")


def _read_index() -> list[dict[str, Any]]:
    ensure_storage()
    try:
        data = json.loads(index_json_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExplainabilityOutputStorageError(f"Explainability index JSON is malformed: {exc}") from exc
    if not isinstance(data, list):
        raise ExplainabilityOutputStorageError("Explainability index JSON must contain a list.")
    return [record for record in data if isinstance(record, dict)]


def _coerce(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    for field in ["coverage_score", "explainability_score"]:
        if normalized.get(field) in {None, ""}:
            normalized[field] = 0.0
    return normalized


def _write_index(records: list[dict[str, Any]]) -> None:
    normalized_records = [
        {field: "" if record.get(field) is None else str(record.get(field, "")) for field in INDEX_FIELDS}
        for record in records
    ]
    with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(normalized_records)
    index_json_path().write_text(json.dumps(normalized_records, indent=2), encoding="utf-8")


def _index_record(report: dict[str, Any], path: Path) -> dict[str, Any]:
    coverage = report.get("evidence_coverage") or {}
    return {
        "explainability_id": report.get("explainability_id", ""),
        "created_at": report.get("created_at", ""),
        "target_type": report.get("target_type", ""),
        "target_id": report.get("target_id", ""),
        "coverage_level": coverage.get("level", ""),
        "coverage_score": coverage.get("score", 0.0),
        "explainability_score": report.get("explainability_score", 0.0),
        "status": report.get("status", ""),
        "report_path": project_relative_path(path),
        "error_message": report.get("error_message", ""),
    }


def save_report(report: dict[str, Any]) -> dict[str, Any]:
    if not save_enabled():
        return {"saved": False, "report_path": ""}
    ensure_storage()
    explainability_id = str(
        report.get("explainability_id")
        or generate_explainability_id(report.get("target_type", "unknown"), report.get("target_id", "unknown"))
    )
    report["explainability_id"] = explainability_id
    path = output_dir() / f"{safe_filename(explainability_id)}.json"
    try:
        path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        records = [record for record in _read_index() if record.get("explainability_id") != explainability_id]
        records.append(_index_record(report, path))
        _write_index(records)
    except OSError as exc:
        raise ExplainabilityOutputStorageError(f"Could not save explainability report: {exc}") from exc
    return {"saved": True, "report_path": project_relative_path(path)}


def read_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    records = [_coerce(record) for record in _read_index()]
    filters = filters or {}
    for key in ["target_type", "status", "coverage_level"]:
        value = filters.get(key)
        if value:
            records = [record for record in records if str(record.get(key, "")).lower() == str(value).lower()]
    return sorted(records, key=lambda item: item.get("created_at", ""), reverse=True)


def read_report(explainability_id: str) -> dict[str, Any] | None:
    clean_id = explainability_id.strip()
    for record in _read_index():
        if record.get("explainability_id") != clean_id:
            continue
        path = PROJECT_ROOT / str(record.get("report_path", ""))
        if not path.exists():
            raise ExplainabilityOutputStorageError(f"Explainability report body is missing for {clean_id}.")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ExplainabilityOutputStorageError(f"Explainability report file is malformed: {exc}") from exc
        return data if isinstance(data, dict) else None
    return None


def output_count() -> int:
    return len(_read_index())
