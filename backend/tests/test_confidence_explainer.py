from backend.app.services.explainability.confidence_explainer import explain_confidence


def test_confidence_explainer_separates_risk_from_confidence() -> None:
    explanation = explain_confidence(
        {"confidence": {"level": "low", "score": 0.3, "reason": "Weak evidence."}},
        {
            "level": "medium",
            "score": 0.55,
            "sources_used": 3,
            "unique_documents": 2,
            "average_retrieval_score": 0.52,
        },
        [],
    )

    assert explanation["level"] == "low"
    assert "High risk does not mean high confidence" in explanation["distinction"]
    assert "Low confidence does not mean low risk" in explanation["explanation"]
