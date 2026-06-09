"""Display saved explainability report history."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.explainability import explainability_output_service


def _short(value: object, width: int = 34) -> str:
    text = str(value or "")
    return text if len(text) <= width else f"{text[: width - 3]}..."


def main() -> int:
    parser = argparse.ArgumentParser(description="Show saved Nexora explainability reports.")
    parser.add_argument("--target-type", choices=["risk", "reasoning", "rag"], default=None)
    parser.add_argument("--status", default=None)
    parser.add_argument("--coverage-level", choices=["low", "medium", "high"], default=None)
    args = parser.parse_args()

    try:
        records = explainability_output_service.read_history(
            {
                "target_type": args.target_type,
                "status": args.status,
                "coverage_level": args.coverage_level,
            }
        )
    except explainability_output_service.ExplainabilityOutputStorageError as exc:
        print(f"Could not read explainability history: {exc}")
        return 1

    if not records:
        print("No saved explainability reports found.")
        return 0

    columns = [
        ("explainability_id", 36),
        ("created_at", 25),
        ("target_type", 12),
        ("target_id", 34),
        ("coverage_level", 15),
        ("coverage_score", 15),
        ("explainability_score", 22),
        ("status", 12),
    ]
    header = "  ".join(name.ljust(width) for name, width in columns)
    print(header)
    print("-" * len(header))
    for record in records:
        print(
            "  ".join(
                _short(record.get(name), width).ljust(width)
                for name, width in columns
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
