"""Coordinator for Nexora's Phase 8 Explainability & Evidence Layer."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import get_explainability_config
from backend.app.services.explainability import (
    citation_expander,
    confidence_explainer,
    document_attribution_service,
    evidence_coverage_service,
    evidence_ranker,
    explainability_output_service,
    explainability_report_service,
    explainability_validation_service,
    limitation_analyzer,
    reasoning_trace_service,
    unsupported_claim_detector,
)
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.rag import rag_response_service
from backend.app.services.reasoning import reasoning_output_service
from backend.app.services.risk import risk_output_service


logger = logging.getLogger(__name__)


class ExplainabilityManagerError(RuntimeError):
    """Raised when an explainability request cannot be completed."""


def _history_available(reader: Any) -> bool:
    try:
        reader({})
        return True
    except Exception:
        return False


def explainability_status() -> dict[str, Any]:
    config = get_explainability_config()
    storage = {
        "output_dir": str(explainability_output_service.output_dir()),
        "index_csv": str(explainability_output_service.index_csv_path()),
        "index_json": str(explainability_output_service.index_json_path()),
        "save_enabled": explainability_output_service.save_enabled(),
    }
    try:
        saved_reports = explainability_output_service.output_count()
    except Exception as exc:
        saved_reports = 0
        storage["error"] = str(exc)
    return {
        "status": "ready",
        "saved_reports": saved_reports,
        "rag_history_available": _history_available(rag_response_service.read_history),
        "reasoning_history_available": _history_available(reasoning_output_service.read_history),
        "risk_history_available": _history_available(risk_output_service.read_history),
        "output_storage": storage,
        "config_status": {
            "loaded": True,
            "explainability": config.get("explainability", {}),
            "coverage": config.get("coverage", {}),
            "guardrails": config.get("guardrails", {}),
        },
    }


def _latest_id(target_type: str) -> str:
    if target_type == "risk":
        history = risk_output_service.read_history({})
        key = "risk_id"
    elif target_type == "reasoning":
        history = reasoning_output_service.read_history({})
        key = "reasoning_id"
    elif target_type == "rag":
        history = rag_response_service.read_history({})
        key = "response_id"
    else:
        raise ExplainabilityManagerError(f"Unsupported target type: {target_type}")
    if not history:
        raise ExplainabilityManagerError(f"No saved {target_type} output exists yet. Generate one before explaining it.")
    return str(history[0].get(key, ""))


def _load_target(target_type: str, target_id: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if target_type == "risk":
        target = risk_output_service.read_output(target_id)
        if target is None:
            raise ExplainabilityManagerError(f"Risk output not found: {target_id}")
        reasoning_output = None
        reasoning_id = target.get("source_reasoning_id")
        if reasoning_id:
            try:
                reasoning_output = reasoning_output_service.read_output(str(reasoning_id))
            except Exception as exc:
                logger.warning("Could not load source reasoning output for risk explanation | %s", exc)
        return target, reasoning_output
    if target_type == "reasoning":
        target = reasoning_output_service.read_output(target_id)
        if target is None:
            raise ExplainabilityManagerError(f"Reasoning output not found: {target_id}")
        return target, target
    if target_type == "rag":
        target = rag_response_service.read_response(target_id)
        if target is None:
            raise ExplainabilityManagerError(f"RAG response not found: {target_id}")
        return target, None
    raise ExplainabilityManagerError(f"Unsupported target type: {target_type}")


def _sources_for(target_type: str, target_output: dict[str, Any], source_reasoning_output: dict[str, Any] | None) -> list[dict[str, Any]]:
    if target_type == "rag":
        return [item for item in target_output.get("sources") or [] if isinstance(item, dict)]
    if target_type == "reasoning":
        return [item for item in target_output.get("evidence_map") or [] if isinstance(item, dict)]
    if target_type == "risk" and source_reasoning_output:
        return [item for item in source_reasoning_output.get("evidence_map") or [] if isinstance(item, dict)]
    return []


def _text_for_detection(target_type: str, target_output: dict[str, Any], source_reasoning_output: dict[str, Any] | None) -> str:
    parts: list[str] = []
    for key in ["answer", "direct_answer", "explanation", "scenario", "question"]:
        if target_output.get(key):
            parts.append(str(target_output[key]))
    if target_type == "risk":
        for driver in target_output.get("risk_drivers") or []:
            if isinstance(driver, dict):
                parts.append(str(driver.get("explanation", "")))
        if source_reasoning_output:
            parts.append(str(source_reasoning_output.get("direct_answer", "")))
    return "\n".join(part for part in parts if part)


def _base_score(coverage: dict[str, Any], ranking: list[dict[str, Any]], unsupported_claims: list[dict[str, Any]]) -> float:
    coverage_score = float(coverage.get("score") or 0.0)
    ranking_score = sum(float(item.get("score") or 0.0) for item in ranking) / len(ranking) if ranking else 0.0
    penalty = min(0.4, 0.08 * len(unsupported_claims))
    return round(max(0.0, min(1.0, (coverage_score * 0.7) + (ranking_score * 0.3) - penalty)), 4)


def explain_target(target_type: str, target_id: str) -> dict[str, Any]:
    clean_type = target_type.strip().lower()
    clean_id = target_id.strip()
    logger.info("Explainability request received | target_type=%s | target_id=%s", clean_type, clean_id)
    target_output, source_reasoning_output = _load_target(clean_type, clean_id)
    target_text = _text_for_detection(clean_type, target_output, source_reasoning_output)
    sources = _sources_for(clean_type, target_output, source_reasoning_output)

    expanded_result = citation_expander.expand_citations(sources, target_text=target_text)
    citations = expanded_result["citations"]
    coverage = evidence_coverage_service.calculate_coverage(citations, target_output)
    ranking = evidence_ranker.rank_evidence(citations)
    unsupported_claims = unsupported_claim_detector.detect_unsupported_claims(target_text, citations_required=True)
    confidence = confidence_explainer.explain_confidence(target_output, coverage, unsupported_claims)
    reasoning_trace = reasoning_trace_service.extract_reasoning_trace(clean_type, target_output, source_reasoning_output)
    attribution = document_attribution_service.attribute_documents(citations)
    limitations = limitation_analyzer.analyze_limitations(clean_type, target_output, citations, coverage)
    for limitation in expanded_result["limitations"]:
        if limitation not in limitations:
            limitations.append(limitation)

    report_parts = explainability_report_service.build_report(
        target_type=clean_type,
        target_id=clean_id,
        target_output=target_output,
        coverage=coverage,
        citations=citations,
        ranking=ranking,
        confidence=confidence,
        reasoning_trace=reasoning_trace,
        document_attribution=attribution,
        limitations=limitations,
        unsupported_claims=unsupported_claims,
    )
    report = {
        "explainability_id": explainability_output_service.generate_explainability_id(clean_type, clean_id),
        "target_type": clean_type,
        "target_id": clean_id,
        "explainability_score": _base_score(coverage, ranking, unsupported_claims),
        "evidence_coverage": coverage,
        "expanded_citations": citations,
        "evidence_ranking": ranking,
        "score_explanation": report_parts["score_explanation"],
        "confidence_explanation": confidence,
        "reasoning_trace": reasoning_trace,
        "limitations": limitations,
        "unsupported_claims": unsupported_claims,
        "document_attribution": attribution,
        "recommendation": report_parts["recommendation"],
        "validation_warnings": [],
        "report": report_parts["report"],
        "status": "success",
        "created_at": utc_now_iso(),
        "error_message": "",
    }
    report = explainability_validation_service.validate_report(report)
    try:
        explainability_output_service.save_report(report)
    except explainability_output_service.ExplainabilityOutputStorageError as exc:
        logger.exception("Explainability report save failed")
        report["status"] = "partial_success"
        report["error_message"] = str(exc)
        report.setdefault("limitations", []).append(str(exc))

    logger.info(
        "Explainability report built | target_type=%s | target_id=%s | sources=%s | coverage=%s | unsupported_claims=%s | warnings=%s",
        clean_type,
        clean_id,
        len(citations),
        coverage.get("score"),
        len(unsupported_claims),
        len(report.get("validation_warnings", [])),
    )
    return report


def explain_latest(target_type: str) -> dict[str, Any]:
    clean_type = target_type.strip().lower()
    return explain_target(clean_type, _latest_id(clean_type))


def explain_risk(risk_id: str) -> dict[str, Any]:
    return explain_target("risk", risk_id)


def explain_reasoning(reasoning_id: str) -> dict[str, Any]:
    return explain_target("reasoning", reasoning_id)


def explain_rag(response_id: str) -> dict[str, Any]:
    return explain_target("rag", response_id)
