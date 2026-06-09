"""Text cleanup utilities for financial documents."""

from __future__ import annotations

import re


def clean_text(text: str, max_repeated_blank_lines: int = 2) -> str:
    """Normalize text without destroying financial values or symbols."""

    if not text:
        return ""

    cleaned = text.replace("\x00", "")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t\f\v]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)

    blank_limit = "\n" * max_repeated_blank_lines
    cleaned = re.sub(r"\n{3,}", blank_limit, cleaned)

    # Remove repeated page-artifact punctuation while preserving financial signs.
    cleaned = re.sub(r"[_]{4,}", " ", cleaned)
    cleaned = re.sub(r"[=]{4,}", " ", cleaned)

    return cleaned.strip()
