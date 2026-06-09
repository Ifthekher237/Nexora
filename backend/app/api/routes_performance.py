"""API routes for Nexora Phase 11 performance optimization."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.performance import (
    BenchmarkRequest,
    BenchmarkResult,
    CacheClearRequest,
    CacheStatsResponse,
    PerformanceHistoryItem,
    PerformanceStatus,
    ResourceResponse,
)
from backend.app.services.performance import cache_service, optimization_manager, performance_report_service


router = APIRouter(tags=["performance"])


@router.get("/performance/status", response_model=PerformanceStatus)
def get_performance_status() -> dict[str, object]:
    return optimization_manager.performance_status()


@router.get("/performance/resources", response_model=ResourceResponse)
def get_resources() -> dict[str, object]:
    return optimization_manager.resources()


@router.get("/performance/cache/stats", response_model=CacheStatsResponse)
def get_cache_stats() -> dict[str, object]:
    return optimization_manager.cache_stats()


@router.post("/performance/cache/clear")
def post_clear_cache(request: CacheClearRequest) -> dict[str, object]:
    try:
        return optimization_manager.clear_cache(request.namespace)
    except cache_service.CacheServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/performance/benchmark/run", response_model=BenchmarkResult)
def post_run_benchmark(request: BenchmarkRequest) -> dict[str, object]:
    try:
        return optimization_manager.run_benchmark(
            queries=request.queries or None,
            scenarios=request.scenarios or None,
            top_k=request.top_k,
            include_rag=request.include_rag,
            include_reasoning=request.include_reasoning,
            include_agents=request.include_agents,
            vector_store=request.vector_store,
            repeat_count=request.repeat_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/performance/benchmark/history", response_model=list[PerformanceHistoryItem])
def get_benchmark_history(status: Optional[str] = Query(default=None)) -> list[dict[str, object]]:
    try:
        return optimization_manager.benchmark_history({"status": status})
    except performance_report_service.PerformanceReportStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/performance/benchmark/history/{benchmark_id}", response_model=BenchmarkResult)
def get_benchmark_report(benchmark_id: str) -> dict[str, object]:
    try:
        report = optimization_manager.benchmark_report(benchmark_id)
    except performance_report_service.PerformanceReportStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if report is None:
        raise HTTPException(status_code=404, detail=f"Benchmark report not found: {benchmark_id}")
    return report
