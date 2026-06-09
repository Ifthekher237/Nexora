"""Citation and source-traceability helpers for Nexora RAG."""

from __future__ import annotations

import re
from typing import Any

from backend.app.schemas.rag import RAGSource


def _metadata(evidence: dict[str, Any]) -> dict[str, str]:
    raw_metadata = evidence.get("metadata") or {}
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}
    return {str(key): str(value or "") for key, value in raw_metadata.items()}


def build_sources(evidence: list[dict[str, Any]]) -> list[RAGSource]:
    sources: list[RAGSource] = []
    for item in evidence:
        metadata = _metadata(item)
        source_number = int(item.get("source_number") or len(sources) + 1)
        sources.append(
            RAGSource(
                rank=source_number,
                score=float(item.get("score") or 0.0),
                chunk_id=str(item.get("chunk_id") or metadata.get("chunk_id", "")),
                source_document_id=metadata.get("source_document_id", ""),
                processed_document_id=metadata.get("processed_document_id", ""),
                company_name=metadata.get("company_name", ""),
                ticker=metadata.get("ticker", ""),
                market=metadata.get("market", ""),
                document_type=metadata.get("document_type", ""),
                source_type=metadata.get("source_type", ""),
                published_at=metadata.get("published_at", ""),
                source_url=metadata.get("source_url", ""),
                section_hint=metadata.get("section_hint", ""),
                evidence_text=str(item.get("chunk_text") or ""),
            )
        )
    return sources


def available_source_numbers(sources: list[RAGSource]) -> set[int]:
    return {source.rank for source in sources}


def answer_citation_numbers(answer: str) -> set[int]:
    return {int(match) for match in re.findall(r"\[Source\s+(\d+)\]", answer)}


def has_traceable_citations(answer: str, sources: list[RAGSource]) -> bool:
    if not sources:
        return False
    cited = answer_citation_numbers(answer)
    return bool(cited) and cited.issubset(available_source_numbers(sources))


def source_reference_list(sources: list[RAGSource]) -> str:
    if not sources:
        return "No sources available."
    lines = []
    for source in sources:
        parts = [
            f"[Source {source.rank}]",
            f"score={source.score:.4f}",
            f"chunk_id={source.chunk_id}",
        ]
        if source.ticker:
            parts.append(f"ticker={source.ticker}")
        if source.document_type:
            parts.append(f"document_type={source.document_type}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)
