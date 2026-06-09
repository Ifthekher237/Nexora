"""Print the current Nexora vector metadata index."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.retrieval.retrieval_metadata_service import read_vector_metadata


def main() -> int:
    frame = read_vector_metadata()
    if frame.empty:
        print("Nexora vector index is empty.")
        return 0

    columns = [
        "vector_id",
        "chunk_id",
        "source_type",
        "ticker",
        "document_type",
        "vector_store",
        "status",
        "indexed_at",
    ]
    print(frame[columns].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
