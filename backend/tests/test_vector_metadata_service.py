import pandas as pd

from backend.app.services.retrieval import retrieval_metadata_service
from backend.app.services.retrieval.retrieval_metadata_service import VECTOR_METADATA_FIELDS


def _record(vector_id: str = "FAISS_CHUNK_001_abcdef") -> dict[str, str]:
    record = {field: "" for field in VECTOR_METADATA_FIELDS}
    record.update(
        {
            "vector_id": vector_id,
            "chunk_id": "CHUNK_001",
            "processed_document_id": "PROC_001",
            "source_document_id": "SRC_001",
            "chunk_index": "0",
            "ticker": "AAPL",
            "document_type": "news",
            "source_type": "rss",
            "section_hint": "risk",
            "embedding_model": "BAAI/bge-small-en-v1.5",
            "embedding_dimension": "384",
            "vector_store": "faiss",
            "indexed_at": "2026-06-08T00:00:00+00:00",
            "chunk_word_count": "50",
            "chunk_char_count": "250",
            "source_chunk_file": "data/processed/chunks/sample_chunks.json",
            "status": "indexed",
        }
    )
    return record


def test_vector_metadata_index_can_be_created(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(retrieval_metadata_service, "vector_csv_path", lambda: tmp_path / "vector_index.csv")
    monkeypatch.setattr(retrieval_metadata_service, "vector_json_path", lambda: tmp_path / "vector_index.json")
    monkeypatch.setattr(retrieval_metadata_service, "benchmark_results_path", lambda: tmp_path / "benchmark.json")

    retrieval_metadata_service.ensure_vector_index()

    assert retrieval_metadata_service.vector_csv_path().exists()
    assert retrieval_metadata_service.vector_json_path().exists()
    frame = retrieval_metadata_service.read_vector_metadata()
    assert list(frame.columns) == VECTOR_METADATA_FIELDS


def test_vector_metadata_filter_and_duplicate_detection(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(retrieval_metadata_service, "vector_csv_path", lambda: tmp_path / "vector_index.csv")
    monkeypatch.setattr(retrieval_metadata_service, "vector_json_path", lambda: tmp_path / "vector_index.json")
    monkeypatch.setattr(retrieval_metadata_service, "benchmark_results_path", lambda: tmp_path / "benchmark.json")
    retrieval_metadata_service.ensure_vector_index()

    retrieval_metadata_service.append_vector_metadata([_record(), _record()])
    frame = pd.read_csv(retrieval_metadata_service.vector_csv_path(), dtype=str).fillna("")
    filtered = retrieval_metadata_service.filter_vector_metadata({"ticker": "AAPL"})

    assert len(frame) == 1
    assert len(filtered) == 1
    assert retrieval_metadata_service.is_chunk_indexed(
        "CHUNK_001",
        "faiss",
        "BAAI/bge-small-en-v1.5",
    )
