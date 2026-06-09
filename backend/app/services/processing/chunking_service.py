"""Word-based chunking for cleaned financial document text."""

from __future__ import annotations

from backend.app.core.config import get_processing_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.processing.enrichment_service import detect_section_hint


def _chunk_settings() -> tuple[int, int, int, int]:
    config = get_processing_config().get("processing", {})
    size = int(config.get("default_chunk_size_words", 350))
    overlap = int(config.get("default_chunk_overlap_words", 60))
    min_words = int(config.get("min_chunk_words", 80))
    max_words = int(config.get("max_chunk_words", 500))

    size = max(min_words, min(size, max_words))
    overlap = max(0, min(overlap, size - 1))
    return size, overlap, min_words, max_words


def create_chunks(
    text: str,
    processed_document_id: str,
    source_document_id: str,
    metadata: dict[str, str],
) -> list[dict[str, object]]:
    """Split cleaned text into ordered overlapping word chunks."""

    words = text.split()
    if not words:
        return []

    chunk_size, overlap, _, _ = _chunk_settings()
    chunks: list[dict[str, object]] = []

    if len(words) <= chunk_size:
        chunk_text = " ".join(words)
        return [
            {
                "chunk_id": f"{processed_document_id}_chunk_0000",
                "processed_document_id": processed_document_id,
                "source_document_id": source_document_id,
                "chunk_index": 0,
                "chunk_text": chunk_text,
                "chunk_word_count": len(words),
                "chunk_char_count": len(chunk_text),
                "company_name": metadata.get("company_name", ""),
                "ticker": metadata.get("ticker", ""),
                "market": metadata.get("market", ""),
                "document_type": metadata.get("document_type", ""),
                "source_type": metadata.get("source_type", ""),
                "published_at": metadata.get("published_at", ""),
                "period": metadata.get("period", ""),
                "section_hint": detect_section_hint(chunk_text),
                "created_at": utc_now_iso(),
            }
        ]

    start = 0
    index = 0
    step = chunk_size - overlap
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        if not chunk_words:
            break

        chunk_text = " ".join(chunk_words)
        chunks.append(
            {
                "chunk_id": f"{processed_document_id}_chunk_{index:04d}",
                "processed_document_id": processed_document_id,
                "source_document_id": source_document_id,
                "chunk_index": index,
                "chunk_text": chunk_text,
                "chunk_word_count": len(chunk_words),
                "chunk_char_count": len(chunk_text),
                "company_name": metadata.get("company_name", ""),
                "ticker": metadata.get("ticker", ""),
                "market": metadata.get("market", ""),
                "document_type": metadata.get("document_type", ""),
                "source_type": metadata.get("source_type", ""),
                "published_at": metadata.get("published_at", ""),
                "period": metadata.get("period", ""),
                "section_hint": detect_section_hint(chunk_text),
                "created_at": utc_now_iso(),
            }
        )

        if end == len(words):
            break
        start += step
        index += 1

    return chunks
