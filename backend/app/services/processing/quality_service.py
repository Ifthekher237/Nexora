"""Quality checks for extracted and chunked document text."""

from __future__ import annotations

from backend.app.core.config import get_processing_config


def text_stats(text: str) -> dict[str, int]:
    words = text.split()
    return {
        "text_length": len(text),
        "word_count": len(words),
    }


def evaluate_quality(text: str, chunk_count: int) -> dict[str, object]:
    config = get_processing_config().get("processing", {})
    min_words = int(config.get("min_chunk_words", 80))
    stats = text_stats(text)
    warnings: list[str] = []

    if not text.strip():
        return {
            **stats,
            "chunk_count": 0,
            "quality_status": "failed",
            "warnings": ["Extracted text is empty."],
        }

    if stats["word_count"] < min_words:
        warnings.append("Extracted text is very short.")
    if chunk_count == 0:
        warnings.append("No chunks were created.")

    return {
        **stats,
        "chunk_count": chunk_count,
        "quality_status": "warning" if warnings else "good",
        "warnings": warnings,
    }
