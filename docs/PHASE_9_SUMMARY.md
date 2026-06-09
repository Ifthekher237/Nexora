# Phase 9 Summary: Streamlit Financial Intelligence Interface

Phase 9 refactors Nexora's Streamlit frontend into a serious operational
financial intelligence interface.

## Implemented

- Sidebar navigation across the full pipeline.
- Professional page headers with clear scope and non-scope.
- Shared API client with backend availability checks, timeout handling, and
  user-friendly errors.
- Shared rendering components for status cards, evidence, confidence,
  limitations, score bars, and charts.
- Home page with pipeline overview and quick counts.
- System status page across Phase 1-8 services.
- Data ingestion page for SEC, RSS, local file, macro CSV, summary, and index.
- Document processing page for batch/single processing and chunks.
- Vector search page for index building, search, metadata, and benchmark.
- RAG assistant page with answers, evidence-only retrieval, sources, history,
  confidence, and limitations.
- Scenario reasoning page with direct answer, causal chain, exposure analysis,
  evidence map, history, confidence, and limitations.
- Risk scoring page with overall risk score, confidence, score breakdown, risk
  drivers, evidence summary, history, and limitations.
- Explainability page with latest/specific explanation, citations, evidence
  ranking, reasoning trace, document attribution, unsupported claims, and history.
- Unified history explorer for RAG, reasoning, risk, and explainability outputs.
- Lightweight endpoint contract test for frontend-connected API routes.

## How To Run

Start the backend:

```bash
./scripts/run_backend.sh
```

Start the frontend:

```bash
./scripts/run_frontend.sh
```

Open the Streamlit URL shown in the terminal. The default configured frontend
port is usually `8501`; if that port is busy Streamlit may use another port such
as `8502`.

## How To Use

1. Start the backend and frontend.
2. Open the Home page and confirm quick counts load.
3. Check System Status for backend, retrieval, RAG, reasoning, risk, and
   explainability availability.
4. Use Data Ingestion and Document Processing to prepare local documents.
5. Build/search the vector index.
6. Ask RAG questions from retrieved evidence.
7. Run scenario reasoning.
8. Generate risk scores.
9. Explain saved outputs and inspect history.

## Verification

Run:

```bash
python3 -m pytest
python3 -c "from backend.app.main import app; print(app.title)"
./scripts/run_frontend.sh
```

Manual checks should include:

- Home page
- System Status page
- RAG Assistant page
- Scenario Reasoning page
- Risk Scoring page
- Explainability page
- History Explorer page

## Known Limitations

- Streamlit is local-first and depends on the FastAPI backend.
- Dashboard polish is functional and presentable, not enterprise SaaS-level.
- Output quality depends on ingestion, processing, retrieval, local LLM, and saved
  output quality.
- The frontend does not invent missing data or fake visualizations.
- Nexora does not provide investment advice.
- Nexora does not predict stock prices.
- Multi-agent collaboration is not implemented yet.

## Ready For Phase 10

The interface now provides a single operational workspace across the full Nexora
pipeline. Phase 10 can add an AI Agent Collaboration System that coordinates
specialized agents across ingestion, retrieval, reasoning, risk, and
explainability workflows.
