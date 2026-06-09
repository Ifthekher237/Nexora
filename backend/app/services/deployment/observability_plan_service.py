"""Observability and monitoring plan for future enterprise deployment."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.services.performance import cache_service, performance_report_service


logger = logging.getLogger(__name__)


def observability_plan() -> dict[str, Any]:
    logger.info("Deployment observability plan requested")
    try:
        benchmark_count = performance_report_service.output_count()
    except Exception:
        benchmark_count = 0
    return {
        "status": "planning_ready",
        "current_observability": {
            "application_logs": "logs/nexora.log plus console logging through existing logging_config.",
            "performance_benchmarks": f"{benchmark_count} saved benchmark report(s).",
            "cache_stats": cache_service.stats(),
            "status_endpoints": [
                "/health",
                "/ingestion/status",
                "/processing/status",
                "/retrieval/status",
                "/rag/status",
                "/reasoning/status",
                "/risk/status",
                "/explainability/status",
                "/agents/status",
                "/performance/status",
                "/deployment/status",
            ],
            "saved_histories": [
                "RAG, reasoning, risk, explainability, agents, performance, and deployment outputs have local history indexes.",
            ],
        },
        "future_observability": [
            "Structured JSON logs with route, request ID, output ID, latency, and status.",
            "Centralized error tracking in future enterprise deployment.",
            "Model availability and model latency monitoring.",
            "Retrieval quality monitoring using benchmark query sets.",
            "Ingestion freshness, processing failures, and vector-index health dashboards.",
            "Audit trails for user actions and generated outputs.",
        ],
        "dashboard_metrics": [
            "Backend uptime and error rate.",
            "P50/P95 route latency.",
            "Cache hit/miss ratios.",
            "Vector index size and latest indexing time.",
            "Ollama/model availability.",
            "Saved output counts by phase and status.",
        ],
        "limitations": [
            "No enterprise log aggregation is implemented in Phase 12.",
            "No production alerting or incident management integration exists yet.",
        ],
    }
