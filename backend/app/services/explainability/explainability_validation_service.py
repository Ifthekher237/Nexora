"""Validation guardrails for explainability reports."""

from __future__ import annotations

from typing import Any


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = list(report.get("validation_warnings") or [])
    limitations: list[str] = list(report.get("limitations") or [])
    score = float(report.get("explainability_score") or 0.0)

    def warn(message: str, penalty: float = 0.05) -> None:
        nonlocal score
        if message not in warnings:
            warnings.append(message)
        if message not in limitations:
            limitations.append(message)
        score = max(0.0, score - penalty)

    if not report.get("target_id"):
        warn("Explainability report is missing a target ID.", 0.15)
    if report.get("target_type") not in {"risk", "reasoning", "rag"}:
        warn("Explainability report has an unsupported target type.", 0.20)
    if not report.get("evidence_coverage"):
        warn("Explainability report is missing evidence coverage.", 0.15)
    if not report.get("confidence_explanation"):
        warn("Explainability report is missing confidence explanation.", 0.15)
    if not limitations:
        warn("Explainability report should include limitations.", 0.05)

    citations = report.get("expanded_citations") or []
    if not citations and report.get("status") == "success":
        warn("No expanded citations were available for this target output.", 0.10)
    for citation in citations:
        if citation.get("source_document_id") == "unknown" and citation.get("chunk_id") == "unknown":
            warn("A citation lacked both source document ID and chunk ID.", 0.10)
            break

    unsupported_claims = report.get("unsupported_claims") or []
    for claim in unsupported_claims:
        if claim.get("issue_type") in {"investment_advice", "stock_prediction"}:
            warn("Unsupported claim detector found investment-advice or stock-prediction language.", 0.20)
            break

    report["validation_warnings"] = warnings
    report["limitations"] = limitations
    report["explainability_score"] = round(max(0.0, min(1.0, score)), 4)
    return report
