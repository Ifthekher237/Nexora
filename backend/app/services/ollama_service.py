"""Small Ollama HTTP client for local model connectivity."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.app.core.config import get_settings


logger = logging.getLogger(__name__)


class OllamaServiceError(RuntimeError):
    """Raised when local Ollama cannot complete the requested operation."""


def _base_url() -> str:
    return get_settings().ollama_base_url


def check_ollama_running(timeout: float = 3.0) -> bool:
    """Return True when the local Ollama API is reachable."""

    try:
        response = httpx.get(f"{_base_url()}/api/tags", timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Ollama connection failed: %s", exc)
        return False

    logger.info("Ollama connection successful")
    return True


def list_local_models(timeout: float = 5.0) -> list[str]:
    """Return model tags currently installed in Ollama."""

    try:
        response = httpx.get(f"{_base_url()}/api/tags", timeout=timeout)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Unable to list Ollama models: %s", exc)
        return []

    return [model.get("name", "") for model in data.get("models", []) if model.get("name")]


def call_ollama_model(
    prompt: str,
    model: str,
    timeout: float = 90.0,
    options: dict[str, Any] | None = None,
) -> str:
    """Call a local Ollama model using the non-streaming generate endpoint."""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if options:
        payload["options"] = options

    try:
        response = httpx.post(
            f"{_base_url()}/api/generate",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except httpx.ConnectError as exc:
        logger.warning("Ollama is not reachable: %s", exc)
        raise OllamaServiceError(
            "Ollama is not running at http://localhost:11434. Start it with `ollama serve` "
            "or open the Ollama app, then try again."
        ) from exc
    except httpx.TimeoutException as exc:
        logger.warning("Ollama request timed out: %s", exc)
        raise OllamaServiceError(
            "The local Ollama request timed out. Confirm the model is installed and has "
            "enough local memory to run."
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning("Ollama returned an HTTP error: %s", exc)
        raise OllamaServiceError(
            f"Ollama returned HTTP {exc.response.status_code}. Check that model '{model}' "
            "is installed locally with `ollama list`."
        ) from exc
    except httpx.HTTPError as exc:
        logger.warning("Ollama request failed: %s", exc)
        raise OllamaServiceError(
            "The local Ollama request failed. Confirm Ollama is installed and running."
        ) from exc

    generated_text = data.get("response")
    if not isinstance(generated_text, str):
        raise OllamaServiceError("Ollama responded without a usable text response.")

    return generated_text.strip()
