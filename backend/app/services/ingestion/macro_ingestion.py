"""Local macroeconomic dataset ingestion."""

from __future__ import annotations

from backend.app.services.ingestion.local_file_ingestion import register_local_file
from backend.app.services.ingestion.validation_service import (
    IngestionValidationError,
    resolve_local_file,
)


def register_macro_csv(
    file_path: str,
    source_name: str = "Manual macro dataset",
    title: str | None = None,
    period: str = "",
    notes: str = "",
) -> dict[str, object]:
    """Register a local CSV macro dataset.

    External macro APIs are intentionally not added in Phase 2.
    """

    path = resolve_local_file(file_path)
    if path.suffix.lower() != ".csv":
        raise IngestionValidationError("Macro ingestion currently supports local CSV files only.")

    result = register_local_file(
        file_path=file_path,
        source_type="macro",
        company_name=source_name,
        ticker="",
        market="MACRO",
        document_type="macro_dataset",
        period=period,
        title=title or path.name,
        notes=notes or "Local macroeconomic CSV dataset registered for future processing.",
    )
    result["source_type"] = "macro"
    return result
