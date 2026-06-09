"""Hallucination-reduction checks for financial RAG answers."""

from __future__ import annotations

import re
from typing import Any

from backend.app.core.config import get_rag_config
from backend.app.services.rag import citation_service
from backend.app.schemas.rag import RAGSource


STOCK_PREDICTION_PATTERNS = [
    r"\bwill\s+(rise|fall|increase|decrease|drop|surge)\b",
    r"\bguaranteed\b",
    r"\btarget price\b",
    r"\bprice target\b",
    r"\bbuy\b|\bsell\b|\bhold\b",
]


def insufficient_evidence_answer(question: str, reason: str) -> str:
    return (
        "- Direct Answer\n"
        "The available retrieved evidence is insufficient to answer the question reliably.\n\n"
        "- Evidence-Based Analysis\n"
        f"{reason}\n\n"
        "- Sources Used\n"
        "No qualifying sources were available.\n\n"
        "- Confidence\n"
        "Low.\n\n"
        "- Limitations\n"
        "Nexora only answers from retrieved local evidence and does not provide financial advice."
    )


def should_block_without_llm(evidence: list[dict[str, Any]]) -> tuple[bool, str]:
    config = get_rag_config().get("rag", {})
    if evidence:
        return False, ""
    if bool(config.get("allow_answer_without_evidence", False)):
        return False, ""
    return True, "No qualifying evidence was retrieved, so the LLM was not called."


def _contains_stock_prediction(answer: str) -> bool:
    lowered = answer.lower()
    return any(re.search(pattern, lowered) for pattern in STOCK_PREDICTION_PATTERNS)


def validate_answer(answer: str, sources: list[RAGSource]) -> dict[str, Any]:
    config = get_rag_config().get("rag", {})
    require_citations = bool(config.get("require_citations", True))
    limitations: list[str] = []
    final_answer = answer.strip()
    status = "success"

    if not final_answer:
        return {
            "answer": insufficient_evidence_answer(
                "",
                "The local LLM returned an empty response.",
            ),
            "status": "error",
            "limitations": ["The local LLM returned an empty response."],
        }

    if require_citations and sources and not citation_service.has_traceable_citations(final_answer, sources):
        limitations.append(
            "The model response did not include valid source citations, so source traceability was appended."
        )
        final_answer = (
            f"{final_answer.rstrip()}\n\n"
            "- Sources Used\n"
            f"{citation_service.source_reference_list(sources)}"
        )

    if _contains_stock_prediction(final_answer):
        limitations.append(
            "The answer was adjusted because Nexora must not provide stock predictions or trading advice."
        )
        final_answer = (
            f"{final_answer.rstrip()}\n\n"
            "Nexora does not provide stock price predictions, buy/sell/hold calls, or investment advice."
        )
        status = "guarded"

    return {"answer": final_answer, "status": status, "limitations": limitations}
