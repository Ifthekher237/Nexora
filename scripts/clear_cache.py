"""Clear Nexora runtime cache namespaces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.performance import optimization_manager


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear Nexora Phase 11 runtime cache.")
    parser.add_argument("--namespace", default="all", choices=["all", "retrieval", "metadata", "response", "status", "benchmark"])
    args = parser.parse_args()
    print(json.dumps(optimization_manager.clear_cache(args.namespace), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
