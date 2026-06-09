"""Local CPU, memory, Python, and platform resource reporting."""

from __future__ import annotations

import logging
import platform
import sys
from typing import Any

from backend.app.core.config import get_performance_config


logger = logging.getLogger(__name__)


def _resource_config() -> dict[str, Any]:
    return get_performance_config().get("resource_monitor", {})


def _apple_silicon_note(machine: str, system: str) -> str:
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        return "Apple Silicon detected. Keep local model sizes aligned with available unified memory."
    if system == "Darwin":
        return "macOS detected. Apple Silicon acceleration depends on hardware and local runtime support."
    return "No Apple Silicon-specific runtime note."


def snapshot() -> dict[str, Any]:
    system = platform.system()
    machine = platform.machine()
    payload: dict[str, Any] = {
        "status": "ok",
        "monitor_enabled": bool(_resource_config().get("enabled", True)),
        "psutil_available": False,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "system": system,
        "machine": machine,
        "processor": platform.processor(),
        "apple_silicon_note": _apple_silicon_note(machine, system),
        "cpu_percent": None,
        "memory_total_mb": None,
        "memory_available_mb": None,
        "memory_used_percent": None,
        "process_memory_mb": None,
        "fallback_note": "",
    }

    if not payload["monitor_enabled"]:
        payload["fallback_note"] = "Resource monitor is disabled by configuration."
        return payload

    if not bool(_resource_config().get("use_psutil_if_available", True)):
        payload["fallback_note"] = "psutil usage is disabled by configuration."
        return payload

    try:
        import psutil  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.info("psutil unavailable; resource monitor using fallback | error=%s", exc)
        payload["fallback_note"] = "psutil is unavailable; returning standard Python/platform information only."
        return payload

    try:
        payload["psutil_available"] = True
        if bool(_resource_config().get("track_cpu", True)):
            payload["cpu_percent"] = psutil.cpu_percent(interval=0.0)
        if bool(_resource_config().get("track_memory", True)):
            memory = psutil.virtual_memory()
            payload["memory_total_mb"] = round(memory.total / (1024 * 1024), 2)
            payload["memory_available_mb"] = round(memory.available / (1024 * 1024), 2)
            payload["memory_used_percent"] = memory.percent
            process = psutil.Process()
            payload["process_memory_mb"] = round(process.memory_info().rss / (1024 * 1024), 2)
    except Exception as exc:  # pragma: no cover - defensive platform guard
        logger.warning("psutil resource snapshot failed | error=%s", exc)
        payload["status"] = "degraded"
        payload["fallback_note"] = f"psutil failed: {exc}"
    return payload
