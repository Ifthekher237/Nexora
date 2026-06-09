"""Run a selected local Nexora agent workflow."""

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
    parser = argparse.ArgumentParser(description="Run selected Nexora agents for one scenario.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--agents", nargs="*", default=None, help="Agent keys. Omit to run all enabled agents.")
    parser.add_argument("--company-name", default=None)
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--market", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--model", default=None)
    parser.add_argument("--vector-store", default="faiss", choices=["faiss", "chroma"])
    parser.add_argument("--source-type", default=None)
    parser.add_argument("--document-type", default=None)
    parser.add_argument("--section-hint", default=None)
    args = parser.parse_args()

    setup_logging()
    result = agent_orchestrator.run_workflow(
        scenario=args.scenario,
        company_name=args.company_name,
        ticker=args.ticker,
        market=args.market,
        top_k=args.top_k,
        model=args.model,
        agents=args.agents,
        vector_store=args.vector_store,
        filters={
            "source_type": args.source_type,
            "document_type": args.document_type,
            "section_hint": args.section_hint,
        },
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
