"""Run a local Phase 10 agent workflow smoke test."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.agents import agent_orchestrator


SCENARIO = "What financial risks could appear if interest rates rise?"


def main() -> int:
    setup_logging()
    result = agent_orchestrator.run_workflow(scenario=SCENARIO, top_k=5)
    print(
        json.dumps(
            {
                "status": result.get("status"),
                "agent_run_id": result.get("agent_run_id"),
                "agents_run": result.get("agents_run", []),
                "overall_confidence": result.get("overall_confidence"),
                "agent_statuses": {
                    output.get("agent_key"): output.get("status")
                    for output in result.get("agent_outputs", [])
                },
                "error_message": result.get("error_message", ""),
            },
            indent=2,
        )
    )
    return 0 if result.get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
