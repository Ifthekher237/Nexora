"""Central coordinator for the Phase 6 Financial Reasoning Engine."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_reasoning_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ollama_service import (
    OllamaServiceError,
    check_ollama_running,
    list_local_models,
)
from backend.app.services.reasoning import (
    causal_chain_service,
    company_mapping_service,
    macro_impact_service,
    multi_hop_reasoning_service,
    operational_exposure_service,
    reasoning_evidence_service,
    reasoning_output_service,
    reasoning_prompt_builder,
    reasoning_validation_service,
    scenario_parser,
    sector_dependency_service,
)
from backend.app.services.rag import rag_manager
from backend.app.services.retrieval import vector_store_manager


logger = logging.getLogger(__name__)


class ReasoningManagerError(RuntimeError):
    """Raised when a reasoning request is invalid before execution."""


def _section(name: str) -> dict[str, Any]:
    return get_reasoning_config().get(name, {})


def _default_model() -> str:
    return str(_section("llm").get("default_model", "llama3.1:8b"))


def _fallback_model() -> str:
    return str(_section("llm").get("fallback_model", "mistral:7b"))


def _default_top_k() -> int:
    return int(_section("reasoning").get("default_top_k", 8))


def _max_top_k() -> int:
    return int(_section("reasoning").get("max_top_k", 12))


def _require_evidence() -> bool:
    return bool(_section("reasoning").get("require_evidence", True))


def _filters_dict(filters: Any) -> dict[str, str | None]:
    if filters is None:
        return {"source_type": None, "document_type": None, "section_hint": None}
    raw = filters.model_dump() if hasattr(filters, "model_dump") else dict(filters)
    return {
        "source_type": raw.get("source_type") or None,
        "document_type": raw.get("document_type") or None,
        "section_hint": raw.get("section_hint") or None,
    }


def _validated_top_k(value: int | None) -> int:
    top_k = int(value or _default_top_k())
    if top_k < 1:
        raise ReasoningManagerError("top_k must be at least 1.")
    if top_k > _max_top_k():
        raise ReasoningManagerError(f"top_k cannot exceed {_max_top_k()} for reasoning requests.")
    return top_k


def _base_limitations(extra: list[str] | None = None) -> list[str]:
    limitations = [
        "Reasoning is limited to evidence retrieved from the local Nexora knowledge base.",
        "Nexora does not provide investment advice, trading recommendations, or stock price predictions.",
        "Phase 6 does not perform final risk scoring or quantify financial impact.",
    ]
    for item in extra or []:
        if item and item not in limitations:
            limitations.append(item)
    return limitations


def _confidence(evidence_map: list[dict[str, Any]], chain: list[dict[str, Any]]) -> dict[str, Any]:
    if not evidence_map:
        return {
            "level": "low",
            "score": 0.0,
            "reason": "No qualifying retrieved evidence was available for this reasoning request.",
        }
    scores = [float(item.get("score") or 0.0) for item in evidence_map]
    average_score = sum(scores) / len(scores)
    supported_steps = sum(1 for step in chain if step.get("supporting_sources"))
    score = round(
        min(
            1.0,
            min(len(evidence_map) / 6, 1.0) * 0.25
            + min(average_score, 1.0) * 0.40
            + min(supported_steps / max(len(chain), 1), 1.0) * 0.25
            + 0.10,
        ),
        2,
    )
    if score >= 0.75:
        level = "high"
    elif score >= 0.45:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "score": score,
        "reason": (
            f"Based on {len(evidence_map)} evidence item(s), average retrieval score "
            f"{average_score:.2f}, and {supported_steps} causal-chain step(s) with supporting sources."
        ),
    }


def _save(output: dict[str, Any]) -> dict[str, Any]:
    try:
        reasoning_output_service.save_output(output)
    except reasoning_output_service.ReasoningOutputStorageError as exc:
        logger.exception("Reasoning output save failed")
        output.setdefault("limitations", []).append(str(exc))
        output["error_message"] = "; ".join(
            item for item in [output.get("error_message", ""), str(exc)] if item
        )
        if output.get("status") == "success":
            output["status"] = "partial_success"
    return output


def reasoning_status() -> dict[str, Any]:
    try:
        retrieval_status = vector_store_manager.retrieval_system_status()
        retrieval_available = retrieval_status.get("status") == "ready"
    except Exception:
        retrieval_available = False
    try:
        rag_status = rag_manager.rag_status()
        rag_available = rag_status.get("status") in {"ready", "degraded"}
    except Exception:
        rag_available = False

    ollama_running = check_ollama_running()
    installed_models = list_local_models() if ollama_running else []
    output_storage = {
        "output_dir": str(reasoning_output_service.output_dir()),
        "index_csv": str(reasoning_output_service.index_csv_path()),
        "index_json": str(reasoning_output_service.index_json_path()),
        "save_enabled": reasoning_output_service.save_enabled(),
    }
    try:
        output_count = reasoning_output_service.output_count()
    except Exception:
        output_count = 0
        output_storage["error"] = "Could not read reasoning index."

    return {
        "status": "ready" if retrieval_available and rag_available else "degraded",
        "rag_available": rag_available,
        "retrieval_available": retrieval_available,
        "ollama_running": ollama_running,
        "installed_models": installed_models,
        "saved_reasoning_outputs": output_count,
        "default_model": _default_model(),
        "fallback_model": _fallback_model(),
        "default_top_k": _default_top_k(),
        "max_top_k": _max_top_k(),
        "min_evidence_score": float(_section("reasoning").get("min_evidence_score", 0.25)),
        "output_storage": output_storage,
    }


def _build_context_objects(
    parsed: dict[str, Any],
    scenario: str,
    company_name: str,
    ticker: str,
    market: str,
    chain: list[dict[str, Any]],
    evidence_map: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], list[str], dict[str, Any]]:
    company_map = company_mapping_service.map_company(company_name, ticker, market, evidence_map)
    sector = company_map.get("sector") or sector_dependency_service.infer_sector(company_name, ticker, evidence_map)
    sector_dependencies = sector_dependency_service.relevant_dependencies(sector, parsed)
    macro_channels = macro_impact_service.identify_macro_channels(parsed, scenario)
    operational_exposures = operational_exposure_service.identify_operational_exposures(parsed, evidence_map)
    return company_map, sector_dependencies, macro_channels, operational_exposures


def analyze_scenario(
    scenario: str,
    company_name: str | None = None,
    ticker: str | None = None,
    market: str | None = None,
    top_k: int | None = None,
    model: str | None = None,
    filters: Any = None,
    vector_store: str = "faiss",
) -> dict[str, Any]:
    clean_scenario = " ".join(scenario.strip().split())
    if not clean_scenario:
        raise ReasoningManagerError("Scenario cannot be empty.")
    selected_top_k = _validated_top_k(top_k)
    selected_model = (model or _default_model()).strip()
    normalized_filters = _filters_dict(filters)
    parsed = scenario_parser.parse_scenario(clean_scenario, company_name, ticker, market)
    chain = causal_chain_service.build_causal_chain(parsed)

    logger.info(
        "Reasoning request received | scenario=%s | type=%s | model=%s | top_k=%s | filters=%s",
        clean_scenario,
        parsed["scenario_type"],
        selected_model,
        selected_top_k,
        normalized_filters,
    )

    try:
        evidence = reasoning_evidence_service.retrieve_reasoning_evidence(
            scenario=clean_scenario,
            parsed_scenario=parsed,
            chain_steps=chain,
            top_k=selected_top_k,
            vector_store=vector_store,
            filters=normalized_filters,
        )
    except Exception as exc:
        logger.exception("Reasoning evidence retrieval failed")
        evidence = {
            "evidence_map": [],
            "evidence_context": "",
            "retrieval_summary": {"results_found": 0, "evidence_used": 0},
            "limitations": [f"Evidence retrieval failed: {exc}"],
        }

    evidence_map = evidence.get("evidence_map", [])
    chain = reasoning_evidence_service.attach_evidence_to_chain(chain, evidence_map)
    company = parsed.get("company_name", "")
    parsed_ticker = parsed.get("ticker", "")
    parsed_market = parsed.get("market", "")
    company_map, sector_dependencies, macro_channels, operational_exposures = _build_context_objects(
        parsed,
        clean_scenario,
        company,
        parsed_ticker,
        parsed_market,
        chain,
        evidence_map,
    )
    exposure_analysis = multi_hop_reasoning_service.build_financial_exposure_analysis(
        parsed,
        company_map,
        sector_dependencies,
        macro_channels,
        operational_exposures,
        evidence_map,
    )
    confidence = _confidence(evidence_map, chain)

    if _require_evidence() and not evidence_map:
        output = {
            "reasoning_id": reasoning_output_service.generate_reasoning_id(clean_scenario),
            "scenario": clean_scenario,
            "company_name": company,
            "ticker": parsed_ticker,
            "market": parsed_market,
            "scenario_type": parsed["scenario_type"],
            "direct_answer": multi_hop_reasoning_service.insufficient_evidence_direct_answer(clean_scenario),
            "causal_chain": chain,
            "financial_exposure_analysis": exposure_analysis,
            "evidence_map": [],
            "confidence": confidence,
            "limitations": _base_limitations(evidence.get("limitations", [])),
            "validation_warnings": ["No qualifying evidence was retrieved, so the local LLM was not called."],
            "not_financial_advice": True,
            "status": "insufficient_evidence",
            "created_at": utc_now_iso(),
            "model": selected_model,
            "error_message": "",
        }
        logger.info("Reasoning request blocked before LLM because no evidence was available")
        return _save(reasoning_validation_service.validate_reasoning_output(output))

    running = check_ollama_running()
    installed = list_local_models() if running else []
    if installed and selected_model not in installed:
        message = f"Requested Ollama model '{selected_model}' is not installed locally."
        output = _error_output(
            clean_scenario,
            parsed,
            chain,
            exposure_analysis,
            evidence_map,
            confidence,
            selected_model,
            message,
            evidence.get("limitations", []),
        )
        return _save(reasoning_validation_service.validate_reasoning_output(output))

    prompt = reasoning_prompt_builder.build_reasoning_prompt(
        clean_scenario,
        parsed,
        chain,
        evidence.get("evidence_context", ""),
        company_map,
        sector_dependencies,
        macro_channels,
        operational_exposures,
    )
    try:
        direct_answer = multi_hop_reasoning_service.run_llm_reasoning(
            prompt,
            selected_model,
            _section("llm"),
        )
        logger.info("Reasoning Ollama call completed | model=%s", selected_model)
    except OllamaServiceError as exc:
        logger.warning("Reasoning Ollama call failed: %s", exc)
        output = _error_output(
            clean_scenario,
            parsed,
            chain,
            exposure_analysis,
            evidence_map,
            confidence,
            selected_model,
            str(exc),
            evidence.get("limitations", []),
        )
        return _save(reasoning_validation_service.validate_reasoning_output(output))

    output = {
        "reasoning_id": reasoning_output_service.generate_reasoning_id(clean_scenario),
        "scenario": clean_scenario,
        "company_name": company,
        "ticker": parsed_ticker,
        "market": parsed_market,
        "scenario_type": parsed["scenario_type"],
        "direct_answer": direct_answer,
        "causal_chain": chain,
        "financial_exposure_analysis": exposure_analysis,
        "evidence_map": evidence_map,
        "confidence": confidence,
        "limitations": _base_limitations(evidence.get("limitations", [])),
        "validation_warnings": [],
        "not_financial_advice": True,
        "status": "success",
        "created_at": utc_now_iso(),
        "model": selected_model,
        "error_message": "",
    }
    output = reasoning_validation_service.validate_reasoning_output(output)
    logger.info(
        "Reasoning response built | confidence=%s | warnings=%s | status=%s",
        output["confidence"].get("score"),
        len(output.get("validation_warnings", [])),
        output["status"],
    )
    return _save(output)


def _error_output(
    scenario: str,
    parsed: dict[str, Any],
    chain: list[dict[str, Any]],
    exposure_analysis: dict[str, str],
    evidence_map: list[dict[str, Any]],
    confidence: dict[str, Any],
    model: str,
    message: str,
    extra_limitations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "reasoning_id": reasoning_output_service.generate_reasoning_id(scenario),
        "scenario": scenario,
        "company_name": parsed.get("company_name", ""),
        "ticker": parsed.get("ticker", ""),
        "market": parsed.get("market", ""),
        "scenario_type": parsed.get("scenario_type", "unknown"),
        "direct_answer": message,
        "causal_chain": chain,
        "financial_exposure_analysis": exposure_analysis,
        "evidence_map": evidence_map,
        "confidence": {"level": "low", "score": 0.0, "reason": "The reasoning request could not complete successfully."}
        if not evidence_map
        else confidence,
        "limitations": _base_limitations([message] + list(extra_limitations or [])),
        "validation_warnings": [message],
        "not_financial_advice": True,
        "status": "error",
        "created_at": utc_now_iso(),
        "model": model,
        "error_message": message,
    }


def causal_chain_only(scenario: str, company_name: str = "", ticker: str = "", market: str = "") -> dict[str, Any]:
    clean_scenario = " ".join(scenario.strip().split())
    if not clean_scenario:
        raise ReasoningManagerError("Scenario cannot be empty.")
    parsed = scenario_parser.parse_scenario(clean_scenario, company_name, ticker, market)
    return {
        "scenario": clean_scenario,
        "scenario_type": parsed["scenario_type"],
        "causal_chain": causal_chain_service.build_causal_chain(parsed),
        "status": "success",
    }


def evidence_map_only(
    scenario: str,
    company_name: str = "",
    ticker: str = "",
    market: str = "",
    top_k: int | None = None,
    filters: Any = None,
    vector_store: str = "faiss",
) -> dict[str, Any]:
    clean_scenario = " ".join(scenario.strip().split())
    if not clean_scenario:
        raise ReasoningManagerError("Scenario cannot be empty.")
    parsed = scenario_parser.parse_scenario(clean_scenario, company_name, ticker, market)
    chain = causal_chain_service.build_causal_chain(parsed)
    evidence = reasoning_evidence_service.retrieve_reasoning_evidence(
        clean_scenario,
        parsed,
        chain,
        _validated_top_k(top_k),
        vector_store=vector_store,
        filters=_filters_dict(filters),
    )
    return {
        "scenario": clean_scenario,
        "scenario_type": parsed["scenario_type"],
        "evidence_map": evidence.get("evidence_map", []),
        "retrieval_summary": evidence.get("retrieval_summary", {}),
        "limitations": _base_limitations(evidence.get("limitations", [])),
        "status": "success" if evidence.get("evidence_map") else "insufficient_evidence",
    }
