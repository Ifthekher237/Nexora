import json

from backend.app.services.processing.document_loader import load_document_text


def test_txt_loader_works(tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("Revenue increased by 12%.", encoding="utf-8")

    loaded = load_document_text(str(sample))

    assert "Revenue increased" in loaded["text"]
    assert loaded["file_format"] == "txt"


def test_json_loader_formats_sec_metadata(tmp_path) -> None:
    sample = tmp_path / "sec.json"
    sample.write_text(
        json.dumps(
            {
                "ticker": "AAPL",
                "cik": "0000320193",
                "company_name": "Apple Inc.",
                "source_url": "https://www.sec.gov/example",
                "filing": {
                    "form_type": "10-K",
                    "filing_date": "2024-11-01",
                    "report_date": "2024-09-30",
                    "accession_number": "0000320193-24-000001",
                    "primary_document": "aapl-20240930.htm",
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_document_text(str(sample))

    assert "Form type: 10-K" in loaded["text"]
    assert "Accession number: 0000320193-24-000001" in loaded["text"]


def test_csv_loader_summarizes_small_csv(tmp_path) -> None:
    sample = tmp_path / "macro.csv"
    sample.write_text("date,value\n2026-01-01,2.5\n", encoding="utf-8")

    loaded = load_document_text(str(sample))

    assert "CSV dataset" in loaded["text"]
    assert "Columns: date, value" in loaded["text"]
