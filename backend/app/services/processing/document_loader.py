"""Load raw ingested documents into extractable text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader

from backend.app.core.config import PROJECT_ROOT, get_processing_config


class DocumentLoadError(RuntimeError):
    """Raised when raw document text cannot be extracted."""


def resolve_source_path(local_path: str) -> Path:
    path = Path(local_path).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _load_pdf(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise DocumentLoadError(f"PDF could not be opened: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise DocumentLoadError("PDF is encrypted and could not be decrypted.") from exc

    parts: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:
            raise DocumentLoadError(f"PDF text extraction failed on page {page_number}: {exc}") from exc
        if page_text.strip():
            parts.append(f"Page {page_number}\n{page_text}")

    if not parts:
        raise DocumentLoadError("PDF extraction returned empty text.")

    return "\n\n".join(parts)


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _sec_json_to_text(data: dict[str, Any]) -> str:
    filing = data.get("filing", {})
    lines = [
        f"Company: {data.get('company_name', '')}",
        f"Ticker: {data.get('ticker', '')}",
        f"CIK: {data.get('cik', '')}",
        f"Form type: {filing.get('form_type', '')}",
        f"Filing date: {filing.get('filing_date', '')}",
        f"Report date: {filing.get('report_date', '')}",
        f"Accession number: {filing.get('accession_number', '')}",
        f"Primary document: {filing.get('primary_document', '')}",
        f"Primary document description: {filing.get('primary_doc_description', '')}",
        f"Source URL: {data.get('source_url', '')}",
    ]
    return "\n".join(lines)


def _json_to_text(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DocumentLoadError(f"Malformed JSON: {exc}") from exc

    if isinstance(data, dict) and "filing" in data:
        return _sec_json_to_text(data)

    return json.dumps(data, indent=2, sort_keys=True)


def _csv_to_text(path: Path) -> str:
    try:
        frame = pd.read_csv(path, nrows=25)
    except Exception as exc:
        raise DocumentLoadError(f"CSV could not be read: {exc}") from exc

    columns = ", ".join(str(column) for column in frame.columns)
    rows_preview = frame.head(10).to_csv(index=False)
    return (
        f"CSV dataset: {path.name}\n"
        f"Columns: {columns}\n"
        f"Preview rows loaded: {len(frame)}\n\n"
        f"{rows_preview}"
    )


def load_document_text(local_path: str, file_format: str | None = None) -> dict[str, str]:
    """Load one local raw document and return extracted text plus format."""

    path = resolve_source_path(local_path)
    if not path.exists():
        raise DocumentLoadError(f"Raw source file does not exist: {local_path}")
    if not path.is_file():
        raise DocumentLoadError(f"Raw source path is not a file: {local_path}")

    extension = path.suffix.lower()
    supported = set(get_processing_config().get("supported_file_types", []))
    if extension not in supported:
        raise DocumentLoadError(f"Unsupported file type '{extension}'.")

    if extension == ".pdf":
        text = _load_pdf(path)
    elif extension in {".txt", ".md"}:
        text = _load_text(path)
    elif extension == ".json":
        text = _json_to_text(path)
    elif extension == ".csv":
        text = _csv_to_text(path)
    else:
        raise DocumentLoadError(f"Unsupported file type '{extension}'.")

    return {
        "text": text,
        "file_format": (file_format or extension.lstrip(".")).lower(),
        "resolved_path": str(path),
    }
