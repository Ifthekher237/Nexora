"""Simple rule-based document classification for Phase 3."""

from __future__ import annotations

from pathlib import Path


CATEGORIES = {
    "annual_report",
    "quarterly_report",
    "sec_filing_metadata",
    "rss_news",
    "earnings_transcript",
    "macro_dataset",
    "asx_announcement",
    "unknown",
}


def classify_document(metadata: dict[str, str], text: str, local_path: str = "") -> str:
    """Classify using source metadata first, then conservative text hints."""

    source_type = metadata.get("source_type", "").lower()
    document_type = metadata.get("document_type", "").lower()
    path_name = Path(local_path).name.lower()
    combined = f"{document_type} {path_name} {text[:2000].lower()}"

    if source_type == "sec" or "accession" in combined and "filing" in combined:
        return "sec_filing_metadata"
    if source_type == "rss":
        return "rss_news"
    if source_type == "macro" or document_type == "macro_dataset":
        return "macro_dataset"
    if source_type == "asx" or "asx" in combined:
        return "asx_announcement"
    if "annual" in combined or document_type == "annual_report":
        return "annual_report"
    if "quarter" in combined or document_type in {"quarterly_report", "10-q"}:
        return "quarterly_report"
    if "transcript" in combined or "earnings call" in combined:
        return "earnings_transcript"

    return "unknown"
