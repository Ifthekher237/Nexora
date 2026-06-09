from backend.app.services.rag import hallucination_guard
from backend.app.services.rag.citation_service import build_sources


def test_hallucination_guard_blocks_no_evidence() -> None:
    blocked, reason = hallucination_guard.should_block_without_llm([])

    assert blocked
    assert "No qualifying evidence" in reason


def test_hallucination_guard_appends_missing_citations() -> None:
    sources = build_sources(
        [{"source_number": 1, "score": 0.7, "chunk_id": "chunk-1", "chunk_text": "Evidence"}]
    )

    result = hallucination_guard.validate_answer("Direct answer without source.", sources)

    assert result["status"] == "success"
    assert "[Source 1]" in result["answer"]
    assert result["limitations"]
