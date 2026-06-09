"""Run a simple Phase 6 reasoning smoke test."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.reasoning import reasoning_manager


SCENARIO = "What financial risks could appear if interest rates rise?"


def main() -> int:
    setup_logging()
    print(f"Scenario: {SCENARIO}")
    evidence = reasoning_manager.evidence_map_only(SCENARIO, top_k=5)
    print("Evidence-map status:")
    print(json.dumps(
        {
            "status": evidence.get("status"),
            "scenario_type": evidence.get("scenario_type"),
            "evidence_count": len(evidence.get("evidence_map", [])),
            "retrieval_summary": evidence.get("retrieval_summary", {}),
        },
        indent=2,
    ))

    result = reasoning_manager.analyze_scenario(SCENARIO, top_k=5)
    print("Reasoning status:")
    print(json.dumps(
        {
            "status": result.get("status"),
            "reasoning_id": result.get("reasoning_id"),
            "scenario_type": result.get("scenario_type"),
            "confidence": result.get("confidence"),
            "evidence_count": len(result.get("evidence_map", [])),
            "error_message": result.get("error_message", ""),
        },
        indent=2,
    ))
    if result.get("status") == "error":
        print(
            "The reasoning request did not complete. If the error mentions Ollama, "
            "start it with `ollama serve` or open the Ollama app, then rerun this script."
        )
        return 0 if "Ollama" in result.get("error_message", "") else 1
    print("Reasoning smoke test completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
