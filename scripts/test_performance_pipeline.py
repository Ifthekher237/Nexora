"""Run a safe local Phase 11 performance smoke test."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.performance import optimization_manager


def main() -> int:
    setup_logging()
    status = optimization_manager.performance_status()
    report = optimization_manager.run_benchmark(
        queries=["financial risk"],
        top_k=5,
        include_rag=False,
        include_reasoning=False,
        include_agents=False,
        repeat_count=1,
    )
    print(
        json.dumps(
            {
                "performance_status": status.get("status"),
                "cache_enabled": status.get("cache_enabled"),
                "benchmark_id": report.get("benchmark_id"),
                "benchmark_status": report.get("status"),
                "retrieval_summary": (report.get("retrieval") or {}).get("summary", {}),
                "error_message": report.get("error_message", ""),
            },
            indent=2,
        )
    )
    return 0 if report.get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
