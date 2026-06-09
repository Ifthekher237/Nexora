"""Validation guardrails for individual agent outputs."""

from __future__ import annotations

import re
from typing import Any


ADVICE_PHRASES = ["buy", "sell", "hold", "must invest", "should invest", "trading recommendation"]
PREDICTION_PHRASES = ["stock will", "share price will", "guaranteed", "will definitely", "risk-free", "no risk"]


def _contains_phrase(text: str, phrases: list[str]) -> str:
    lowered = text.lower()
    for phrase in phrases:
        if " " not in phrase and re.search(rf"\b{re.escape(phrase)}\b", lowered):
            return phrase
        if " " in phrase and phrase in lowered:
            return phrase
    return ""


def _reduce_confidence(output: dict[str, Any], penalty: float) -> None:
    confidence = output.setdefault("confidence", {"level": "low", "score": 0.0, "reason": ""})
    try:
        score = max(0.0, float(confidence.get("score", 0.0)) - penalty)
    except (TypeError, ValueError):
        score = 0.0
    confidence["score"] = round(score, 4)
    if score < 0.4:
        confidence["level"] = "low"
    elif score < 0.7:
        confidence["level"] = "medium"
    else:
        confidence["level"] = "high"


def validate_agent_output(output: dict[str, Any]) -> dict[str, Any]:
    warnings = list(output.get("validation_warnings") or [])
    limitations = list(output.get("limitations") or [])
    text = " ".join(
        [
            str(output.get("summary", "")),
            " ".join(str(item) for item in output.get("key_findings", [])),
        ]
    )

    advice_phrase = _contains_phrase(text, ADVICE_PHRASES)
    if advice_phrase:
        warnings.append(f"Investment-advice language detected: {advice_phrase}.")
        limitations.append("Agent output was adjusted because investment-advice language is not allowed.")
        _reduce_confidence(output, 0.25)

    prediction_phrase = _contains_phrase(text, PREDICTION_PHRASES)
    if prediction_phrase:
        warnings.append(f"Stock-prediction or certainty language detected: {prediction_phrase}.")
        limitations.append("Agent output was adjusted because prediction/certainty language is not allowed.")
        _reduce_confidence(output, 0.25)

    if output.get("status") == "success" and not output.get("evidence_used"):
        warnings.append("Successful agent output did not include evidence references.")
        limitations.append("Evidence references were missing, so confidence is reduced.")
        _reduce_confidence(output, 0.15)

    if not output.get("confidence"):
        warnings.append("Agent output did not include confidence.")
        output["confidence"] = {"level": "low", "score": 0.0, "reason": "Confidence was missing before validation."}

    if not limitations:
        warnings.append("Agent output did not include limitations.")
        limitations.append("No explicit limitation was supplied by the agent.")
        _reduce_confidence(output, 0.1)

    for item in output.get("evidence_used", []):
        if not item.get("chunk_id") and not item.get("source_document_id"):
            warnings.append("Evidence item lacked both chunk_id and source_document_id.")
            limitations.append("One evidence item could not be traced to a chunk or document ID.")
            _reduce_confidence(output, 0.1)
            break

    output["validation_warnings"] = sorted(set(warnings))
    output["limitations"] = sorted(set(limitations))
    return output
