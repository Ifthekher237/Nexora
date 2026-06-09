"""Display saved deployment readiness and final project reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.deployment.final_report_service import read_history


def main() -> int:
    parser = argparse.ArgumentParser(description="Show saved Nexora deployment reports.")
    parser.add_argument("--report-type", default=None)
    args = parser.parse_args()
    records = read_history({"report_type": args.report_type})
    if not records:
        print("No saved deployment reports found.")
        return 0

    columns = ["report_id", "created_at", "report_type", "readiness_score", "readiness_level", "status", "json_path"]
    widths = {column: len(column) for column in columns}
    for record in records:
        for column in columns:
            widths[column] = min(max(widths[column], len(str(record.get(column, "")))), 42)
    header = "  ".join(column.ljust(widths[column]) for column in columns)
    print(header)
    print("-" * len(header))
    for record in records:
        values = []
        for column in columns:
            value = str(record.get(column, ""))
            if len(value) > widths[column]:
                value = value[: widths[column] - 3] + "..."
            values.append(value.ljust(widths[column]))
        print("  ".join(values))
    return 0


if __name__ == "__main__":
    sys.exit(main())
