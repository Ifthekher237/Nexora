# Nexora Performance Optimization Architecture

Phase 11 adds a local-first performance and scaling layer for Nexora. It focuses
on practical speed, stability, cache visibility, resource monitoring, benchmark
readiness, and Streamlit responsiveness without adding cloud infrastructure or
heavy observability tooling.

## Components

- `configs/performance_config.yaml`: enables performance services, TTLs, cache
  limits, benchmark defaults, output paths, and Streamlit cache hints.
- `backend/app/api/routes_performance.py`: FastAPI endpoints for status,
  resources, cache stats/clear, benchmark execution, and benchmark history.
- `backend/app/schemas/performance.py`: Pydantic request/response contracts.
- `backend/app/services/performance/cache_service.py`: namespace-aware in-memory
  TTL cache with optional disk backing, JSON-safe serialization, max item limit,
  cache keys, and hit/miss counters.
- `backend/app/services/performance/metadata_cache_service.py`: mtime-aware
  cache wrappers for ingestion, processing, vector, RAG, reasoning, risk,
  explainability, and agent history/index reads.
- `backend/app/services/performance/response_cache_service.py`: safe cache
  helpers for retrieval results, status payloads, and history tables.
- `backend/app/services/performance/latency_tracker.py`: elapsed-time
  measurement helper used by benchmark runs.
- `backend/app/services/performance/resource_monitor.py`: local CPU, memory,
  process memory, Python, platform, and Apple Silicon notes with psutil fallback.
- `backend/app/services/performance/benchmark_service.py`: real local benchmark
  runner for retrieval, optional RAG, optional reasoning, and optional agents.
- `backend/app/services/performance/performance_report_service.py`: persistent
  benchmark JSON reports and CSV/JSON history indexes.
- `backend/app/services/performance/optimization_manager.py`: coordinator for
  status, cache, resource, benchmark, and readiness summaries.
- `frontend/app_pages/performance_page.py`: Streamlit page for status,
  resources, cache operations, benchmark runner, history, and scaling notes.

## Cache Strategy

The cache is intentionally small and understandable:

- Namespaces: `retrieval`, `metadata`, `response`, `status`, `benchmark`.
- In-memory entries store JSON-safe values, creation time, and expiry time.
- Optional disk cache stores the same JSON-safe entry format under
  `data/performance_outputs/cache/`.
- Cache keys are SHA-256 hashes of normalized payloads.
- Max item limit is enforced per namespace by removing oldest entries.
- Hit, miss, set, delete, expiry, disk hit, and disk error counters are reported.

## Invalidation Rules

- TTL expiry removes stale entries.
- Manual invalidation is available through `/performance/cache/clear` and
  `scripts/clear_cache.py`.
- Retrieval cache keys include the vector metadata index path, modified time, and
  file size, so vector index rebuilds naturally produce new cache keys.
- Metadata cache keys include each index file path, modified time, and file size.
- Corrupt disk cache files are removed and counted as disk errors.

## Benchmark Methodology

Benchmarks are real local measurements:

- Retrieval benchmarks call the existing Phase 4 retrieval service.
- RAG benchmarks call the existing Phase 5 RAG manager when enabled.
- Reasoning benchmarks call the existing Phase 6 reasoning manager when enabled.
- Agent benchmarks call the existing Phase 10 agent orchestrator when enabled.
- Each operation records latency, success/failure, result counts, and error
  messages.
- Resource snapshots are captured before and after each benchmark.
- If Ollama is unavailable, RAG/reasoning failures are recorded honestly.

Saved benchmark reports live under:

```text
data/performance_outputs/benchmark_runs/
```

Indexes live at:

```text
data/performance_outputs/performance_index.csv
data/performance_outputs/performance_index.json
```

## Streamlit Responsiveness

The Performance & Scaling page uses short-lived Streamlit cache wrappers for
status, resource, cache, and history calls. This reduces repeated backend calls
while still refreshing quickly enough for local operation.

## Local-First Scaling Notes

Phase 11 prepares Nexora for larger local workloads by improving observability
and avoiding repeated work where safe. It does not add cloud deployment, Docker,
Kubernetes, distributed tracing, paid APIs, or enterprise load testing.

Performance still depends on:

- Mac hardware and memory
- selected Ollama model size
- vector index size
- document volume
- whether local models and embedding models are already warm

## Phase 12 Readiness

The performance layer gives Phase 12 a concrete base for Enterprise Deployment
Architecture: health signals, cache controls, runtime inspection, benchmark
history, and local scaling evidence.
