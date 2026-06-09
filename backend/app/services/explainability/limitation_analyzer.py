"""Extract and generate cautious limitations from saved outputs and metadata."""

from __future__ import annotations

import re
from typing import Any


def _add_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def analyze_limitations(
    target_type: str,
    target_output: dict[str, Any],
    citations: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> list[str]:
    limitations: list[str] = []
    for item in target_output.get("limitations") or []:
        _add_unique(limitations, str(item))

    if coverage.get("level") == "low":
        _add_unique(limitations, "Evidence coverage is low, so the explanation should be used cautiously.")
    if int(coverage.get("sources_used") or 0) < 3:
        _add_unique(limitations, "Limited evidence was available in the saved output.")
    if float(coverage.get("average_retrieval_score") or 0.0) < 0.45:
        _add_unique(limitations, "Average retrieval scores are weak for this explanation.")
    if not coverage.get("company_specific_evidence"):
        _add_unique(limitations, "Company-specific evidence is missing or limited in the available citations.")

    document_types = {str(citation.get("document_type", "")).lower() for citation in citations}
    if not document_types.intersection({"annual_report", "10-k", "10-q", "financial_statement"}):
        _add_unique(limitations, "No full annual report or comparable financial statement evidence was found in the saved citations.")

    combined_text = " ".join(
        str(target_output.get(key, ""))
        for key in ["answer", "direct_answer", "explanation", "scenario", "question"]
    )
    if not re.search(r"\b\d+(\.\d+)?\s?%|\bratio\b|\bmargin\b|\brevenue\b|\bdebt\b", combined_text, re.IGNORECASE):
        _add_unique(limitations, "No numerical financial ratio or trend evidence was present in the saved generated text.")

    dates = {
        citation.get("published_date")
        for citation in citations
        if citation.get("published_date") not in {None, "", "unknown"}
    }
    if len(dates) < 2:
        _add_unique(limitations, "Historical trend coverage is limited because fewer than two source dates were available.")

    if target_type in {"reasoning", "risk"}:
        _add_unique(limitations, "Model-generated reasoning depends on the retrieved local evidence and may be incomplete.")
    _add_unique(limitations, "This explainability report audits saved outputs; it does not provide investment advice.")
    _add_unique(limitations, "This explainability report does not predict stock prices.")
    return limitations
