"""Print the current Nexora ingestion metadata index."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.ingestion.metadata_service import read_metadata


def main() -> int:
    frame = read_metadata()
    if frame.empty:
        print("Nexora ingestion index is empty.")
        return 0

    display_columns = [
        "document_id",
        "source_type",
        "ticker",
        "document_type",
        "title",
        "status",
        "ingested_at",
    ]
    print(frame[display_columns].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
