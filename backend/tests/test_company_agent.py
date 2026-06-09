from backend.app.services.agents import agent_memory_service
from backend.app.services.agents.company_analysis_agent import CompanyAnalysisAgent


def test_company_agent_requires_company_or_ticker() -> None:
    agent = CompanyAnalysisAgent()

    output = agent.run(
        {"scenario": "What if interest rates rise?", "company_name": "", "ticker": "", "top_k": 5},
        agent_memory_service.create_memory("What if interest rates rise?", {}),
    )

    assert output["status"] == "insufficient_evidence"
    assert any("company name or ticker" in limitation.lower() for limitation in output["limitations"])
