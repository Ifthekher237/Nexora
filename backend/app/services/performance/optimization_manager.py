"""Coordinator for Phase 11 performance status, cache, resources, and benchmarks."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import get_performance_config
from backend.app.services.performance import (
    benchmark_service,
    cache_service,
    performance_report_service,
    resource_monitor,
)


logger = logging.getLogger(__name__)


def config_status() -> dict[str, Any]:
    config = get_performance_config()
    return {
        "loaded": True,
        "performance": config.get("performance", {}),
        "cache": config.get("cache", {}),
        "benchmark": config.get("benchmark", {}),
        "resource_monitor": config.get("resource_monitor", {}),
        "streamlit": config.get("streamlit", {}),
    }


def optimization_readiness() -> dict[str, Any]:
    config = get_performance_config()
    cache = config.get("cache", {})
    performance = config.get("performance", {})
    return {
        "ready": bool(performance.get("enabled", True)),
        "local_first": bool(performance.get("local_first", True)),
        "safe_cache_invalidation": bool(cache.get("clear_on_rebuild_index", True)),
        "disk_cache_enabled": bool(cache.get("allow_disk_cache", True)),
        "benchmark_storage_enabled": performance_report_service.save_enabled(),
        "notes": [
            "Retrieval cache keys include vector index file modified time.",
            "Metadata caches refresh when index file modified time or size changes.",
            "Benchmarks record real local success/failure and do not fake Ollama availability.",
        ],
    }


def performance_status() -> dict[str, Any]:
    logger.info("Performance status requested")
    try:
        benchmark_count = performance_report_service.output_count()
    except Exception as exc:
        benchmark_count = 0
        benchmark_error = str(exc)
    else:
        benchmark_error = ""
    return {
        "status": "ready" if get_performance_config().get("performance", {}).get("enabled", True) else "disabled",
        "cache_enabled": cache_service.enabled(),
        "cache_stats": cache_service.stats(),
        "resource_usage": resource_monitor.snapshot(),
        "benchmark_count": benchmark_count,
        "benchmark_error": benchmark_error,
        "config_status": config_status(),
        "optimization_readiness": optimization_readiness(),
    }


def clear_cache(namespace: str = "all") -> dict[str, Any]:
    return cache_service.clear(namespace)


def cache_stats() -> dict[str, Any]:
    return cache_service.stats()


def resources() -> dict[str, Any]:
    return resource_monitor.snapshot()


def run_benchmark(**kwargs: Any) -> dict[str, Any]:
    return benchmark_service.run_benchmark(**kwargs)


def benchmark_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    return performance_report_service.read_history(filters)


def benchmark_report(benchmark_id: str) -> dict[str, Any] | None:
    return performance_report_service.read_report(benchmark_id)
