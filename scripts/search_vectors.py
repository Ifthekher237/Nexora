"""CLI entry point for semantic vector search."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.retrieval.retrieval_service import search


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the Nexora vector index.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--vector-store", default="faiss", choices=["faiss", "chroma"])
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--source-type", default=None)
    parser.add_argument("--document-type", default=None)
    parser.add_argument("--market", default=None)
    parser.add_argument("--section-hint", default=None)
    args = parser.parse_args()

    setup_logging()
    result = search(
        query=args.query,
        top_k=args.top_k,
        vector_store=args.vector_store,
        filters={
            "ticker": args.ticker,
            "source_type": args.source_type,
            "document_type": args.document_type,
            "market": args.market,
            "section_hint": args.section_hint,
        },
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
