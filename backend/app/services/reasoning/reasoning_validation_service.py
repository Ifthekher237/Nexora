"""Validation guardrails for financial reasoning outputs."""

from __future__ import annotations

import re
from typing import Any


INVESTMENT_ADVICE_PATTERNS = [
    r"\bshould\s+(buy|sell|hold|invest)\b",
    r"\brecommend(?:ed|s)?\s+(buying|selling|investing)\b",
]

STOCK_PREDICTION_PATTERNS = [
    r"\bstock price will\b",
    r"\bshare price will\b",
    r"\btarget price\b",
    r"\bprice target\b",
    r"\bwill\s+(rise|fall|surge|crash|drop)\b",
]


def _has_citation(text: str) -> bool:
    return bool(re.search(r"\[?Source\s+\d+\]?", text))


def _lower_confidence(confidence: dict[str, Any], amount: float = 0.15) -> dict[str, Any]:
    score = max(0.0, round(float(confidence.get("score") or 0.0) - amount, 2))
    confidence["score"] = score
    if score >= 0.75:
        confidence["level"] = "high"
    elif score >= 0.45:
        confidence["level"] = "medium"
    else:
        confidence["level"] = "low"
    return confidence


def validate_reasoning_output(output: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = list(output.get("validation_warnings", []))
    limitations: list[str] = list(output.get("limitations", []))
    direct_answer = str(output.get("direct_answer", ""))
    confidence = dict(output.get("confidence") or {"level": "low", "score": 0.0, "reason": ""})

    if output.get("evidence_map") and not _has_citation(direct_answer):
        warnings.append("The direct answer did not include source citations.")
        limitations.append("Some reasoning text lacked direct source citations; inspect the evidence map before relying on it.")
        confidence = _lower_confidence(confidence)

    if not output.get("causal_chain"):
        warnings.append("The reasoning output did not include a causal chain.")
        limitations.append("No causal chain was available for this scenario.")
        confidence = _lower_confidence(confidence)

    if not output.get("evidence_map"):
        warnings.append("The reasoning output did not include an evidence map.")
        limitations.append("No supporting evidence map was available.")
        confidence = _lower_confidence(confidence)

    if not limitations:
        warnings.append("The reasoning output did not include limitations.")
        limitations.append("Reasoning is limited to retrieved Nexora evidence and rule-based Phase 6 scaffolds.")

    lowered = direct_answer.lower()
    if any(re.search(pattern, lowered) for pattern in INVESTMENT_ADVICE_PATTERNS):
        warnings.append("Investment advice language was detected.")
        limitations.append("Nexora does not provide investment advice or trading recommendations.")
        confidence = _lower_confidence(confidence, amount=0.25)
        output["status"] = "guarded"

    if any(re.search(pattern, lowered) for pattern in STOCK_PREDICTION_PATTERNS):
        warnings.append("Stock prediction language was detected.")
        limitations.append("Nexora does not predict exact stock prices or future share-price moves.")
        confidence = _lower_confidence(confidence, amount=0.25)
        output["status"] = "guarded"

    if confidence.get("level") == "low" and re.search(r"\b(certain|certainly|guaranteed|definitely)\b", lowered):
        warnings.append("Certainty language was detected despite low confidence.")
        limitations.append("Low-confidence reasoning must be treated as uncertain.")
        confidence = _lower_confidence(confidence)

    output["confidence"] = confidence
    output["limitations"] = list(dict.fromkeys(limitations))
    output["validation_warnings"] = list(dict.fromkeys(warnings))
    output["not_financial_advice"] = True
    return output
