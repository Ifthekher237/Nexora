"""Local per-workflow shared memory for agent collaboration."""

from __future__ import annotations

from typing import Any

from backend.app.services.ingestion.metadata_service import utc_now_iso


def create_memory(scenario: str, parsed_inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "parsed_inputs": parsed_inputs,
        "evidence_collected": {},
        "agent_outputs": {},
        "intermediate_findings": [],
        "shared_warnings": [],
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }


def store_evidence(memory: dict[str, Any], agent_key: str, evidence: list[dict[str, Any]]) -> None:
    memory.setdefault("evidence_collected", {})[agent_key] = evidence
    memory["updated_at"] = utc_now_iso()


def get_evidence(memory: dict[str, Any], agent_key: str) -> list[dict[str, Any]]:
    evidence = memory.get("evidence_collected", {}).get(agent_key, [])
    return evidence if isinstance(evidence, list) else []


def store_agent_output(memory: dict[str, Any], agent_key: str, output: dict[str, Any]) -> None:
    memory.setdefault("agent_outputs", {})[agent_key] = output
    summary = output.get("summary")
    if summary:
        memory.setdefault("intermediate_findings", []).append(
            {"agent_key": agent_key, "summary": summary, "status": output.get("status", "")}
        )
    for warning in output.get("validation_warnings", []):
        add_warning(memory, str(warning))
    memory["updated_at"] = utc_now_iso()


def get_agent_output(memory: dict[str, Any], agent_key: str) -> dict[str, Any] | None:
    output = memory.get("agent_outputs", {}).get(agent_key)
    return output if isinstance(output, dict) else None


def add_warning(memory: dict[str, Any], warning: str) -> None:
    if warning and warning not in memory.setdefault("shared_warnings", []):
        memory["shared_warnings"].append(warning)
        memory["updated_at"] = utc_now_iso()
