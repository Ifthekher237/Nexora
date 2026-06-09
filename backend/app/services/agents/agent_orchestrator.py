"""Orchestrator for Nexora's local-first multi-agent workflows."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import get_agents_config
from backend.app.services.agents import (
    agent_memory_service,
    agent_output_service,
    agent_validation_service,
    collaboration_summary_service,
)
from backend.app.services.agents.company_analysis_agent import CompanyAnalysisAgent
from backend.app.services.agents.macroeconomic_agent import MacroeconomicAgent
from backend.app.services.agents.news_intelligence_agent import NewsIntelligenceAgent
from backend.app.services.agents.risk_propagation_agent import RiskPropagationAgent
from backend.app.services.agents.sector_analysis_agent import SectorAnalysisAgent
from backend.app.services.explainability import explainability_manager
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.rag import rag_manager
from backend.app.services.reasoning import reasoning_manager, scenario_parser
from backend.app.services.risk import risk_manager


logger = logging.getLogger(__name__)


class AgentOrchestratorError(RuntimeError):
    """Raised when an agent workflow request is invalid."""


AGENT_CLASSES = {
    MacroeconomicAgent.agent_key: MacroeconomicAgent,
    CompanyAnalysisAgent.agent_key: CompanyAnalysisAgent,
    SectorAnalysisAgent.agent_key: SectorAnalysisAgent,
    NewsIntelligenceAgent.agent_key: NewsIntelligenceAgent,
    RiskPropagationAgent.agent_key: RiskPropagationAgent,
}


def _agents_config() -> dict[str, Any]:
    return get_agents_config().get("agents", {})


def _workflow_config() -> dict[str, Any]:
    return get_agents_config().get("workflow", {})


def _llm_config() -> dict[str, Any]:
    return get_agents_config().get("llm", {})


def enabled_agent_keys() -> list[str]:
    configured = get_agents_config().get("enabled_agents", list(AGENT_CLASSES))
    return [key for key in configured if key in AGENT_CLASSES]


def available_agents() -> list[dict[str, str]]:
    return [
        {
            "agent_key": key,
            "agent_name": AGENT_CLASSES[key].agent_name,
            "description": AGENT_CLASSES[key].description,
        }
        for key in enabled_agent_keys()
    ]


def _service_available(status_reader: Any) -> bool:
    try:
        status = status_reader()
        return status.get("status") in {"ready", "degraded"}
    except Exception:
        return False


def agent_status() -> dict[str, Any]:
    storage = {
        "output_dir": str(agent_output_service.output_dir()),
        "index_csv": str(agent_output_service.index_csv_path()),
        "index_json": str(agent_output_service.index_json_path()),
        "save_enabled": agent_output_service.save_enabled(),
    }
    try:
        saved_count = agent_output_service.output_count()
    except Exception as exc:
        saved_count = 0
        storage["error"] = str(exc)
    return {
        "status": "ready" if _agents_config().get("enabled", True) else "disabled",
        "enabled_agents": enabled_agent_keys(),
        "rag_available": _service_available(rag_manager.rag_status),
        "reasoning_available": _service_available(reasoning_manager.reasoning_status),
        "risk_available": _service_available(risk_manager.risk_status),
        "explainability_available": _service_available(explainability_manager.explainability_status),
        "saved_agent_runs": saved_count,
        "output_storage": storage,
        "config_status": {
            "loaded": True,
            "agents": _agents_config(),
            "workflow": _workflow_config(),
            "llm": _llm_config(),
        },
    }


def _validated_top_k(value: int | None) -> int:
    top_k = int(value or _agents_config().get("default_top_k", 8))
    if top_k < 1:
        raise AgentOrchestratorError("top_k must be at least 1.")
    max_top_k = int(_agents_config().get("max_top_k", 12))
    if top_k > max_top_k:
        raise AgentOrchestratorError(f"top_k cannot exceed {max_top_k}.")
    return top_k


def _filters_dict(filters: Any) -> dict[str, str | None]:
    if filters is None:
        return {"source_type": None, "document_type": None, "section_hint": None}
    raw = filters.model_dump() if hasattr(filters, "model_dump") else dict(filters)
    return {
        "source_type": raw.get("source_type") or None,
        "document_type": raw.get("document_type") or None,
        "section_hint": raw.get("section_hint") or None,
    }


def _selected_agents(selected: list[str] | None) -> list[str]:
    if not selected:
        return enabled_agent_keys()
    clean = [item.strip() for item in selected if item and item.strip()]
    invalid = [item for item in clean if item not in AGENT_CLASSES]
    if invalid:
        raise AgentOrchestratorError(f"Invalid agent name(s): {', '.join(invalid)}")
    return clean


def _agent_failure(agent_key: str, message: str) -> dict[str, Any]:
    cls = AGENT_CLASSES.get(agent_key)
    return {
        "agent_name": cls.agent_name if cls else agent_key,
        "agent_key": agent_key,
        "status": "error",
        "summary": f"Agent failed: {message}",
        "key_findings": [],
        "evidence_used": [],
        "confidence": {"level": "low", "score": 0.0, "reason": "Agent failed before producing evidence-backed output."},
        "limitations": [message, "Agent output is not financial advice and does not predict stock prices."],
        "validation_warnings": [message],
        "details": {},
    }


def _base_limitations(agent_outputs: list[dict[str, Any]]) -> list[str]:
    limitations = [
        "Agent collaboration is local-first and depends on available Nexora evidence.",
        "Nexora agents do not provide investment advice or stock price predictions.",
    ]
    for output in agent_outputs:
        for limitation in output.get("limitations", []):
            if limitation not in limitations and any(term in limitation.lower() for term in ["limited", "missing", "no ", "weak"]):
                limitations.append(limitation)
    return limitations[:12]


def run_workflow(
    *,
    scenario: str,
    company_name: str | None = None,
    ticker: str | None = None,
    market: str | None = None,
    top_k: int | None = None,
    model: str | None = None,
    agents: list[str] | None = None,
    filters: Any = None,
    vector_store: str = "faiss",
) -> dict[str, Any]:
    clean_scenario = " ".join(scenario.strip().split())
    if not clean_scenario:
        raise AgentOrchestratorError("Scenario cannot be empty.")
    selected = _selected_agents(agents)
    selected_top_k = _validated_top_k(top_k)
    selected_model = model or str(_llm_config().get("default_model", "llama3.1:8b"))
    parsed = scenario_parser.parse_scenario(clean_scenario, company_name, ticker, market)
    normalized_filters = _filters_dict(filters)
    context = {
        "scenario": clean_scenario,
        "company_name": company_name or "",
        "ticker": (ticker or "").upper(),
        "market": (market or "").upper(),
        "top_k": selected_top_k,
        "model": selected_model,
        "filters": normalized_filters,
        "vector_store": vector_store,
        "parsed_scenario": parsed,
    }
    memory = agent_memory_service.create_memory(clean_scenario, parsed)
    logger.info(
        "Agent workflow request received | scenario=%s | agents=%s | ticker=%s | top_k=%s",
        clean_scenario,
        selected,
        ticker,
        selected_top_k,
    )

    outputs: list[dict[str, Any]] = []
    allow_partial = bool(_workflow_config().get("allow_partial_results", True))
    for agent_key in selected:
        logger.info("Agent start | agent=%s", agent_key)
        try:
            agent = AGENT_CLASSES[agent_key]()
            output = agent.run(context, memory)
            agent_memory_service.store_evidence(memory, agent_key, output.get("evidence_used", []))
            output = agent_validation_service.validate_agent_output(output)
            logger.info(
                "Agent completed | agent=%s | evidence=%s | confidence=%s | warnings=%s",
                agent_key,
                len(output.get("evidence_used", [])),
                (output.get("confidence") or {}).get("score"),
                len(output.get("validation_warnings", [])),
            )
        except Exception as exc:
            logger.exception("Agent failed | agent=%s", agent_key)
            output = _agent_failure(agent_key, str(exc))
            if not allow_partial:
                outputs.append(output)
                break
        agent_memory_service.store_agent_output(memory, agent_key, output)
        outputs.append(output)

    summary = collaboration_summary_service.build_summary(outputs, clean_scenario)
    confidence = collaboration_summary_service.overall_confidence(outputs)
    successful_outputs = [output for output in outputs if output.get("status") == "success"]
    errored_outputs = [output for output in outputs if output.get("status") == "error"]
    insufficient_outputs = [output for output in outputs if output.get("status") == "insufficient_evidence"]
    status = "success"
    if not outputs:
        status = "error"
    elif errored_outputs and not successful_outputs and not insufficient_outputs:
        status = "error"
    elif errored_outputs:
        status = "partial_success"
    elif insufficient_outputs and not successful_outputs:
        status = "insufficient_evidence"

    result = {
        "agent_run_id": agent_output_service.generate_agent_run_id(clean_scenario),
        "scenario": clean_scenario,
        "company_name": company_name or "",
        "ticker": (ticker or "").upper(),
        "market": (market or "").upper(),
        "agents_run": [output.get("agent_key", "") for output in outputs],
        "agent_outputs": outputs,
        "collaboration_summary": summary,
        "overall_confidence": confidence,
        "limitations": _base_limitations(outputs),
        "not_financial_advice": True,
        "status": status,
        "created_at": utc_now_iso(),
        "model": selected_model,
        "error_message": "" if status != "error" else "No agents completed.",
    }
    try:
        agent_output_service.save_output(result)
        logger.info("Agent workflow output saved | run_id=%s", result["agent_run_id"])
    except agent_output_service.AgentOutputStorageError as exc:
        logger.exception("Agent output save failed")
        result["status"] = "partial_success"
        result["error_message"] = str(exc)
        result["limitations"].append(str(exc))
    return result


def run_single_agent(
    *,
    agent_name: str,
    scenario: str,
    company_name: str | None = None,
    ticker: str | None = None,
    market: str | None = None,
    top_k: int | None = None,
    model: str | None = None,
    filters: Any = None,
    vector_store: str = "faiss",
) -> dict[str, Any]:
    return run_workflow(
        scenario=scenario,
        company_name=company_name,
        ticker=ticker,
        market=market,
        top_k=top_k,
        model=model,
        agents=[agent_name],
        filters=filters,
        vector_store=vector_store,
    )
