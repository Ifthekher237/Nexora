"""Build compact source-grounded context from Phase 4 retrieval results."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import get_rag_config


DEFAULT_MAX_CONTEXT_CHARS = 7000
DEFAULT_MAX_CHUNK_CHARS = 1400


def configured_min_score() -> float:
    return float(get_rag_config().get("rag", {}).get("min_retrieval_score", 0.25))


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def _shorten_text(text: str, max_chars: int) -> tuple[str, bool]:
    clean = _clean_text(text)
    if len(clean) <= max_chars:
        return clean, False
    return clean[: max_chars - 3].rstrip() + "...", True


def _metadata(result: dict[str, Any]) -> dict[str, str]:
    raw_metadata = result.get("metadata") or {}
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}
    return {str(key): str(value or "") for key, value in raw_metadata.items()}


def build_context(
    retrieval_result: dict[str, Any],
    min_score: float | None = None,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> dict[str, Any]:
    threshold = configured_min_score() if min_score is None else float(min_score)
    raw_results = retrieval_result.get("results", [])
    if not isinstance(raw_results, list):
        raw_results = []

    evidence: list[dict[str, Any]] = []
    context_blocks: list[str] = []
    total_chars = 0
    truncated = False

    for result in raw_results:
        if not isinstance(result, dict):
            continue
        score = float(result.get("score") or 0.0)
        if score < threshold:
            continue

        metadata = _metadata(result)
        chunk_text, chunk_truncated = _shorten_text(
            str(result.get("chunk_text") or ""),
            max_chars=max_chunk_chars,
        )
        if not chunk_text:
            continue

        source_number = len(evidence) + 1
        block = "\n".join(
            [
                f"[Source {source_number}]",
                f"Score: {score:.4f}",
                f"Company: {metadata.get('company_name', '')}",
                f"Ticker: {metadata.get('ticker', '')}",
                f"Document Type: {metadata.get('document_type', '')}",
                f"Source Type: {metadata.get('source_type', '')}",
                f"Published: {metadata.get('published_at', '')}",
                f"Chunk ID: {result.get('chunk_id', '')}",
                "Text:",
                chunk_text,
            ]
        )

        if total_chars + len(block) > max_context_chars and evidence:
            truncated = True
            break

        total_chars += len(block)
        truncated = truncated or chunk_truncated
        evidence.append(
            {
                "source_number": source_number,
                "original_rank": int(result.get("rank") or source_number),
                "score": score,
                "chunk_id": str(result.get("chunk_id") or metadata.get("chunk_id", "")),
                "chunk_text": chunk_text,
                "metadata": metadata,
            }
        )
        context_blocks.append(block)

    limitations: list[str] = []
    if not raw_results:
        limitations.append("No retrieval results were returned by the vector store.")
    elif not evidence:
        limitations.append(
            f"No retrieved result met the minimum evidence score of {threshold:.2f}."
        )
    if truncated:
        limitations.append("Some retrieved text was shortened to keep the prompt context compact.")

    return {
        "evidence": evidence,
        "evidence_context": "\n\n".join(context_blocks),
        "results_found": len(raw_results),
        "evidence_used": len(evidence),
        "min_score": threshold,
        "limitations": limitations,
    }
