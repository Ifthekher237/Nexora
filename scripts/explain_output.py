"""Explain a saved RAG, reasoning, or risk output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.explainability import explainability_manager


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain saved Nexora outputs.")
    parser.add_argument("--target-type", required=True, choices=["risk", "reasoning", "rag"])
    parser.add_argument("--target-id", default="", help="Specific saved output ID.")
    parser.add_argument("--latest", action="store_true", help="Explain the latest saved output of the selected type.")
    args = parser.parse_args()

    try:
        if args.latest:
            report = explainability_manager.explain_latest(args.target_type)
        elif args.target_id:
            report = explainability_manager.explain_target(args.target_type, args.target_id)
        else:
            print("Provide --latest or --target-id.", file=sys.stderr)
            return 2
    except explainability_manager.ExplainabilityManagerError as exc:
        print(f"Could not explain output: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2))
    return 0 if report.get("status") in {"success", "partial_success"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
