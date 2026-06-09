"""Map company hints to available Nexora metadata without a fake company database."""

from __future__ import annotations

from typing import Any

from backend.app.services.reasoning import sector_dependency_service
from backend.app.services.retrieval.retrieval_metadata_service import read_vector_metadata


def map_company(
    company_name: str = "",
    ticker: str = "",
    market: str = "",
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    evidence = evidence or []
    has_company_hint = bool(company_name or ticker or market)
    if not has_company_hint:
        return {
            "company_name": "",
            "ticker": "",
            "market": "",
            "sector": "unknown",
            "source_documents_found": sorted(
                {
                    str(item.get("source_document_id", ""))
                    for item in evidence
                    if item.get("source_document_id")
                }
            ),
            "note": "No company, ticker, or market was provided; retrieved documents are scenario context, not company mapping.",
        }

    try:
        frame = read_vector_metadata()
    except Exception:
        frame = None

    source_documents: list[str] = []
    if frame is not None and not frame.empty:
        filtered = frame.fillna("")
        if ticker:
            filtered = filtered[filtered["ticker"].str.lower() == ticker.lower()]
        if market:
            filtered = filtered[filtered["market"].str.lower() == market.lower()]
        if company_name and "company_name" in filtered.columns:
            name_mask = filtered["company_name"].str.lower().str.contains(company_name.lower(), regex=False)
            if name_mask.any():
                filtered = filtered[name_mask]
        source_documents = sorted(set(filtered.get("source_document_id", [])))[:20]

    if not source_documents:
        source_documents = sorted(
            {
                str((item.get("metadata") or {}).get("source_document_id") or item.get("source_document_id", ""))
                for item in evidence
                if (item.get("metadata") or {}).get("source_document_id") or item.get("source_document_id")
            }
        )

    sector = sector_dependency_service.infer_sector(company_name, ticker, evidence)
    return {
        "company_name": company_name,
        "ticker": ticker,
        "market": market,
        "sector": sector,
        "source_documents_found": source_documents,
    }
