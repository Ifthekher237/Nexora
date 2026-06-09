"""Metadata index management for indexed vectors."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.config import PROJECT_ROOT, get_retrieval_config


VECTOR_METADATA_FIELDS = [
    "vector_id",
    "chunk_id",
    "processed_document_id",
    "source_document_id",
    "chunk_index",
    "company_name",
    "ticker",
    "market",
    "document_type",
    "source_type",
    "published_at",
    "period",
    "section_hint",
    "embedding_model",
    "embedding_dimension",
    "vector_store",
    "indexed_at",
    "chunk_word_count",
    "chunk_char_count",
    "source_chunk_file",
    "status",
    "error_message",
]


def vector_store_root() -> Path:
    root = get_retrieval_config().get("retrieval", {}).get(
        "vector_store_root", "data/vector_store"
    )
    return PROJECT_ROOT / root


def faiss_dir() -> Path:
    return vector_store_root() / "faiss"


def chroma_dir() -> Path:
    return vector_store_root() / "chroma"


def metadata_dir() -> Path:
    return vector_store_root() / "metadata"


def vector_csv_path() -> Path:
    configured = get_retrieval_config().get("indexing", {}).get(
        "vector_metadata_csv", "data/vector_store/metadata/vector_index.csv"
    )
    return PROJECT_ROOT / configured


def vector_json_path() -> Path:
    configured = get_retrieval_config().get("indexing", {}).get(
        "vector_metadata_json", "data/vector_store/metadata/vector_index.json"
    )
    return PROJECT_ROOT / configured


def benchmark_results_path() -> Path:
    return metadata_dir() / "retrieval_benchmark_results.json"


def ensure_vector_directories() -> None:
    faiss_dir().mkdir(parents=True, exist_ok=True)
    chroma_dir().mkdir(parents=True, exist_ok=True)
    metadata_dir().mkdir(parents=True, exist_ok=True)


def empty_vector_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=VECTOR_METADATA_FIELDS)


def ensure_vector_index() -> None:
    ensure_vector_directories()
    if not vector_csv_path().exists():
        empty_vector_frame().to_csv(vector_csv_path(), index=False)
    if not vector_json_path().exists():
        vector_json_path().write_text("[]", encoding="utf-8")
    if not benchmark_results_path().exists():
        benchmark_results_path().write_text("[]", encoding="utf-8")


def read_vector_metadata() -> pd.DataFrame:
    ensure_vector_index()
    if vector_csv_path().stat().st_size == 0:
        return empty_vector_frame()

    frame = pd.read_csv(vector_csv_path(), dtype=str).fillna("")
    for field in VECTOR_METADATA_FIELDS:
        if field not in frame.columns:
            frame[field] = ""
    return frame[VECTOR_METADATA_FIELDS]


def write_vector_metadata(frame: pd.DataFrame) -> None:
    ensure_vector_index()
    normalized = frame.copy()
    for field in VECTOR_METADATA_FIELDS:
        if field not in normalized.columns:
            normalized[field] = ""
    normalized = normalized[VECTOR_METADATA_FIELDS].fillna("")
    normalized.to_csv(vector_csv_path(), index=False)
    normalized.to_json(vector_json_path(), orient="records", indent=2)


def normalize_vector_record(record: dict[str, Any]) -> dict[str, str]:
    return {field: str(record.get(field, "") or "") for field in VECTOR_METADATA_FIELDS}


def is_chunk_indexed(chunk_id: str, vector_store: str, embedding_model: str) -> bool:
    frame = read_vector_metadata()
    if frame.empty:
        return False
    matches = frame[
        (frame["chunk_id"] == chunk_id)
        & (frame["vector_store"] == vector_store)
        & (frame["embedding_model"] == embedding_model)
        & (frame["status"] == "indexed")
    ]
    return not matches.empty


def append_vector_metadata(records: list[dict[str, Any]], rebuild_store: str | None = None) -> None:
    frame = read_vector_metadata()
    if rebuild_store:
        frame = frame[frame["vector_store"] != rebuild_store]

    normalized = [normalize_vector_record(record) for record in records]
    if normalized:
        existing_ids = set(frame["vector_id"].tolist()) if not frame.empty else set()
        deduped: list[dict[str, str]] = []
        seen_ids = set(existing_ids)
        for record in normalized:
            if record["vector_id"] in seen_ids:
                continue
            deduped.append(record)
            seen_ids.add(record["vector_id"])
        frame = pd.concat([frame, pd.DataFrame(deduped)], ignore_index=True)
    write_vector_metadata(frame)


def filter_vector_metadata(filters: dict[str, str | None]) -> list[dict[str, str]]:
    frame = read_vector_metadata()
    for field, value in filters.items():
        if value and field in frame.columns:
            frame = frame[frame[field].str.lower() == value.lower()]
    return frame.fillna("").to_dict(orient="records")


def vector_metadata_status() -> dict[str, object]:
    frame = read_vector_metadata()
    return {
        "csv_index": str(vector_csv_path()),
        "json_index": str(vector_json_path()),
        "exists": vector_csv_path().exists() and vector_json_path().exists(),
        "indexed_chunks": int((frame["status"] == "indexed").sum()) if not frame.empty else 0,
    }


def vector_summary() -> dict[str, Any]:
    frame = read_vector_metadata()
    indexed = frame[frame["status"] == "indexed"] if not frame.empty else frame
    if indexed.empty:
        return {
            "total_indexed_chunks": 0,
            "indexed_chunks_by_source_type": {},
            "indexed_chunks_by_ticker": {},
            "indexed_chunks_by_document_type": {},
            "embedding_model_used": "",
            "vector_stores_available": [],
            "latest_indexing_time": "",
        }
    return {
        "total_indexed_chunks": int(len(indexed)),
        "indexed_chunks_by_source_type": indexed["source_type"].value_counts().to_dict(),
        "indexed_chunks_by_ticker": indexed["ticker"].replace("", pd.NA).dropna().value_counts().to_dict(),
        "indexed_chunks_by_document_type": indexed["document_type"].value_counts().to_dict(),
        "embedding_model_used": str(indexed["embedding_model"].mode().iloc[0]),
        "vector_stores_available": sorted(indexed["vector_store"].unique().tolist()),
        "latest_indexing_time": str(indexed["indexed_at"].max()),
    }
