"""RSS feed ingestion for public financial and economic feeds."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from html import unescape
from xml.etree import ElementTree

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
    safe_filename,
    save_text_content,
)
from backend.app.services.ingestion.validation_service import (
    get_configured_rss_feed,
    validate_limit,
)


logger = logging.getLogger(__name__)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ElementTree.Element, names: set[str]) -> str:
    for child in list(element):
        if _local_name(child.tag) in names and child.text:
            return unescape(child.text.strip())
    return ""


def _child_link(element: ElementTree.Element) -> str:
    for child in list(element):
        if _local_name(child.tag) == "link":
            if child.text and child.text.strip():
                return child.text.strip()
            if child.attrib.get("href"):
                return child.attrib["href"].strip()
    return ""


def _parse_feed_items(content: bytes) -> list[dict[str, str]]:
    root = ElementTree.fromstring(content)
    parsed_items: list[dict[str, str]] = []

    for element in root.iter():
        if _local_name(element.tag) not in {"item", "entry"}:
            continue
        parsed_items.append(
            {
                "title": _child_text(element, {"title"}),
                "link": _child_link(element),
                "published_at": _child_text(element, {"pubdate", "published", "updated"}),
                "description": _child_text(element, {"description", "summary", "content"}),
            }
        )

    return parsed_items


def _date_label(published_at: str) -> str:
    if not published_at:
        return datetime.now(UTC).strftime("%Y%m%d")
    cleaned = "".join(character for character in published_at if character.isdigit())
    return cleaned[:8] or datetime.now(UTC).strftime("%Y%m%d")


def ingest_rss_feed(feed_name: str, limit: int) -> dict[str, object]:
    normalized_limit = validate_limit(limit)
    feed = get_configured_rss_feed(feed_name)
    config = get_ingestion_config().get("ingestion", {})
    timeout = int(config.get("request_timeout_seconds", 30))
    headers = {"User-Agent": config.get("default_user_agent", "Nexora local research")}

    logger.info("RSS ingestion started | feed=%s | limit=%s", feed["name"], normalized_limit)
    try:
        response = requests.get(feed["url"], headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("RSS ingestion failed for %s: %s", feed["name"], exc)
        return {
            "status": "error",
            "source_type": "rss",
            "message": f"RSS feed '{feed['name']}' could not be fetched.",
            "documents_found": 0,
            "documents_saved": 0,
            "duplicates_skipped": 0,
            "errors": [str(exc)],
            "documents": [],
        }

    try:
        items = _parse_feed_items(response.content)
    except ElementTree.ParseError as exc:
        logger.error("RSS XML parsing failed for %s: %s", feed["name"], exc)
        return {
            "status": "error",
            "source_type": "rss",
            "message": f"RSS feed '{feed['name']}' could not be parsed.",
            "documents_found": 0,
            "documents_saved": 0,
            "duplicates_skipped": 0,
            "errors": [str(exc)],
            "documents": [],
        }
    if not items:
        return {
            "status": "error",
            "source_type": "rss",
            "message": f"RSS feed '{feed['name']}' returned no parsable items.",
            "documents_found": 0,
            "documents_saved": 0,
            "duplicates_skipped": 0,
            "errors": ["No item or entry tags found in feed XML."],
            "documents": [],
        }

    saved = 0
    duplicates = 0
    documents: list[dict[str, str]] = []

    for item in items[:normalized_limit]:
        title = item.get("title") or "Untitled RSS item"
        link = item.get("link", "")
        published_at = item.get("published_at", "")
        description = item.get("description", "")
        text_content = (
            f"Feed: {feed['name']}\n"
            f"Title: {title}\n"
            f"Published: {published_at}\n"
            f"Source URL: {link}\n\n"
            f"{description}\n"
        )
        content_hash = content_hash_for_bytes(text_content.encode("utf-8"))
        document_id = build_document_id(
            "rss",
            safe_filename(feed["name"]).upper(),
            "news",
            _date_label(published_at),
            content_hash,
        )

        duplicate = find_duplicate_record(
            {
                "document_id": document_id,
                "source_url": link,
                "content_hash": content_hash,
            }
        )
        if duplicate:
            duplicates += 1
            documents.append(duplicate)
            continue

        local_path = save_text_content("rss", f"{document_id}.txt", text_content)
        record = {
            "document_id": document_id,
            "source_type": "rss",
            "source_name": feed["name"],
            "company_name": "",
            "ticker": "",
            "market": "",
            "document_type": "news",
            "title": title,
            "source_url": link,
            "local_path": project_relative_path(local_path),
            "file_format": "txt",
            "ingested_at": utc_now_iso(),
            "published_at": published_at,
            "period": "",
            "status": "saved",
            "error_message": "",
            "content_hash": content_hash,
            "notes": "RSS item summary stored for future document processing.",
        }
        result = append_metadata(record)
        documents.append(result["record"])
        if result["created"]:
            saved += 1
        else:
            duplicates += 1

    logger.info(
        "RSS ingestion finished | feed=%s | found=%s | saved=%s | duplicates=%s",
        feed["name"],
        len(items[:normalized_limit]),
        saved,
        duplicates,
    )
    return {
        "status": "success",
        "source_type": "rss",
        "message": f"RSS ingestion completed for {feed['name']}.",
        "documents_found": len(items[:normalized_limit]),
        "documents_saved": saved,
        "duplicates_skipped": duplicates,
        "errors": [],
        "documents": documents,
    }
