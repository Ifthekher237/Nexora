"""Run a local Phase 7 risk pipeline check."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.risk import risk_manager


SCENARIO = "What financial risks could appear if interest rates rise?"


def main() -> int:
    setup_logging()
    result = risk_manager.score_scenario(SCENARIO, top_k=5)
    print(json.dumps(
        {
            "status": result.get("status"),
            "overall_risk_score": result.get("overall_risk_score"),
            "overall_risk_level": result.get("overall_risk_level"),
            "confidence": result.get("confidence"),
            "sources_used": (result.get("evidence_summary") or {}).get("sources_used"),
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
