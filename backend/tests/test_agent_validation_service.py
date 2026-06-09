from backend.app.services.agents import agent_validation_service


def test_agent_validation_flags_advice_and_prediction_language() -> None:
    output = {
        "agent_name": "Unsafe Agent",
        "agent_key": "unsafe_agent",
        "status": "success",
        "summary": "You should buy this stock because the share price will rise.",
        "key_findings": [],
        "evidence_used": [{"chunk_id": "CHUNK_1", "source_document_id": "DOC_1"}],
        "confidence": {"level": "high", "score": 0.9, "reason": "mock"},
        "limitations": ["Local evidence only."],
        "validation_warnings": [],
        "details": {},
    }

    validated = agent_validation_service.validate_agent_output(output)

    assert validated["confidence"]["score"] < 0.9
    assert any("Investment-advice" in warning for warning in validated["validation_warnings"])
    assert any("Stock-prediction" in warning for warning in validated["validation_warnings"])


def test_agent_validation_requires_evidence_for_success() -> None:
    output = {
        "agent_name": "Evidence Agent",
        "agent_key": "evidence_agent",
        "status": "success",
        "summary": "Evidence-grounded summary.",
        "key_findings": [],
        "evidence_used": [],
        "confidence": {"level": "medium", "score": 0.6, "reason": "mock"},
        "limitations": ["Local evidence only."],
        "validation_warnings": [],
        "details": {},
    }

    validated = agent_validation_service.validate_agent_output(output)

    assert validated["confidence"]["score"] < 0.6
    assert "Successful agent output did not include evidence references." in validated["validation_warnings"]


def test_agent_validation_does_not_flag_buyout_as_buy_advice() -> None:
    output = {
        "agent_name": "News Agent",
        "agent_key": "news_agent",
        "status": "success",
        "summary": "A local article mentioned a buyout approval.",
        "key_findings": [],
        "evidence_used": [{"chunk_id": "CHUNK_1", "source_document_id": "DOC_1"}],
        "confidence": {"level": "medium", "score": 0.5, "reason": "mock"},
        "limitations": ["Local evidence only."],
        "validation_warnings": [],
        "details": {},
    }

    validated = agent_validation_service.validate_agent_output(output)

    assert not any("Investment-advice" in warning for warning in validated["validation_warnings"])
    assert validated["confidence"]["score"] == 0.5
