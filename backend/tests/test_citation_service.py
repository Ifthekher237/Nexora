from backend.app.services.rag.citation_service import build_sources, has_traceable_citations


def test_citation_service_preserves_metadata() -> None:
    sources = build_sources(
        [
            {
                "source_number": 1,
                "score": 0.82,
                "chunk_id": "chunk-1",
                "chunk_text": "Evidence text.",
                "metadata": {
                    "source_document_id": "SEC_AAPL_4",
                    "processed_document_id": "PROC_SEC_AAPL_4",
                    "company_name": "Apple Inc.",
                    "ticker": "AAPL",
                    "document_type": "SEC Filing Metadata",
                    "source_type": "sec",
                    "published_at": "2026-05-29",
                    "source_url": "https://example.test/sec",
                },
            }
        ]
    )

    assert sources[0].rank == 1
    assert sources[0].chunk_id == "chunk-1"
    assert sources[0].source_document_id == "SEC_AAPL_4"
    assert sources[0].ticker == "AAPL"
    assert sources[0].source_url == "https://example.test/sec"


def test_citation_service_detects_traceable_citations() -> None:
    sources = build_sources(
        [{"source_number": 1, "score": 0.7, "chunk_id": "chunk-1", "chunk_text": "Text"}]
    )

    assert has_traceable_citations("Answer [Source 1]", sources)
    assert not has_traceable_citations("Answer [Source 2]", sources)
    assert not has_traceable_citations("Answer without citation", sources)
