"""ASX ingestion module.

Phase 2 supports honest manual ASX announcement registration. Live ASX scraping
is intentionally left for a future phase because it needs source-specific access
handling and careful reliability checks.
"""

from __future__ import annotations

from backend.app.services.ingestion.local_file_ingestion import register_local_file


def register_asx_announcement(
    file_path: str,
    company_name: str,
    ticker: str,
    document_type: str = "asx_announcement",
    period: str = "",
    title: str | None = None,
    notes: str = "",
) -> dict[str, object]:
    return register_local_file(
        file_path=file_path,
        source_type="asx",
        company_name=company_name,
        ticker=ticker,
        market="ASX",
        document_type=document_type,
        period=period,
        title=title,
        notes=notes
        or "Manual ASX announcement registration. Live ASX ingestion is a future extension.",
    )
