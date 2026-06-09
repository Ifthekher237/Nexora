# Phase 11 Summary: Performance Optimization & Scaling

Phase 11 adds a serious local-first performance layer for Nexora. It improves
runtime visibility, cache control, benchmarkability, and Streamlit responsiveness
without changing the Phase 1-10 architecture or adding cloud tooling.

## Implemented

- Performance configuration in `configs/performance_config.yaml`.
- Runtime cache service with namespaces, TTL expiry, optional disk cache, max
  item limit, JSON-safe values, cache key hashing, and hit/miss counters.
- Retrieval result caching inside the existing retrieval service.
- Metadata and response cache wrapper services.
- Latency tracker for local benchmark timings.
- Resource monitor with psutil support and graceful fallback.
- Benchmark service for retrieval, optional RAG, optional reasoning, and optional
  agent workflows.
- Benchmark report storage under `data/performance_outputs/`.
- FastAPI `/performance/*` endpoints.
- Streamlit `Performance & Scaling` page.
- CLI scripts for runtime inspection, cache clearing, benchmarks, benchmark
  history, and smoke testing.
- Tests for cache behavior, latency tracking, resource fallback, manager status,
  and benchmark failure handling.

## API Endpoints

- `GET /performance/status`
- `GET /performance/resources`
- `GET /performance/cache/stats`
- `POST /performance/cache/clear`
- `POST /performance/benchmark/run`
- `GET /performance/benchmark/history`
- `GET /performance/benchmark/history/{benchmark_id}`

## How To Inspect Runtime

```bash
python3 scripts/inspect_runtime.py
```

## How To Run A Benchmark

```bash
python3 scripts/run_performance_benchmark.py \
  --queries "financial risk" "interest rate risk" \
  --top-k 5 \
  --include-rag
```

For a safer retrieval-only smoke test:

```bash
python3 scripts/test_performance_pipeline.py
```

## How To Clear Cache

```bash
python3 scripts/clear_cache.py --namespace all
python3 scripts/clear_cache.py --namespace retrieval
```

## How To View Benchmark History

```bash
python3 scripts/show_performance_history.py
```

## Benchmark Storage

Saved benchmark reports are stored under:

```text
data/performance_outputs/benchmark_runs/
```

History indexes are stored at:

```text
data/performance_outputs/performance_index.csv
data/performance_outputs/performance_index.json
```

## Known Limitations

- Benchmarks are local measurements, not enterprise load tests.
- Local performance depends on Mac hardware, memory, model size, and data volume.
- Ollama/model latency depends on selected model and warm/cold runtime state.
- Retrieval cache does not guarantee faster results for every query.
- Async and streaming remain limited because Phase 11 avoids risky rewrites.
- No cloud scaling, Docker, Kubernetes, paid APIs, or OpenAI API were added.

## Ready For Phase 12

Phase 11 prepares Nexora for Enterprise Deployment Architecture by adding
performance status, resource snapshots, benchmark evidence, cache invalidation,
history storage, and a dashboard surface for local operational readiness.
