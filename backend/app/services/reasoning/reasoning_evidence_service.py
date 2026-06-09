"""Retrieve and map evidence for financial reasoning scenarios."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import get_reasoning_config
from backend.app.services.rag import citation_service, context_builder
from backend.app.services.retrieval import retrieval_service


def _min_score() -> float:
    return float(get_reasoning_config().get("reasoning", {}).get("min_evidence_score", 0.25))


def _query_for_scenario(scenario: str, parsed_scenario: dict[str, Any]) -> str:
    parts = [
        scenario,
        parsed_scenario.get("company_name", ""),
        parsed_scenario.get("ticker", ""),
        parsed_scenario.get("scenario_type", ""),
        parsed_scenario.get("macro_trigger", ""),
        parsed_scenario.get("sector_trigger", ""),
        " ".join(parsed_scenario.get("key_risk_keywords", [])),
    ]
    return " ".join(part for part in parts if part).strip()


def _normalized_filters(
    parsed_scenario: dict[str, Any],
    filters: dict[str, Any] | None = None,
) -> dict[str, str | None]:
    filters = filters or {}
    return {
        "ticker": parsed_scenario.get("ticker") or None,
        "market": parsed_scenario.get("market") or None,
        "source_type": filters.get("source_type") or None,
        "document_type": filters.get("document_type") or None,
        "section_hint": filters.get("section_hint") or None,
    }


def _used_for(source_text: str, chain_steps: list[dict[str, Any]]) -> str:
    lowered = source_text.lower()
    for step in chain_steps:
        words = f"{step.get('cause', '')} {step.get('effect', '')}".lower().replace("/", " ").split()
        if any(len(word) > 4 and word in lowered for word in words):
            return str(step.get("effect") or step.get("cause") or "scenario exposure")
    return "general scenario context"


def _relevance(source: Any, parsed_scenario: dict[str, Any]) -> str:
    text = " ".join(
        [
            getattr(source, "evidence_text", ""),
            getattr(source, "ticker", ""),
            getattr(source, "document_type", ""),
            parsed_scenario.get("scenario_type", ""),
        ]
    ).lower()
    matches = [
        keyword
        for keyword in parsed_scenario.get("key_risk_keywords", [])
        if keyword and keyword in text
    ]
    if getattr(source, "ticker", "") and source.ticker == parsed_scenario.get("ticker"):
        matches.append("ticker match")
    return ", ".join(matches) if matches else "retrieved semantic match"


def retrieve_reasoning_evidence(
    scenario: str,
    parsed_scenario: dict[str, Any],
    chain_steps: list[dict[str, Any]],
    top_k: int,
    vector_store: str = "faiss",
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = _query_for_scenario(scenario, parsed_scenario)
    retrieval_result = retrieval_service.search(
        query=query,
        top_k=top_k,
        vector_store=vector_store,
        filters=_normalized_filters(parsed_scenario, filters),
    )
    context = context_builder.build_context(retrieval_result, min_score=_min_score())
    sources = citation_service.build_sources(context["evidence"])

    evidence_map: list[dict[str, Any]] = []
    for source in sources:
        item = {
            "source_number": f"Source {source.rank}",
            "chunk_id": source.chunk_id,
            "source_document_id": source.source_document_id,
            "processed_document_id": source.processed_document_id,
            "relevance": _relevance(source, parsed_scenario),
            "used_for": _used_for(source.evidence_text, chain_steps),
            "score": source.score,
            "evidence_text": source.evidence_text,
            "metadata": {
                "company_name": source.company_name,
                "ticker": source.ticker,
                "market": source.market,
                "document_type": source.document_type,
                "source_type": source.source_type,
                "published_at": source.published_at,
                "section_hint": source.section_hint,
            },
        }
        evidence_map.append(item)

    retrieval_summary = {
        "results_found": int(context.get("results_found", 0)),
        "evidence_used": int(context.get("evidence_used", 0)),
        "min_score": float(context.get("min_score", _min_score())),
    }
    return {
        "query": query,
        "evidence_context": context["evidence_context"],
        "evidence": context["evidence"],
        "sources": sources,
        "evidence_map": evidence_map,
        "retrieval_summary": retrieval_summary,
        "limitations": context.get("limitations", []),
    }


def attach_evidence_to_chain(
    chain_steps: list[dict[str, Any]],
    evidence_map: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for step in chain_steps:
        step_text = f"{step.get('cause', '')} {step.get('effect', '')}".lower()
        supporting = [
            item["source_number"]
            for item in evidence_map
            if any(word in item.get("evidence_text", "").lower() for word in step_text.split() if len(word) > 4)
        ]
        unique_supporting = sorted(set(supporting), key=supporting.index)
        updated = dict(step)
        updated["supporting_sources"] = unique_supporting[:4]
        if len(unique_supporting) >= 2:
            updated["evidence_strength"] = "medium"
            updated["uncertainty"] = "Supported by multiple retrieved sources, but Phase 6 does not quantify impact."
        elif len(unique_supporting) == 1:
            updated["evidence_strength"] = "low"
            updated["uncertainty"] = "Partially supported by one retrieved source; treat the link as cautious."
        else:
            updated["evidence_strength"] = "low"
            updated["uncertainty"] = "Plausible scenario scaffold step, but not directly confirmed by retrieved evidence."
        enriched.append(updated)
    return enriched
