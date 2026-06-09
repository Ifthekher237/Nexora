"""Configuration loading for the local-first Nexora backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "configs"
APP_CONFIG_PATH = CONFIG_DIR / "app_config.yaml"
MODEL_CONFIG_PATH = CONFIG_DIR / "model_config.yaml"
INGESTION_CONFIG_PATH = CONFIG_DIR / "ingestion_sources.yaml"
PROCESSING_CONFIG_PATH = CONFIG_DIR / "processing_config.yaml"
RETRIEVAL_CONFIG_PATH = CONFIG_DIR / "retrieval_config.yaml"
RAG_CONFIG_PATH = CONFIG_DIR / "rag_config.yaml"
REASONING_CONFIG_PATH = CONFIG_DIR / "reasoning_config.yaml"
RISK_CONFIG_PATH = CONFIG_DIR / "risk_config.yaml"
EXPLAINABILITY_CONFIG_PATH = CONFIG_DIR / "explainability_config.yaml"
AGENTS_CONFIG_PATH = CONFIG_DIR / "agents_config.yaml"
PERFORMANCE_CONFIG_PATH = CONFIG_DIR / "performance_config.yaml"
DEPLOYMENT_CONFIG_PATH = CONFIG_DIR / "deployment_config.yaml"
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    """Runtime settings used by the API, scripts, and services."""

    app_name: str
    environment: str
    local_first: bool
    debug: bool
    backend_host: str
    backend_port: int
    frontend_port: int
    log_level: str
    log_to_file: bool
    ollama_base_url: str


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required config file was not found: {path}")

    with path.open("r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a YAML object: {path}")

    return data


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_app_config() -> dict[str, Any]:
    """Load the app-level YAML configuration."""

    return _load_yaml_file(APP_CONFIG_PATH)


@lru_cache
def get_model_config() -> dict[str, Any]:
    """Load the model runtime YAML configuration."""

    return _load_yaml_file(MODEL_CONFIG_PATH)


@lru_cache
def get_ingestion_config() -> dict[str, Any]:
    """Load source configuration for the ingestion engine."""

    return _load_yaml_file(INGESTION_CONFIG_PATH)


@lru_cache
def get_processing_config() -> dict[str, Any]:
    """Load document processing configuration."""

    return _load_yaml_file(PROCESSING_CONFIG_PATH)


@lru_cache
def get_retrieval_config() -> dict[str, Any]:
    """Load vector retrieval configuration."""

    return _load_yaml_file(RETRIEVAL_CONFIG_PATH)


@lru_cache
def get_rag_config() -> dict[str, Any]:
    """Load retrieval-augmented generation configuration."""

    return _load_yaml_file(RAG_CONFIG_PATH)


@lru_cache
def get_reasoning_config() -> dict[str, Any]:
    """Load financial reasoning engine configuration."""

    return _load_yaml_file(REASONING_CONFIG_PATH)


@lru_cache
def get_risk_config() -> dict[str, Any]:
    """Load risk scoring engine configuration."""

    return _load_yaml_file(RISK_CONFIG_PATH)


@lru_cache
def get_explainability_config() -> dict[str, Any]:
    """Load explainability and evidence audit configuration."""

    return _load_yaml_file(EXPLAINABILITY_CONFIG_PATH)


@lru_cache
def get_agents_config() -> dict[str, Any]:
    """Load AI agent collaboration configuration."""

    return _load_yaml_file(AGENTS_CONFIG_PATH)


@lru_cache
def get_performance_config() -> dict[str, Any]:
    """Load performance optimization configuration."""

    return _load_yaml_file(PERFORMANCE_CONFIG_PATH)


@lru_cache
def get_deployment_config() -> dict[str, Any]:
    """Load enterprise deployment planning configuration."""

    return _load_yaml_file(DEPLOYMENT_CONFIG_PATH)


@lru_cache
def get_settings() -> Settings:
    """Build final settings from YAML with small, local `.env` overrides."""

    config = get_app_config()
    app_config = config.get("app", {})
    backend_config = config.get("backend", {})
    frontend_config = config.get("frontend", {})
    logging_config = config.get("logging", {})

    return Settings(
        app_name=os.getenv("NEXORA_APP_NAME", app_config.get("name", "Nexora")),
        environment=os.getenv(
            "NEXORA_ENVIRONMENT", app_config.get("environment", "local")
        ),
        local_first=_env_bool(
            "NEXORA_LOCAL_FIRST", bool(app_config.get("local_first", True))
        ),
        debug=_env_bool("NEXORA_DEBUG", bool(app_config.get("debug", True))),
        backend_host=os.getenv(
            "NEXORA_BACKEND_HOST", backend_config.get("host", "127.0.0.1")
        ),
        backend_port=int(
            os.getenv("NEXORA_BACKEND_PORT", backend_config.get("port", 8000))
        ),
        frontend_port=int(
            os.getenv("NEXORA_FRONTEND_PORT", frontend_config.get("port", 8501))
        ),
        log_level=os.getenv(
            "NEXORA_LOG_LEVEL", logging_config.get("level", "INFO")
        ).upper(),
        log_to_file=_env_bool(
            "NEXORA_LOG_TO_FILE", bool(logging_config.get("log_to_file", True))
        ),
        ollama_base_url=os.getenv(
            "NEXORA_OLLAMA_BASE_URL", "http://localhost:11434"
        ).rstrip("/"),
    )
