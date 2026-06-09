"""Analyze a financial scenario with Nexora's Phase 6 reasoning engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.reasoning.reasoning_manager import analyze_scenario


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Nexora financial scenario reasoning.")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--company-name", default=None)
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--market", default=None)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--model", default=None)
    parser.add_argument("--vector-store", default="faiss", choices=["faiss", "chroma"])
    parser.add_argument("--source-type", default=None)
    parser.add_argument("--document-type", default=None)
    parser.add_argument("--section-hint", default=None)
    args = parser.parse_args()

    setup_logging()
    result = analyze_scenario(
        scenario=args.scenario,
        company_name=args.company_name,
        ticker=args.ticker,
        market=args.market,
        top_k=args.top_k,
        model=args.model,
        vector_store=args.vector_store,
        filters={
            "source_type": args.source_type,
            "document_type": args.document_type,
            "section_hint": args.section_hint,
        },
    )
    print(json.dumps(result, indent=2))
    return 1 if result.get("status") == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
