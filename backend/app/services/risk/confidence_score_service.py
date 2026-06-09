"""Confidence scoring separate from risk scoring."""

from __future__ import annotations

from typing import Any


def _level(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def score_confidence(
    reasoning_output: dict[str, Any],
    evidence_strength_score: int,
    validation_warnings: list[str] | None = None,
) -> dict[str, Any]:
    reasoning_confidence = reasoning_output.get("confidence") or {}
    base = float(reasoning_confidence.get("score") or 0.0)
    evidence_factor = evidence_strength_score / 100
    evidence_map = reasoning_output.get("evidence_map") or []
    warnings = list(validation_warnings or reasoning_output.get("validation_warnings") or [])
    limitations = reasoning_output.get("limitations") or []

    score = (base * 0.60) + (evidence_factor * 0.40)
    if not evidence_map:
        score -= 0.25
    score -= min(len(warnings) * 0.08, 0.32)
    score -= min(len(limitations) * 0.015, 0.12)
    score = max(0.0, min(1.0, round(score, 2)))

    return {
        "confidence_score": score,
        "confidence_level": _level(score),
        "reason": (
            f"Confidence combines Phase 6 confidence {base:.2f}, evidence strength "
            f"{evidence_strength_score}/100, {len(warnings)} validation warning(s), "
            f"and {len(limitations)} limitation(s)."
        ),
    }
