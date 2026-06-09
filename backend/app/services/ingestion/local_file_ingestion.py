"""Manual local file registration for reports, transcripts, and datasets."""

from __future__ import annotations

from pathlib import Path

from backend.app.services.ingestion.metadata_service import (
    append_metadata,
    find_duplicate_record,
    utc_now_iso,
)
from backend.app.services.ingestion.storage_service import (
    build_document_id,
    content_hash_for_file,
    copy_local_file,
    project_relative_path,
)
from backend.app.services.ingestion.validation_service import (
    get_allowed_local_extensions,
    resolve_local_file,
    validate_document_type,
    validate_file_extension,
    validate_source_type,
    validate_ticker,
)


def register_local_file(
    file_path: str,
    source_type: str,
    company_name: str,
    ticker: str,
    market: str,
    document_type: str,
    period: str = "",
    title: str | None = None,
    notes: str = "",
) -> dict[str, object]:
    """Register a real local file by copying it into Nexora raw storage."""

    normalized_source = validate_source_type(source_type)
    normalized_ticker = validate_ticker(ticker, allow_empty=True)
    normalized_document_type = validate_document_type(document_type)
    source_path = resolve_local_file(file_path)
    extension = validate_file_extension(source_path, get_allowed_local_extensions())
    content_hash = content_hash_for_file(source_path)
    date_label = period or str(int(source_path.stat().st_mtime))
    document_id = build_document_id(
        normalized_source,
        normalized_ticker,
        normalized_document_type,
        date_label,
        content_hash,
    )

    duplicate = find_duplicate_record(
        {
            "document_id": document_id,
            "source_url": "",
            "content_hash": content_hash,
        }
    )
    if duplicate:
        return {
            "status": "success",
            "source_type": normalized_source,
            "message": "Duplicate local file skipped.",
            "documents_found": 1,
            "documents_saved": 0,
            "duplicates_skipped": 1,
            "errors": [],
            "documents": [duplicate],
        }

    target_path = copy_local_file(
        source_path,
        normalized_source,
        f"{document_id}{extension}",
    )
    display_title = title or Path(file_path).name

    record = {
        "document_id": document_id,
        "source_type": normalized_source,
        "source_name": "Manual local file",
        "company_name": company_name.strip(),
        "ticker": normalized_ticker,
        "market": market.strip().upper(),
        "document_type": normalized_document_type,
        "title": display_title,
        "source_url": "",
        "local_path": project_relative_path(target_path),
        "file_format": extension.lstrip("."),
        "ingested_at": utc_now_iso(),
        "published_at": "",
        "period": period,
        "status": "saved",
        "error_message": "",
        "content_hash": content_hash,
        "notes": notes,
    }

    metadata_result = append_metadata(record)
    return {
        "status": "success",
        "source_type": normalized_source,
        "message": metadata_result["message"],
        "documents_found": 1,
        "documents_saved": 1 if metadata_result["created"] else 0,
        "duplicates_skipped": 1 if metadata_result["duplicate"] else 0,
        "errors": [],
        "documents": [metadata_result["record"]],
    }
