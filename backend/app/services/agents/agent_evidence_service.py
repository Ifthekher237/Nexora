"""Evidence retrieval helpers for financial agents."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.services.retrieval import retrieval_service


logger = logging.getLogger(__name__)


class AgentEvidenceError(RuntimeError):
    """Raised when agent evidence retrieval fails."""


def _filters(
    base_filters: dict[str, Any] | None = None,
    *,
    ticker: str = "",
    market: str = "",
    source_type: str | None = None,
) -> dict[str, Any]:
    raw = dict(base_filters or {})
    if ticker and not raw.get("ticker"):
        raw["ticker"] = ticker
    if market and not raw.get("market"):
        raw["market"] = market
    if source_type:
        raw["source_type"] = source_type
    return {
        "ticker": raw.get("ticker") or None,
        "source_type": raw.get("source_type") or None,
        "document_type": raw.get("document_type") or None,
        "market": raw.get("market") or None,
        "section_hint": raw.get("section_hint") or None,
    }


def _normalize_result(result: dict[str, Any], rank: int, relevance: str) -> dict[str, Any]:
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    return {
        "source_number": f"Source {rank}",
        "chunk_id": metadata.get("chunk_id") or result.get("chunk_id", ""),
        "source_document_id": metadata.get("source_document_id", ""),
        "processed_document_id": metadata.get("processed_document_id", ""),
        "relevance": relevance,
        "score": float(result.get("score") or 0.0),
        "evidence_text": str(result.get("chunk_text") or "")[:800],
        "metadata": metadata,
    }


def retrieve_agent_evidence(
    *,
    scenario: str,
    focus_terms: list[str],
    top_k: int,
    vector_store: str = "faiss",
    filters: dict[str, Any] | None = None,
    ticker: str = "",
    market: str = "",
    source_type: str | None = None,
) -> list[dict[str, Any]]:
    query_terms = " ".join(term for term in focus_terms if term)
    query = " ".join([scenario.strip(), query_terms]).strip()
    if not query:
        raise AgentEvidenceError("Agent evidence query cannot be empty.")
    normalized_filters = _filters(filters, ticker=ticker, market=market, source_type=source_type)
    try:
        result = retrieval_service.search(
            query=query,
            top_k=top_k,
            vector_store=vector_store,
            filters=normalized_filters,
        )
    except Exception as exc:
        logger.exception("Agent evidence retrieval failed")
        raise AgentEvidenceError(str(exc)) from exc
    evidence = [
        _normalize_result(item, rank=index, relevance=query_terms or "scenario evidence")
        for index, item in enumerate(result.get("results", []), start=1)
        if isinstance(item, dict)
    ]
    logger.info("Agent evidence retrieved | query=%s | count=%s", query, len(evidence))
    return evidence
