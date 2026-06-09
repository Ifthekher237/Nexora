"""Evidence-quality confidence estimation for RAG answers."""

from __future__ import annotations

from typing import Any


DIRECT_MATCH_TERMS = {
    "risk",
    "revenue",
    "debt",
    "liquidity",
    "inflation",
    "interest",
    "rate",
    "oil",
    "regulation",
    "supply",
    "chain",
}


def _score_level(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def estimate_confidence(
    evidence: list[dict[str, Any]],
    question: str,
    retrieval_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not evidence:
        return {
            "level": "low",
            "score": 0.0,
            "reason": "No usable retrieved evidence met the configured relevance threshold.",
        }

    scores = [float(item.get("score") or 0.0) for item in evidence]
    top_score = max(scores)
    average_score = sum(scores) / len(scores)
    unique_documents = {
        str((item.get("metadata") or {}).get("source_document_id") or item.get("chunk_id"))
        for item in evidence
    }
    question_terms = {
        token
        for token in question.lower().replace("-", " ").split()
        if len(token) > 3 or token in {"oil", "debt"}
    }
    evidence_text = " ".join(str(item.get("chunk_text") or "").lower() for item in evidence)
    matching_terms = question_terms.intersection(set(evidence_text.split()))
    direct_risk_match = bool(DIRECT_MATCH_TERMS.intersection(question_terms).intersection(evidence_text.split()))

    evidence_count_factor = min(len(evidence) / 5, 1.0) * 0.20
    avg_score_factor = min(average_score, 1.0) * 0.35
    top_score_factor = min(top_score, 1.0) * 0.20
    source_diversity_factor = min(len(unique_documents) / 3, 1.0) * 0.15
    direct_match_factor = (0.10 if matching_terms or direct_risk_match else 0.0)
    confidence_score = round(
        min(
            1.0,
            evidence_count_factor
            + avg_score_factor
            + top_score_factor
            + source_diversity_factor
            + direct_match_factor,
        ),
        2,
    )

    level = _score_level(confidence_score)
    summary = retrieval_summary or {}
    reason = (
        f"Based on {len(evidence)} evidence chunk(s), average score {average_score:.2f}, "
        f"top score {top_score:.2f}, and {len(unique_documents)} unique source document(s)."
    )
    if summary.get("results_found", len(evidence)) > len(evidence):
        reason += " Some retrieved results were filtered out as weak evidence."
    if not matching_terms and not direct_risk_match:
        reason += " The retrieved evidence has limited direct term overlap with the question."

    return {"level": level, "score": confidence_score, "reason": reason}
