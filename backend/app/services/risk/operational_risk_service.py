"""Operational risk scoring from Phase 6 exposure analysis."""

from __future__ import annotations

from typing import Any

from backend.app.services.risk.scoring_engine import clamp_score


OPERATIONAL_TERMS = {
    "cost structure": 14,
    "supply chain": 16,
    "labor": 10,
    "pricing power": 12,
    "customer demand": 12,
    "production": 12,
    "service disruption": 14,
    "margin": 10,
}


def score_operational_risk(reasoning_output: dict[str, Any]) -> dict[str, Any]:
    exposure = reasoning_output.get("financial_exposure_analysis") or {}
    text = f"{exposure.get('operational_exposure', '')} {reasoning_output.get('direct_answer', '')}".lower()
    matched = [term for term in OPERATIONAL_TERMS if term in text]
    score = clamp_score(25 + sum(OPERATIONAL_TERMS[term] for term in matched))
    return {
        "operational_risk_score": score,
        "matched_terms": matched,
        "reason": f"Operational risk reflects matched operational exposure terms: {', '.join(matched) or 'none'}."
    }
