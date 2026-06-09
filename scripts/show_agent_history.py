"""Display saved Nexora agent workflow history."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.agents.agent_output_service import read_history


def main() -> int:
    parser = argparse.ArgumentParser(description="Show saved Nexora agent workflow runs.")
    parser.add_argument("--status", default=None)
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--agent-name", default=None)
    parser.add_argument("--confidence-level", default=None, choices=["low", "medium", "high"])
    args = parser.parse_args()

    records = read_history(
        {
            "status": args.status,
            "ticker": args.ticker,
            "agent_name": args.agent_name,
            "confidence_level": args.confidence_level,
        }
    )
    if not records:
        print("No saved agent runs found.")
        return 0

    columns = [
        "agent_run_id",
        "created_at",
        "status",
        "overall_confidence_level",
        "overall_confidence_score",
        "agents_run",
        "scenario",
    ]
    widths = {column: len(column) for column in columns}
    for record in records:
        for column in columns:
            max_width = 56 if column in {"scenario", "agents_run"} else 34
            widths[column] = min(max(widths[column], len(str(record.get(column, "")))), max_width)

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
