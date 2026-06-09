from backend.app.schemas.performance import BenchmarkResult
from backend.app.services.performance import benchmark_service, optimization_manager


def test_performance_manager_returns_status() -> None:
    status = optimization_manager.performance_status()

    assert status["status"] in {"ready", "disabled"}
    assert "cache_stats" in status
    assert "resource_usage" in status


def test_benchmark_service_records_retrieval_failure(monkeypatch) -> None:
    def failing_search(**kwargs):
        raise RuntimeError("retrieval unavailable")

    monkeypatch.setattr(benchmark_service.retrieval_service, "search", failing_search)
    monkeypatch.setattr(
        benchmark_service.performance_report_service,
        "save_report",
        lambda report: {"saved": False, "report_path": ""},
    )

    report = benchmark_service.run_benchmark(
        queries=["financial risk"],
        top_k=5,
        include_rag=False,
        include_reasoning=False,
        include_agents=False,
        repeat_count=1,
    )

    assert report["status"] == "partial_success"
    assert report["retrieval"]["summary"]["failure_count"] == 1
    BenchmarkResult(**report)
