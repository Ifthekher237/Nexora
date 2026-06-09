"""Explain one saved Phase 7 risk output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.explainability import explainability_manager


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain a saved Nexora risk output.")
    parser.add_argument("--risk-id", required=True, help="Saved risk ID, for example RISK_20260609_xxxxxx.")
    args = parser.parse_args()

    try:
        report = explainability_manager.explain_risk(args.risk_id)
    except explainability_manager.ExplainabilityManagerError as exc:
        print(f"Could not explain risk output: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2))
    return 0 if report.get("status") in {"success", "partial_success"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
