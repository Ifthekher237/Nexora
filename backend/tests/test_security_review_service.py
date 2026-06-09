from backend.app.services.deployment import security_review_service


def test_security_review_does_not_claim_production_security_complete() -> None:
    review = security_review_service.security_review()

    assert review["production_security_complete"] is False
    assert review["authentication_implemented"] is False
    assert review["authorization_implemented"] is False
    assert any("not implemented" in limitation.lower() for limitation in review["limitations"])
