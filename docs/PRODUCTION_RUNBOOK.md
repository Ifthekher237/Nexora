# Nexora Production-Style Local Runbook

This runbook supports local-first operation and future team onboarding. It is not
cloud deployment automation.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## Local Model Runtime

```bash
ollama serve
ollama list
```

Pull configured local models if needed.

## Run Backend

```bash
./scripts/run_backend.sh
```

## Run Frontend

```bash
./scripts/run_frontend.sh
```

## Validate The System

```bash
python3 -m pytest
python3 scripts/inspect_runtime.py
python3 scripts/run_deployment_readiness_check.py
python3 scripts/final_system_check.py
```

## Pipeline Commands

```bash
python3 scripts/ingest_rss.py --feed-name "Yahoo Finance" --limit 5
python3 scripts/process_documents.py
python3 scripts/build_vector_index.py --store faiss --rebuild
python3 scripts/ask_rag.py --question "What financial risks could appear if interest rates rise?"
python3 scripts/run_reasoning.py --scenario "What financial risks could appear if interest rates rise?"
python3 scripts/score_risk.py --scenario "What financial risks could appear if interest rates rise?"
python3 scripts/run_agents.py
python3 scripts/run_performance_benchmark.py --queries "financial risk" --top-k 5
python3 scripts/generate_final_project_report.py
```

## Troubleshooting

- Backend port busy: stop the old uvicorn process or use another port.
- Streamlit port busy: use the alternate URL Streamlit prints.
- Ollama unavailable: run `ollama serve` or open the Ollama desktop app.
- No retrieval results: process documents and rebuild the vector index.
- Slow first request: local model, embedding, and FAISS warm-up can dominate the
  first run.

## Enterprise Notes

Before enterprise production deployment, add authentication, authorization,
secrets management, audit logging, data retention/deletion workflows, and
production observability.
