"""Coordinator for Nexora ingestion operations."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_ingestion_config
from backend.app.services.ingestion import local_file_ingestion, macro_ingestion, rss_ingestion, sec_ingestion
from backend.app.services.ingestion.metadata_service import (
    filter_metadata,
    metadata_status,
    read_metadata,
    summary_statistics,
)
from backend.app.services.ingestion.storage_service import (
    ensure_storage_directories,
    metadata_root,
    storage_root,
)
from backend.app.services.ingestion.validation_service import IngestionValidationError


logger = logging.getLogger(__name__)


AVAILABLE_SOURCE_MODULES = ["sec", "rss", "local_uploads", "macro", "asx"]


def ingestion_status() -> dict[str, Any]:
    ensure_storage_directories()
    status = metadata_status()
    return {
        "status": "ready",
        "available_source_modules": AVAILABLE_SOURCE_MODULES,
        "storage_paths": {
            "storage_root": str(storage_root()),
            "metadata_root": str(metadata_root()),
            "project_root": str(PROJECT_ROOT),
        },
        "metadata_index": status,
        "ingested_documents": status["document_count"],
    }


def configured_sources() -> dict[str, Any]:
    return get_ingestion_config()


def list_documents(filters: dict[str, str | None]) -> list[dict[str, str]]:
    return filter_metadata(filters)


def ingestion_summary() -> dict[str, Any]:
    return summary_statistics()


def ingest_sec_company(ticker: str, company_name: str, limit: int) -> dict[str, Any]:
    logger.info("Ingestion manager dispatch | source=sec | ticker=%s", ticker)
    return sec_ingestion.ingest_sec_company(ticker=ticker, company_name=company_name, limit=limit)


def ingest_rss(feed_name: str, limit: int) -> dict[str, Any]:
    logger.info("Ingestion manager dispatch | source=rss | feed=%s", feed_name)
    return rss_ingestion.ingest_rss_feed(feed_name=feed_name, limit=limit)


def ingest_local_file(
    file_path: str,
    source_type: str,
    company_name: str,
    ticker: str,
    market: str,
    document_type: str,
    period: str = "",
    title: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    logger.info("Ingestion manager dispatch | source=%s | file=%s", source_type, file_path)
    return local_file_ingestion.register_local_file(
        file_path=file_path,
        source_type=source_type,
        company_name=company_name,
        ticker=ticker,
        market=market,
        document_type=document_type,
        period=period,
        title=title,
        notes=notes,
    )


def ingest_macro_dataset(
    file_path: str,
    source_name: str,
    title: str | None = None,
    period: str = "",
    notes: str = "",
) -> dict[str, Any]:
    logger.info("Ingestion manager dispatch | source=macro | file=%s", file_path)
    return macro_ingestion.register_macro_csv(
        file_path=file_path,
        source_name=source_name,
        title=title,
        period=period,
        notes=notes,
    )


def clear_runtime_caches_for_tests() -> None:
    """Small helper for isolated tests; not used by the API."""

    read_metadata.cache_clear() if hasattr(read_metadata, "cache_clear") else None
