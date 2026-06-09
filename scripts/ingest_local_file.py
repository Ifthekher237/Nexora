"""CLI entry point for manually registering a local financial file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.ingestion.ingestion_manager import ingest_local_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Register a local file in Nexora.")
    parser.add_argument("--file-path", required=True)
    parser.add_argument("--source-type", default="local_uploads")
    parser.add_argument("--company-name", default="")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--market", default="")
    parser.add_argument("--document-type", required=True)
    parser.add_argument("--period", default="")
    parser.add_argument("--title", default=None)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    setup_logging()
    result = ingest_local_file(
        file_path=args.file_path,
        source_type=args.source_type,
        company_name=args.company_name,
        ticker=args.ticker,
        market=args.market,
        document_type=args.document_type,
        period=args.period,
        title=args.title,
        notes=args.notes,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
