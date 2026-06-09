"""Schemas for local inference connectivity testing."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = Field(
        default=None,
        description="Configured local model name. Uses the default model if omitted.",
    )


class InferenceResponse(BaseModel):
    model: str
    prompt: str
    response: str
    runtime: str
    status: str


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None
