"""CLI entry point for public RSS feed ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.ingestion.ingestion_manager import ingest_rss


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a configured RSS feed.")
    parser.add_argument("--feed-name", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    setup_logging()
    result = ingest_rss(feed_name=args.feed_name, limit=args.limit)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
