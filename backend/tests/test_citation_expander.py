from backend.app.services.explainability import citation_expander


def test_citation_expander_preserves_source_metadata() -> None:
    result = citation_expander.expand_citations(
        [
            {
                "rank": 1,
                "chunk_id": "CHUNK_1",
                "source_document_id": "DOC_1",
                "processed_document_id": "PROC_1",
                "company_name": "Apple Inc.",
                "ticker": "AAPL",
                "market": "US",
                "document_type": "10-k",
                "source_type": "sec",
                "published_at": "2026-05-29",
                "score": 0.82,
                "evidence_text": "Revenue and debt evidence.",
            }
        ],
        target_text="The answer cites Source 1.",
    )

    citation = result["citations"][0]

    assert citation["source_number"] == "Source 1"
    assert citation["chunk_id"] == "CHUNK_1"
    assert citation["source_document_id"] == "DOC_1"
    assert citation["ticker"] == "AAPL"
    assert citation["retrieval_score"] == 0.82
    assert citation["citation_usage_count"] == 1


def test_citation_expander_marks_missing_fields_unknown() -> None:
    result = citation_expander.expand_citations([{"source_number": "Source X", "score": 0.4}])

    citation = result["citations"][0]

    assert citation["chunk_id"] == "unknown"
    assert citation["source_document_id"] == "unknown"
    assert "chunk_id" in citation["missing_fields"]
    assert result["limitations"]
