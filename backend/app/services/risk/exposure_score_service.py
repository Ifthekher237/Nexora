"""Exposure breadth scoring for risk outputs."""

from __future__ import annotations

from typing import Any

from backend.app.services.risk.scoring_engine import clamp_score


EXPOSURE_KEYWORDS = [
    "cost structure",
    "pricing power",
    "customer demand",
    "debt",
    "refinancing",
    "cash flow",
    "supply chain",
    "labor",
    "regulatory",
    "revenue",
    "margin",
]


def score_exposure(reasoning_output: dict[str, Any]) -> dict[str, Any]:
    exposure = reasoning_output.get("financial_exposure_analysis") or {}
    text = " ".join(str(value) for value in exposure.values()).lower()
    chain = reasoning_output.get("causal_chain") or []
    evidence_map = reasoning_output.get("evidence_map") or []
    matched = [keyword for keyword in EXPOSURE_KEYWORDS if keyword in text]
    supported = sum(1 for step in chain if step.get("supporting_sources"))
    evidence_used_for = {item.get("used_for", "") for item in evidence_map if item.get("used_for")}
    score = clamp_score(min(len(matched) / 7, 1.0) * 55 + min(len(chain) / 5, 1.0) * 20 + min(supported / 3, 1.0) * 15 + min(len(evidence_used_for) / 4, 1.0) * 10)
    level = "high" if score >= 67 else "moderate" if score >= 34 else "low"
    return {
        "exposure_score": score,
        "exposure_level": level,
        "matched_exposures": matched,
        "reason": f"Exposure score found {len(matched)} exposure area(s), {len(chain)} causal step(s), and {supported} evidence-supported step(s).",
    }
