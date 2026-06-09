from backend.app.services.reasoning import causal_chain_service, reasoning_evidence_service


def test_reasoning_evidence_service_maps_retrieval_to_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        reasoning_evidence_service.retrieval_service,
        "search",
        lambda **kwargs: {
            "query": kwargs["query"],
            "top_k": kwargs["top_k"],
            "results": [
                {
                    "rank": 1,
                    "score": 0.86,
                    "chunk_id": "chunk-1",
                    "chunk_text": "Interest rate increases can affect borrowing cost and refinancing pressure.",
                    "metadata": {
                        "source_document_id": "DOC_1",
                        "processed_document_id": "PROC_1",
                        "company_name": "Example Co",
                        "ticker": "EXM",
                        "market": "US",
                        "document_type": "annual_report",
                        "source_type": "local",
                        "published_at": "2026-01-01",
                    },
                }
            ],
        },
    )
    parsed = {"scenario_type": "interest_rate_change", "ticker": "EXM", "market": "US", "key_risk_keywords": ["interest rate"]}
    chain = causal_chain_service.build_causal_chain(parsed)

    result = reasoning_evidence_service.retrieve_reasoning_evidence(
        "interest rates rise",
        parsed,
        chain,
        top_k=5,
    )

    assert result["retrieval_summary"]["evidence_used"] == 1
    assert result["evidence_map"][0]["source_number"] == "Source 1"
    assert result["evidence_map"][0]["source_document_id"] == "DOC_1"
