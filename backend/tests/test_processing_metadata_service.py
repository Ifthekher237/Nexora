import pandas as pd

from backend.app.services.processing import processing_metadata_service
from backend.app.services.processing.processing_metadata_service import PROCESSING_METADATA_FIELDS


def _record(processed_id: str = "PROC_SRC_abcdef") -> dict[str, str]:
    record = {field: "" for field in PROCESSING_METADATA_FIELDS}
    record.update(
        {
            "processed_document_id": processed_id,
            "source_document_id": "SRC_001",
            "source_type": "rss",
            "source_name": "Yahoo Finance",
            "document_type": "news",
            "source_local_path": "data/raw/rss/item.txt",
            "processed_text_path": "data/processed/documents/PROC_SRC_abcdef.txt",
            "chunk_file_path": "data/processed/chunks/PROC_SRC_abcdef_chunks.json",
            "file_format": "txt",
            "processing_status": "good",
            "processed_at": "2026-06-08T00:00:00+00:00",
            "text_length": "1200",
            "word_count": "180",
            "chunk_count": "1",
            "language": "en",
            "detected_document_category": "rss_news",
            "content_hash": "abcdef123456",
        }
    )
    return record


def test_processing_index_can_be_created(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(processing_metadata_service, "metadata_dir", lambda: tmp_path)

    processing_metadata_service.ensure_processing_index()

    assert processing_metadata_service.processing_csv_path().exists()
    assert processing_metadata_service.processing_json_path().exists()
    frame = processing_metadata_service.read_processing_metadata()
    assert list(frame.columns) == PROCESSING_METADATA_FIELDS


def test_processing_metadata_append_and_duplicate_detection(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(processing_metadata_service, "metadata_dir", lambda: tmp_path)
    processing_metadata_service.ensure_processing_index()

    first = processing_metadata_service.append_processing_metadata(_record())
    duplicate = processing_metadata_service.append_processing_metadata(_record())
    found = processing_metadata_service.find_processed_by_source("SRC_001")
    filtered = processing_metadata_service.filter_processing_metadata({"source_type": "rss"})
    frame = pd.read_csv(processing_metadata_service.processing_csv_path(), dtype=str).fillna("")

    assert first["created"] is True
    assert duplicate["duplicate"] is True
    assert found is not None
    assert len(filtered) == 1
    assert len(frame) == 1
