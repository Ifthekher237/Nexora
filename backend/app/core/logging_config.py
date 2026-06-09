"""Logging setup for Nexora."""

from __future__ import annotations

import logging
from logging import Handler

from backend.app.core.config import PROJECT_ROOT, get_settings


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging() -> None:
    """Configure console logging and optional local file logging."""

    settings = get_settings()
    handlers: list[Handler] = [logging.StreamHandler()]

    if settings.log_to_file:
        log_dir = PROJECT_ROOT / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_dir / "nexora.log", encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format=LOG_FORMAT,
        handlers=handlers,
        force=True,
    )

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger(__name__).info("Nexora logging configured")
