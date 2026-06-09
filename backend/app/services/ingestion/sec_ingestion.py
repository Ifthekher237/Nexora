"""SEC EDGAR filing metadata ingestion."""

from __future__ import annotations

import logging
from typing import Any

import requests

from backend.app.core.config import get_ingestion_config
from backend.app.services.ingestion.metadata_service import (
    append_metadata,
    find_duplicate_record,
    utc_now_iso,
)
from backend.app.services.ingestion.storage_service import (
    build_document_id,
    content_hash_for_bytes,
    project_relative_path,
    save_json_content,
)
from backend.app.services.ingestion.validation_service import validate_limit, validate_ticker


logger = logging.getLogger(__name__)


def _request_json(url: str) -> dict[str, Any]:
    config = get_ingestion_config().get("ingestion", {})
    timeout = int(config.get("request_timeout_seconds", 30))
    headers = {
        "User-Agent": config.get("default_user_agent", "Nexora local research"),
        "Accept-Encoding": "gzip, deflate",
        "Host": url.split("/")[2],
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _lookup_cik(ticker: str) -> tuple[str, str]:
    source_config = get_ingestion_config().get("sources", {}).get("sec", {})
    mapping = _request_json(source_config["company_ticker_url"])
    normalized_ticker = ticker.upper()

    for entry in mapping.values():
        if entry.get("ticker", "").upper() == normalized_ticker:
            cik = str(entry["cik_str"]).zfill(10)
            return cik, entry.get("title", "")

    raise ValueError(f"Ticker '{ticker}' was not found in the public SEC ticker mapping.")


def _filing_url(cik: str, accession_number: str, primary_document: str) -> str:
    source_config = get_ingestion_config().get("sources", {}).get("sec", {})
    archive_cik = str(int(cik))
    accession_clean = accession_number.replace("-", "")
    return (
        f"{source_config['archives_base_url']}/"
        f"{archive_cik}/{accession_clean}/{primary_document}"
    )


def _recent_filings(submission: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    recent = submission.get("filings", {}).get("recent", {})
    filings: list[dict[str, Any]] = []

    for index, accession in enumerate(recent.get("accessionNumber", [])[:limit]):
        filings.append(
            {
                "accession_number": accession,
                "filing_date": recent.get("filingDate", [""])[index],
                "report_date": recent.get("reportDate", [""])[index],
                "form_type": recent.get("form", [""])[index],
                "primary_document": recent.get("primaryDocument", [""])[index],
                "primary_doc_description": recent.get("primaryDocDescription", [""])[index],
            }
        )

    return filings


def ingest_sec_company(ticker: str, company_name: str, limit: int) -> dict[str, object]:
    normalized_ticker = validate_ticker(ticker)
    normalized_limit = validate_limit(limit)
    source_config = get_ingestion_config().get("sources", {}).get("sec", {})

    logger.info("SEC ingestion started | ticker=%s | limit=%s", normalized_ticker, normalized_limit)
    try:
        cik, sec_company_name = _lookup_cik(normalized_ticker)
        submission_url = f"{source_config['base_url']}/submissions/CIK{cik}.json"
        submission = _request_json(submission_url)
    except (requests.RequestException, ValueError) as exc:
        logger.error("SEC ingestion failed for %s: %s", normalized_ticker, exc)
        return {
            "status": "error",
            "source_type": "sec",
            "message": f"SEC metadata could not be fetched for {normalized_ticker}.",
            "documents_found": 0,
            "documents_saved": 0,
            "duplicates_skipped": 0,
            "errors": [str(exc)],
            "documents": [],
        }

    filings = _recent_filings(submission, normalized_limit)
    saved = 0
    duplicates = 0
    documents: list[dict[str, str]] = []

    for filing in filings:
        primary_document = filing.get("primary_document", "")
        source_url = _filing_url(cik, filing["accession_number"], primary_document)
        filing_payload = {
            "ticker": normalized_ticker,
            "cik": cik,
            "company_name": company_name or sec_company_name,
            "filing": filing,
            "source_url": source_url,
        }
        content = str(filing_payload).encode("utf-8")
        content_hash = content_hash_for_bytes(content)
        form_type = filing.get("form_type", "sec_filing_metadata").lower().replace("/", "_")
        document_id = build_document_id(
            "sec",
            normalized_ticker,
            form_type,
            filing.get("filing_date", ""),
            content_hash,
        )

        duplicate = find_duplicate_record(
            {
                "document_id": document_id,
                "source_url": source_url,
                "content_hash": content_hash,
            }
        )
        if duplicate:
            duplicates += 1
            documents.append(duplicate)
            continue

        local_path = save_json_content("sec", f"{document_id}.json", filing_payload)
        record = {
            "document_id": document_id,
            "source_type": "sec",
            "source_name": "SEC EDGAR company submissions",
            "company_name": company_name or sec_company_name,
            "ticker": normalized_ticker,
            "market": "US",
            "document_type": form_type,
            "title": f"{normalized_ticker} {filing.get('form_type', '')} filing metadata",
            "source_url": source_url,
            "local_path": project_relative_path(local_path),
            "file_format": "json",
            "ingested_at": utc_now_iso(),
            "published_at": filing.get("filing_date", ""),
            "period": filing.get("report_date", ""),
            "status": "saved",
            "error_message": "",
            "content_hash": content_hash,
            "notes": (
                f"Accession {filing.get('accession_number', '')}; "
                f"primary document {primary_document}; SEC metadata only."
            ),
        }
        result = append_metadata(record)
        documents.append(result["record"])
        if result["created"]:
            saved += 1
        else:
            duplicates += 1

    logger.info(
        "SEC ingestion finished | ticker=%s | found=%s | saved=%s | duplicates=%s",
        normalized_ticker,
        len(filings),
        saved,
        duplicates,
    )
    return {
        "status": "success",
        "source_type": "sec",
        "message": f"SEC filing metadata ingestion completed for {normalized_ticker}.",
        "documents_found": len(filings),
        "documents_saved": saved,
        "duplicates_skipped": duplicates,
        "errors": [],
        "documents": documents,
    }
