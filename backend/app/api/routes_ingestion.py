"""API routes for the Nexora financial data ingestion engine."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.app.schemas.ingestion import (
    DocumentMetadata,
    IngestionResult,
    IngestionStatus,
    IngestionSummary,
    LocalFileIngestionRequest,
    MacroDatasetIngestionRequest,
    RSSIngestionRequest,
    SECIngestionRequest,
)
from backend.app.services.ingestion import ingestion_manager
from backend.app.services.ingestion.validation_service import IngestionValidationError


router = APIRouter(tags=["ingestion"])


def _error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "source_type": "ingestion",
            "message": message,
            "documents_found": 0,
            "documents_saved": 0,
            "duplicates_skipped": 0,
            "errors": [message],
            "documents": [],
        },
    )


@router.get("/ingestion/status", response_model=IngestionStatus)
def get_ingestion_status() -> dict[str, object]:
    return ingestion_manager.ingestion_status()


@router.get("/ingestion/sources")
def get_ingestion_sources() -> dict[str, object]:
    return ingestion_manager.configured_sources()


@router.get("/ingestion/documents", response_model=list[DocumentMetadata])
def get_ingestion_documents(
    source_type: Optional[str] = Query(default=None),
    ticker: Optional[str] = Query(default=None),
    document_type: Optional[str] = Query(default=None),
    market: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> list[dict[str, str]]:
    return ingestion_manager.list_documents(
        {
            "source_type": source_type,
            "ticker": ticker,
            "document_type": document_type,
            "market": market,
            "status": status,
        }
    )


@router.post("/ingestion/sec/company", response_model=IngestionResult)
def post_sec_company(request: SECIngestionRequest) -> IngestionResult | JSONResponse:
    try:
        return ingestion_manager.ingest_sec_company(
            ticker=request.ticker,
            company_name=request.company_name,
            limit=request.limit,
        )
    except IngestionValidationError as exc:
        return _error_response(str(exc))


@router.post("/ingestion/rss", response_model=IngestionResult)
def post_rss(request: RSSIngestionRequest) -> IngestionResult | JSONResponse:
    try:
        return ingestion_manager.ingest_rss(feed_name=request.feed_name, limit=request.limit)
    except IngestionValidationError as exc:
        return _error_response(str(exc))


@router.post("/ingestion/local-file", response_model=IngestionResult)
def post_local_file(request: LocalFileIngestionRequest) -> IngestionResult | JSONResponse:
    try:
        return ingestion_manager.ingest_local_file(
            file_path=request.file_path,
            source_type=request.source_type,
            company_name=request.company_name,
            ticker=request.ticker,
            market=request.market,
            document_type=request.document_type,
            period=request.period,
            title=request.title,
            notes=request.notes,
        )
    except IngestionValidationError as exc:
        return _error_response(str(exc))


@router.post("/ingestion/macro/local-csv", response_model=IngestionResult)
def post_macro_csv(request: MacroDatasetIngestionRequest) -> IngestionResult | JSONResponse:
    try:
        return ingestion_manager.ingest_macro_dataset(
            file_path=request.file_path,
            source_name=request.source_name,
            title=request.title,
            period=request.period,
            notes=request.notes,
        )
    except IngestionValidationError as exc:
        return _error_response(str(exc))


@router.get("/ingestion/summary", response_model=IngestionSummary)
def get_ingestion_summary() -> dict[str, object]:
    return ingestion_manager.ingestion_summary()
