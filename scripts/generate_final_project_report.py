"""Generate Nexora final project report in JSON and Markdown."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.deployment import final_report_service


def main() -> int:
    setup_logging()
    report = final_report_service.generate_final_project_report()
    print(
        json.dumps(
            {
                "report_id": report.get("report_id", ""),
                "status": report.get("status"),
                "readiness_score": report.get("readiness_score"),
                "readiness_level": report.get("readiness_level"),
                "json_path": report.get("json_path", ""),
                "markdown_path": report.get("markdown_path", ""),
                "error_message": report.get("error_message", ""),
            },
            indent=2,
        )
    )
    return 0 if report.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
