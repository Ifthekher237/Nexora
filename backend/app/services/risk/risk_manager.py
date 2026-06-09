"""Central coordinator for Nexora's Phase 7 Risk Scoring Engine."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import get_risk_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.rag import rag_manager
from backend.app.services.reasoning import reasoning_manager, reasoning_output_service
from backend.app.services.risk import (
    company_risk_service,
    confidence_score_service,
    evidence_score_service,
    exposure_score_service,
    macro_risk_service,
    operational_risk_service,
    risk_explanation_service,
    risk_output_service,
    risk_validation_service,
    scoring_engine,
    sector_risk_service,
    vulnerability_score_service,
)
from backend.app.services.retrieval import vector_store_manager


logger = logging.getLogger(__name__)


class RiskManagerError(RuntimeError):
    """Raised when a risk scoring request is invalid before scoring."""


def _section(name: str) -> dict[str, Any]:
    return get_risk_config().get(name, {})


def _filters_dict(filters: Any) -> dict[str, str | None]:
    if filters is None:
        return {"source_type": None, "document_type": None, "section_hint": None}
    raw = filters.model_dump() if hasattr(filters, "model_dump") else dict(filters)
    return {
        "source_type": raw.get("source_type") or None,
        "document_type": raw.get("document_type") or None,
        "section_hint": raw.get("section_hint") or None,
    }


def _base_limitations(extra: list[str] | None = None) -> list[str]:
    limitations = [
        "Risk scores are evidence-backed analytical estimates, not predictions.",
        "Nexora does not provide investment advice, trading recommendations, or stock price predictions.",
        "Scores depend on available local evidence and Phase 6 reasoning quality.",
    ]
    for item in extra or []:
        if item and item not in limitations:
            limitations.append(item)
    return limitations


def _save(output: dict[str, Any]) -> dict[str, Any]:
    try:
        risk_output_service.save_output(output)
    except risk_output_service.RiskOutputStorageError as exc:
        logger.exception("Risk output save failed")
        output.setdefault("limitations", []).append(str(exc))
        output["error_message"] = "; ".join(
            item for item in [output.get("error_message", ""), str(exc)] if item
        )
        if output.get("status") == "success":
            output["status"] = "partial_success"
    return output


def risk_status() -> dict[str, Any]:
    try:
        reasoning_status = reasoning_manager.reasoning_status()
        reasoning_available = reasoning_status.get("status") in {"ready", "degraded"}
        rag_available = bool(reasoning_status.get("rag_available"))
        retrieval_available = bool(reasoning_status.get("retrieval_available"))
    except Exception:
        reasoning_available = False
        rag_available = False
        retrieval_available = False

    try:
        retrieval_available = retrieval_available or vector_store_manager.retrieval_system_status().get("status") == "ready"
    except Exception:
        pass

    try:
        rag_available = rag_available or rag_manager.rag_status().get("status") in {"ready", "degraded"}
    except Exception:
        pass

    scoring_config = get_risk_config()
    output_storage = {
        "output_dir": str(risk_output_service.output_dir()),
        "index_csv": str(risk_output_service.index_csv_path()),
        "index_json": str(risk_output_service.index_json_path()),
        "save_enabled": risk_output_service.save_enabled(),
    }
    try:
        saved_count = risk_output_service.output_count()
    except Exception:
        saved_count = 0
        output_storage["error"] = "Could not read risk index."

    return {
        "status": "ready" if reasoning_available and retrieval_available else "degraded",
        "reasoning_available": reasoning_available,
        "rag_available": rag_available,
        "retrieval_available": retrieval_available,
        "saved_risk_outputs": saved_count,
        "scoring_config_status": {
            "loaded": True,
            "scale": scoring_config.get("risk_scoring", {}),
            "weights": scoring_config.get("weights", {}),
        },
        "output_storage": output_storage,
    }


def _empty_breakdown() -> dict[str, int]:
    return {
        "evidence_strength_score": 0,
        "exposure_score": 0,
        "vulnerability_score": 0,
        "operational_risk_score": 0,
        "macro_risk_score": 0,
        "sector_risk_score": 0,
        "company_specific_risk_score": 0,
    }


def _error_output(
    scenario: str,
    message: str,
    reasoning_output: dict[str, Any] | None = None,
    status: str = "error",
) -> dict[str, Any]:
    reasoning_output = reasoning_output or {}
    output = {
        "risk_id": risk_output_service.generate_risk_id(scenario),
        "source_reasoning_id": reasoning_output.get("reasoning_id", ""),
        "scenario": scenario,
        "company_name": reasoning_output.get("company_name", ""),
        "ticker": reasoning_output.get("ticker", ""),
        "market": reasoning_output.get("market", ""),
        "scenario_type": reasoning_output.get("scenario_type", "unknown"),
        "overall_risk_score": 0,
        "overall_risk_level": "very_low",
        "confidence": {"level": "low", "score": 0.0, "reason": message},
        "score_breakdown": _empty_breakdown(),
        "risk_drivers": [],
        "evidence_summary": {
            "sources_used": 0,
            "unique_documents": 0,
            "average_retrieval_score": 0.0,
            "top_retrieval_score": 0.0,
            "supported_chain_steps": 0,
            "source_diversity": 0.0,
        },
        "explanation": message,
        "limitations": _base_limitations([message]),
        "validation_warnings": [message],
        "not_financial_advice": True,
        "status": status,
        "created_at": utc_now_iso(),
        "model": reasoning_output.get("model", ""),
        "error_message": "" if status != "error" else message,
    }
    return _save(risk_validation_service.validate_risk_output(output))


def score_reasoning_output(reasoning_output: dict[str, Any]) -> dict[str, Any]:
    scenario = str(reasoning_output.get("scenario", "")).strip()
    if not scenario:
        raise RiskManagerError("Reasoning output is missing a scenario.")

    evidence_map = reasoning_output.get("evidence_map") or []
    if bool(_section("risk_scoring").get("require_evidence", True)) and not evidence_map:
        return _error_output(
            scenario,
            "No evidence map was available, so risk scoring was not produced.",
            reasoning_output,
            status="insufficient_evidence",
        )

    evidence_result = evidence_score_service.score_evidence_strength(reasoning_output)
    exposure_result = exposure_score_service.score_exposure(reasoning_output)
    vulnerability_result = vulnerability_score_service.score_vulnerability(reasoning_output)
    operational_result = operational_risk_service.score_operational_risk(reasoning_output)
    macro_result = macro_risk_service.score_macro_risk(reasoning_output)
    sector_result = sector_risk_service.score_sector_risk(reasoning_output)
    company_result = company_risk_service.score_company_risk(reasoning_output)

    breakdown = {
        "evidence_strength_score": evidence_result["evidence_strength_score"],
        "exposure_score": exposure_result["exposure_score"],
        "vulnerability_score": vulnerability_result["vulnerability_score"],
        "operational_risk_score": operational_result["operational_risk_score"],
        "macro_risk_score": macro_result["macro_risk_score"],
        "sector_risk_score": sector_result["sector_risk_score"],
        "company_specific_risk_score": company_result["company_specific_risk_score"],
    }
    causal_score = scoring_engine.causal_chain_strength_score(reasoning_output)
    diversity_score = scoring_engine.source_diversity_score(evidence_result["evidence_summary"])
    confidence_result = confidence_score_service.score_confidence(
        reasoning_output,
        evidence_result["evidence_strength_score"],
    )
    final = scoring_engine.combine_scores(
        evidence_strength_score=evidence_result["evidence_strength_score"],
        reasoning_confidence_score=float((reasoning_output.get("confidence") or {}).get("score") or 0.0),
        causal_chain_score=causal_score,
        exposure_score=exposure_result["exposure_score"],
        macro_risk_score=macro_result["macro_risk_score"],
        source_diversity=diversity_score,
    )
    risk_drivers = risk_explanation_service.build_risk_drivers(breakdown, reasoning_output)
    limitations = _base_limitations(reasoning_output.get("limitations", []))
    for component in [sector_result, company_result]:
        if component.get("limitation"):
            limitations.append(component["limitation"])
    if evidence_result["evidence_quality_level"] == "weak":
        limitations.append("Evidence quality is weak, so score confidence is reduced.")

    output = {
        "risk_id": risk_output_service.generate_risk_id(scenario),
        "source_reasoning_id": reasoning_output.get("reasoning_id", ""),
        "scenario": scenario,
        "company_name": reasoning_output.get("company_name", ""),
        "ticker": reasoning_output.get("ticker", ""),
        "market": reasoning_output.get("market", ""),
        "scenario_type": reasoning_output.get("scenario_type", "unknown"),
        "overall_risk_score": final["overall_risk_score"],
        "overall_risk_level": final["overall_risk_level"],
        "confidence": {
            "level": confidence_result["confidence_level"],
            "score": confidence_result["confidence_score"],
            "reason": confidence_result["reason"],
        },
        "score_breakdown": breakdown,
        "risk_drivers": risk_drivers,
        "evidence_summary": evidence_result["evidence_summary"],
        "explanation": "",
        "limitations": limitations,
        "validation_warnings": [],
        "not_financial_advice": True,
        "status": "success",
        "created_at": utc_now_iso(),
        "model": reasoning_output.get("model", ""),
        "error_message": "",
    }
    output["explanation"] = risk_explanation_service.explain_score(
        output,
        final["calculation_explanation"],
    )
    output = risk_validation_service.validate_risk_output(output)
    logger.info(
        "Risk score built | scenario_type=%s | score=%s | confidence=%s | warnings=%s",
        output["scenario_type"],
        output["overall_risk_score"],
        output["confidence"].get("score"),
        len(output.get("validation_warnings", [])),
    )
    return _save(output)


def score_scenario(
    scenario: str,
    company_name: str | None = None,
    ticker: str | None = None,
    market: str | None = None,
    top_k: int = 8,
    model: str | None = None,
    filters: Any = None,
    vector_store: str = "faiss",
) -> dict[str, Any]:
    clean_scenario = " ".join(scenario.strip().split())
    if not clean_scenario:
        raise RiskManagerError("Scenario cannot be empty.")
    normalized_filters = _filters_dict(filters)
    logger.info(
        "Risk scoring request received | scenario=%s | company=%s | ticker=%s | market=%s | top_k=%s | filters=%s",
        clean_scenario,
        company_name,
        ticker,
        market,
        top_k,
        normalized_filters,
    )
    reasoning_output = reasoning_manager.analyze_scenario(
        scenario=clean_scenario,
        company_name=company_name,
        ticker=ticker,
        market=market,
        top_k=top_k,
        model=model,
        filters=normalized_filters,
        vector_store=vector_store,
    )
    if reasoning_output.get("status") == "error":
        return _error_output(clean_scenario, reasoning_output.get("error_message", "Reasoning failed."), reasoning_output)
    return score_reasoning_output(reasoning_output)


def score_from_reasoning(reasoning_id: str) -> dict[str, Any]:
    reasoning_output = reasoning_output_service.read_output(reasoning_id)
    if reasoning_output is None:
        raise RiskManagerError(f"Reasoning output not found: {reasoning_id}")
    return score_reasoning_output(reasoning_output)


def explain_score(risk_id: str | None = None, risk_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if risk_id:
        risk_output = risk_output_service.read_output(risk_id)
        if risk_output is None:
            raise RiskManagerError(f"Risk output not found: {risk_id}")
    elif risk_payload:
        risk_output = risk_payload
    else:
        raise RiskManagerError("Provide either risk_id or risk_payload.")
    return {
        "risk_id": risk_output.get("risk_id", ""),
        "explanation": risk_explanation_service.explain_score(risk_output),
        "limitations": risk_output.get("limitations", []),
        "status": "success",
    }
