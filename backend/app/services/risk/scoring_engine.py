"""Deterministic score combination and risk-level mapping."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import get_risk_config


def clamp_score(value: float | int) -> int:
    config = get_risk_config().get("risk_scoring", {})
    minimum = int(config.get("scale_min", 0))
    maximum = int(config.get("scale_max", 100))
    return max(minimum, min(maximum, int(round(float(value)))))


def risk_level(score: int) -> str:
    levels = get_risk_config().get("risk_levels", {})
    for level, bounds in levels.items():
        if int(bounds.get("min", 0)) <= score <= int(bounds.get("max", 100)):
            return level
    return "unknown"


def causal_chain_strength_score(reasoning_output: dict[str, Any]) -> int:
    chain = reasoning_output.get("causal_chain") or []
    if not chain:
        return 0
    supported = sum(1 for step in chain if step.get("supporting_sources"))
    return clamp_score((supported / len(chain)) * 100)


def source_diversity_score(evidence_summary: dict[str, Any]) -> int:
    sources = int(evidence_summary.get("sources_used") or 0)
    if sources <= 0:
        return 0
    diversity = float(evidence_summary.get("source_diversity") or 0.0)
    return clamp_score(diversity * 100)


def combine_scores(
    evidence_strength_score: int,
    reasoning_confidence_score: float,
    causal_chain_score: int,
    exposure_score: int,
    macro_risk_score: int,
    source_diversity: int,
) -> dict[str, Any]:
    weights = get_risk_config().get("weights", {})
    weighted = {
        "evidence_strength": evidence_strength_score * float(weights.get("evidence_strength", 0.25)),
        "reasoning_confidence": reasoning_confidence_score * 100 * float(weights.get("reasoning_confidence", 0.20)),
        "causal_chain_strength": causal_chain_score * float(weights.get("causal_chain_strength", 0.20)),
        "exposure_breadth": exposure_score * float(weights.get("exposure_breadth", 0.15)),
        "macro_relevance": macro_risk_score * float(weights.get("macro_relevance", 0.10)),
        "source_diversity": source_diversity * float(weights.get("source_diversity", 0.10)),
    }
    score = clamp_score(sum(weighted.values()))
    return {
        "overall_risk_score": score,
        "overall_risk_level": risk_level(score),
        "weighted_components": weighted,
        "calculation_explanation": (
            "Overall risk is a weighted 0-100 analytical estimate using configured "
            "weights for evidence strength, reasoning confidence, causal-chain support, "
            "exposure breadth, macro relevance, and source diversity."
        ),
    }
