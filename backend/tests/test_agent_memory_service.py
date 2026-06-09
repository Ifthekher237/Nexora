from backend.app.services.agents import agent_memory_service


def test_agent_memory_stores_evidence_outputs_and_warnings() -> None:
    memory = agent_memory_service.create_memory("Interest rates rise", {"scenario_type": "interest_rate_change"})
    evidence = [{"source_number": "Source 1", "chunk_id": "CHUNK_1"}]
    output = {
        "summary": "Macro pressure appears in the evidence.",
        "status": "success",
        "validation_warnings": ["Check evidence coverage."],
    }

    agent_memory_service.store_evidence(memory, "macroeconomic_agent", evidence)
    agent_memory_service.store_agent_output(memory, "macroeconomic_agent", output)
    agent_memory_service.add_warning(memory, "Check evidence coverage.")

    assert agent_memory_service.get_evidence(memory, "macroeconomic_agent") == evidence
    assert agent_memory_service.get_agent_output(memory, "macroeconomic_agent") == output
    assert memory["shared_warnings"] == ["Check evidence coverage."]
    assert memory["intermediate_findings"][0]["agent_key"] == "macroeconomic_agent"
