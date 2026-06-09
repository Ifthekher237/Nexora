"""Group expanded citations by source document."""

from __future__ import annotations

from typing import Any


def attribute_documents(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for citation in citations:
        document_id = str(citation.get("source_document_id") or "unknown")
        group = grouped.setdefault(
            document_id,
            {
                "source_document_id": document_id,
                "company_name": citation.get("company_name", "unknown"),
                "ticker": citation.get("ticker", "unknown"),
                "document_type": citation.get("document_type", "unknown"),
                "source_type": citation.get("source_type", "unknown"),
                "published_date": citation.get("published_date", "unknown"),
                "evidence_chunk_count": 0,
                "average_retrieval_score": 0.0,
                "_scores": [],
                "supported_items": [],
            },
        )
        group["evidence_chunk_count"] += 1
        group["_scores"].append(float(citation.get("retrieval_score") or 0.0))
        support_text = f"{citation.get('source_number')}: {citation.get('chunk_text_excerpt', '')[:140]}"
        group["supported_items"].append(support_text)

    attributions: list[dict[str, Any]] = []
    for group in grouped.values():
        scores = group.pop("_scores", [])
        group["average_retrieval_score"] = round(sum(scores) / len(scores), 4) if scores else 0.0
        attributions.append(group)
    return sorted(attributions, key=lambda item: item["evidence_chunk_count"], reverse=True)
