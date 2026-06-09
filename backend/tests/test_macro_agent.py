from backend.app.services.agents import agent_memory_service
from backend.app.services.agents.macroeconomic_agent import MacroeconomicAgent


def test_macro_agent_handles_missing_evidence(monkeypatch) -> None:
    agent = MacroeconomicAgent()
    monkeypatch.setattr(agent, "retrieve_evidence", lambda context: [])

    output = agent.run(
        {"scenario": "What if interest rates rise?", "top_k": 5, "parsed_scenario": {}},
        agent_memory_service.create_memory("What if interest rates rise?", {}),
    )

    assert output["agent_key"] == "macroeconomic_agent"
    assert output["status"] == "insufficient_evidence"
    assert output["confidence"]["level"] == "low"
