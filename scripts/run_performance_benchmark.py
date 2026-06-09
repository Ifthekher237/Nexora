"""Run a real local Nexora Phase 11 performance benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging_config import setup_logging
from backend.app.services.performance import optimization_manager


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Nexora local performance benchmark.")
    parser.add_argument("--queries", nargs="*", default=None)
    parser.add_argument("--scenarios", nargs="*", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--repeat-count", type=int, default=1)
    parser.add_argument("--vector-store", default="faiss", choices=["faiss", "chroma"])
    parser.add_argument("--include-rag", action="store_true")
    parser.add_argument("--include-reasoning", action="store_true")
    parser.add_argument("--include-agents", action="store_true")
    args = parser.parse_args()

    setup_logging()
    report = optimization_manager.run_benchmark(
        queries=args.queries,
        scenarios=args.scenarios,
        top_k=args.top_k,
        repeat_count=args.repeat_count,
        vector_store=args.vector_store,
        include_rag=args.include_rag,
        include_reasoning=args.include_reasoning,
        include_agents=args.include_agents,
    )
    print(
        json.dumps(
            {
                "benchmark_id": report.get("benchmark_id"),
                "status": report.get("status"),
                "total_runtime_ms": report.get("total_runtime_ms"),
                "retrieval": (report.get("retrieval") or {}).get("summary", {}),
                "rag": (report.get("rag") or {}).get("summary", {}),
                "reasoning": (report.get("reasoning") or {}).get("summary", {}),
                "agents": (report.get("agents") or {}).get("summary", {}),
                "error_message": report.get("error_message", ""),
            },
            indent=2,
        )
    )
    return 0 if report.get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
