"""Inference coordination layer for Phase 1 connectivity tests."""

from __future__ import annotations

import logging
from typing import Optional

from backend.app.schemas.inference import InferenceResponse
from backend.app.services.model_registry import validate_model
from backend.app.services.ollama_service import call_ollama_model


logger = logging.getLogger(__name__)


def run_test_inference(prompt: str, model: Optional[str] = None) -> InferenceResponse:
    """Validate the model and send a plain connectivity prompt to Ollama."""

    selected_model = validate_model(model)
    logger.info("Inference request received for model '%s'", selected_model)

    response_text = call_ollama_model(prompt=prompt, model=selected_model)

    return InferenceResponse(
        model=selected_model,
        prompt=prompt,
        response=response_text,
        runtime="ollama",
        status="success",
    )
