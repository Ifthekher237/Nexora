"""Company-specific risk scoring without fake company data."""

from __future__ import annotations

from typing import Any

from backend.app.services.risk.scoring_engine import clamp_score


RELEVANT_DOCUMENT_TYPES = {"annual_report", "10-k", "10-q", "sec", "sd", "4", "144", "news"}


def score_company_risk(reasoning_output: dict[str, Any]) -> dict[str, Any]:
    ticker = reasoning_output.get("ticker", "")
    company_name = reasoning_output.get("company_name", "")
    evidence_map = reasoning_output.get("evidence_map") or []
    if not ticker and not company_name:
        return {
            "company_specific_risk_score": 20,
            "company_specific": False,
            "company_source_count": 0,
            "reason": "No company or ticker was supplied; company-specific risk is intentionally limited.",
            "limitation": "Company-specific score is company-agnostic because no company/ticker was provided.",
        }

    company_sources = []
    for item in evidence_map:
        metadata = item.get("metadata") or {}
        text = f"{metadata.get('ticker', '')} {metadata.get('company_name', '')} {item.get('evidence_text', '')}".lower()
        if (ticker and ticker.lower() in text) or (company_name and company_name.lower() in text):
            company_sources.append(item)

    relevant_docs = [
        item
        for item in company_sources
        if str((item.get("metadata") or {}).get("document_type", "")).lower() in RELEVANT_DOCUMENT_TYPES
    ]
    avg_score = sum(float(item.get("score") or 0.0) for item in company_sources) / len(company_sources) if company_sources else 0.0
    score = clamp_score(min(len(company_sources) / 4, 1.0) * 45 + min(len(relevant_docs) / 3, 1.0) * 25 + avg_score * 30)
    return {
        "company_specific_risk_score": score,
        "company_specific": True,
        "company_source_count": len(company_sources),
        "reason": f"Company-specific risk uses {len(company_sources)} matching source(s), {len(relevant_docs)} relevant document type(s), and average score {avg_score:.2f}.",
        "limitation": "" if company_sources else "No company-specific evidence matched the supplied company/ticker.",
    }
