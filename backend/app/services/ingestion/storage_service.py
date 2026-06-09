"""Local file storage utilities for ingested financial sources."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_ingestion_config


SOURCE_FOLDERS = {
    "sec": "sec",
    "asx": "asx",
    "rss": "rss",
    "macro": "macro",
    "local_uploads": "local_uploads",
}


def storage_root() -> Path:
    root = get_ingestion_config().get("ingestion", {}).get("storage_root", "data/raw")
    return PROJECT_ROOT / root


def metadata_root() -> Path:
    root = get_ingestion_config().get("ingestion", {}).get("metadata_root", "data/metadata")
    return PROJECT_ROOT / root


def ensure_storage_directories() -> None:
    """Create all required local storage folders."""

    storage_root().mkdir(parents=True, exist_ok=True)
    metadata_root().mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "external").mkdir(parents=True, exist_ok=True)

    for folder in SOURCE_FOLDERS.values():
        (storage_root() / folder).mkdir(parents=True, exist_ok=True)


def source_directory(source_type: str) -> Path:
    ensure_storage_directories()
    folder_name = SOURCE_FOLDERS.get(source_type, source_type)
    directory = storage_root() / folder_name
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_filename(value: str, max_length: int = 140) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    cleaned = cleaned.strip("._-") or "document"
    return cleaned[:max_length]


def content_hash_for_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def content_hash_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_local_file(source_path: Path, source_type: str, target_name: str) -> Path:
    target = source_directory(source_type) / safe_filename(target_name)
    if target.exists():
        return target

    shutil.copy2(source_path, target)
    return target


def save_text_content(source_type: str, file_name: str, content: str) -> Path:
    target = source_directory(source_type) / safe_filename(file_name)
    target.write_text(content, encoding="utf-8")
    return target


def save_json_content(source_type: str, file_name: str, content: dict[str, Any]) -> Path:
    target = source_directory(source_type) / safe_filename(file_name)
    target.write_text(json.dumps(content, indent=2, sort_keys=True), encoding="utf-8")
    return target


def project_relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def build_document_id(
    source_type: str,
    ticker: str,
    document_type: str,
    date_label: str,
    content_hash: str,
) -> str:
    source_part = safe_filename(source_type).upper()
    ticker_part = safe_filename(ticker or "GENERAL").upper()
    document_part = safe_filename(document_type).replace("_", "").replace("-", "").upper()
    date_part = safe_filename(date_label or "UNDATED").upper()
    hash_part = content_hash[:6]
    return f"{source_part}_{ticker_part}_{document_part}_{date_part}_{hash_part}"
