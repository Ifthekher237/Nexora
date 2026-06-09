"""Plain-English risk explanations and drivers."""

from __future__ import annotations

from typing import Any


def _impact(score: int) -> str:
    if score >= 67:
        return "high"
    if score >= 34:
        return "medium"
    return "low"


def build_risk_drivers(
    breakdown: dict[str, int],
    reasoning_output: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence_map = reasoning_output.get("evidence_map") or []
    source_refs = [item.get("source_number", "") for item in evidence_map[:3] if item.get("source_number")]
    labels = {
        "operational_risk_score": "Operational exposure",
        "macro_risk_score": "Macro sensitivity",
        "sector_risk_score": "Sector dependency",
        "company_specific_risk_score": "Company-specific evidence",
        "vulnerability_score": "Scenario vulnerability",
        "evidence_strength_score": "Evidence strength",
    }
    ranked = sorted(breakdown.items(), key=lambda item: item[1], reverse=True)
    return [
        {
            "driver": labels.get(key, key.replace("_", " ")),
            "score_impact": _impact(score),
            "supporting_sources": source_refs,
            "explanation": f"{labels.get(key, key)} contributed a component score of {score}/100.",
        }
        for key, score in ranked[:4]
    ]


def explain_score(
    risk_output: dict[str, Any],
    calculation_explanation: str = "",
) -> str:
    confidence = risk_output.get("confidence") or {}
    evidence_summary = risk_output.get("evidence_summary") or {}
    return (
        f"The overall risk score is {risk_output.get('overall_risk_score')}/100 "
        f"({risk_output.get('overall_risk_level')}). This is an evidence-backed analytical "
        "estimate, not a forecast or investment recommendation. "
        f"{calculation_explanation} Confidence is {confidence.get('level')} "
        f"({confidence.get('score')}) because {confidence.get('reason', '')} "
        f"The score used {evidence_summary.get('sources_used', 0)} source(s), "
        f"{evidence_summary.get('unique_documents', 0)} unique document(s), and "
        f"{evidence_summary.get('supported_chain_steps', 0)} evidence-supported causal step(s). "
        "Risk score measures estimated exposure/vulnerability; confidence measures how well the available evidence supports that estimate."
    )
