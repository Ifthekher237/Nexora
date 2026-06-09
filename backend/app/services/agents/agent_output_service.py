"""Persistent storage for multi-agent workflow outputs."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.app.core.config import PROJECT_ROOT, get_agents_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ingestion.storage_service import project_relative_path, safe_filename


INDEX_FIELDS = [
    "agent_run_id",
    "created_at",
    "scenario",
    "company_name",
    "ticker",
    "market",
    "agents_run",
    "overall_confidence_level",
    "overall_confidence_score",
    "status",
    "response_path",
    "error_message",
]


class AgentOutputStorageError(RuntimeError):
    """Raised when agent output persistence fails."""


def _config() -> dict[str, Any]:
    return get_agents_config().get("agents", {})


def save_enabled() -> bool:
    return bool(_config().get("save_agent_outputs", True))


def output_dir() -> Path:
    return PROJECT_ROOT / _config().get("output_dir", "data/agent_outputs/runs")


def index_csv_path() -> Path:
    return PROJECT_ROOT / _config().get("index_csv", "data/agent_outputs/agent_run_index.csv")


def index_json_path() -> Path:
    return PROJECT_ROOT / _config().get("index_json", "data/agent_outputs/agent_run_index.json")


def ensure_storage() -> None:
    output_dir().mkdir(parents=True, exist_ok=True)
    index_csv_path().parent.mkdir(parents=True, exist_ok=True)
    if not index_csv_path().exists():
        with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
            writer.writeheader()
    if not index_json_path().exists():
        index_json_path().write_text("[]", encoding="utf-8")


def generate_agent_run_id(scenario: str) -> str:
    timestamp = utc_now_iso().replace("+00:00", "Z").replace(":", "").replace("-", "")
    digest = hashlib.sha1(scenario.encode("utf-8")).hexdigest()[:8]
    nonce = uuid4().hex[:8]
    return safe_filename(f"AGENT_RUN_{timestamp}_{digest}_{nonce}")


def _read_index() -> list[dict[str, Any]]:
    ensure_storage()
    try:
        data = json.loads(index_json_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AgentOutputStorageError(f"Agent run index JSON is malformed: {exc}") from exc
    if not isinstance(data, list):
        raise AgentOutputStorageError("Agent run index JSON must contain a list.")
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


def _index_record(output: dict[str, Any], path: Path) -> dict[str, Any]:
    confidence = output.get("overall_confidence") or {}
    return {
        "agent_run_id": output.get("agent_run_id", ""),
        "created_at": output.get("created_at", ""),
        "scenario": output.get("scenario", ""),
        "company_name": output.get("company_name", ""),
        "ticker": output.get("ticker", ""),
        "market": output.get("market", ""),
        "agents_run": ",".join(output.get("agents_run", [])),
        "overall_confidence_level": confidence.get("level", ""),
        "overall_confidence_score": confidence.get("score", 0.0),
        "status": output.get("status", ""),
        "response_path": project_relative_path(path),
        "error_message": output.get("error_message", ""),
    }


def save_output(output: dict[str, Any]) -> dict[str, Any]:
    if not save_enabled():
        return {"saved": False, "response_path": ""}
    ensure_storage()
    agent_run_id = str(output.get("agent_run_id") or generate_agent_run_id(output.get("scenario", "")))
    output["agent_run_id"] = agent_run_id
    path = output_dir() / f"{safe_filename(agent_run_id)}.json"
    try:
        path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
        records = [record for record in _read_index() if record.get("agent_run_id") != agent_run_id]
        records.append(_index_record(output, path))
        _write_index(records)
    except OSError as exc:
        raise AgentOutputStorageError(f"Could not save agent output: {exc}") from exc
    return {"saved": True, "response_path": project_relative_path(path)}


def read_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    records = _read_index()
    filters = filters or {}
    for key in ["status", "ticker"]:
        value = filters.get(key)
        if value:
            records = [record for record in records if str(record.get(key, "")).lower() == str(value).lower()]
    agent_name = filters.get("agent_name")
    if agent_name:
        records = [record for record in records if agent_name.lower() in str(record.get("agents_run", "")).lower()]
    confidence_level = filters.get("confidence_level")
    if confidence_level:
        records = [
            record
            for record in records
            if str(record.get("overall_confidence_level", "")).lower() == confidence_level.lower()
        ]
    return sorted(records, key=lambda item: item.get("created_at", ""), reverse=True)


def read_output(agent_run_id: str) -> dict[str, Any] | None:
    clean_id = agent_run_id.strip()
    for record in _read_index():
        if record.get("agent_run_id") != clean_id:
            continue
        path = PROJECT_ROOT / str(record.get("response_path", ""))
        if not path.exists():
            raise AgentOutputStorageError(f"Agent output body is missing for {clean_id}.")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AgentOutputStorageError(f"Agent output file is malformed: {exc}") from exc
        return data if isinstance(data, dict) else None
    return None


def output_count() -> int:
    return len(_read_index())
