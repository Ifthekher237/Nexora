from backend.app.services.explainability.limitation_analyzer import analyze_limitations


def test_limitation_analyzer_detects_limited_evidence() -> None:
    limitations = analyze_limitations(
        "risk",
        {"limitations": []},
        [],
        {
            "level": "low",
            "score": 0.2,
            "sources_used": 0,
            "unique_documents": 0,
            "average_retrieval_score": 0.0,
            "company_specific_evidence": False,
        },
    )

    assert any("Evidence coverage is low" in item for item in limitations)
    assert any("Limited evidence" in item for item in limitations)
    assert any("does not provide investment advice" in item for item in limitations)
