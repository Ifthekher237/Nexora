import pytest

from backend.app.services.retrieval import retrieval_service
from backend.app.services.retrieval.faiss_store import FaissStoreError, search_vectors


def test_retrieval_service_handles_empty_index_without_model_load(monkeypatch) -> None:
    monkeypatch.setattr(retrieval_service, "filter_vector_metadata", lambda filters: [])

    result = retrieval_service.search(
        query="financial risk",
        top_k=5,
        vector_store="faiss",
        filters={},
    )

    assert result == {"query": "financial risk", "top_k": 5, "results": []}


def test_faiss_store_handles_missing_index(tmp_path, monkeypatch) -> None:
    from backend.app.services.retrieval import faiss_store

    monkeypatch.setattr(faiss_store, "index_path", lambda: tmp_path / "missing.index")

    with pytest.raises(FaissStoreError):
        search_vectors([[0.1, 0.2]], top_k=1)
