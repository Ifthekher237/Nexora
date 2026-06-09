# Nexora Streamlit Interface Architecture

Phase 9 turns the existing Nexora backend into a unified local-first Streamlit
financial intelligence interface.

The frontend does not duplicate backend business logic. It calls FastAPI
endpoints from Phases 1-8 and displays real API responses, saved local histories,
citations, confidence values, limitations, and status messages.

## Organization

The Streamlit entry point is:

```text
frontend/streamlit_app.py
```

Reusable components live under:

```text
frontend/components/
```

Page modules live under:

```text
frontend/app_pages/
```

The app uses custom sidebar navigation so the interface behaves like one
cohesive dashboard.

## Components

- `api_client.py`: reusable GET/POST client, timeout handling, JSON parsing,
  backend health checks, Ollama checks, and user-friendly errors.
- `layout.py`: page headers, safety notice, empty states, backend error display,
  and global restrained styling.
- `status_cards.py`: status rows and metric cards.
- `result_cards.py`: confidence, limitations, warnings, score bars, and JSON
  expanders.
- `evidence_cards.py`: consistent source/evidence display with unknown fields
  shown as `unknown`.
- `charts.py`: simple built-in Streamlit bar charts.

## Pages

- Home: project overview, capability map, pipeline view, quick counts.
- System Status: health, system, ingestion, processing, retrieval, RAG,
  reasoning, risk, explainability, and Ollama status.
- Data Ingestion: SEC, RSS, local file, macro CSV, source list, summary, index.
- Document Processing: status, batch processing, single-document processing,
  processed index, chunks.
- Vector Search: retrieval status, index build, semantic search, vector index,
  benchmark.
- RAG Assistant: ask questions, evidence-only retrieval, sources, confidence,
  limitations, history.
- Scenario Reasoning: scenario analysis, causal chain, evidence map, confidence,
  limitations, history.
- Risk Scoring: scenario scoring, risk score, confidence, breakdown, drivers,
  evidence summary, limitations, history.
- Explainability: explain latest/specific saved outputs, expanded citations,
  evidence ranking, confidence explanation, unsupported claim warnings, history.
- AI Agent Collaboration: run full or selected local agents, inspect
  collaboration summaries, evidence, confidence, limitations, warnings, and
  saved agent run history.
- Performance & Scaling: inspect runtime resources, cache stats, cache clearing,
  real local benchmarks, benchmark history, and local-first scaling notes.
- Deployment Readiness: run enterprise-readiness checks, inspect API/security/
  governance/observability plans, generate final reports, and review the local
  runbook.
- History Explorer: unified RAG, reasoning, risk, and explainability history
  viewer.

## Backend Mapping

Each page maps directly to existing FastAPI endpoints. For example:

- Data Ingestion uses `/ingestion/*`
- Document Processing uses `/processing/*`
- Vector Search uses `/retrieval/*`
- RAG Assistant uses `/rag/*`
- Scenario Reasoning uses `/reasoning/*`
- Risk Scoring uses `/risk/*`
- Explainability uses `/explainability/*`
- AI Agent Collaboration uses `/agents/*`
- Performance & Scaling uses `/performance/*`
- Deployment Readiness uses `/deployment/*`
- History Explorer uses the saved history endpoints across those phases

## Safety and Trust

RAG, reasoning, risk, and explainability pages show the consistent safety notice:

```text
Nexora provides evidence-backed financial analysis support. It does not provide
financial advice, trading recommendations, or stock price predictions.
```

Long source text, evidence maps, JSON payloads, warnings, and limitations are
placed in tables or expanders to keep the interface readable.

## Error Handling

The frontend handles:

- backend offline
- endpoint errors
- timeout errors
- non-JSON responses
- empty histories
- missing vector indexes
- missing saved outputs
- Ollama offline
- invalid user input
- performance benchmark failures
- cache clear errors

When the backend is unavailable, the API client reports:

```text
Backend is not reachable. Please run ./scripts/run_backend.sh
```

## Known Limitations

- The interface is local-first and expects the FastAPI backend to be running.
- Output quality depends on previous pipeline stages and local source quality.
- Streamlit polish is functional and presentation-ready, but not enterprise SaaS
  design polish.
- The frontend does not add multi-user roles or cloud collaboration.
- Nexora does not provide investment advice or stock price predictions.

## Phase 11 Readiness

The interface now exposes the full local pipeline plus agent collaboration,
performance tooling, and deployment readiness planning. All 12 project phases
are available through local FastAPI and Streamlit surfaces.
