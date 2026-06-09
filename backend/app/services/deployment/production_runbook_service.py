"""Local-first production-style runbook content."""

from __future__ import annotations

from typing import Any


def production_runbook() -> dict[str, Any]:
    return {
        "status": "local_runbook_ready",
        "scope": "Local-first operating runbook and future team onboarding guide. This is not cloud deployment automation.",
        "steps": [
            {"step": "Create virtual environment", "command": "python3 -m venv .venv"},
            {"step": "Activate virtual environment", "command": "source .venv/bin/activate"},
            {"step": "Install requirements", "command": "python -m pip install -r requirements.txt"},
            {"step": "Copy environment template", "command": "cp .env.example .env"},
            {"step": "Start Ollama", "command": "ollama serve"},
            {"step": "Confirm local models", "command": "ollama list"},
            {"step": "Run backend", "command": "./scripts/run_backend.sh"},
            {"step": "Run frontend", "command": "./scripts/run_frontend.sh"},
            {"step": "Run tests", "command": "python3 -m pytest"},
            {"step": "Run ingestion", "command": "python3 scripts/ingest_rss.py --feed-name \"Yahoo Finance\" --limit 5"},
            {"step": "Process documents", "command": "python3 scripts/process_documents.py"},
            {"step": "Build vector index", "command": "python3 scripts/build_vector_index.py --store faiss --rebuild"},
            {"step": "Run RAG", "command": "python3 scripts/ask_rag.py --question \"What financial risks could appear if interest rates rise?\""},
            {"step": "Run reasoning", "command": "python3 scripts/run_reasoning.py --scenario \"What financial risks could appear if interest rates rise?\""},
            {"step": "Run risk scoring", "command": "python3 scripts/score_risk.py --scenario \"What financial risks could appear if interest rates rise?\""},
            {"step": "Run explainability", "command": "python3 scripts/explain_output.py --target-type risk --latest"},
            {"step": "Run agents", "command": "python3 scripts/run_agents.py"},
            {"step": "Run performance benchmark", "command": "python3 scripts/run_performance_benchmark.py --queries \"financial risk\" --top-k 5"},
            {"step": "Run deployment readiness", "command": "python3 scripts/run_deployment_readiness_check.py"},
        ],
        "troubleshooting": [
            {"symptom": "Backend port is busy", "action": "Stop the old uvicorn process or change the configured backend port."},
            {"symptom": "Streamlit port is busy", "action": "Use the alternate URL printed by Streamlit."},
            {"symptom": "Ollama unavailable", "action": "Open the Ollama app or run `ollama serve`, then verify `ollama list`."},
            {"symptom": "No retrieval results", "action": "Confirm documents are processed and vector index is built."},
            {"symptom": "Slow first query", "action": "Model/embedding/index warm-up can dominate first local request latency."},
        ],
        "future_enterprise_notes": [
            "Add authentication and authorization before multi-user deployment.",
            "Add secrets management and audit logging before production use.",
            "Add retention/deletion controls for sensitive company data.",
        ],
    }
