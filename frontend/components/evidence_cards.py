"""Consistent source and evidence rendering."""

from __future__ import annotations

from typing import Any

import streamlit as st


SOURCE_FIELDS = [
    "source_number",
    "rank",
    "chunk_id",
    "source_document_id",
    "processed_document_id",
    "company_name",
    "ticker",
    "market",
    "document_type",
    "source_type",
    "published_at",
    "published_date",
    "retrieval_score",
    "score",
]


def unknown(value: Any) -> Any:
    return value if value not in {None, ""} else "unknown"


def normalize_source(source: dict[str, Any]) -> dict[str, Any]:
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    return {
        "Source Number": unknown(source.get("source_number") or source.get("rank")),
        "Chunk ID": unknown(source.get("chunk_id")),
        "Document ID": unknown(source.get("source_document_id")),
        "Processed Document ID": unknown(source.get("processed_document_id")),
        "Company": unknown(source.get("company_name") or metadata.get("company_name")),
        "Ticker": unknown(source.get("ticker") or metadata.get("ticker")),
        "Market": unknown(source.get("market") or metadata.get("market")),
        "Document Type": unknown(source.get("document_type") or metadata.get("document_type")),
        "Source Type": unknown(source.get("source_type") or metadata.get("source_type")),
        "Retrieval Score": unknown(source.get("retrieval_score") or source.get("score")),
        "Published": unknown(source.get("published_date") or source.get("published_at") or metadata.get("published_at")),
    }


def render_sources(sources: list[dict[str, Any]], *, title: str = "Sources / Evidence") -> None:
    st.subheader(title)
    if not sources:
        st.info("No source evidence was returned.")
        return
    table_rows = [normalize_source(source) for source in sources if isinstance(source, dict)]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            continue
        normalized = normalize_source(source)
        label = (
            f"Source {normalized.get('Source Number', index)} | "
            f"{normalized.get('Document ID')} | score {normalized.get('Retrieval Score')}"
        )
        text = (
            source.get("chunk_text_excerpt")
            or source.get("evidence_text")
            or source.get("chunk_text")
            or "No text excerpt was saved for this source."
        )
        with st.expander(label, expanded=False):
            st.write(text)
            st.json({key: value for key, value in source.items() if key not in {"evidence_text", "chunk_text", "chunk_text_excerpt"}})


def render_evidence_ranking(items: list[dict[str, Any]]) -> None:
    st.subheader("Evidence Ranking")
    if not items:
        st.info("No evidence ranking was returned.")
        return
    st.dataframe(items, use_container_width=True, hide_index=True)
