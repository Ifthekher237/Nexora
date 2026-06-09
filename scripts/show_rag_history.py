"""Display saved Nexora RAG response history."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.rag.rag_response_service import read_history


def main() -> int:
    parser = argparse.ArgumentParser(description="Show saved Nexora RAG responses.")
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--confidence-level", default=None, choices=["low", "medium", "high"])
    parser.add_argument("--status", default=None)
    args = parser.parse_args()

    records = read_history(
        {
            "ticker": args.ticker,
            "model": args.model,
            "confidence_level": args.confidence_level,
            "status": args.status,
        }
    )
    if not records:
        print("No saved RAG responses found.")
        return 0

    columns = [
        "response_id",
        "created_at",
        "model",
        "ticker",
        "confidence_level",
        "confidence_score",
        "source_count",
        "status",
        "question",
    ]
    widths = {column: len(column) for column in columns}
    for record in records:
        for column in columns:
            widths[column] = min(
                max(widths[column], len(str(record.get(column, "")))),
                42 if column == "question" else 32,
            )

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
