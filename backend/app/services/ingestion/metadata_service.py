"""Metadata index management for ingested documents."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.services.ingestion.storage_service import ensure_storage_directories, metadata_root
from backend.app.services.ingestion.validation_service import (
    REQUIRED_METADATA_FIELDS,
    validate_required_metadata,
)


logger = logging.getLogger(__name__)

CSV_INDEX_NAME = "ingestion_index.csv"
JSON_INDEX_NAME = "ingestion_index.json"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def csv_index_path() -> Path:
    return metadata_root() / CSV_INDEX_NAME


def json_index_path() -> Path:
    return metadata_root() / JSON_INDEX_NAME


def empty_metadata_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=REQUIRED_METADATA_FIELDS)


def ensure_metadata_index() -> None:
    ensure_storage_directories()
    if not csv_index_path().exists():
        empty_metadata_frame().to_csv(csv_index_path(), index=False)
    if not json_index_path().exists():
        json_index_path().write_text("[]", encoding="utf-8")


def read_metadata() -> pd.DataFrame:
    ensure_metadata_index()
    if csv_index_path().stat().st_size == 0:
        return empty_metadata_frame()

    frame = pd.read_csv(csv_index_path(), dtype=str).fillna("")
    for field in REQUIRED_METADATA_FIELDS:
        if field not in frame.columns:
            frame[field] = ""
    return frame[REQUIRED_METADATA_FIELDS]


def write_metadata(frame: pd.DataFrame) -> None:
    ensure_metadata_index()
    normalized = frame.copy()
    for field in REQUIRED_METADATA_FIELDS:
        if field not in normalized.columns:
            normalized[field] = ""

    normalized = normalized[REQUIRED_METADATA_FIELDS].fillna("")
    normalized.to_csv(csv_index_path(), index=False)
    normalized.to_json(json_index_path(), orient="records", indent=2)
    logger.info("Metadata index updated with %s records", len(normalized))


def _duplicate_mask(frame: pd.DataFrame, record: dict[str, Any]) -> pd.Series:
    mask = pd.Series(False, index=frame.index)
    for field in ["document_id", "source_url", "content_hash"]:
        value = str(record.get(field, "") or "")
        if value:
            mask = mask | (frame[field].fillna("") == value)
    return mask


def find_duplicate_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """Find an existing metadata record by document ID, source URL, or hash."""

    frame = read_metadata()
    if frame.empty:
        return None

    duplicate_mask = _duplicate_mask(frame, record)
    if not duplicate_mask.any():
        return None

    return frame[duplicate_mask].iloc[0].fillna("").to_dict()


def append_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Append one metadata record unless it already exists.

    Duplicate checks use document ID, source URL, and content hash. When a
    duplicate is found, blank fields on the existing record are filled from the
    new record, but the document is not stored again.
    """

    normalized = validate_required_metadata(record)
    frame = read_metadata()

    duplicate_mask = _duplicate_mask(frame, normalized)
    if duplicate_mask.any():
        duplicate_index = frame[duplicate_mask].index[0]
        updated = False
        for field in REQUIRED_METADATA_FIELDS:
            existing_value = str(frame.at[duplicate_index, field] or "")
            new_value = str(normalized.get(field, "") or "")
            if not existing_value and new_value:
                frame.at[duplicate_index, field] = new_value
                updated = True

        if updated:
            write_metadata(frame)
        logger.info("Duplicate ingestion skipped for %s", normalized["document_id"])
        return {
            "record": frame.loc[duplicate_index].to_dict(),
            "created": False,
            "duplicate": True,
            "message": "Duplicate document skipped.",
        }

    updated_frame = pd.concat([frame, pd.DataFrame([normalized])], ignore_index=True)
    write_metadata(updated_frame)
    return {
        "record": normalized,
        "created": True,
        "duplicate": False,
        "message": "Metadata record added.",
    }


def filter_metadata(filters: dict[str, str | None]) -> list[dict[str, str]]:
    frame = read_metadata()
    for field, value in filters.items():
        if value and field in frame.columns:
            frame = frame[frame[field].str.lower() == value.lower()]
    return frame.fillna("").to_dict(orient="records")


def metadata_status() -> dict[str, Any]:
    frame = read_metadata()
    return {
        "csv_index": str(csv_index_path()),
        "json_index": str(json_index_path()),
        "exists": csv_index_path().exists() and json_index_path().exists(),
        "document_count": int(len(frame)),
    }


def summary_statistics() -> dict[str, Any]:
    frame = read_metadata()
    if frame.empty:
        return {
            "total_documents": 0,
            "documents_by_source_type": {},
            "documents_by_status": {},
            "latest_ingestion_time": "",
            "top_companies": {},
            "top_tickers": {},
        }

    return {
        "total_documents": int(len(frame)),
        "documents_by_source_type": frame["source_type"].value_counts().to_dict(),
        "documents_by_status": frame["status"].value_counts().to_dict(),
        "latest_ingestion_time": str(frame["ingested_at"].max()),
        "top_companies": frame["company_name"].replace("", pd.NA).dropna().value_counts().head(10).to_dict(),
        "top_tickers": frame["ticker"].replace("", pd.NA).dropna().value_counts().head(10).to_dict(),
    }
