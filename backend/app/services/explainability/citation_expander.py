"""Expand saved source references into auditable citation objects."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from backend.app.core.config import PROJECT_ROOT


UNKNOWN = "unknown"
VECTOR_INDEX_PATH = PROJECT_ROOT / "data/vector_store/metadata/vector_index.json"
TEXT_LIMIT = 420


def _clean(value: Any, default: str = UNKNOWN) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


@lru_cache
def _vector_metadata_by_chunk() -> dict[str, dict[str, Any]]:
    if not VECTOR_INDEX_PATH.exists():
        return {}
    try:
        records = json.loads(VECTOR_INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(records, list):
        return {}
    return {
        str(record.get("chunk_id")): record
        for record in records
        if isinstance(record, dict) and record.get("chunk_id")
    }


def _source_number(raw: dict[str, Any], index: int) -> str:
    value = raw.get("source_number")
    if value:
        return _clean(value)
    rank = raw.get("rank")
    if rank:
        return f"Source {rank}"
    return f"Source {index + 1}"


def _metadata_value(raw: dict[str, Any], metadata: dict[str, Any], key: str) -> Any:
    return raw.get(key) or metadata.get(key)


def _excerpt(raw: dict[str, Any]) -> str:
    text = _clean(raw.get("evidence_text") or raw.get("chunk_text") or raw.get("text"))
    if text == UNKNOWN:
        return text
    return re.sub(r"\s+", " ", text)[:TEXT_LIMIT]


def expand_citations(raw_sources: list[dict[str, Any]] | None, target_text: str = "") -> dict[str, Any]:
    """Return normalized citations and limitation notes without inventing metadata."""

    raw_sources = [item for item in raw_sources or [] if isinstance(item, dict)]
    vector_metadata = _vector_metadata_by_chunk()
    citations: list[dict[str, Any]] = []
    limitations: list[str] = []
    required_fields = [
        "chunk_id",
        "source_document_id",
        "processed_document_id",
        "company_name",
        "ticker",
        "market",
        "document_type",
        "source_type",
        "published_date",
    ]

    for index, raw in enumerate(raw_sources):
        source_number = _source_number(raw, index)
        raw_metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
        vector_metadata_for_chunk = vector_metadata.get(str(raw.get("chunk_id")), {})
        metadata = {**vector_metadata_for_chunk, **raw_metadata}

        citation = {
            "source_number": source_number,
            "chunk_id": _clean(_metadata_value(raw, metadata, "chunk_id")),
            "source_document_id": _clean(_metadata_value(raw, metadata, "source_document_id")),
            "processed_document_id": _clean(_metadata_value(raw, metadata, "processed_document_id")),
            "company_name": _clean(_metadata_value(raw, metadata, "company_name")),
            "ticker": _clean(_metadata_value(raw, metadata, "ticker")),
            "market": _clean(_metadata_value(raw, metadata, "market")),
            "document_type": _clean(_metadata_value(raw, metadata, "document_type")),
            "source_type": _clean(_metadata_value(raw, metadata, "source_type")),
            "published_date": _clean(
                raw.get("published_date")
                or raw.get("published_at")
                or metadata.get("published_date")
                or metadata.get("published_at")
            ),
            "retrieval_score": _score(raw.get("score") or raw.get("retrieval_score")),
            "chunk_text_excerpt": _excerpt(raw),
            "source_url": _clean(_metadata_value(raw, metadata, "source_url")),
            "citation_usage_count": len(re.findall(re.escape(source_number), target_text or "", flags=re.IGNORECASE)),
            "missing_fields": [],
        }
        for field in required_fields:
            if citation[field] == UNKNOWN:
                citation["missing_fields"].append(field)
        if citation["missing_fields"]:
            limitations.append(
                f"{source_number} is missing metadata field(s): {', '.join(citation['missing_fields'])}."
            )
        citations.append(citation)

    if not citations:
        limitations.append("No expandable source citations were present in the saved target output.")
    return {"citations": citations, "limitations": limitations}
