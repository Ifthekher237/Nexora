"""Health endpoints for Nexora."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.core.health import get_system_health


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "app": settings.app_name,
        "status": "healthy",
        "message": "Nexora backend health check passed.",
    }


@router.get("/health/system")
def system_health() -> dict[str, object]:
    return get_system_health()
