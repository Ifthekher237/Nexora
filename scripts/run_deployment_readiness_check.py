"""Run Nexora Phase 12 deployment readiness check."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.deployment import deployment_readiness_service


def main() -> int:
    setup_logging()
    result = deployment_readiness_service.run_readiness_check(save=True)
    print(
        json.dumps(
            {
                "report_id": result.get("report_id", ""),
                "status": result.get("status"),
                "readiness_score": result.get("readiness_score"),
                "readiness_level": result.get("readiness_level"),
                "summary": result.get("summary", {}),
                "json_path": result.get("json_path", ""),
                "error_message": result.get("error_message", ""),
            },
            indent=2,
        )
    )
    return 0 if result.get("status") in {"success", "partial_success"} else 1


if __name__ == "__main__":
    sys.exit(main())
