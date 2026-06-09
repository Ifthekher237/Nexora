"""Macro risk scoring from scenario type and macro exposure analysis."""

from __future__ import annotations

from typing import Any

from backend.app.services.risk.scoring_engine import clamp_score


MACRO_TERMS = {
    "interest rates": 18,
    "inflation": 18,
    "commodity": 16,
    "exchange rates": 14,
    "unemployment": 10,
    "liquidity": 14,
    "regulation": 12,
}

SCENARIO_MACRO_BASE = {
    "interest_rate_change": 42,
    "inflation_pressure": 42,
    "oil_price_shock": 40,
    "currency_movement": 38,
    "liquidity_stress": 44,
    "regulatory_change": 36,
    "unknown": 25,
}


def score_macro_risk(reasoning_output: dict[str, Any]) -> dict[str, Any]:
    scenario_type = reasoning_output.get("scenario_type", "unknown")
    exposure = reasoning_output.get("financial_exposure_analysis") or {}
    text = f"{scenario_type} {exposure.get('macro_exposure', '')} {reasoning_output.get('scenario', '')}".lower()
    matched = [term for term in MACRO_TERMS if term in text]
    score = clamp_score(SCENARIO_MACRO_BASE.get(scenario_type, SCENARIO_MACRO_BASE["unknown"]) + sum(MACRO_TERMS[term] for term in matched))
    return {
        "macro_risk_score": score,
        "matched_terms": matched,
        "reason": f"Macro risk uses scenario type {scenario_type} and macro channel mentions: {', '.join(matched) or 'none'}."
    }
