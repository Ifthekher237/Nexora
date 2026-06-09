import pytest

from backend.app.schemas.explainability import ExplainabilityReportResponse
from backend.app.services.explainability import explainability_manager


def _mock_risk_output() -> dict[str, object]:
    return {
        "risk_id": "RISK_TEST",
        "source_reasoning_id": "REASON_TEST",
        "scenario": "What financial risks could appear if interest rates rise?",
        "scenario_type": "interest_rate_change",
        "overall_risk_score": 46,
        "overall_risk_level": "moderate",
        "confidence": {"level": "low", "score": 0.33, "reason": "Weak evidence."},
        "explanation": "The risk score is moderate because borrowing costs may rise.",
        "limitations": ["Risk scores are estimates, not predictions."],
        "risk_drivers": [],
        "validation_warnings": [],
        "status": "success",
    }


def _mock_reasoning_output() -> dict[str, object]:
    return {
        "reasoning_id": "REASON_TEST",
        "scenario": "What financial risks could appear if interest rates rise?",
        "scenario_type": "interest_rate_change",
        "direct_answer": "Borrowing costs may rise. [Source 1]",
        "causal_chain": [
            {
                "step": 1,
                "cause": "Rate increase",
                "effect": "Borrowing cost increase",
                "evidence_strength": "medium",
                "supporting_sources": ["Source 1"],
                "uncertainty": "",
            }
        ],
        "evidence_map": [
            {
                "source_number": "Source 1",
                "chunk_id": "CHUNK_1",
                "source_document_id": "DOC_1",
                "processed_document_id": "PROC_1",
                "score": 0.75,
                "evidence_text": "Debt refinancing evidence.",
                "metadata": {
                    "company_name": "Apple Inc.",
                    "ticker": "AAPL",
                    "market": "US",
                    "document_type": "10-k",
                    "source_type": "sec",
                    "published_at": "2026-05-29",
                },
            }
        ],
        "confidence": {"level": "medium", "score": 0.6, "reason": "Mock confidence."},
        "limitations": [],
        "validation_warnings": [],
    }


def test_explainability_manager_handles_missing_target_gracefully(monkeypatch) -> None:
    monkeypatch.setattr(explainability_manager.risk_output_service, "read_output", lambda risk_id: None)

    with pytest.raises(explainability_manager.ExplainabilityManagerError) as exc:
        explainability_manager.explain_risk("MISSING_RISK")

    assert "Risk output not found" in str(exc.value)


def test_explainability_manager_can_explain_mocked_risk_output(monkeypatch) -> None:
    monkeypatch.setattr(explainability_manager.risk_output_service, "read_output", lambda risk_id: _mock_risk_output())
    monkeypatch.setattr(
        explainability_manager.reasoning_output_service,
        "read_output",
        lambda reasoning_id: _mock_reasoning_output(),
    )
    monkeypatch.setattr(
        explainability_manager.explainability_output_service,
        "save_report",
        lambda report: {"saved": False, "report_path": ""},
    )

    report = explainability_manager.explain_risk("RISK_TEST")

    assert report["status"] == "success"
    assert report["target_type"] == "risk"
    assert report["target_id"] == "RISK_TEST"
    assert report["expanded_citations"][0]["source_document_id"] == "DOC_1"
    assert report["evidence_coverage"]["sources_used"] == 1
    ExplainabilityReportResponse(**report)
