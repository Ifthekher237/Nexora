"""Explain one saved Phase 6 reasoning output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.explainability import explainability_manager


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain a saved Nexora reasoning output.")
    parser.add_argument("--reasoning-id", required=True, help="Saved reasoning ID, for example REASON_20260609_xxxxxx.")
    args = parser.parse_args()

    try:
        report = explainability_manager.explain_reasoning(args.reasoning_id)
    except explainability_manager.ExplainabilityManagerError as exc:
        print(f"Could not explain reasoning output: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2))
    return 0 if report.get("status") in {"success", "partial_success"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
