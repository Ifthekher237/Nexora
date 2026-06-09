from backend.app.services.risk.confidence_score_service import score_confidence


def test_confidence_score_decreases_with_warnings_and_missing_evidence() -> None:
    reasoning = {
        "confidence": {"score": 0.8},
        "evidence_map": [{"source_number": "Source 1"}],
        "limitations": [],
    }
    clean = score_confidence(reasoning, evidence_strength_score=80, validation_warnings=[])
    weak = score_confidence(
        {"confidence": {"score": 0.8}, "evidence_map": [], "limitations": ["limited"]},
        evidence_strength_score=20,
        validation_warnings=["missing evidence", "missing citations"],
    )

    assert clean["confidence_score"] > weak["confidence_score"]
    assert weak["confidence_level"] == "low"
