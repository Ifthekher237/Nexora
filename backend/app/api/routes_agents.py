"""API routes for Nexora's AI Agent Collaboration System."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.app.schemas.agents import (
    AgentHistoryItem,
    AgentStatus,
    AgentWorkflowRequest,
    AgentWorkflowResponse,
    AvailableAgentDescription,
    SingleAgentRequest,
)
from backend.app.services.agents import agent_orchestrator, agent_output_service


router = APIRouter(tags=["agents"])


def _error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@router.get("/agents/status", response_model=AgentStatus)
def get_agent_status() -> dict[str, object]:
    return agent_orchestrator.agent_status()


@router.get("/agents/available", response_model=list[AvailableAgentDescription])
def get_available_agents() -> list[dict[str, str]]:
    return agent_orchestrator.available_agents()


@router.post("/agents/run-workflow", response_model=AgentWorkflowResponse)
def post_run_workflow(request: AgentWorkflowRequest) -> dict[str, object] | JSONResponse:
    try:
        return agent_orchestrator.run_workflow(
            scenario=request.scenario,
            company_name=request.company_name,
            ticker=request.ticker,
            market=request.market,
            top_k=request.top_k,
            model=request.model,
            agents=request.agents,
            filters=request.filters,
            vector_store=request.vector_store,
        )
    except agent_orchestrator.AgentOrchestratorError as exc:
        return _error_response(str(exc), status_code=400)


@router.post("/agents/run-single", response_model=AgentWorkflowResponse)
def post_run_single(request: SingleAgentRequest) -> dict[str, object] | JSONResponse:
    try:
        return agent_orchestrator.run_single_agent(
            agent_name=request.agent_name,
            scenario=request.scenario,
            company_name=request.company_name,
            ticker=request.ticker,
            market=request.market,
            top_k=request.top_k,
            model=request.model,
            filters=request.filters,
            vector_store=request.vector_store,
        )
    except agent_orchestrator.AgentOrchestratorError as exc:
        return _error_response(str(exc), status_code=400)


@router.get("/agents/history", response_model=list[AgentHistoryItem])
def get_agent_history(
    status: Optional[str] = Query(default=None),
    ticker: Optional[str] = Query(default=None),
    agent_name: Optional[str] = Query(default=None),
    confidence_level: Optional[str] = Query(default=None),
) -> list[dict[str, object]] | JSONResponse:
    try:
        return agent_output_service.read_history(
            {
                "status": status,
                "ticker": ticker,
                "agent_name": agent_name,
                "confidence_level": confidence_level,
            }
        )
    except agent_output_service.AgentOutputStorageError as exc:
        return _error_response(str(exc), status_code=500)


@router.get("/agents/history/{agent_run_id}", response_model=AgentWorkflowResponse)
def get_agent_output(agent_run_id: str) -> dict[str, object] | JSONResponse:
    try:
        output = agent_output_service.read_output(agent_run_id)
    except agent_output_service.AgentOutputStorageError as exc:
        return _error_response(str(exc), status_code=500)
    if output is None:
        return _error_response(f"Agent run not found: {agent_run_id}", status_code=404)
    return output
