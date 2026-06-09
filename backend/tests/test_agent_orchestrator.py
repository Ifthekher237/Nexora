from backend.app.schemas.agents import AgentWorkflowResponse
from backend.app.services.agents import agent_orchestrator, agent_output_service


class StubSuccessAgent:
    agent_key = "stub_success"
    agent_name = "Stub Success Agent"
    description = "Test success agent."

    def run(self, context, memory):
        return {
            "agent_name": self.agent_name,
            "agent_key": self.agent_key,
            "status": "success",
            "summary": "Evidence-backed stub summary.",
            "key_findings": ["Source 1 supports the stub finding."],
            "evidence_used": [
                {
                    "source_number": "Source 1",
                    "chunk_id": "CHUNK_1",
                    "source_document_id": "DOC_1",
                    "processed_document_id": "PROC_1",
                    "relevance": "stub",
                    "score": 0.8,
                    "evidence_text": "interest rates and borrowing costs",
                    "metadata": {},
                }
            ],
            "confidence": {"level": "high", "score": 0.8, "reason": "mock"},
            "limitations": ["Local evidence only."],
            "validation_warnings": [],
            "details": {},
        }


class StubFailingAgent:
    agent_key = "stub_failure"
    agent_name = "Stub Failing Agent"
    description = "Test failing agent."

    def run(self, context, memory):
        raise RuntimeError("planned test failure")


class StubInsufficientAgent:
    agent_key = "stub_insufficient"
    agent_name = "Stub Insufficient Agent"
    description = "Test insufficient agent."

    def run(self, context, memory):
        return {
            "agent_name": self.agent_name,
            "agent_key": self.agent_key,
            "status": "insufficient_evidence",
            "summary": "No evidence was found.",
            "key_findings": [],
            "evidence_used": [],
            "confidence": {"level": "low", "score": 0.0, "reason": "No evidence."},
            "limitations": ["No local evidence was found."],
            "validation_warnings": [],
            "details": {},
        }


def test_available_agents_lists_phase_10_agents() -> None:
    agents = agent_orchestrator.available_agents()
    keys = {agent["agent_key"] for agent in agents}

    assert {
        "macroeconomic_agent",
        "company_analysis_agent",
        "sector_analysis_agent",
        "news_intelligence_agent",
        "risk_propagation_agent",
    }.issubset(keys)


def test_agent_run_ids_are_unique_for_same_scenario() -> None:
    first = agent_output_service.generate_agent_run_id("What if interest rates rise?")
    second = agent_output_service.generate_agent_run_id("What if interest rates rise?")

    assert first != second
    assert first.startswith("AGENT_RUN_")
    assert second.startswith("AGENT_RUN_")


def test_agent_orchestrator_saves_workflow_output(monkeypatch) -> None:
    saved = {}
    monkeypatch.setattr(agent_orchestrator, "AGENT_CLASSES", {"stub_success": StubSuccessAgent})
    monkeypatch.setattr(
        agent_orchestrator.agent_output_service,
        "save_output",
        lambda output: saved.setdefault("output", output) or {"saved": True},
    )

    result = agent_orchestrator.run_workflow(
        scenario="What financial risks could appear if interest rates rise?",
        agents=["stub_success"],
        top_k=5,
    )

    assert result["status"] == "success"
    assert saved["output"]["agent_run_id"] == result["agent_run_id"]
    AgentWorkflowResponse(**result)


def test_agent_orchestrator_all_insufficient_status(monkeypatch) -> None:
    monkeypatch.setattr(agent_orchestrator, "AGENT_CLASSES", {"stub_insufficient": StubInsufficientAgent})
    monkeypatch.setattr(agent_orchestrator.agent_output_service, "save_output", lambda output: {"saved": False})

    result = agent_orchestrator.run_workflow(
        scenario="What financial risks could appear if interest rates rise?",
        agents=["stub_insufficient"],
        top_k=5,
    )

    assert result["status"] == "insufficient_evidence"
    AgentWorkflowResponse(**result)


def test_agent_orchestrator_allows_partial_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        agent_orchestrator,
        "AGENT_CLASSES",
        {"stub_success": StubSuccessAgent, "stub_failure": StubFailingAgent},
    )
    monkeypatch.setattr(agent_orchestrator.agent_output_service, "save_output", lambda output: {"saved": False})

    result = agent_orchestrator.run_workflow(
        scenario="What financial risks could appear if interest rates rise?",
        agents=["stub_success", "stub_failure"],
        top_k=5,
    )

    assert result["status"] == "partial_success"
    assert result["agents_run"] == ["stub_success", "stub_failure"]
    AgentWorkflowResponse(**result)
