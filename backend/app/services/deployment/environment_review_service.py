"""Local environment review for enterprise deployment planning."""

from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_deployment_config
from backend.app.services.ollama_service import check_ollama_running, list_local_models


REQUIRED_CONFIGS = [
    "app_config.yaml",
    "model_config.yaml",
    "ingestion_sources.yaml",
    "processing_config.yaml",
    "retrieval_config.yaml",
    "rag_config.yaml",
    "reasoning_config.yaml",
    "risk_config.yaml",
    "explainability_config.yaml",
    "agents_config.yaml",
    "performance_config.yaml",
    "deployment_config.yaml",
]

REQUIRED_DIRECTORIES = [
    "backend/app",
    "frontend/app_pages",
    "configs",
    "scripts",
    "docs",
    "data/raw",
    "data/processed",
    "data/vector_store",
    "data/deployment_outputs/reports",
]

IMPORTANT_SCRIPTS = [
    "scripts/run_backend.sh",
    "scripts/run_frontend.sh",
    "scripts/test_performance_pipeline.py",
    "scripts/run_agents.py",
]

IMPORTANT_DOCS = [
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/PERFORMANCE_OPTIMIZATION_ARCHITECTURE.md",
    "docs/AGENT_COLLABORATION_ARCHITECTURE.md",
]


def _exists(path: str) -> bool:
    return (PROJECT_ROOT / path).exists()


def review_environment(check_ollama: bool = True) -> dict[str, Any]:
    config = get_deployment_config()
    env_config = config.get("environment", {})
    python_version = sys.version.split()[0]
    required_python = str(env_config.get("required_python_version", "3.11"))
    ollama_running = False
    installed_models: list[str] = []
    ollama_note = "Ollama check skipped."
    if check_ollama:
        ollama_running = check_ollama_running(timeout=1.0)
        installed_models = list_local_models(timeout=1.0) if ollama_running else []
        ollama_note = (
            "Ollama is reachable."
            if ollama_running
            else "Ollama is not reachable. This is a warning for enterprise readiness, not a local project failure."
        )

    config_files = [{"path": f"configs/{name}", "exists": _exists(f"configs/{name}")} for name in REQUIRED_CONFIGS]
    directories = [{"path": item, "exists": _exists(item)} for item in REQUIRED_DIRECTORIES]
    scripts = [{"path": item, "exists": _exists(item)} for item in IMPORTANT_SCRIPTS]
    docs = [{"path": item, "exists": _exists(item)} for item in IMPORTANT_DOCS]
    return {
        "python_version": python_version,
        "required_python_version": required_python,
        "python_version_ok": python_version.startswith(required_python),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "backend": env_config.get("required_backend", "FastAPI"),
        "frontend": env_config.get("required_frontend", "Streamlit"),
        "llm_runtime": env_config.get("required_llm_runtime", "Ollama"),
        "required_vector_store": env_config.get("required_vector_store", "FAISS"),
        "optional_vector_store": env_config.get("optional_vector_store", "ChromaDB"),
        "config_files": config_files,
        "required_directories": directories,
        "important_scripts": scripts,
        "important_docs": docs,
        "ollama_running": ollama_running,
        "installed_models": installed_models,
        "ollama_note": ollama_note,
        "local_model_runtime_note": "Nexora remains local-first. Enterprise deployment would need explicit model-runtime operations planning.",
    }
