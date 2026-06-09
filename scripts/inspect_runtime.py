"""Inspect local runtime resources for Nexora Phase 11."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.performance import optimization_manager


def main() -> int:
    print(json.dumps(optimization_manager.resources(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
