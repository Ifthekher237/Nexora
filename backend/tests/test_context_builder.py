from backend.app.services.rag.context_builder import build_context


def _result(score: float, chunk_id: str = "chunk-1") -> dict[str, object]:
    return {
        "rank": 1,
        "score": score,
        "chunk_id": chunk_id,
        "chunk_text": "Revenue risk increased because of debt and liquidity pressure.",
        "metadata": {
            "company_name": "Apple Inc.",
            "ticker": "AAPL",
            "document_type": "SEC Filing Metadata",
            "source_type": "sec",
            "published_at": "2026-05-29",
            "source_document_id": "SEC_AAPL_4",
            "processed_document_id": "PROC_SEC_AAPL_4",
        },
    }


def test_context_builder_formats_evidence() -> None:
    context = build_context({"results": [_result(0.82)]}, min_score=0.25)

    assert context["evidence_used"] == 1
    assert "[Source 1]" in context["evidence_context"]
    assert "Score: 0.8200" in context["evidence_context"]
    assert "Company: Apple Inc." in context["evidence_context"]
    assert context["evidence"][0]["metadata"]["ticker"] == "AAPL"


def test_context_builder_filters_weak_results() -> None:
    context = build_context({"results": [_result(0.12)]}, min_score=0.25)

    assert context["results_found"] == 1
    assert context["evidence_used"] == 0
    assert context["evidence_context"] == ""
    assert "minimum evidence score" in context["limitations"][0]
