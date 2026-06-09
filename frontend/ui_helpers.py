"""Small HTTP helpers for the Streamlit interface."""

from __future__ import annotations

from typing import Any

import requests

from components import api_client


BACKEND_URL = api_client.BACKEND_URL
OLLAMA_URL = api_client.OLLAMA_URL
FINANCIAL_SAFETY_NOTICE = (
    "Nexora provides evidence-backed financial analysis support. It does not provide "
    "financial advice, trading recommendations, or stock price predictions."
)
EXPLAINABILITY_NOTICE = (
    "This layer audits saved AI outputs, checks evidence support, and does not generate investment advice."
)


def clean_optional_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop empty query parameters before sending requests to FastAPI."""

    return api_client.clean_optional_params(params)


def get_backend_json(
    path: str,
    timeout: float = 5.0,
    params: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any] | list[dict[str, Any]]]:
    """Read JSON from the FastAPI backend and normalize connection errors."""

    return api_client.get_json(path, params=params, timeout=timeout)


def post_backend_json(
    path: str,
    payload: dict[str, Any],
    timeout: float = 120.0,
) -> tuple[bool, dict[str, Any]]:
    """Post JSON to the FastAPI backend and return a consistent result."""

    return api_client.post_json(path, payload, timeout=timeout)


def check_ollama_direct(timeout: float = 5.0) -> tuple[bool, dict[str, Any]]:
    """Check local Ollama directly from the Streamlit process."""

    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as exc:
        return False, {
            "message": f"Ollama is not reachable at {OLLAMA_URL}.",
            "detail": str(exc),
        }
