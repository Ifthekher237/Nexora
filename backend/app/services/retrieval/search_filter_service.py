"""Validation and application of retrieval metadata filters."""

from __future__ import annotations

from typing import Any


SUPPORTED_FILTERS = {"ticker", "source_type", "document_type", "market", "section_hint", "status"}


class RetrievalFilterError(ValueError):
    """Raised when retrieval filters are not valid."""


def normalize_filters(filters: dict[str, Any] | None) -> dict[str, str]:
    if not filters:
        return {}

    normalized: dict[str, str] = {}
    for key, value in filters.items():
        if key not in SUPPORTED_FILTERS:
            raise RetrievalFilterError(f"Unsupported retrieval filter: {key}")
        if value is None or value == "":
            continue
        normalized[key] = str(value).strip()
    return normalized


def apply_filters(records: list[dict[str, Any]], filters: dict[str, str]) -> list[dict[str, Any]]:
    if not filters:
        return records

    filtered = records
    for key, value in filters.items():
        filtered = [
            record
            for record in filtered
            if str(record.get(key, "")).lower() == value.lower()
        ]
    return filtered
