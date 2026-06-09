"""Performance and scaling page for Phase 11."""

from __future__ import annotations

from typing import Any

import streamlit as st

from components import api_client
from components.layout import backend_error, empty_state, page_header, render_bullets
from components.result_cards import render_json
from components.status_cards import metric_row


DEFAULT_QUERIES = ["financial risk", "interest rate risk"]
DEFAULT_SCENARIOS = ["What financial risks could appear if interest rates rise?"]


@st.cache_data(ttl=15)
def _status_payload() -> tuple[bool, dict[str, Any] | list[dict[str, Any]]]:
    return api_client.get_json("/performance/status", timeout=20)


@st.cache_data(ttl=15)
def _resource_payload() -> tuple[bool, dict[str, Any] | list[dict[str, Any]]]:
    return api_client.get_json("/performance/resources", timeout=20)


@st.cache_data(ttl=15)
def _cache_payload() -> tuple[bool, dict[str, Any] | list[dict[str, Any]]]:
    return api_client.get_json("/performance/cache/stats", timeout=20)


@st.cache_data(ttl=30)
def _history_payload(status: str = "") -> tuple[bool, dict[str, Any] | list[dict[str, Any]]]:
    return api_client.get_json("/performance/benchmark/history", params={"status": status}, timeout=20)


def _clear_cached_frontend_payloads() -> None:
    _status_payload.clear()
    _resource_payload.clear()
    _cache_payload.clear()
    _history_payload.clear()


def _render_resources(resources: dict[str, Any]) -> None:
    metric_row(
        {
            "CPU %": resources.get("cpu_percent", "unknown"),
            "Memory %": resources.get("memory_used_percent", "unknown"),
            "Process MB": resources.get("process_memory_mb", "unknown"),
            "Python": resources.get("python_version", "unknown"),
        }
    )
    st.caption(resources.get("apple_silicon_note", ""))
    if resources.get("fallback_note"):
        st.info(resources.get("fallback_note"))
    render_json("Full resource payload", resources)


def _render_cache(cache_stats: dict[str, Any]) -> None:
    namespaces = cache_stats.get("namespaces", {})
    rows = []
    if isinstance(namespaces, dict):
        for name, stats in namespaces.items():
            if isinstance(stats, dict):
                rows.append(
                    {
                        "namespace": name,
                        "memory_items": stats.get("size", 0),
                        "disk_items": stats.get("disk_items", 0),
                        "hits": stats.get("hits", 0),
                        "misses": stats.get("misses", 0),
                        "sets": stats.get("sets", 0),
                        "expired": stats.get("expired", 0),
                    }
                )
    metric_row(
        {
            "Cache": "enabled" if cache_stats.get("enabled") else "disabled",
            "Disk cache": "enabled" if cache_stats.get("allow_disk_cache") else "disabled",
            "Max items": cache_stats.get("max_items", 0),
            "Namespaces": len(rows),
        }
    )
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    render_json("Full cache payload", cache_stats)


def _run_benchmark_form() -> None:
    st.write("Benchmarks are real local measurements. Missing Ollama or empty indexes are reported honestly.")
    query_text = st.text_area("Queries, one per line", value="\n".join(DEFAULT_QUERIES), height=90)
    scenario_text = st.text_area("Scenarios, one per line", value="\n".join(DEFAULT_SCENARIOS), height=90)
    cols = st.columns(4)
    with cols[0]:
        top_k = st.number_input("Top K", min_value=1, max_value=20, value=5)
    with cols[1]:
        repeat_count = st.number_input("Repeat count", min_value=1, max_value=10, value=1)
    with cols[2]:
        vector_store = st.selectbox("Vector store", options=["faiss", "chroma"])
    with cols[3]:
        include_rag = st.checkbox("Include RAG", value=False)
    cols = st.columns(2)
    with cols[0]:
        include_reasoning = st.checkbox("Include reasoning", value=False)
    with cols[1]:
        include_agents = st.checkbox("Include agents", value=False)

    if st.button("Run benchmark", type="primary"):
        payload = {
            "queries": [line.strip() for line in query_text.splitlines() if line.strip()],
            "scenarios": [line.strip() for line in scenario_text.splitlines() if line.strip()],
            "top_k": int(top_k),
            "repeat_count": int(repeat_count),
            "vector_store": vector_store,
            "include_rag": include_rag,
            "include_reasoning": include_reasoning,
            "include_agents": include_agents,
        }
        ok, result = api_client.post_json("/performance/benchmark/run", payload, timeout=600)
        _clear_cached_frontend_payloads()
        if ok:
            st.success(f"Benchmark status: {result.get('status', 'unknown')}")
            _render_benchmark(result)
        else:
            backend_error(result)


