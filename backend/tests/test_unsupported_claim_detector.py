from backend.app.services.explainability.unsupported_claim_detector import detect_unsupported_claims


def test_unsupported_claim_detector_flags_investment_advice_language() -> None:
    claims = detect_unsupported_claims("Investors must invest now and buy the stock.")

    issue_types = {claim["issue_type"] for claim in claims}

    assert "investment_advice" in issue_types


def test_unsupported_claim_detector_flags_stock_prediction_language() -> None:
    claims = detect_unsupported_claims("The stock will definitely rise next month.")

    issue_types = {claim["issue_type"] for claim in claims}

    assert "stock_prediction" in issue_types
    assert "unsupported_certainty" in issue_types
