"""Small, defensive API client used by the Streamlit interface."""

from __future__ import annotations

import os
from typing import Any

import requests


BACKEND_URL = os.getenv("NEXORA_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
OLLAMA_URL = os.getenv("NEXORA_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
BACKEND_OFFLINE_MESSAGE = "Backend is not reachable. Please run ./scripts/run_backend.sh"


def clean_optional_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop empty query parameters so FastAPI receives only deliberate filters."""

    if not params:
        return None
    return {key: value for key, value in params.items() if value not in {None, ""}}


def _decode_json(response: requests.Response) -> dict[str, Any] | list[dict[str, Any]]:
    try:
        return response.json()
    except ValueError:
        return {
            "message": "Backend returned a non-JSON response.",
            "detail": response.text[:800],
            "status_code": response.status_code,
        }


def get_json(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> tuple[bool, dict[str, Any] | list[dict[str, Any]]]:
    """GET JSON from FastAPI and normalize connection and timeout errors."""

    try:
        response = requests.get(
            f"{BACKEND_URL}{path}",
            params=clean_optional_params(params),
            timeout=timeout,
        )
        payload = _decode_json(response)
        if response.status_code >= 400:
            return False, payload
        return True, payload
    except requests.Timeout as exc:
        return False, {"message": "Backend request timed out.", "detail": str(exc)}
    except requests.RequestException as exc:
        return False, {"message": BACKEND_OFFLINE_MESSAGE, "detail": str(exc)}


def post_json(
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 120.0,
) -> tuple[bool, dict[str, Any]]:
    """POST JSON to FastAPI and return a user-friendly result object."""

    try:
        response = requests.post(f"{BACKEND_URL}{path}", json=payload or {}, timeout=timeout)
        decoded = _decode_json(response)
        if response.status_code >= 400:
            return False, decoded if isinstance(decoded, dict) else {"message": "Backend request failed."}
        return True, decoded if isinstance(decoded, dict) else {"items": decoded}
    except requests.Timeout as exc:
        return False, {"message": "Backend request timed out.", "detail": str(exc)}
    except requests.RequestException as exc:
        return False, {"message": BACKEND_OFFLINE_MESSAGE, "detail": str(exc)}


def check_backend(timeout: float = 2.0) -> tuple[bool, dict[str, Any]]:
    """Return backend health without raising if the server is offline."""

    ok, payload = get_json("/health", timeout=timeout)
    return ok, payload if isinstance(payload, dict) else {"message": "Unexpected backend health payload."}


def check_ollama(timeout: float = 3.0) -> tuple[bool, dict[str, Any]]:
    """Check local Ollama directly from the frontend process."""

    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        decoded = _decode_json(response)
        if response.status_code >= 400:
            return False, decoded if isinstance(decoded, dict) else {"message": "Ollama request failed."}
        return True, decoded if isinstance(decoded, dict) else {"models": decoded}
    except requests.Timeout as exc:
        return False, {"message": "Ollama request timed out.", "detail": str(exc)}
    except requests.RequestException as exc:
        return False, {
            "message": f"Ollama is not reachable at {OLLAMA_URL}.",
            "detail": str(exc),
        }
