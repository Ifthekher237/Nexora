"""API routes for Nexora's Financial Reasoning Engine."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.app.schemas.reasoning import (
    CausalChainOnlyResponse,
    EvidenceMapResponse,
    ReasoningHistoryItem,
    ReasoningStatus,
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse,
)
from backend.app.services.reasoning import reasoning_manager, reasoning_output_service


router = APIRouter(tags=["reasoning"])


def _error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@router.get("/reasoning/status", response_model=ReasoningStatus)
def get_reasoning_status() -> dict[str, object]:
    return reasoning_manager.reasoning_status()


@router.post("/reasoning/analyze-scenario", response_model=ScenarioAnalysisResponse)
def post_analyze_scenario(request: ScenarioAnalysisRequest) -> dict[str, object] | JSONResponse:
    try:
        result = reasoning_manager.analyze_scenario(
            scenario=request.scenario,
            company_name=request.company_name,
            ticker=request.ticker,
            market=request.market,
            top_k=request.top_k,
            model=request.model,
            filters=request.filters,
            vector_store=request.vector_store,
        )
    except reasoning_manager.ReasoningManagerError as exc:
        return _error_response(str(exc), status_code=400)

    if result.get("status") == "error":
        return JSONResponse(status_code=503, content=result)
    return result


@router.post("/reasoning/causal-chain", response_model=CausalChainOnlyResponse)
def post_causal_chain(request: ScenarioAnalysisRequest) -> dict[str, object] | JSONResponse:
    try:
        return reasoning_manager.causal_chain_only(
            scenario=request.scenario,
            company_name=request.company_name or "",
            ticker=request.ticker or "",
            market=request.market or "",
        )
    except reasoning_manager.ReasoningManagerError as exc:
        return _error_response(str(exc), status_code=400)


@router.post("/reasoning/evidence-map", response_model=EvidenceMapResponse)
def post_evidence_map(request: ScenarioAnalysisRequest) -> dict[str, object] | JSONResponse:
    try:
        return reasoning_manager.evidence_map_only(
            scenario=request.scenario,
            company_name=request.company_name or "",
            ticker=request.ticker or "",
            market=request.market or "",
            top_k=request.top_k,
            filters=request.filters,
            vector_store=request.vector_store,
        )
    except reasoning_manager.ReasoningManagerError as exc:
        return _error_response(str(exc), status_code=400)
    except Exception as exc:
        return _error_response(f"Reasoning evidence mapping failed: {exc}", status_code=503)


@router.get("/reasoning/history", response_model=list[ReasoningHistoryItem])
def get_reasoning_history(
    ticker: Optional[str] = Query(default=None),
    market: Optional[str] = Query(default=None),
    scenario_type: Optional[str] = Query(default=None),
    confidence_level: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> list[dict[str, object]] | JSONResponse:
    try:
        return reasoning_output_service.read_history(
            {
                "ticker": ticker,
                "market": market,
                "scenario_type": scenario_type,
                "confidence_level": confidence_level,
                "status": status,
            }
        )
    except reasoning_output_service.ReasoningOutputStorageError as exc:
        return _error_response(str(exc), status_code=500)


@router.get("/reasoning/history/{reasoning_id}", response_model=ScenarioAnalysisResponse)
def get_reasoning_output(reasoning_id: str) -> dict[str, object] | JSONResponse:
    try:
        output = reasoning_output_service.read_output(reasoning_id)
    except reasoning_output_service.ReasoningOutputStorageError as exc:
        return _error_response(str(exc), status_code=500)
    if output is None:
        return _error_response(f"Reasoning output not found: {reasoning_id}", status_code=404)
    return output
