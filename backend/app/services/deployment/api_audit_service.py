"""FastAPI route surface audit for deployment readiness."""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)

GROUP_PREFIXES = {
    "health": ["/health", "/"],
    "models/inference": ["/models", "/inference"],
    "ingestion": ["/ingestion"],
    "processing": ["/processing"],
    "retrieval": ["/retrieval"],
    "rag": ["/rag"],
    "reasoning": ["/reasoning"],
    "risk": ["/risk"],
    "explainability": ["/explainability"],
    "agents": ["/agents"],
    "performance": ["/performance"],
    "deployment": ["/deployment"],
}


def _group_for_path(path: str) -> str:
    for group, prefixes in GROUP_PREFIXES.items():
        if any(path == prefix or path.startswith(f"{prefix}/") for prefix in prefixes):
            return group
    return "other"


def _purpose_for_group(group: str) -> str:
    return {
        "health": "Health and system readiness",
        "models/inference": "Local model registry and Ollama connectivity checks",
        "ingestion": "Financial source ingestion",
        "processing": "Document extraction, cleaning, and chunking",
        "retrieval": "Vector search and index management",
        "rag": "Evidence-backed question answering",
        "reasoning": "Scenario reasoning and causal chains",
        "risk": "Evidence-backed risk scoring",
        "explainability": "Evidence and trust audit reports",
        "agents": "Multi-agent collaboration workflows",
        "performance": "Local performance, cache, resource, and benchmark tools",
        "deployment": "Enterprise readiness planning and final reports",
    }.get(group, "Auxiliary API surface")


def audit_api_routes() -> dict[str, Any]:
    logger.info("Deployment API audit requested")
    try:
        from backend.app.main import app
    except Exception as exc:
        return {"status": "error", "routes": [], "groups": {}, "error_message": str(exc)}

    routes: list[dict[str, Any]] = []
    for route in getattr(app, "routes", []):
        path = getattr(route, "path", "")
        methods = sorted(getattr(route, "methods", []) or [])
        if "HEAD" in methods:
            methods.remove("HEAD")
        group = _group_for_path(path)
        routes.append(
            {
                "path": path,
                "methods": methods,
                "group": group,
                "tags": list(getattr(route, "tags", []) or []),
                "purpose": _purpose_for_group(group),
                "readiness_note": "Registered in FastAPI route table.",
            }
        )
    groups: dict[str, Any] = {}
    for route in routes:
        group = route["group"]
        groups.setdefault(group, {"count": 0, "routes": []})
        groups[group]["count"] += 1
        groups[group]["routes"].append(route["path"])
    return {
        "status": "success",
        "route_count": len(routes),
        "routes": sorted(routes, key=lambda item: item["path"]),
        "groups": groups,
        "missing_expected_groups": [group for group in GROUP_PREFIXES if group not in groups],
    }
