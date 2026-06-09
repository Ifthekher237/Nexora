from backend.app.services.risk.risk_validation_service import validate_risk_output


def _risk_output(explanation: str) -> dict[str, object]:
    return {
        "overall_risk_score": 50,
        "overall_risk_level": "moderate",
        "confidence": {"level": "medium", "score": 0.6, "reason": "test"},
        "evidence_summary": {"sources_used": 1},
        "limitations": ["limited"],
        "not_financial_advice": True,
        "risk_drivers": [{"explanation": ""}],
        "explanation": explanation,
        "validation_warnings": [],
        "status": "success",
    }


def test_risk_validation_blocks_investment_advice_language() -> None:
    result = validate_risk_output(_risk_output("Investors should buy this stock."))

    assert result["status"] == "guarded"
    assert any("Investment recommendation" in warning for warning in result["validation_warnings"])


def test_risk_validation_blocks_stock_prediction_language() -> None:
    result = validate_risk_output(_risk_output("The stock price will rise."))

    assert result["status"] == "guarded"
    assert any("Stock prediction" in warning for warning in result["validation_warnings"])
