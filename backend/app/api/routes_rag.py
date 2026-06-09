"""API routes for Nexora's core financial RAG pipeline."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.app.schemas.rag import (
    RAGAskRequest,
    RAGAskResponse,
    RAGEvidenceOnlyRequest,
    RAGEvidenceOnlyResponse,
    RAGHistoryItem,
    RAGStatus,
)
from backend.app.services.rag import rag_manager, rag_response_service


router = APIRouter(tags=["rag"])


def _error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@router.get("/rag/status", response_model=RAGStatus)
def get_rag_status() -> dict[str, object]:
    return rag_manager.rag_status()


@router.post("/rag/ask", response_model=RAGAskResponse)
def post_rag_ask(request: RAGAskRequest) -> dict[str, object] | JSONResponse:
    try:
        result = rag_manager.ask_question(
            question=request.question,
            top_k=request.top_k,
            model=request.model,
            filters=request.filters,
            vector_store=request.vector_store,
        )
    except rag_manager.RAGManagerError as exc:
        return _error_response(str(exc), status_code=400)

    if result.get("status") == "error":
        return JSONResponse(status_code=503, content=result)
    return result


@router.post("/rag/evidence-only", response_model=RAGEvidenceOnlyResponse)
def post_rag_evidence_only(
    request: RAGEvidenceOnlyRequest,
) -> dict[str, object] | JSONResponse:
    try:
        return rag_manager.evidence_only(
            question=request.question,
            top_k=request.top_k,
            filters=request.filters,
            vector_store=request.vector_store,
        )
    except rag_manager.RAGManagerError as exc:
        return _error_response(str(exc), status_code=400)
    except Exception as exc:
        return _error_response(f"Evidence retrieval failed: {exc}", status_code=503)


@router.get("/rag/history", response_model=list[RAGHistoryItem])
def get_rag_history(
    ticker: Optional[str] = Query(default=None),
    model: Optional[str] = Query(default=None),
    confidence_level: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> list[dict[str, object]] | JSONResponse:
    try:
        return rag_response_service.read_history(
            {
                "ticker": ticker,
                "model": model,
                "confidence_level": confidence_level,
                "status": status,
            }
        )
    except rag_response_service.RAGResponseStorageError as exc:
        return _error_response(str(exc), status_code=500)


@router.get("/rag/history/{response_id}", response_model=RAGAskResponse)
def get_rag_response(response_id: str) -> dict[str, object] | JSONResponse:
    try:
        response = rag_response_service.read_response(response_id)
    except rag_response_service.RAGResponseStorageError as exc:
        return _error_response(str(exc), status_code=500)
    if response is None:
        return _error_response(f"RAG response not found: {response_id}", status_code=404)
    return response
