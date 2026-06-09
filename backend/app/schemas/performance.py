"""Pydantic schemas for Phase 11 performance optimization."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CacheClearRequest(BaseModel):
    namespace: str = "all"


class CacheStatsResponse(BaseModel):
    enabled: bool
    allow_disk_cache: bool
    cache_dir: str
    max_items: int
    namespaces: dict[str, object]


class ResourceResponse(BaseModel):
    status: str
    monitor_enabled: bool
    psutil_available: bool
    python_version: str
    platform: str
    system: str
    machine: str
    processor: str = ""
    apple_silicon_note: str
    cpu_percent: Optional[float] = None
    memory_total_mb: Optional[float] = None
    memory_available_mb: Optional[float] = None
    memory_used_percent: Optional[float] = None
    process_memory_mb: Optional[float] = None
    fallback_note: str = ""


class BenchmarkRequest(BaseModel):
    queries: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1)
    include_rag: bool = False
    include_reasoning: bool = False
    include_agents: bool = False
    vector_store: str = "faiss"
    repeat_count: int = Field(default=1, ge=1, le=10)


class BenchmarkResult(BaseModel):
    benchmark_id: str
    started_at: str
    completed_at: str
    total_runtime_ms: float
    queries: list[str]
    scenarios: list[str] = Field(default_factory=list)
    top_k: int
    vector_store: str
    repeat_count: int
    include_rag: bool
    include_reasoning: bool
    include_agents: bool
    resource_before: dict[str, object]
    resource_after: dict[str, object]
    retrieval: dict[str, object] = Field(default_factory=dict)
    rag: dict[str, object] = Field(default_factory=dict)
    reasoning: dict[str, object] = Field(default_factory=dict)
    agents: dict[str, object] = Field(default_factory=dict)
    status: str
    error_message: str = ""


class PerformanceStatus(BaseModel):
    status: str
    cache_enabled: bool
    cache_stats: dict[str, object]
    resource_usage: dict[str, object]
    benchmark_count: int
    benchmark_error: str = ""
    config_status: dict[str, object]
    optimization_readiness: dict[str, object]


class PerformanceHistoryItem(BaseModel):
    benchmark_id: str
    started_at: str
    completed_at: str
    total_runtime_ms: float
    query_count: int
    scenario_count: int
    include_rag: bool
    include_reasoning: bool
    include_agents: bool
    status: str
    report_path: str
    error_message: str = ""
