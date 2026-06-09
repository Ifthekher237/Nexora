"""Local inference connectivity endpoint."""

from __future__ import annotations

from typing import Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.schemas.inference import ErrorResponse, InferenceRequest, InferenceResponse
from backend.app.services.inference_service import run_test_inference
from backend.app.services.model_registry import ModelNotConfiguredError
from backend.app.services.ollama_service import OllamaServiceError


router = APIRouter(tags=["inference"])


@router.post(
    "/inference/test",
    response_model=InferenceResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def test_inference(request: InferenceRequest) -> Union[InferenceResponse, JSONResponse]:
    try:
        return run_test_inference(prompt=request.prompt, model=request.model)
    except ModelNotConfiguredError as exc:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(message=str(exc)).dict(),
        )
    except OllamaServiceError as exc:
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(message=str(exc)).dict(),
        )
