"""Print the current Nexora processing metadata index."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.processing.processing_metadata_service import read_processing_metadata


def main() -> int:
    frame = read_processing_metadata()
    if frame.empty:
        print("Nexora processing index is empty.")
        return 0

    display_columns = [
        "processed_document_id",
        "source_document_id",
        "source_type",
        "document_type",
        "processing_status",
        "word_count",
        "chunk_count",
        "processed_at",
    ]
    print(frame[display_columns].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
