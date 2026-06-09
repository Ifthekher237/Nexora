"""CLI entry point for SEC filing metadata ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.ingestion.ingestion_manager import ingest_sec_company


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest SEC filing metadata.")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--company-name", default="")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    setup_logging()
    result = ingest_sec_company(
        ticker=args.ticker,
        company_name=args.company_name,
        limit=args.limit,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
