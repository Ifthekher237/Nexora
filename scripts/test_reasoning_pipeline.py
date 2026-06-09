"""Run a safe local Phase 6 reasoning pipeline check."""

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
    result = reasoning_manager.analyze_scenario(SCENARIO, top_k=5)
    print(json.dumps(
        {
            "status": result.get("status"),
            "scenario_type": result.get("scenario_type"),
            "chain_steps": len(result.get("causal_chain", [])),
            "evidence_count": len(result.get("evidence_map", [])),
            "confidence": result.get("confidence"),
            "validation_warnings": result.get("validation_warnings", []),
            "error_message": result.get("error_message", ""),
        },
        indent=2,
    ))
    if result.get("status") == "error":
        return 0 if "Ollama" in result.get("error_message", "") else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
