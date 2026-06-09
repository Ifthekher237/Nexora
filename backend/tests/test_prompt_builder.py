from backend.app.services.rag.prompt_builder import build_prompt


def test_prompt_contains_grounding_rules() -> None:
    prompt = build_prompt(
        question="What risks are mentioned?",
        evidence_context="[Source 1]\nText:\nRisk disclosure.",
        query_understanding={"query_type": "risk_question", "risk_keywords": ["debt"]},
    )

    assert "Use only the evidence provided" in prompt
    assert "Do not invent facts" in prompt
    assert "Cite sources using [Source 1]" in prompt
    assert "Do not give investment advice" in prompt
    assert "Do not predict exact stock prices" in prompt
    assert "- Direct Answer" in prompt
