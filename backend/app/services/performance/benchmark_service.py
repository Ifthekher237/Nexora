"""Real local benchmark runner for retrieval, RAG, reasoning, and agents."""

from __future__ import annotations

import logging
from statistics import mean
from typing import Any

from backend.app.core.config import get_performance_config
from backend.app.services.agents import agent_orchestrator
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.performance import performance_report_service, resource_monitor
from backend.app.services.performance.latency_tracker import LatencyTracker
from backend.app.services.rag import rag_manager
from backend.app.services.reasoning import reasoning_manager
from backend.app.services.retrieval import retrieval_service


logger = logging.getLogger(__name__)


def _benchmark_config() -> dict[str, Any]:
    return get_performance_config().get("benchmark", {})


def _default_queries() -> list[str]:
    return [str(item) for item in _benchmark_config().get("default_queries", ["financial risk"])]


def _default_scenarios() -> list[str]:
    return [str(item) for item in _benchmark_config().get("default_scenarios", [])]


def _summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [float(item.get("latency_ms", 0.0)) for item in items if item.get("status") == "success"]
    failures = [item for item in items if item.get("status") != "success"]
    return {
        "operation_count": len(items),
        "success_count": len(items) - len(failures),
        "failure_count": len(failures),
        "average_latency_ms": round(mean(latencies), 3) if latencies else 0.0,
        "max_latency_ms": round(max(latencies), 3) if latencies else 0.0,
    }


def _run_timed(label: str, tracker: LatencyTracker, func: Any) -> tuple[float, Any, str]:
    tracker.start(label)
    try:
        result = func()
        elapsed = tracker.stop(label)
        return elapsed, result, ""
    except Exception as exc:
        elapsed = tracker.stop(label)
        return elapsed, None, str(exc)


def _retrieval_benchmark(queries: list[str], repeat_count: int, top_k: int, vector_store: str) -> dict[str, Any]:
    tracker = LatencyTracker()
    items: list[dict[str, Any]] = []
    for query in queries:
        for repeat in range(repeat_count):
            label = f"retrieval:{query}:{repeat}"
            elapsed, result, error = _run_timed(
                label,
                tracker,
                lambda query=query: retrieval_service.search(query=query, top_k=top_k, vector_store=vector_store, filters={}),
            )
            items.append(
                {
                    "query": query,
                    "repeat": repeat + 1,
                    "latency_ms": elapsed,
                    "result_count": len(result.get("results", [])) if isinstance(result, dict) else 0,
                    "status": "success" if not error else "error",
                    "error_message": error,
                }
            )
    return {"summary": _summary(items), "items": items, "timings": tracker.as_dict()}


def _rag_benchmark(queries: list[str], repeat_count: int, top_k: int, vector_store: str) -> dict[str, Any]:
    tracker = LatencyTracker()
    items: list[dict[str, Any]] = []
    for query in queries:
        for repeat in range(repeat_count):
            label = f"rag:{query}:{repeat}"
            elapsed, result, error = _run_timed(
                label,
                tracker,
                lambda query=query: rag_manager.ask_question(query, top_k=top_k, vector_store=vector_store),
            )
            status = "error" if error else str(result.get("status", "success"))
            items.append(
                {
                    "query": query,
                    "repeat": repeat + 1,
                    "latency_ms": elapsed,
                    "source_count": len(result.get("sources", [])) if isinstance(result, dict) else 0,
                    "status": status,
                    "error_message": error or (result.get("error_message", "") if isinstance(result, dict) else ""),
                }
            )
    return {"summary": _summary(items), "items": items, "timings": tracker.as_dict()}


def _reasoning_benchmark(scenarios: list[str], repeat_count: int, top_k: int, vector_store: str) -> dict[str, Any]:
    tracker = LatencyTracker()
    items: list[dict[str, Any]] = []
    for scenario in scenarios:
        for repeat in range(repeat_count):
            label = f"reasoning:{scenario}:{repeat}"
            elapsed, result, error = _run_timed(
                label,
                tracker,
                lambda scenario=scenario: reasoning_manager.analyze_scenario(scenario, top_k=top_k, vector_store=vector_store),
            )
            status = "error" if error else str(result.get("status", "success"))
            items.append(
                {
                    "scenario": scenario,
                    "repeat": repeat + 1,
                    "latency_ms": elapsed,
                    "evidence_count": len(result.get("evidence_map", [])) if isinstance(result, dict) else 0,
                    "status": status,
                    "error_message": error or (result.get("error_message", "") if isinstance(result, dict) else ""),
                }
            )
    return {"summary": _summary(items), "items": items, "timings": tracker.as_dict()}


