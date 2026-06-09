from backend.app.services.reasoning.reasoning_validation_service import validate_reasoning_output


def _output(direct_answer: str) -> dict[str, object]:
    return {
        "direct_answer": direct_answer,
        "causal_chain": [{"step": 1, "cause": "A", "effect": "B"}],
        "evidence_map": [{"source_number": "Source 1"}],
        "confidence": {"level": "medium", "score": 0.6, "reason": "test"},
        "limitations": ["limited evidence"],
        "validation_warnings": [],
        "status": "success",
    }


def test_reasoning_validation_flags_missing_citations() -> None:
    result = validate_reasoning_output(_output("Reasoning without citations."))

    assert "source citations" in result["validation_warnings"][0]
    assert result["confidence"]["score"] < 0.6


def test_reasoning_validation_blocks_investment_advice_language() -> None:
    result = validate_reasoning_output(_output("Investors should buy this stock. [Source 1]"))

    assert result["status"] == "guarded"
    assert any("Investment advice" in warning for warning in result["validation_warnings"])
