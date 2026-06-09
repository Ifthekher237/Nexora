"""Display saved Nexora performance benchmark history."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.performance.performance_report_service import read_history


def main() -> int:
    parser = argparse.ArgumentParser(description="Show saved performance benchmark reports.")
    parser.add_argument("--status", default=None)
    args = parser.parse_args()
    records = read_history({"status": args.status})
    if not records:
        print("No saved performance benchmark reports found.")
        return 0

    columns = ["benchmark_id", "started_at", "total_runtime_ms", "query_count", "include_rag", "include_reasoning", "include_agents", "status"]
    widths = {column: len(column) for column in columns}
    for record in records:
        for column in columns:
            widths[column] = min(max(widths[column], len(str(record.get(column, "")))), 36)
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
