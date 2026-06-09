from backend.app.services.rag.confidence_service import estimate_confidence


def test_confidence_high_for_multiple_strong_sources() -> None:
    evidence = [
        {
            "score": 0.92,
            "chunk_text": "Revenue risk and debt risk are discussed.",
            "metadata": {"source_document_id": f"doc-{index % 3}"},
        }
        for index in range(5)
    ]

    confidence = estimate_confidence(evidence, "What revenue debt risk is mentioned?")

    assert confidence["level"] == "high"
    assert confidence["score"] >= 0.75


def test_confidence_low_without_evidence() -> None:
    confidence = estimate_confidence([], "What risks are mentioned?")

    assert confidence["level"] == "low"
    assert confidence["score"] == 0.0
    assert "No usable retrieved evidence" in confidence["reason"]
