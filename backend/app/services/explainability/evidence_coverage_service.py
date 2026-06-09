"""Coverage scoring for saved Nexora evidence."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import get_explainability_config
from backend.app.services.explainability.evidence_ranker import RELEVANT_DOCUMENT_TYPES


def _coverage_config() -> dict[str, Any]:
    return get_explainability_config().get("coverage", {})


def calculate_coverage(citations: list[dict[str, Any]], target: dict[str, Any] | None = None) -> dict[str, Any]:
    target = target or {}
    config = _coverage_config()
    min_sources = max(1, int(config.get("min_sources_for_good_coverage", 3)))
    min_docs = max(1, int(config.get("min_unique_documents_for_good_coverage", 2)))

    sources_used = len(citations)
    unique_documents = len(
        {
            citation.get("source_document_id")
            for citation in citations
            if citation.get("source_document_id") not in {None, "", "unknown"}
        }
    )
    scores = [float(citation.get("retrieval_score") or 0.0) for citation in citations]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0
    company_specific = any(
        citation.get("company_name") not in {None, "", "unknown"}
        or citation.get("ticker") not in {None, "", "unknown"}
        for citation in citations
    )
    relevant_doc_types = any(
        str(citation.get("document_type", "")).lower() in RELEVANT_DOCUMENT_TYPES
        for citation in citations
    )

    score = (
        0.30 * min(1.0, sources_used / min_sources)
        + 0.25 * min(1.0, unique_documents / min_docs)
        + 0.25 * avg_score
        + 0.10 * (1.0 if company_specific else 0.0)
        + 0.10 * (1.0 if relevant_doc_types else 0.0)
    )
    score = round(max(0.0, min(1.0, score)), 4)
    low_threshold = float(config.get("low_coverage_threshold", 0.35))
    medium_threshold = float(config.get("medium_coverage_threshold", 0.65))
    if score < low_threshold:
        level = "low"
    elif score < medium_threshold:
        level = "medium"
    else:
        level = "high"

    target_hint = ""
    if target.get("ticker") and not company_specific:
        target_hint = f" No company-specific evidence was found for {target.get('ticker')}."
    reason = (
        f"Coverage uses {sources_used} source(s), {unique_documents} unique document(s), "
        f"average retrieval score {avg_score:.2f}, company-specific evidence={company_specific}, "
        f"and relevant document types={relevant_doc_types}.{target_hint}"
    )
    return {
        "level": level,
        "score": score,
        "reason": reason,
        "sources_used": sources_used,
        "unique_documents": unique_documents,
        "average_retrieval_score": avg_score,
        "company_specific_evidence": company_specific,
        "relevant_document_types": relevant_doc_types,
    }
