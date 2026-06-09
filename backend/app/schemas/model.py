"""Schemas for model configuration responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    label: str
    purpose: str
    recommended_for: str
    quantized: bool = True


class ModelListResponse(BaseModel):
    default: str = Field(..., description="Configured default local model")
    runtime: str = Field(..., description="Primary configured LLM runtime")
    models: list[ModelInfo]


class DefaultModelResponse(BaseModel):
    default: str
    model: ModelInfo
