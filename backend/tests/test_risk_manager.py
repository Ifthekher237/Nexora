from backend.app.schemas.risk import RiskScoringResponse
from backend.app.services.risk import risk_manager


def _mock_reasoning_output(evidence: bool = True) -> dict[str, object]:
    return {
        "reasoning_id": "REASON_TEST",
        "scenario": "What financial risks could appear if interest rates rise?",
        "company_name": "",
        "ticker": "",
        "market": "",
        "scenario_type": "interest_rate_change",
        "direct_answer": "Interest rate risk is evidence-limited. [Source 1]",
        "causal_chain": [
            {"step": 1, "cause": "Interest rate increase", "effect": "Borrowing cost increase", "supporting_sources": ["Source 1"]},
            {"step": 2, "cause": "Borrowing cost increase", "effect": "Cash flow pressure", "supporting_sources": []},
        ],
        "financial_exposure_analysis": {
            "operational_exposure": "Potential operational exposure areas: debt/refinancing, cash flow, customer demand.",
            "macro_exposure": "Relevant macro channel(s): interest rates.",
            "sector_exposure": "Inferred sector: unknown.",
            "company_specific_exposure": "No company or ticker was specified, so company-specific exposure cannot be confirmed.",
        },
        "evidence_map": [
            {"source_number": "Source 1", "score": 0.75, "source_document_id": "DOC_1", "evidence_text": "interest rate borrowing cost debt"}
        ] if evidence else [],
        "confidence": {"level": "medium", "score": 0.6, "reason": "mock"},
        "limitations": [],
        "validation_warnings": [],
        "status": "success",
        "model": "llama3.1:8b",
    }


def test_risk_manager_handles_no_evidence_gracefully(monkeypatch) -> None:
    monkeypatch.setattr(risk_manager.reasoning_manager, "analyze_scenario", lambda **kwargs: _mock_reasoning_output(evidence=False))
    monkeypatch.setattr(risk_manager.risk_output_service, "save_output", lambda output: {"saved": False})

    result = risk_manager.score_scenario("What happens if interest rates rise?", top_k=5)

    assert result["status"] == "insufficient_evidence"
    assert result["overall_risk_score"] == 0
    RiskScoringResponse(**result)


def test_risk_manager_scores_from_mocked_reasoning_output(monkeypatch) -> None:
    monkeypatch.setattr(risk_manager.risk_output_service, "save_output", lambda output: {"saved": False})

    result = risk_manager.score_reasoning_output(_mock_reasoning_output())

    assert result["status"] == "success"
    assert 0 <= result["overall_risk_score"] <= 100
    assert any("company-agnostic" in limitation for limitation in result["limitations"])
    RiskScoringResponse(**result)
