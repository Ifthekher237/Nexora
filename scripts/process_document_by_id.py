"""CLI entry point for processing one ingestion document ID."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.processing.processing_manager import process_document_by_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Process one Nexora document by source ID.")
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--reprocess", action="store_true")
    args = parser.parse_args()

    setup_logging()
    result = process_document_by_id(args.document_id, reprocess=args.reprocess)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in {"success", "skipped"} else 1


if __name__ == "__main__":
    sys.exit(main())
