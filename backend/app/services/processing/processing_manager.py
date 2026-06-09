"""Coordinator for the Nexora document processing pipeline."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_processing_config
from backend.app.services.ingestion.metadata_service import read_metadata, utc_now_iso
from backend.app.services.ingestion.storage_service import (
    content_hash_for_bytes,
    project_relative_path,
    safe_filename,
)
from backend.app.services.processing import (
    chunking_service,
    classification_service,
    document_loader,
    enrichment_service,
    quality_service,
    text_cleaner,
)
from backend.app.services.processing.processing_metadata_service import (
    append_processing_metadata,
    chunks_dir,
    documents_dir,
    ensure_processing_directories,
    filter_processing_metadata,
    find_processed_by_source,
    processing_csv_path,
    processing_json_path,
    processing_summary,
    read_processing_metadata,
)


logger = logging.getLogger(__name__)


def _processed_document_id(source_document_id: str, content_hash: str) -> str:
    return f"PROC_{safe_filename(source_document_id)}_{content_hash[:6]}"


def _source_record_by_id(document_id: str) -> dict[str, str] | None:
    frame = read_metadata()
    if frame.empty:
        return None
    matches = frame[frame["document_id"] == document_id]
    if matches.empty:
        return None
    return matches.iloc[0].fillna("").to_dict()


def _eligible_ingestion_records(
    limit: int,
    source_type: str | None = None,
    ticker: str | None = None,
    document_type: str | None = None,
    reprocess: bool = False,
) -> list[dict[str, str]]:
    frame = read_metadata()
    if frame.empty:
        return []

    frame = frame[frame["status"].str.lower() == "saved"]
    if source_type:
        frame = frame[frame["source_type"].str.lower() == source_type.lower()]
    if ticker:
        frame = frame[frame["ticker"].str.lower() == ticker.lower()]
    if document_type:
        frame = frame[frame["document_type"].str.lower() == document_type.lower()]

    records: list[dict[str, str]] = []
    for record in frame.fillna("").to_dict(orient="records"):
        if not reprocess and find_processed_by_source(record["document_id"]):
            continue
        records.append(record)
        if len(records) >= limit:
            break

    return records


def _save_processed_text(processed_id: str, text: str) -> Path:
    documents_dir().mkdir(parents=True, exist_ok=True)
    path = documents_dir() / f"{processed_id}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def _save_chunks(processed_id: str, chunks: list[dict[str, object]]) -> Path:
    chunks_dir().mkdir(parents=True, exist_ok=True)
    path = chunks_dir() / f"{processed_id}_chunks.json"
    path.write_text(json.dumps(chunks, indent=2), encoding="utf-8")
    return path


def _failure_record(
    source_metadata: dict[str, str],
    error_message: str,
    content_hash: str = "",
) -> dict[str, Any]:
    source_id = source_metadata.get("document_id", "")
    processed_id = _processed_document_id(source_id, content_hash or "failed000000")
    config = get_processing_config().get("processing", {})
    return {
        "processed_document_id": processed_id,
        "source_document_id": source_id,
        "source_type": source_metadata.get("source_type", ""),
        "source_name": source_metadata.get("source_name", ""),
        "company_name": source_metadata.get("company_name", ""),
        "ticker": source_metadata.get("ticker", ""),
        "market": source_metadata.get("market", ""),
        "document_type": source_metadata.get("document_type", ""),
        "source_local_path": source_metadata.get("local_path", ""),
        "processed_text_path": "",
        "chunk_file_path": "",
        "file_format": source_metadata.get("file_format", ""),
        "processing_status": "failed",
        "processing_error": error_message,
        "processed_at": utc_now_iso(),
        "published_at": source_metadata.get("published_at", ""),
        "period": source_metadata.get("period", ""),
        "text_length": 0,
        "word_count": 0,
        "chunk_count": 0,
        "language": config.get("language_default", "en"),
        "detected_document_category": "unknown",
        "content_hash": content_hash,
        "notes": "Processing failed; see processing_error.",
    }


def process_source_record(
    source_metadata: dict[str, str],
    reprocess: bool = False,
) -> dict[str, Any]:
    """Process one ingestion metadata record into text and chunk artifacts."""

    ensure_processing_directories()
    source_id = source_metadata.get("document_id", "")
    logger.info(
        "Processing document started | document_id=%s | source_type=%s | path=%s",
        source_id,
        source_metadata.get("source_type", ""),
        source_metadata.get("local_path", ""),
    )

    existing = find_processed_by_source(source_id)
    if existing and not reprocess:
        logger.info("Processing skipped duplicate | document_id=%s", source_id)
        return {
            "status": "skipped",
            "message": "Document already processed.",
            "document": existing,
            "chunks_created": int(existing.get("chunk_count", 0) or 0),
            "errors": [],
        }

    try:
        loaded = document_loader.load_document_text(
            source_metadata.get("local_path", ""),
            source_metadata.get("file_format", ""),
        )
        extracted_text = loaded["text"]
        cleaned_text = (
            text_cleaner.clean_text(extracted_text)
            if get_processing_config().get("processing", {}).get("clean_text", True)
            else extracted_text
        )
        content_hash = content_hash_for_bytes(cleaned_text.encode("utf-8"))
        processed_id = _processed_document_id(source_id, content_hash)
        detected_category = classification_service.classify_document(
            source_metadata,
            cleaned_text,
            source_metadata.get("local_path", ""),
        )
        enrichment = enrichment_service.base_enrichment(source_metadata, detected_category)
        chunks = chunking_service.create_chunks(
            cleaned_text,
            processed_id,
            source_id,
            enrichment,
        )
        quality = quality_service.evaluate_quality(cleaned_text, len(chunks))
        status = str(quality["quality_status"])

        processed_text_path = _save_processed_text(processed_id, cleaned_text)
        chunk_file_path = _save_chunks(processed_id, chunks)
        config = get_processing_config().get("processing", {})

        record = {
            "processed_document_id": processed_id,
            "source_document_id": source_id,
            "source_type": enrichment["source_type"],
            "source_name": enrichment["source_name"],
            "company_name": enrichment["company_name"],
            "ticker": enrichment["ticker"],
            "market": enrichment["market"],
            "document_type": enrichment["document_type"],
            "source_local_path": enrichment["source_local_path"],
            "processed_text_path": project_relative_path(processed_text_path),
            "chunk_file_path": project_relative_path(chunk_file_path),
            "file_format": loaded["file_format"],
            "processing_status": status,
            "processing_error": "; ".join(quality.get("warnings", [])),
            "processed_at": utc_now_iso(),
            "published_at": enrichment["published_at"],
            "period": enrichment["period"],
            "text_length": quality["text_length"],
            "word_count": quality["word_count"],
            "chunk_count": quality["chunk_count"],
            "language": config.get("language_default", "en"),
            "detected_document_category": detected_category,
            "content_hash": content_hash,
            "notes": "Embedding-ready text and chunks created; embeddings are not generated in Phase 3.",
        }
        metadata_result = append_processing_metadata(record, reprocess=reprocess)
        logger.info(
            "Processing finished | document_id=%s | status=%s | chunks=%s",
            source_id,
            status,
            quality["chunk_count"],
        )
        return {
            "status": "success" if status != "failed" else "error",
            "message": metadata_result["message"],
            "document": metadata_result["record"],
            "chunks_created": int(quality["chunk_count"]),
            "errors": [record["processing_error"]] if record["processing_error"] else [],
        }
    except Exception as exc:
        logger.exception("Processing failed | document_id=%s", source_id)
        failure = _failure_record(source_metadata, str(exc))
        metadata_result = append_processing_metadata(failure, reprocess=reprocess)
        return {
            "status": "error",
            "message": "Document processing failed.",
            "document": metadata_result["record"],
            "chunks_created": 0,
            "errors": [str(exc)],
        }


def process_document_by_id(document_id: str, reprocess: bool = False) -> dict[str, Any]:
    source_record = _source_record_by_id(document_id)
    if not source_record:
        return {
            "status": "error",
            "message": f"Document ID '{document_id}' was not found in the ingestion index.",
            "document": None,
            "chunks_created": 0,
            "errors": [f"Invalid document ID: {document_id}"],
        }
    return process_source_record(source_record, reprocess=reprocess)


def process_documents(
    limit: int,
    source_type: str | None = None,
    ticker: str | None = None,
    document_type: str | None = None,
    reprocess: bool = False,
) -> dict[str, Any]:
    selected = _eligible_ingestion_records(
        limit=limit,
        source_type=source_type,
        ticker=ticker,
        document_type=document_type,
        reprocess=reprocess,
    )
    logger.info(
        "Batch processing started | selected=%s | source_type=%s | ticker=%s | document_type=%s | reprocess=%s",
        len(selected),
        source_type,
        ticker,
        document_type,
        reprocess,
    )

    processed = 0
    failed = 0
    skipped = 0
    chunks_created = 0
    errors: list[str] = []
    documents: list[dict[str, str]] = []

    for record in selected:
        result = process_source_record(record, reprocess=reprocess)
        if result["document"]:
            documents.append(result["document"])
        if result["status"] == "skipped":
            skipped += 1
        elif result["status"] == "error":
            failed += 1
            errors.extend(result["errors"])
        else:
            processed += 1
        chunks_created += int(result.get("chunks_created", 0) or 0)

    return {
        "status": "success" if failed == 0 else "partial_success",
        "message": "Batch processing completed.",
        "documents_selected": len(selected),
        "documents_processed": processed,
        "documents_skipped": skipped,
        "documents_failed": failed,
        "chunks_created": chunks_created,
        "errors": errors,
        "documents": documents,
    }


def processing_status() -> dict[str, Any]:
    ensure_processing_directories()
    frame = read_processing_metadata()
    summary = processing_summary()
    failed_count = int((frame["processing_status"] == "failed").sum()) if not frame.empty else 0
    return {
        "status": "ready",
        "processed_document_count": int(len(frame)),
        "chunk_count": int(summary["total_chunks"]),
        "failed_document_count": failed_count,
        "processing_storage_paths": {
            "processed_documents": str(documents_dir()),
            "chunks": str(chunks_dir()),
            "metadata_csv": str(processing_csv_path()),
            "metadata_json": str(processing_json_path()),
            "project_root": str(PROJECT_ROOT),
        },
        "config_status": "loaded",
    }


def list_processed_documents(filters: dict[str, str | None]) -> list[dict[str, str]]:
    return filter_processing_metadata(filters)


def get_processing_summary() -> dict[str, Any]:
    return processing_summary()


def load_chunks(processed_document_id: str) -> list[dict[str, Any]]:
    safe_id = safe_filename(processed_document_id)
    chunk_path = chunks_dir() / f"{safe_id}_chunks.json"
    if not chunk_path.exists():
        # Fallback to the metadata index in case the ID contains characters safe_filename changed.
        frame = read_processing_metadata()
        matches = frame[frame["processed_document_id"] == processed_document_id]
        if not matches.empty:
            path_value = matches.iloc[-1]["chunk_file_path"]
            chunk_path = Path(path_value)
            if not chunk_path.is_absolute():
                chunk_path = PROJECT_ROOT / chunk_path

    if not chunk_path.exists():
        raise FileNotFoundError(f"Chunk file was not found for {processed_document_id}.")

    return json.loads(chunk_path.read_text(encoding="utf-8"))
