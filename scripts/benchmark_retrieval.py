"""Run simple retrieval benchmark queries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.retrieval.retrieval_benchmark_service import run_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run retrieval benchmark queries.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--vector-store", default="faiss", choices=["faiss", "chroma"])
    parser.add_argument("queries", nargs="*")
    args = parser.parse_args()

    setup_logging()
    result = run_benchmark(queries=args.queries, top_k=args.top_k, vector_store=args.vector_store)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
