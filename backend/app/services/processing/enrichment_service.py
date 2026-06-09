"""Metadata enrichment helpers for processed documents and chunks."""

from __future__ import annotations


SECTION_HINTS = {
    "risk": ["risk", "uncertainty", "volatility", "exposure"],
    "revenue": ["revenue", "sales", "income", "turnover"],
    "debt": ["debt", "liability", "borrowings", "leverage"],
    "operations": ["operations", "operating", "supply", "production"],
    "macro": ["inflation", "interest rate", "gdp", "unemployment", "central bank"],
    "management": ["management", "director", "chair", "executive", "board"],
}


def base_enrichment(source_metadata: dict[str, str], detected_category: str) -> dict[str, str]:
    """Copy source traceability fields into processing metadata."""

    return {
        "source_document_id": source_metadata.get("document_id", ""),
        "source_type": source_metadata.get("source_type", ""),
        "source_name": source_metadata.get("source_name", ""),
        "company_name": source_metadata.get("company_name", ""),
        "ticker": source_metadata.get("ticker", ""),
        "market": source_metadata.get("market", ""),
        "document_type": source_metadata.get("document_type", ""),
        "source_local_path": source_metadata.get("local_path", ""),
        "published_at": source_metadata.get("published_at", ""),
        "period": source_metadata.get("period", ""),
        "detected_document_category": detected_category,
    }


def detect_section_hint(text: str) -> str:
    window = text[:1200].lower()
    for section, keywords in SECTION_HINTS.items():
        if any(keyword in window for keyword in keywords):
            return section
    return "unknown"
