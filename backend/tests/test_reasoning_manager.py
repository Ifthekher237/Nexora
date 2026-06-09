from backend.app.schemas.reasoning import ScenarioAnalysisResponse
from backend.app.services.reasoning import reasoning_manager


def test_reasoning_manager_handles_no_evidence_gracefully(monkeypatch) -> None:
    monkeypatch.setattr(
        reasoning_manager.reasoning_evidence_service,
        "retrieve_reasoning_evidence",
        lambda **kwargs: {
            "evidence_map": [],
            "evidence_context": "",
            "retrieval_summary": {"results_found": 0, "evidence_used": 0},
            "limitations": ["No retrieval results were returned."],
        },
    )
    monkeypatch.setattr(
        reasoning_manager.reasoning_output_service,
        "save_output",
        lambda output: {"saved": False, "response_path": ""},
    )

    result = reasoning_manager.analyze_scenario("What happens if oil prices rise?", top_k=5)

    assert result["status"] == "insufficient_evidence"
    assert result["confidence"]["level"] == "low"
    assert result["evidence_map"] == []
    assert "not called" in result["validation_warnings"][0]
    ScenarioAnalysisResponse(**result)
