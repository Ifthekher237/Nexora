"""Run a final safe local Nexora system check."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.deployment import api_audit_service, deployment_readiness_service, final_report_service
from backend.app.services.performance import optimization_manager


def main() -> int:
    setup_logging()
    readiness = deployment_readiness_service.run_readiness_check(save=False)
    api_audit = api_audit_service.audit_api_routes()
    performance = optimization_manager.performance_status()
    deployment_reports = final_report_service.read_history({})
    result = {
        "status": "ready" if readiness.get("readiness_score", 0) >= 80 and api_audit.get("status") == "success" else "needs_attention",
        "readiness_score": readiness.get("readiness_score"),
        "readiness_level": readiness.get("readiness_level"),
        "api_route_count": api_audit.get("route_count", 0),
        "performance_status": performance.get("status"),
        "deployment_report_count": len(deployment_reports),
        "not_cloud_deployed": True,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
