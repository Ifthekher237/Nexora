"""Validation guardrails for risk scoring outputs."""

from __future__ import annotations

import re
from typing import Any


ADVICE_PATTERNS = [
    r"\bshould\s+(buy|sell|hold|invest)\b",
    r"\brecommend(?:ed|s)?\s+(buying|selling|investing)\b",
]

PREDICTION_PATTERNS = [
    r"\bstock price will\b",
    r"\bshare price will\b",
    r"\btarget price\b",
    r"\bprice target\b",
]


def _lower_confidence(confidence: dict[str, Any], amount: float = 0.15) -> dict[str, Any]:
    score = max(0.0, round(float(confidence.get("score") or 0.0) - amount, 2))
    confidence["score"] = score
    confidence["level"] = "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"
    return confidence


def validate_risk_output(output: dict[str, Any]) -> dict[str, Any]:
    warnings = list(output.get("validation_warnings", []))
    limitations = list(output.get("limitations", []))
    confidence = dict(output.get("confidence") or {"level": "low", "score": 0.0, "reason": ""})

    score = output.get("overall_risk_score")
    if not isinstance(score, int) or score < 0 or score > 100:
        warnings.append("Overall risk score was invalid and must be clamped to 0-100.")
        output["overall_risk_score"] = max(0, min(100, int(score or 0)))
        confidence = _lower_confidence(confidence)

    if not output.get("overall_risk_level"):
        warnings.append("Risk level was missing.")
        limitations.append("Risk level could not be mapped from the score.")
        confidence = _lower_confidence(confidence)

    if not output.get("evidence_summary"):
        warnings.append("Evidence summary was missing.")
        limitations.append("Risk score has limited support because evidence summary was unavailable.")
        confidence = _lower_confidence(confidence)

    if not limitations:
        warnings.append("Limitations were missing.")
        limitations.append("Risk scoring is limited to available Nexora evidence and Phase 6 reasoning output.")

    if not output.get("not_financial_advice", False):
        warnings.append("Financial advice notice was missing.")
        limitations.append("Nexora risk scores are not investment advice.")
        confidence = _lower_confidence(confidence)

    text = " ".join(
        [
            output.get("explanation", ""),
            " ".join(driver.get("explanation", "") for driver in output.get("risk_drivers", [])),
        ]
    ).lower()
    if any(re.search(pattern, text) for pattern in ADVICE_PATTERNS):
        warnings.append("Investment recommendation language was detected.")
        limitations.append("Nexora does not provide buy/sell/hold recommendations.")
        confidence = _lower_confidence(confidence, amount=0.25)
        output["status"] = "guarded"

    if any(re.search(pattern, text) for pattern in PREDICTION_PATTERNS):
        warnings.append("Stock prediction language was detected.")
        limitations.append("Nexora does not predict exact stock prices.")
        confidence = _lower_confidence(confidence, amount=0.25)
        output["status"] = "guarded"

    if confidence.get("level") == "low" and re.search(r"\b(certain|guaranteed|definitely)\b", text):
        warnings.append("Unsupported certainty language was detected.")
        limitations.append("Low-confidence scores must be treated as uncertain analytical estimates.")
        confidence = _lower_confidence(confidence)

    output["confidence"] = confidence
    output["limitations"] = list(dict.fromkeys(limitations))
    output["validation_warnings"] = list(dict.fromkeys(warnings))
    output["not_financial_advice"] = True
    return output
