"""API routes for Nexora's Explainability & Evidence Layer."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.app.schemas.explainability import (
    ExplainLatestRequest,
    ExplainabilityHistoryItem,
    ExplainabilityReportResponse,
    ExplainabilityStatus,
)
from backend.app.services.explainability import explainability_manager, explainability_output_service


router = APIRouter(tags=["explainability"])


def _error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@router.get("/explainability/status", response_model=ExplainabilityStatus)
def get_explainability_status() -> dict[str, object]:
    return explainability_manager.explainability_status()


@router.post("/explainability/explain-risk/{risk_id}", response_model=ExplainabilityReportResponse)
def post_explain_risk(risk_id: str) -> dict[str, object] | JSONResponse:
    try:
        return explainability_manager.explain_risk(risk_id)
    except explainability_manager.ExplainabilityManagerError as exc:
        return _error_response(str(exc), status_code=404)


@router.post("/explainability/explain-reasoning/{reasoning_id}", response_model=ExplainabilityReportResponse)
def post_explain_reasoning(reasoning_id: str) -> dict[str, object] | JSONResponse:
    try:
        return explainability_manager.explain_reasoning(reasoning_id)
    except explainability_manager.ExplainabilityManagerError as exc:
        return _error_response(str(exc), status_code=404)


@router.post("/explainability/explain-rag/{response_id}", response_model=ExplainabilityReportResponse)
def post_explain_rag(response_id: str) -> dict[str, object] | JSONResponse:
    try:
        return explainability_manager.explain_rag(response_id)
    except explainability_manager.ExplainabilityManagerError as exc:
        return _error_response(str(exc), status_code=404)


@router.post("/explainability/explain-latest", response_model=ExplainabilityReportResponse)
def post_explain_latest(request: ExplainLatestRequest) -> dict[str, object] | JSONResponse:
    try:
        return explainability_manager.explain_latest(request.target_type)
    except explainability_manager.ExplainabilityManagerError as exc:
        return _error_response(str(exc), status_code=404)


@router.get("/explainability/history", response_model=list[ExplainabilityHistoryItem])
def get_explainability_history(
    target_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    coverage_level: Optional[str] = Query(default=None),
) -> list[dict[str, object]] | JSONResponse:
    try:
        return explainability_output_service.read_history(
            {
                "target_type": target_type,
                "status": status,
                "coverage_level": coverage_level,
            }
        )
    except explainability_output_service.ExplainabilityOutputStorageError as exc:
        return _error_response(str(exc), status_code=500)


@router.get("/explainability/history/{explainability_id}", response_model=ExplainabilityReportResponse)
def get_explainability_report(explainability_id: str) -> dict[str, object] | JSONResponse:
    try:
        report = explainability_output_service.read_report(explainability_id)
    except explainability_output_service.ExplainabilityOutputStorageError as exc:
        return _error_response(str(exc), status_code=500)
    if report is None:
        return _error_response(f"Explainability report not found: {explainability_id}", status_code=404)
    return report