def _render_benchmark(report: dict[str, Any]) -> None:
    metric_row(
        {
            "Benchmark": report.get("status", "unknown"),
            "Runtime ms": report.get("total_runtime_ms", 0),
            "Queries": len(report.get("queries", [])),
            "Top K": report.get("top_k", 0),
        }
    )
    for section in ["retrieval", "rag", "reasoning", "agents"]:
        payload = report.get(section)
        if not isinstance(payload, dict) or not payload:
            continue
        st.subheader(section.title())
        summary = payload.get("summary", {})
        if isinstance(summary, dict):
            metric_row(
                {
                    "Ops": summary.get("operation_count", 0),
                    "Success": summary.get("success_count", 0),
                    "Failures": summary.get("failure_count", 0),
                    "Avg ms": summary.get("average_latency_ms", 0),
                }
            )
        items = payload.get("items", [])
        if isinstance(items, list) and items:
            st.dataframe(items, use_container_width=True, hide_index=True)
    render_json("Full benchmark report", report)


def _history_tab() -> None:
    status_filter = st.selectbox("Status filter", options=["", "success", "partial_success", "error"])
    ok, payload = _history_payload(status_filter)
    if ok and isinstance(payload, list) and payload:
        st.dataframe(payload, use_container_width=True, hide_index=True)
        ids = [row.get("benchmark_id") for row in payload if row.get("benchmark_id")]
        selected = st.selectbox("Benchmark report", options=ids or [""])
        if selected and st.button("Load benchmark report"):
            detail_ok, detail = api_client.get_json(f"/performance/benchmark/history/{selected}", timeout=30)
            if detail_ok and isinstance(detail, dict):
                _render_benchmark(detail)
            else:
                backend_error(detail)
    elif ok:
        empty_state("No benchmark reports matched the current filters.", "Run a benchmark first.")
    else:
        backend_error(payload)


def render() -> None:
    page_header(
        "Performance & Scaling",
        "Monitors local runtime resources, caches, and real benchmark measurements for Nexora.",
        "Does not fake metrics, run cloud load tests, or implement cloud deployment.",
        safety=True,
    )

    status_ok, status = _status_payload()
    status_payload = status if isinstance(status, dict) else {}
    if status_ok:
        metric_row(
            {
                "Performance": status_payload.get("status", "unknown"),
                "Cache": "enabled" if status_payload.get("cache_enabled") else "disabled",
                "Benchmarks": status_payload.get("benchmark_count", 0),
                "Ready": bool((status_payload.get("optimization_readiness") or {}).get("ready")),
            }
        )
    else:
        backend_error(status)

    tabs = st.tabs(["Status", "Resources", "Cache", "Run Benchmark", "History", "Scaling Notes"])
    with tabs[0]:
        if status_ok and isinstance(status_payload, dict):
            render_json("Performance status", status_payload, expanded=True)
        else:
            backend_error(status)
    with tabs[1]:
        ok, resources = _resource_payload()
        if ok and isinstance(resources, dict):
            _render_resources(resources)
        else:
            backend_error(resources)
    with tabs[2]:
        ok, cache_stats = _cache_payload()
        if ok and isinstance(cache_stats, dict):
            _render_cache(cache_stats)
        else:
            backend_error(cache_stats)
        namespace = st.selectbox("Cache namespace", options=["all", "retrieval", "metadata", "response", "status", "benchmark"])
        if st.button("Clear cache"):
            clear_ok, clear_payload = api_client.post_json("/performance/cache/clear", {"namespace": namespace}, timeout=30)
            _clear_cached_frontend_payloads()
            if clear_ok:
                st.success(f"Cache cleared: {namespace}")
                st.json(clear_payload)
            else:
                backend_error(clear_payload)
    with tabs[3]:
        _run_benchmark_form()
    with tabs[4]:
        _history_tab()
    with tabs[5]:
        render_bullets(
            [
                "Benchmarks are local measurements on this machine and data volume.",
                "Ollama/model latency depends on selected model size and whether the model is already loaded.",
                "Retrieval cache is invalidated by vector index modified time and cache TTL.",
                "Metadata cache is invalidated by index file modified time, file size, and cache TTL.",
                "Phase 11 does not add cloud scaling, Docker, Kubernetes, or paid APIs.",
                "Phase 12 can build deployment architecture using these local observability foundations.",
            ]
        )
