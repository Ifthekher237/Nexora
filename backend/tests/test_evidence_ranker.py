from backend.app.services.explainability.evidence_ranker import rank_evidence


def test_evidence_ranker_prefers_stronger_available_signals() -> None:
    ranked = rank_evidence(
        [
            {
                "source_number": "Source 1",
                "chunk_id": "weak",
                "source_document_id": "DOC_WEAK",
                "document_type": "unknown",
                "source_type": "unknown",
                "published_date": "unknown",
                "retrieval_score": 0.2,
                "citation_usage_count": 0,
            },
            {
                "source_number": "Source 2",
                "chunk_id": "strong",
                "source_document_id": "DOC_STRONG",
                "document_type": "10-k",
                "source_type": "sec",
                "published_date": "2026-06-01",
                "retrieval_score": 0.85,
                "citation_usage_count": 2,
            },
        ]
    )

    assert ranked[0]["evidence_id"] == "strong"
    assert ranked[0]["score"] > ranked[1]["score"]
