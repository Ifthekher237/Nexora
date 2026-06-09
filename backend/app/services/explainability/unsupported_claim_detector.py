"""Simple rule-based unsupported claim detection for saved generated text."""

from __future__ import annotations

import re
from typing import Any

from backend.app.core.config import get_explainability_config


NEGATION_HINTS = ["not", "no ", "does not", "do not", "without", "avoid"]


def _config() -> dict[str, Any]:
    return get_explainability_config().get("unsupported_claim_detection", {})


def _guardrails() -> dict[str, Any]:
    return get_explainability_config().get("guardrails", {})


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text or "") if sentence.strip()]


def _is_negated(sentence: str, phrase: str) -> bool:
    lower = sentence.lower()
    index = lower.find(phrase.lower())
    if index < 0:
        return False
    window = lower[max(0, index - 35) : index]
    return any(hint in window for hint in NEGATION_HINTS)


def _claim_without_citation(sentence: str) -> bool:
    if len(sentence.split()) < 8:
        return False
    if re.search(r"\[Source\s+\d+\]|Source\s+\d+", sentence):
        return False
    financial_terms = ["risk", "cost", "pressure", "revenue", "cash flow", "debt", "margin", "stock", "profit"]
    return any(term in sentence.lower() for term in financial_terms)


def detect_unsupported_claims(text: str, citations_required: bool = True) -> list[dict[str, str]]:
    config = _config()
    if not bool(config.get("enabled", True)):
        return []

    risky_phrases = [str(phrase).lower() for phrase in config.get("risky_phrases", [])]
    claims: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for sentence in _sentences(text):
        lower = sentence.lower()
        for phrase in risky_phrases:
            if phrase in lower and not _is_negated(sentence, phrase):
                issue_type = "stock_prediction" if "stock" in phrase else "investment_advice"
                if phrase in {"will definitely", "guaranteed", "certainly", "no risk", "risk-free"}:
                    issue_type = "unsupported_certainty"
                key = (sentence, issue_type)
                if key not in seen:
                    claims.append(
                        {
                            "claim": sentence,
                            "issue_type": issue_type,
                            "severity": "high" if issue_type in {"investment_advice", "stock_prediction"} else "medium",
                            "suggested_fix": "Rephrase as evidence-limited analysis and add source support or a limitation.",
                        }
                    )
                    seen.add(key)
        if citations_required and bool(_guardrails().get("require_evidence_reference_for_claims", True)):
            if _claim_without_citation(sentence):
                key = (sentence, "missing_citation")
                if key not in seen:
                    claims.append(
                        {
                            "claim": sentence,
                            "issue_type": "missing_citation",
                            "severity": "medium",
                            "suggested_fix": "Add a source reference or mark the statement as unsupported/uncertain.",
                        }
                    )
                    seen.add(key)
    return claims
