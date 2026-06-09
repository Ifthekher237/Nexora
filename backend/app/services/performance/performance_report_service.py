"""Persistent storage for Phase 11 performance benchmark reports."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.app.core.config import PROJECT_ROOT, get_performance_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ingestion.storage_service import project_relative_path, safe_filename


INDEX_FIELDS = [
    "benchmark_id",
    "started_at",
    "completed_at",
    "total_runtime_ms",
    "query_count",
    "scenario_count",
    "include_rag",
    "include_reasoning",
    "include_agents",
    "status",
    "report_path",
    "error_message",
]


class PerformanceReportStorageError(RuntimeError):
    """Raised when performance report storage cannot be read or written."""


def _performance_config() -> dict[str, Any]:
    return get_performance_config().get("performance", {})


def save_enabled() -> bool:
    return bool(_performance_config().get("save_benchmark_results", True))


def output_dir() -> Path:
    return PROJECT_ROOT / _performance_config().get("output_dir", "data/performance_outputs/benchmark_runs")


def index_csv_path() -> Path:
    return PROJECT_ROOT / _performance_config().get("index_csv", "data/performance_outputs/performance_index.csv")


def index_json_path() -> Path:
    return PROJECT_ROOT / _performance_config().get("index_json", "data/performance_outputs/performance_index.json")


def ensure_storage() -> None:
    output_dir().mkdir(parents=True, exist_ok=True)
    index_csv_path().parent.mkdir(parents=True, exist_ok=True)
    if not index_csv_path().exists():
        with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=INDEX_FIELDS).writeheader()
    if not index_json_path().exists():
        index_json_path().write_text("[]", encoding="utf-8")


def generate_benchmark_id(payload: Any) -> str:
    timestamp = utc_now_iso().replace("+00:00", "Z").replace(":", "").replace("-", "")
    digest = hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:8]
    return safe_filename(f"PERF_{timestamp}_{digest}_{uuid4().hex[:8]}")


def _read_index() -> list[dict[str, Any]]:
    ensure_storage()
    try:
        data = json.loads(index_json_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PerformanceReportStorageError(f"Performance index JSON is malformed: {exc}") from exc
    if not isinstance(data, list):
        raise PerformanceReportStorageError("Performance index JSON must contain a list.")
    return [record for record in data if isinstance(record, dict)]


def _write_index(records: list[dict[str, Any]]) -> None:
    normalized = [
        {field: "" if record.get(field) is None else str(record.get(field, "")) for field in INDEX_FIELDS}
        for record in records
    ]
    with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(normalized)
    index_json_path().write_text(json.dumps(normalized, indent=2), encoding="utf-8")


def _index_record(report: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "benchmark_id": report.get("benchmark_id", ""),
        "started_at": report.get("started_at", ""),
        "completed_at": report.get("completed_at", ""),
        "total_runtime_ms": report.get("total_runtime_ms", 0.0),
        "query_count": len(report.get("queries", [])),
        "scenario_count": len(report.get("scenarios", [])),
        "include_rag": bool(report.get("include_rag", False)),
        "include_reasoning": bool(report.get("include_reasoning", False)),
        "include_agents": bool(report.get("include_agents", False)),
        "status": report.get("status", ""),
        "report_path": project_relative_path(path),
        "error_message": report.get("error_message", ""),
    }


def save_report(report: dict[str, Any]) -> dict[str, Any]:
    if not save_enabled():
        return {"saved": False, "report_path": ""}
    ensure_storage()
    benchmark_id = str(report.get("benchmark_id") or generate_benchmark_id(report))
    report["benchmark_id"] = benchmark_id
    path = output_dir() / f"{safe_filename(benchmark_id)}.json"
    try:
        path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
        records = [record for record in _read_index() if record.get("benchmark_id") != benchmark_id]
        records.append(_index_record(report, path))
        _write_index(records)
    except OSError as exc:
        raise PerformanceReportStorageError(f"Could not save performance report: {exc}") from exc
    return {"saved": True, "report_path": project_relative_path(path)}


def read_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    records = _read_index()
    filters = filters or {}
    status = filters.get("status")
    if status:
        records = [record for record in records if str(record.get("status", "")).lower() == status.lower()]
    return sorted(records, key=lambda item: item.get("started_at", ""), reverse=True)


def read_report(benchmark_id: str) -> dict[str, Any] | None:
    clean_id = benchmark_id.strip()
    for record in _read_index():
        if record.get("benchmark_id") != clean_id:
            continue
        path = PROJECT_ROOT / str(record.get("report_path", ""))
        if not path.exists():
            raise PerformanceReportStorageError(f"Performance report body is missing for {clean_id}.")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PerformanceReportStorageError(f"Performance report file is malformed: {exc}") from exc
        return data if isinstance(data, dict) else None
    return None


def output_count() -> int:
    return len(_read_index())
