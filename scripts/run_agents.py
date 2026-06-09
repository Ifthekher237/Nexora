"""Run the default local Nexora agent workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.agents import agent_orchestrator


DEFAULT_SCENARIO = "What financial risks could appear if interest rates rise?"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all enabled Nexora agents for one scenario.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--company-name", default=None)
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--market", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--model", default=None)
    parser.add_argument("--vector-store", default="faiss", choices=["faiss", "chroma"])
    args = parser.parse_args()

    setup_logging()
    result = agent_orchestrator.run_workflow(
        scenario=args.scenario,
        company_name=args.company_name,
        ticker=args.ticker,
        market=args.market,
        top_k=args.top_k,
        model=args.model,
        vector_store=args.vector_store,
    )
    print(
        json.dumps(
            {
                "status": result.get("status"),
                "agent_run_id": result.get("agent_run_id"),
                "agents_run": result.get("agents_run", []),
                "overall_confidence": result.get("overall_confidence"),
                "collaboration_summary": result.get("collaboration_summary", {}),
                "limitations": result.get("limitations", []),
                "error_message": result.get("error_message", ""),
            },
            indent=2,
        )
    )
    return 0 if result.get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
