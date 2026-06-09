from backend.app.services.agents import agent_memory_service
from backend.app.services.agents.risk_propagation_agent import RiskPropagationAgent


def test_risk_propagation_agent_returns_chain_without_evidence(monkeypatch) -> None:
    agent = RiskPropagationAgent()
    monkeypatch.setattr(agent, "retrieve_evidence", lambda context: [])

    output = agent.run(
        {
            "scenario": "What if interest rates rise?",
            "top_k": 5,
            "parsed_scenario": {"scenario_type": "interest_rate_change", "macro_trigger": "interest rates"},
        },
        agent_memory_service.create_memory("What if interest rates rise?", {}),
    )

    assert output["status"] == "insufficient_evidence"
    assert output["details"]["causal_chain"]
    assert output["evidence_used"] == []