def _agents_benchmark(scenarios: list[str], repeat_count: int, top_k: int, vector_store: str) -> dict[str, Any]:
    tracker = LatencyTracker()
    items: list[dict[str, Any]] = []
    for scenario in scenarios:
        for repeat in range(repeat_count):
            label = f"agents:{scenario}:{repeat}"
            elapsed, result, error = _run_timed(
                label,
                tracker,
                lambda scenario=scenario: agent_orchestrator.run_workflow(
                    scenario=scenario,
                    top_k=top_k,
                    vector_store=vector_store,
                ),
            )
            status = "error" if error else str(result.get("status", "success"))
            items.append(
                {
                    "scenario": scenario,
                    "repeat": repeat + 1,
                    "latency_ms": elapsed,
                    "agents_run": result.get("agents_run", []) if isinstance(result, dict) else [],
                    "status": status,
                    "error_message": error or (result.get("error_message", "") if isinstance(result, dict) else ""),
                }
            )
    return {"summary": _summary(items), "items": items, "timings": tracker.as_dict()}


def run_benchmark(
    *,
    queries: list[str] | None = None,
    scenarios: list[str] | None = None,
    top_k: int | None = None,
    include_rag: bool = False,
    include_reasoning: bool = False,
    include_agents: bool = False,
    vector_store: str = "faiss",
    repeat_count: int | None = None,
) -> dict[str, Any]:
    selected_queries = [item.strip() for item in (queries or _default_queries()) if item and item.strip()]
    selected_scenarios = [item.strip() for item in (scenarios or _default_scenarios()) if item and item.strip()]
    selected_top_k = int(top_k or _benchmark_config().get("top_k", 5))
    selected_repeat = max(1, int(repeat_count or _benchmark_config().get("repeat_count", 1)))
    if not selected_queries:
        raise ValueError("At least one benchmark query is required.")
    if (include_reasoning or include_agents) and not selected_scenarios:
        raise ValueError("At least one scenario is required for reasoning or agent benchmarks.")

    started_at = utc_now_iso()
    report: dict[str, Any] = {
        "benchmark_id": performance_report_service.generate_benchmark_id(
            {
                "queries": selected_queries,
                "scenarios": selected_scenarios,
                "top_k": selected_top_k,
                "include_rag": include_rag,
                "include_reasoning": include_reasoning,
                "include_agents": include_agents,
            }
        ),
        "started_at": started_at,
        "completed_at": "",
        "queries": selected_queries,
        "scenarios": selected_scenarios,
        "top_k": selected_top_k,
        "vector_store": vector_store,
        "repeat_count": selected_repeat,
        "include_rag": include_rag,
        "include_reasoning": include_reasoning,
        "include_agents": include_agents,
        "resource_before": resource_monitor.snapshot(),
        "resource_after": {},
        "retrieval": {},
        "rag": {},
        "reasoning": {},
        "agents": {},
        "total_runtime_ms": 0.0,
        "status": "success",
        "error_message": "",
    }

    total_tracker = LatencyTracker()
    total_tracker.start("benchmark_total")
    logger.info("Performance benchmark started | id=%s", report["benchmark_id"])
    try:
        report["retrieval"] = _retrieval_benchmark(selected_queries, selected_repeat, selected_top_k, vector_store)
        if include_rag:
            report["rag"] = _rag_benchmark(selected_queries, selected_repeat, selected_top_k, vector_store)
        if include_reasoning:
            report["reasoning"] = _reasoning_benchmark(selected_scenarios, selected_repeat, selected_top_k, vector_store)
        if include_agents:
            report["agents"] = _agents_benchmark(selected_scenarios, selected_repeat, selected_top_k, vector_store)
    except Exception as exc:
        logger.exception("Performance benchmark failed | id=%s", report["benchmark_id"])
        report["status"] = "error"
        report["error_message"] = str(exc)
    finally:
        report["total_runtime_ms"] = total_tracker.stop("benchmark_total")
        report["completed_at"] = utc_now_iso()
        report["resource_after"] = resource_monitor.snapshot()

    section_summaries = [
        report.get("retrieval", {}).get("summary", {}),
        report.get("rag", {}).get("summary", {}) if include_rag else {},
        report.get("reasoning", {}).get("summary", {}) if include_reasoning else {},
        report.get("agents", {}).get("summary", {}) if include_agents else {},
    ]
    if report["status"] != "error" and any(int(summary.get("failure_count", 0)) > 0 for summary in section_summaries):
        report["status"] = "partial_success"

    try:
        performance_report_service.save_report(report)
        logger.info("Performance benchmark completed | id=%s | status=%s", report["benchmark_id"], report["status"])
    except performance_report_service.PerformanceReportStorageError as exc:
        report["status"] = "partial_success"
        report["error_message"] = "; ".join(item for item in [report.get("error_message", ""), str(exc)] if item)
        logger.exception("Performance benchmark report save failed | id=%s", report["benchmark_id"])
    return report
