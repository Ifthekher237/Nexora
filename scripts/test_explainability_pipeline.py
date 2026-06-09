"""Run a small Phase 8 smoke test using the latest saved risk output if available."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.explainability import explainability_manager


def main() -> int:
    try:
        report = explainability_manager.explain_latest("risk")
    except explainability_manager.ExplainabilityManagerError as exc:
        print(
            "Explainability smoke test needs at least one saved risk output. "
            f"Generate one with scripts/score_risk.py first. Detail: {exc}",
            file=sys.stderr,
        )
        return 1

    summary = {
        "status": report.get("status"),
        "explainability_id": report.get("explainability_id"),
        "target_type": report.get("target_type"),
        "target_id": report.get("target_id"),
        "explainability_score": report.get("explainability_score"),
        "coverage": report.get("evidence_coverage"),
        "citations": len(report.get("expanded_citations") or []),
        "unsupported_claims": len(report.get("unsupported_claims") or []),
        "validation_warnings": report.get("validation_warnings", []),
    }
    print(json.dumps(summary, indent=2))
    return 0 if report.get("status") in {"success", "partial_success"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
