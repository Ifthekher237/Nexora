"""Enterprise deployment readiness checks for local-first Nexora."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_app_config, get_deployment_config
from backend.app.services.deployment import environment_review_service, final_report_service
from backend.app.services.ingestion.metadata_service import utc_now_iso


logger = logging.getLogger(__name__)

REQUIRED_FILES = [
    "README.md",
    ".env.example",
    "requirements.txt",
    "configs/app_config.yaml",
    "configs/model_config.yaml",
    "configs/ingestion_sources.yaml",
    "configs/processing_config.yaml",
    "configs/retrieval_config.yaml",
    "configs/rag_config.yaml",
    "configs/reasoning_config.yaml",
    "configs/risk_config.yaml",
    "configs/explainability_config.yaml",
    "configs/agents_config.yaml",
    "configs/performance_config.yaml",
    "configs/deployment_config.yaml",
]

REQUIRED_DIRS = [
    "backend/app/api",
    "backend/app/services",
    "backend/app/schemas",
    "frontend/app_pages",
    "scripts",
    "docs",
    "data/metadata",
    "data/processed",
    "data/vector_store",
    "data/deployment_outputs/reports",
]

REQUIRED_INDEXES = [
    "data/metadata/ingestion_index.json",
    "data/processed/processing_metadata/processing_index.json",
    "data/vector_store/metadata/vector_index.json",
    "data/rag_outputs/rag_response_index.json",
    "data/reasoning_outputs/reasoning_index.json",
    "data/risk_outputs/risk_index.json",
    "data/explainability_outputs/explainability_index.json",
    "data/agent_outputs/agent_run_index.json",
    "data/performance_outputs/performance_index.json",
    "data/deployment_outputs/deployment_readiness_index.json",
]

REQUIRED_DOCS = [
    "docs/ARCHITECTURE.md",
    "docs/INGESTION_ARCHITECTURE.md",
    "docs/RAG_ARCHITECTURE.md",
    "docs/RISK_SCORING_ARCHITECTURE.md",
    "docs/AGENT_COLLABORATION_ARCHITECTURE.md",
    "docs/PERFORMANCE_OPTIMIZATION_ARCHITECTURE.md",
    "docs/ENTERPRISE_DEPLOYMENT_ARCHITECTURE.md",
    "docs/SECURITY_AND_GOVERNANCE_PLAN.md",
    "docs/PRODUCTION_RUNBOOK.md",
    "docs/FINAL_PROJECT_SUMMARY.md",
    "docs/PHASE_12_SUMMARY.md",
]

REQUIRED_TESTS = [
    "backend/tests/test_deployment_readiness_service.py",
    "backend/tests/test_security_review_service.py",
    "backend/tests/test_api_audit_service.py",
    "backend/tests/test_environment_review_service.py",
]

EXPECTED_STREAMLIT_PAGES = [
    "Home",
    "System Status",
    "Data Ingestion",
    "Document Processing",
    "Vector Search",
    "RAG Assistant",
    "Scenario Reasoning",
    "Risk Scoring",
    "Explainability",
    "AI Agent Collaboration",
    "Performance & Scaling",
    "Deployment Readiness",
    "History Explorer",
]


def _item(name: str, status: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "status": status, "message": message, "details": details or {}}


def _path_item(path: str, kind: str) -> dict[str, Any]:
    exists = (PROJECT_ROOT / path).exists()
    status = "pass" if exists else "fail"
    return _item(f"{kind}: {path}", status, f"{path} {'exists' if exists else 'is missing'}.", {"path": path})


def _score(items: list[dict[str, Any]]) -> float:
    if not items:
        return 0.0
    points = 0.0
    for item in items:
        if item["status"] == "pass":
            points += 1.0
        elif item["status"] == "warning":
            points += 0.5
    return round((points / len(items)) * 100, 2)


def readiness_level(score: float) -> str:
    if score < 50:
        return "early"
    if score < 70:
        return "local_ready"
    if score < 85:
        return "portfolio_ready"
    return "enterprise_planning_ready"


def _backend_import_check() -> dict[str, Any]:
    try:
        from backend.app.main import app
        return _item("Backend import readiness", "pass", f"FastAPI app imports with {len(app.routes)} registered route(s).")
    except Exception as exc:
        return _item("Backend import readiness", "fail", f"Backend import failed: {exc}")


def _api_routes_check() -> dict[str, Any]:
    try:
        from backend.app.main import app
        paths = {route.path for route in app.routes}
    except Exception as exc:
        return _item("API routes registered", "fail", f"Could not inspect API routes: {exc}")
    required = [
        "/health",
        "/ingestion/status",
        "/processing/status",
        "/retrieval/status",
        "/rag/status",
        "/reasoning/status",
        "/risk/status",
        "/explainability/status",
        "/agents/status",
        "/performance/status",
        "/deployment/status",
    ]
    missing = [path for path in required if path not in paths]
    status = "pass" if not missing else "fail"
    return _item("API routes registered", status, "Required API route groups are registered." if not missing else f"Missing routes: {missing}", {"missing": missing})


def _streamlit_pages_check() -> dict[str, Any]:
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "frontend"))
        import streamlit_app
        page_names = set(streamlit_app.PAGES)
    except Exception as exc:
        return _item("Streamlit pages registered", "fail", f"Could not import Streamlit app: {exc}")
    missing = [page for page in EXPECTED_STREAMLIT_PAGES if page not in page_names]
    status = "pass" if not missing else "fail"
    return _item("Streamlit pages registered", status, "All expected pages are registered." if not missing else f"Missing pages: {missing}", {"missing": missing})


def _secrets_check() -> dict[str, Any]:
    findings = []
    for path in PROJECT_ROOT.iterdir():
        if path.name == ".env":
            findings.append(".env exists locally; ensure it is untracked and not shared.")
        if path.suffix in {".pem", ".key"} or path.name in {"id_rsa", "id_ed25519"}:
            findings.append(f"Potential secret file at project root: {path.name}")
    status = "warning" if findings else "pass"
    return _item("No obvious committed secret files", status, "Review local secret files before sharing." if findings else "No obvious root-level secret files detected.", {"findings": findings})


def _local_first_check() -> dict[str, Any]:
    app_config = get_app_config().get("app", {})
    deployment_config = get_deployment_config().get("deployment", {})
    local_first = bool(app_config.get("local_first", True)) and bool(deployment_config.get("local_first", True))
    no_cloud = not bool(deployment_config.get("actual_cloud_deployment", False))
    status = "pass" if local_first and no_cloud else "fail"
    return _item("Local-first mode preserved", status, "Nexora remains local-first and no actual cloud deployment is configured.", {"local_first": local_first, "actual_cloud_deployment": deployment_config.get("actual_cloud_deployment", False)})


def run_readiness_check(
    *,
    save: bool = True,
    extra_required_files: list[str] | None = None,
) -> dict[str, Any]:
    logger.info("Deployment readiness check started")
    items: list[dict[str, Any]] = [_backend_import_check()]
    for path in REQUIRED_FILES + list(extra_required_files or []):
        items.append(_path_item(path, "Required file"))
    for path in REQUIRED_DIRS:
        items.append(_path_item(path, "Required directory"))
    for path in REQUIRED_INDEXES:
        item = _path_item(path, "Data index")
        if item["status"] == "fail":
            item["status"] = "warning"
            item["message"] = f"{path} is missing; create it through the relevant pipeline before enterprise use."
        items.append(item)
    items.append(_api_routes_check())
    items.append(_streamlit_pages_check())
    for path in REQUIRED_DOCS:
        items.append(_path_item(path, "Required doc"))
    for path in REQUIRED_TESTS:
        items.append(_path_item(path, "Required test"))
    items.append(_secrets_check())
    items.append(_local_first_check())
    env_review = environment_review_service.review_environment(check_ollama=True)
    if not env_review.get("python_version_ok"):
        items.append(_item("Python version", "warning", f"Python {env_review.get('python_version')} does not start with required {env_review.get('required_python_version')}."))
    else:
        items.append(_item("Python version", "pass", f"Python {env_review.get('python_version')} matches required planning version."))
    if not env_review.get("ollama_running"):
        items.append(_item("Ollama availability", "warning", env_review.get("ollama_note", "Ollama unavailable.")))
    else:
        items.append(_item("Ollama availability", "pass", "Ollama is reachable locally."))

    score = _score(items)
    level = readiness_level(score)
    fail_count = sum(1 for item in items if item["status"] == "fail")
    warning_count = sum(1 for item in items if item["status"] == "warning")
    result = {
        "report_type": "deployment_readiness",
        "created_at": utc_now_iso(),
        "status": "success" if fail_count == 0 else "needs_attention",
        "readiness_score": score,
        "readiness_level": level,
        "summary": {
            "total_checks": len(items),
            "pass_count": sum(1 for item in items if item["status"] == "pass"),
            "warning_count": warning_count,
            "fail_count": fail_count,
        },
        "checks": items,
        "environment_review": env_review,
        "local_first": True,
        "cloud_ready_planning_only": True,
        "actual_cloud_deployment": False,
        "limitations": [
            "No real cloud deployment is implemented.",
            "Production authentication and authorization are not implemented yet.",
            "Enterprise use requires security and data-governance review.",
        ],
        "error_message": "",
    }
    if save:
        try:
            save_info = final_report_service.save_deployment_report(result)
            result.update(save_info)
        except final_report_service.DeploymentReportStorageError as exc:
            result["status"] = "partial_success"
            result["error_message"] = str(exc)
    logger.info("Deployment readiness check completed | score=%s | level=%s", score, level)
    return result


def deployment_status() -> dict[str, Any]:
    config = get_deployment_config()
    latest = final_report_service.latest_report()
    required_docs_available = all((PROJECT_ROOT / path).exists() for path in REQUIRED_DOCS)
    return {
        "status": "ready",
        "local_first": bool(config.get("deployment", {}).get("local_first", True)),
        "cloud_ready_planning_only": bool(config.get("deployment", {}).get("cloud_ready_planning_only", True)),
        "actual_cloud_deployment": bool(config.get("deployment", {}).get("actual_cloud_deployment", False)),
        "required_reports_available": required_docs_available,
        "latest_readiness_report": final_report_service.latest_report("deployment_readiness"),
        "latest_report": latest,
        "saved_report_count": final_report_service.output_count(),
        "config_status": {
            "loaded": True,
            "deployment": config.get("deployment", {}),
            "readiness_checks": config.get("readiness_checks", {}),
            "enterprise_planning": config.get("enterprise_planning", {}),
        },
    }
