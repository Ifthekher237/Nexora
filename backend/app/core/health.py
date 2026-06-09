"""Small health helpers for local development checks."""

from __future__ import annotations

import platform
import sys

from backend.app.core.config import get_settings


def get_system_health() -> dict[str, object]:
    """Return a compact local system health snapshot."""

    settings = get_settings()
    machine = platform.machine().lower()
    is_apple_silicon = platform.system() == "Darwin" and machine in {
        "arm64",
        "aarch64",
    }

    apple_note = (
        "Apple Silicon detected; local model performance should benefit from native runtimes."
        if is_apple_silicon
        else "Apple Silicon was not detected in this runtime."
    )

    return {
        "app": settings.app_name,
        "environment": settings.environment,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "local_first": settings.local_first,
        "apple_silicon_note": apple_note,
        "backend_status": "running",
    }
