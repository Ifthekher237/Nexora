"""API routes for the Nexora document processing pipeline."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.app.schemas.processing import (
    BatchProcessingResponse,
    ChunkMetadata,
    ProcessedDocumentMetadata,
    ProcessingRunRequest,
    ProcessingStatus,
    ProcessingSummary,
    SingleProcessingResponse,
)
from backend.app.services.processing import processing_manager


router = APIRouter(tags=["processing"])


@router.get("/processing/status", response_model=ProcessingStatus)
def get_processing_status() -> dict[str, object]:
    return processing_manager.processing_status()


@router.get("/processing/documents", response_model=list[ProcessedDocumentMetadata])
def get_processing_documents(
    source_type: Optional[str] = Query(default=None),
    ticker: Optional[str] = Query(default=None),
    document_type: Optional[str] = Query(default=None),
    processing_status: Optional[str] = Query(default=None),
    market: Optional[str] = Query(default=None),
) -> list[dict[str, str]]:
    return processing_manager.list_processed_documents(
        {
            "source_type": source_type,
            "ticker": ticker,
            "document_type": document_type,
            "processing_status": processing_status,
            "market": market,
        }
    )


@router.post("/processing/run", response_model=BatchProcessingResponse)
def post_processing_run(request: ProcessingRunRequest) -> dict[str, object]:
    return processing_manager.process_documents(
        limit=request.limit,
        source_type=request.source_type,
        ticker=request.ticker,
        document_type=request.document_type,
        reprocess=request.reprocess,
    )


@router.post("/processing/document/{document_id}", response_model=SingleProcessingResponse)
def post_process_document(document_id: str, reprocess: bool = False) -> dict[str, object]:
    return processing_manager.process_document_by_id(document_id, reprocess=reprocess)


@router.get("/processing/chunks/{processed_document_id}", response_model=list[ChunkMetadata])
def get_processing_chunks(processed_document_id: str) -> list[dict[str, object]] | JSONResponse:
    try:
        return processing_manager.load_chunks(processed_document_id)
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": str(exc), "chunks": []},
        )


@router.get("/processing/summary", response_model=ProcessingSummary)
def get_processing_summary() -> dict[str, object]:
    return processing_manager.get_processing_summary()
