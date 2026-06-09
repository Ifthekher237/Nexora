"""Model configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.model import DefaultModelResponse, ModelListResponse
from backend.app.services.model_registry import (
    get_available_models,
    get_default_model,
    get_model_by_name,
    get_primary_runtime,
)


router = APIRouter(tags=["models"])


@router.get("/models/available", response_model=ModelListResponse)
def available_models() -> ModelListResponse:
    default_model = get_default_model()
    return ModelListResponse(
        default=default_model,
        runtime=get_primary_runtime(),
        models=get_available_models(),
    )


@router.get("/models/default", response_model=DefaultModelResponse)
def default_model() -> DefaultModelResponse:
    default_name = get_default_model()
    return DefaultModelResponse(
        default=default_name,
        model=get_model_by_name(default_name),
    )
