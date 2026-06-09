"""API routes for Nexora's Risk Scoring Engine."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.app.schemas.risk import (
    ExplainScoreRequest,
    ExplainScoreResponse,
    RiskHistoryItem,
    RiskScoringRequest,
    RiskScoringResponse,
    RiskStatus,
)
from backend.app.services.risk import risk_manager, risk_output_service


router = APIRouter(tags=["risk"])


def _error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@router.get("/risk/status", response_model=RiskStatus)
def get_risk_status() -> dict[str, object]:
    return risk_manager.risk_status()


@router.post("/risk/score-scenario", response_model=RiskScoringResponse)
def post_score_scenario(request: RiskScoringRequest) -> dict[str, object] | JSONResponse:
    try:
        result = risk_manager.score_scenario(
            scenario=request.scenario,
            company_name=request.company_name,
            ticker=request.ticker,
            market=request.market,
            top_k=request.top_k,
            model=request.model,
            filters=request.filters,
            vector_store=request.vector_store,
        )
    except risk_manager.RiskManagerError as exc:
        return _error_response(str(exc), status_code=400)
    if result.get("status") == "error":
        return JSONResponse(status_code=503, content=result)
    return result


@router.post("/risk/score-from-reasoning/{reasoning_id}", response_model=RiskScoringResponse)
def post_score_from_reasoning(reasoning_id: str) -> dict[str, object] | JSONResponse:
    try:
        return risk_manager.score_from_reasoning(reasoning_id)
    except risk_manager.RiskManagerError as exc:
        return _error_response(str(exc), status_code=404)


@router.get("/risk/history", response_model=list[RiskHistoryItem])
def get_risk_history(
    ticker: Optional[str] = Query(default=None),
    market: Optional[str] = Query(default=None),
    scenario_type: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    confidence_level: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> list[dict[str, object]] | JSONResponse:
    try:
        return risk_output_service.read_history(
            {
                "ticker": ticker,
                "market": market,
                "scenario_type": scenario_type,
                "overall_risk_level": risk_level,
                "confidence_level": confidence_level,
                "status": status,
            }
        )
    except risk_output_service.RiskOutputStorageError as exc:
        return _error_response(str(exc), status_code=500)


@router.get("/risk/history/{risk_id}", response_model=RiskScoringResponse)
def get_risk_output(risk_id: str) -> dict[str, object] | JSONResponse:
    try:
        output = risk_output_service.read_output(risk_id)
    except risk_output_service.RiskOutputStorageError as exc:
        return _error_response(str(exc), status_code=500)
    if output is None:
        return _error_response(f"Risk output not found: {risk_id}", status_code=404)
    return output


@router.post("/risk/explain-score", response_model=ExplainScoreResponse)
def post_explain_score(request: ExplainScoreRequest) -> dict[str, object] | JSONResponse:
    try:
        return risk_manager.explain_score(
            risk_id=request.risk_id,
            risk_payload=request.risk_payload,
        )
    except risk_manager.RiskManagerError as exc:
        return _error_response(str(exc), status_code=400)
