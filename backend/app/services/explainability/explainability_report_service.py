"""Build final user-facing explainability reports."""

from __future__ import annotations

from typing import Any


def recommendation_for(coverage: dict[str, Any], unsupported_claims: list[dict[str, Any]], limitations: list[str]) -> str:
    level = coverage.get("level", "unknown")
    if unsupported_claims:
        return (
            f"Use cautiously because evidence coverage is {level} and unsupported-claim warnings require review."
        )
    if level == "high":
        return "Use as an evidence-backed audit trail, while remembering it is not investment advice."
    if level == "medium":
        return "Use cautiously because evidence coverage is medium and some evidence may be indirect."
    return "Use cautiously because evidence coverage is low or source support is limited."


def build_report(
    *,
    target_type: str,
    target_id: str,
    target_output: dict[str, Any],
    coverage: dict[str, Any],
    citations: list[dict[str, Any]],
    ranking: list[dict[str, Any]],
    confidence: dict[str, Any],
    reasoning_trace: dict[str, Any],
    document_attribution: list[dict[str, Any]],
    limitations: list[str],
    unsupported_claims: list[dict[str, Any]],
) -> dict[str, Any]:
    recommendation = recommendation_for(coverage, unsupported_claims, limitations)
    source_explanation = (
        f"{len(citations)} expanded citation(s) were available from saved {target_type} evidence. "
        "Fields marked unknown were absent from the saved output and were not invented."
    )
    overview = (
        f"This report explains saved {target_type} output {target_id}. "
        f"Evidence coverage is {coverage.get('level')} ({coverage.get('score')})."
    )
    score_explanation = str(
        target_output.get("explanation")
        or target_output.get("direct_answer")
        or target_output.get("answer")
        or "No generated explanation text was present in the saved output."
    )
    report = {
        "overview": overview,
        "source_explanation": source_explanation,
        "evidence_ranking": ranking,
        "confidence_explanation": confidence,
        "reasoning_trace": reasoning_trace,
        "document_attribution": document_attribution,
        "limitations": limitations,
        "unsupported_claim_warnings": unsupported_claims,
        "recommendation_for_use": recommendation,
    }
    return {
        "score_explanation": score_explanation,
        "recommendation": recommendation,
        "report": report,
    }
