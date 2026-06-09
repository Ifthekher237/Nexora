"""Processing metadata index management."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.config import PROJECT_ROOT, get_processing_config


PROCESSING_METADATA_FIELDS = [
    "processed_document_id",
    "source_document_id",
    "source_type",
    "source_name",
    "company_name",
    "ticker",
    "market",
    "document_type",
    "source_local_path",
    "processed_text_path",
    "chunk_file_path",
    "file_format",
    "processing_status",
    "processing_error",
    "processed_at",
    "published_at",
    "period",
    "text_length",
    "word_count",
    "chunk_count",
    "language",
    "detected_document_category",
    "content_hash",
    "notes",
]


def processing_root() -> Path:
    root = get_processing_config().get("processing", {}).get("processed_root", "data/processed")
    return PROJECT_ROOT / root


def documents_dir() -> Path:
    path = get_processing_config().get("processing", {}).get(
        "documents_dir", "data/processed/documents"
    )
    return PROJECT_ROOT / path


def chunks_dir() -> Path:
    path = get_processing_config().get("processing", {}).get("chunks_dir", "data/processed/chunks")
    return PROJECT_ROOT / path


def metadata_dir() -> Path:
    path = get_processing_config().get("processing", {}).get(
        "metadata_dir", "data/processed/processing_metadata"
    )
    return PROJECT_ROOT / path


def ensure_processing_directories() -> None:
    documents_dir().mkdir(parents=True, exist_ok=True)
    chunks_dir().mkdir(parents=True, exist_ok=True)
    metadata_dir().mkdir(parents=True, exist_ok=True)


def processing_csv_path() -> Path:
    return metadata_dir() / "processing_index.csv"


def processing_json_path() -> Path:
    return metadata_dir() / "processing_index.json"


def empty_processing_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=PROCESSING_METADATA_FIELDS)


def ensure_processing_index() -> None:
    ensure_processing_directories()
    if not processing_csv_path().exists():
        empty_processing_frame().to_csv(processing_csv_path(), index=False)
    if not processing_json_path().exists():
        processing_json_path().write_text("[]", encoding="utf-8")


def read_processing_metadata() -> pd.DataFrame:
    ensure_processing_index()
    if processing_csv_path().stat().st_size == 0:
        return empty_processing_frame()

    frame = pd.read_csv(processing_csv_path(), dtype=str).fillna("")
    for field in PROCESSING_METADATA_FIELDS:
        if field not in frame.columns:
            frame[field] = ""
    return frame[PROCESSING_METADATA_FIELDS]


def write_processing_metadata(frame: pd.DataFrame) -> None:
    ensure_processing_index()
    normalized = frame.copy()
    for field in PROCESSING_METADATA_FIELDS:
        if field not in normalized.columns:
            normalized[field] = ""
    normalized = normalized[PROCESSING_METADATA_FIELDS].fillna("")
    normalized.to_csv(processing_csv_path(), index=False)
    normalized.to_json(processing_json_path(), orient="records", indent=2)


def normalize_processing_record(record: dict[str, Any]) -> dict[str, str]:
    return {field: str(record.get(field, "") or "") for field in PROCESSING_METADATA_FIELDS}


def find_processed_by_source(source_document_id: str) -> dict[str, str] | None:
    frame = read_processing_metadata()
    if frame.empty:
        return None
    matches = frame[frame["source_document_id"] == source_document_id]
    if matches.empty:
        return None
    return matches.iloc[-1].fillna("").to_dict()


def append_processing_metadata(
    record: dict[str, Any],
    reprocess: bool = False,
) -> dict[str, Any]:
    normalized = normalize_processing_record(record)
    frame = read_processing_metadata()

    duplicate_mask = (
        (frame["processed_document_id"] == normalized["processed_document_id"])
        | (frame["source_document_id"] == normalized["source_document_id"])
    )
    if duplicate_mask.any():
        if not reprocess:
            existing = frame[duplicate_mask].iloc[-1].fillna("").to_dict()
            return {
                "record": existing,
                "created": False,
                "duplicate": True,
                "message": "Processed document already exists.",
            }

        frame = frame[~duplicate_mask]

    updated = pd.concat([frame, pd.DataFrame([normalized])], ignore_index=True)
    write_processing_metadata(updated)
    return {
        "record": normalized,
        "created": True,
        "duplicate": False,
        "message": "Processing metadata record saved.",
    }


def filter_processing_metadata(filters: dict[str, str | None]) -> list[dict[str, str]]:
    frame = read_processing_metadata()
    for field, value in filters.items():
        if value and field in frame.columns:
            frame = frame[frame[field].str.lower() == value.lower()]
    return frame.fillna("").to_dict(orient="records")


def processing_summary() -> dict[str, Any]:
    frame = read_processing_metadata()
    if frame.empty:
        return {
            "total_processed_documents": 0,
            "total_chunks": 0,
            "documents_by_source_type": {},
            "documents_by_document_type": {},
            "documents_by_processing_status": {},
            "latest_processed_time": "",
        }

    chunk_total = pd.to_numeric(frame["chunk_count"], errors="coerce").fillna(0).astype(int).sum()
    return {
        "total_processed_documents": int(len(frame)),
        "total_chunks": int(chunk_total),
        "documents_by_source_type": frame["source_type"].value_counts().to_dict(),
        "documents_by_document_type": frame["document_type"].value_counts().to_dict(),
        "documents_by_processing_status": frame["processing_status"].value_counts().to_dict(),
        "latest_processed_time": str(frame["processed_at"].max()),
    }
