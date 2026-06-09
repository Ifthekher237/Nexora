"""Model registry backed by `configs/model_config.yaml`."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Optional

from backend.app.core.config import get_model_config


logger = logging.getLogger(__name__)


class ModelNotConfiguredError(ValueError):
    """Raised when a request references a model outside the local registry."""


@lru_cache
def _registry() -> dict[str, Any]:
    config = get_model_config()
    models_config = config.get("models", {})
    available = models_config.get("available", [])

    if not available:
        raise ValueError("No models are configured in configs/model_config.yaml")

    logger.info("Model registry loaded with %s configured models", len(available))
    return config


def get_primary_runtime() -> str:
    return _registry().get("llm_runtime", {}).get("primary", "ollama")


def get_available_models() -> list[dict[str, Any]]:
    return list(_registry().get("models", {}).get("available", []))


def get_default_model() -> str:
    default_model = _registry().get("models", {}).get("default")
    if not default_model:
        raise ValueError("Default model is missing from configs/model_config.yaml")

    validate_model(default_model)
    return str(default_model)


def get_model_by_name(model_name: str) -> dict[str, Any]:
    for model in get_available_models():
        if model.get("name") == model_name:
            return dict(model)

    configured = ", ".join(model["name"] for model in get_available_models())
    raise ModelNotConfiguredError(
        f"Model '{model_name}' is not configured. Available models: {configured}"
    )


def validate_model(model_name: Optional[str]) -> str:
    selected_model = model_name or _registry().get("models", {}).get("default")
    if not selected_model:
        raise ModelNotConfiguredError("No model was provided and no default is configured.")

    get_model_by_name(str(selected_model))
    return str(selected_model)
