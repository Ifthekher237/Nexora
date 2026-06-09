"""Validation helpers for ingestion requests and metadata records."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_ingestion_config


REQUIRED_METADATA_FIELDS = [
    "document_id",
    "source_type",
    "source_name",
    "company_name",
    "ticker",
    "market",
    "document_type",
    "title",
    "source_url",
    "local_path",
    "file_format",
    "ingested_at",
    "published_at",
    "period",
    "status",
    "error_message",
    "content_hash",
    "notes",
]

COMMON_DOCUMENT_TYPES = {
    "10-k",
    "10-q",
    "8-k",
    "sec_filing_metadata",
    "annual_report",
    "quarterly_report",
    "earnings_transcript",
    "rss_item",
    "news",
    "macro_dataset",
    "asx_announcement",
}


class IngestionValidationError(ValueError):
    """Raised when an ingestion request is not valid."""


def validate_limit(limit: int | None) -> int:
    config = get_ingestion_config()
    max_limit = int(config.get("ingestion", {}).get("max_documents_per_run", 10))
    requested = 1 if limit is None else int(limit)

    if requested < 1:
        raise IngestionValidationError("Limit must be at least 1.")
    if requested > max_limit:
        raise IngestionValidationError(f"Limit cannot exceed {max_limit}.")

    return requested


def validate_source_type(source_type: str) -> str:
    normalized = source_type.strip().lower()
    sources = get_ingestion_config().get("sources", {})

    if normalized not in sources:
        configured = ", ".join(sorted(sources.keys()))
        raise IngestionValidationError(
            f"Unsupported source type '{source_type}'. Configured sources: {configured}"
        )
    if not sources[normalized].get("enabled", False):
        raise IngestionValidationError(f"Source type '{source_type}' is disabled.")

    return normalized


def validate_ticker(ticker: str | None, allow_empty: bool = False) -> str:
    normalized = (ticker or "").strip().upper()
    if allow_empty and not normalized:
        return ""
    if not normalized:
        raise IngestionValidationError("Ticker is required.")
    if not re.fullmatch(r"[A-Z0-9.\-]{1,12}", normalized):
        raise IngestionValidationError(
            "Ticker must be 1-12 characters using letters, numbers, dots, or hyphens."
        )
    return normalized


def validate_document_type(document_type: str) -> str:
    normalized = document_type.strip().lower().replace(" ", "_")
    if not normalized:
        raise IngestionValidationError("Document type is required.")
    if not re.fullmatch(r"[a-z0-9_\-]+", normalized):
        raise IngestionValidationError(
            "Document type can only use letters, numbers, hyphens, and underscores."
        )
    return normalized


def resolve_local_file(file_path: str) -> Path:
    candidate = Path(file_path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate

    if not candidate.exists():
        raise IngestionValidationError(f"Local file does not exist: {file_path}")
    if not candidate.is_file():
        raise IngestionValidationError(f"Path is not a file: {file_path}")

    return candidate


def validate_file_extension(path: Path, allowed_extensions: list[str]) -> str:
    extension = path.suffix.lower()
    normalized_allowed = [item.lower() for item in allowed_extensions]

    if extension not in normalized_allowed:
        allowed = ", ".join(normalized_allowed)
        raise IngestionValidationError(
            f"Unsupported file extension '{extension}'. Allowed extensions: {allowed}"
        )

    return extension


def validate_required_metadata(record: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_METADATA_FIELDS if field not in record]
    if missing:
        raise IngestionValidationError(
            f"Metadata record is missing required fields: {', '.join(missing)}"
        )

    return {field: record.get(field, "") for field in REQUIRED_METADATA_FIELDS}


def get_allowed_local_extensions() -> list[str]:
    source_config = get_ingestion_config().get("sources", {}).get("local_uploads", {})
    return list(source_config.get("allowed_extensions", [".pdf", ".txt", ".csv", ".md"]))


def get_configured_rss_feed(feed_name: str) -> dict[str, Any]:
    feeds = get_ingestion_config().get("sources", {}).get("rss", {}).get("feeds", [])
    for feed in feeds:
        if feed.get("name", "").lower() == feed_name.strip().lower():
            return dict(feed)

    configured = ", ".join(feed.get("name", "") for feed in feeds)
    raise IngestionValidationError(
        f"RSS feed '{feed_name}' is not configured. Available feeds: {configured}"
    )
