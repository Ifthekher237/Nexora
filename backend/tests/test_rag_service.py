from backend.app.schemas.rag import RAGAskResponse
from backend.app.services.rag import rag_manager


def test_rag_service_handles_empty_retrieval_gracefully(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_manager.retrieval_service,
        "search",
        lambda **kwargs: {"query": kwargs["query"], "top_k": kwargs["top_k"], "results": []},
    )
    monkeypatch.setattr(
        rag_manager,
        "call_ollama_model",
        lambda **kwargs: "This should not run.",
    )
    monkeypatch.setattr(
        rag_manager.rag_response_service,
        "save_response",
        lambda response: {"saved": False, "response_path": ""},
    )

    result = rag_manager.ask_question("What risks are mentioned?", top_k=5)

    assert result["status"] == "insufficient_evidence"
    assert result["sources"] == []
    assert "LLM was not called" in result["answer"]
    RAGAskResponse(**result)


def test_rag_service_returns_schema_valid_answer(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_manager.retrieval_service,
        "search",
        lambda **kwargs: {
            "query": kwargs["query"],
            "top_k": kwargs["top_k"],
            "results": [
                {
                    "rank": 1,
                    "score": 0.88,
                    "chunk_id": "chunk-1",
                    "chunk_text": "The document mentions debt and liquidity risk.",
                    "metadata": {
                        "source_document_id": "SEC_AAPL_4",
                        "processed_document_id": "PROC_SEC_AAPL_4",
                        "company_name": "Apple Inc.",
                        "ticker": "AAPL",
                        "document_type": "SEC Filing Metadata",
                        "source_type": "sec",
                        "published_at": "2026-05-29",
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        rag_manager,
        "call_ollama_model",
        lambda **kwargs: "- Direct Answer\nDebt and liquidity risk are mentioned. [Source 1]",
    )
    monkeypatch.setattr(
        rag_manager.rag_response_service,
        "save_response",
        lambda response: {"saved": False, "response_path": ""},
    )

    result = rag_manager.ask_question("What debt risk is mentioned?", top_k=5)

    assert result["status"] == "success"
    assert result["sources"][0]["ticker"] == "AAPL"
    assert result["confidence"]["level"] in {"medium", "high"}
    RAGAskResponse(**result)
