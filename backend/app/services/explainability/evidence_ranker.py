"""Rank evidence using only available retrieval and metadata signals."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.core.config import get_explainability_config


RELEVANT_DOCUMENT_TYPES = {
    "annual_report",
    "10-k",
    "10-q",
    "8-k",
    "sec",
    "financial_statement",
    "transcript",
    "news",
    "sd",
    "144",
    "4",
}


def _weights() -> dict[str, float]:
    return get_explainability_config().get("evidence_ranking", {}).get("weights", {})


def _parse_date(value: str) -> datetime | None:
    if not value or value == "unknown":
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).replace(tzinfo=None)
    except ValueError:
        try:
            return datetime.fromisoformat(text[:10]).replace(tzinfo=None)
        except ValueError:
            return None


def _recency_scores(citations: list[dict[str, Any]]) -> dict[str, float]:
    parsed = {
        citation.get("chunk_id", ""): _parse_date(str(citation.get("published_date", "")))
        for citation in citations
    }
    valid_dates = [date for date in parsed.values() if date is not None]
    if not valid_dates:
        return {citation.get("chunk_id", ""): 0.0 for citation in citations}
    newest = max(valid_dates)
    scores: dict[str, float] = {}
    for chunk_id, date in parsed.items():
        if date is None:
            scores[chunk_id] = 0.0
            continue
        days = max(0, (newest - date).days)
        if days <= 30:
            scores[chunk_id] = 1.0
        elif days <= 180:
            scores[chunk_id] = 0.75
        elif days <= 365:
            scores[chunk_id] = 0.5
        else:
            scores[chunk_id] = 0.25
    return scores


def _document_relevance(document_type: str) -> float:
    normalized = (document_type or "unknown").lower()
    if normalized in {"unknown", ""}:
        return 0.0
    if normalized in RELEVANT_DOCUMENT_TYPES:
        return 0.85
    return 0.45


def rank_evidence(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weights = _weights()
    recency_by_chunk = _recency_scores(citations)
    type_counts: dict[str, int] = {}
    for citation in citations:
        source_type = str(citation.get("source_type", "unknown")).lower()
        type_counts[source_type] = type_counts.get(source_type, 0) + 1

    ranked: list[dict[str, Any]] = []
    for citation in citations:
        source_type = str(citation.get("source_type", "unknown")).lower()
        retrieval = float(citation.get("retrieval_score") or 0.0)
        citation_usage = min(1.0, float(citation.get("citation_usage_count") or 0) / 3.0)
        diversity = 0.0 if source_type == "unknown" else 1.0 / max(1, type_counts.get(source_type, 1))
        relevance = _document_relevance(str(citation.get("document_type", "unknown")))
        recency = recency_by_chunk.get(citation.get("chunk_id", ""), 0.0)
        components = {
            "retrieval_score": retrieval,
            "source_diversity": diversity,
            "document_relevance": relevance,
            "citation_usage": citation_usage,
            "recency": recency,
        }
        weighted_score = sum(
            components[name] * float(weights.get(name, 0.0))
            for name in components
        )
        evidence_id = citation.get("chunk_id") or citation.get("source_document_id") or citation.get("source_number")
        summary = (
            f"{citation.get('source_number')} from {citation.get('source_type')} "
            f"{citation.get('document_type')} document {citation.get('source_document_id')}"
        )
        ranked.append(
            {
                "rank": 0,
                "evidence_id": str(evidence_id),
                "score": round(max(0.0, min(1.0, weighted_score)), 4),
                "rank_reason": (
                    f"retrieval={retrieval:.2f}, citation_usage={citation_usage:.2f}, "
                    f"document_relevance={relevance:.2f}, recency={recency:.2f}"
                ),
                "source_summary": summary,
                "score_components": {key: round(value, 4) for key, value in components.items()},
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
    return ranked
