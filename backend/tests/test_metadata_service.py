import pandas as pd

from backend.app.services.ingestion import metadata_service
from backend.app.services.ingestion.validation_service import REQUIRED_METADATA_FIELDS


def _record(document_id: str = "LOCAL_QAN_ANNUALREPORT_2024_abcdef") -> dict[str, str]:
    record = {field: "" for field in REQUIRED_METADATA_FIELDS}
    record.update(
        {
            "document_id": document_id,
            "source_type": "local_uploads",
            "source_name": "Manual local file",
            "company_name": "Qantas Airways",
            "ticker": "QAN",
            "market": "ASX",
            "document_type": "annual_report",
            "title": "Qantas annual report 2024",
            "local_path": "data/raw/local_uploads/report.pdf",
            "file_format": "pdf",
            "ingested_at": "2026-06-08T00:00:00+00:00",
            "period": "2024",
            "status": "saved",
            "content_hash": "abcdef123456",
        }
    )
    return record


def test_metadata_index_can_be_created(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(metadata_service, "metadata_root", lambda: tmp_path)

    metadata_service.ensure_metadata_index()

    assert metadata_service.csv_index_path().exists()
    assert metadata_service.json_index_path().exists()
    frame = metadata_service.read_metadata()
    assert list(frame.columns) == REQUIRED_METADATA_FIELDS


def test_metadata_append_duplicate_and_filter(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(metadata_service, "metadata_root", lambda: tmp_path)
    metadata_service.ensure_metadata_index()

    first = metadata_service.append_metadata(_record())
    duplicate = metadata_service.append_metadata(_record())
    filtered = metadata_service.filter_metadata({"ticker": "QAN", "source_type": None})
    frame = pd.read_csv(metadata_service.csv_index_path(), dtype=str).fillna("")

    assert first["created"] is True
    assert duplicate["duplicate"] is True
    assert len(frame) == 1
    assert len(filtered) == 1
    assert filtered[0]["document_id"] == "LOCAL_QAN_ANNUALREPORT_2024_abcdef"
