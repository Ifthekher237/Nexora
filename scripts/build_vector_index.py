"""CLI entry point for building the Nexora vector index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.retrieval.vector_store_manager import build_vector_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local vector index from processed chunks.")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--vector-store", default="faiss", choices=["faiss", "chroma"])
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    setup_logging()
    result = build_vector_index(args.limit, args.vector_store, rebuild=args.rebuild)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in {"success", "partial_success"} else 1


if __name__ == "__main__":
    sys.exit(main())
