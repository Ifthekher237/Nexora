"""CLI entry point for batch document processing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.processing.processing_manager import process_documents


def main() -> int:
    parser = argparse.ArgumentParser(description="Process ingested Nexora documents.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--source-type", default=None)
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--document-type", default=None)
    parser.add_argument("--reprocess", action="store_true")
    args = parser.parse_args()

    setup_logging()
    result = process_documents(
        limit=args.limit,
        source_type=args.source_type,
        ticker=args.ticker,
        document_type=args.document_type,
        reprocess=args.reprocess,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in {"success", "partial_success"} else 1


if __name__ == "__main__":
    sys.exit(main())
