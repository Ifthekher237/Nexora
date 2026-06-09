"""Practical security review and future security plan."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from backend.app.core.config import PROJECT_ROOT, get_app_config, get_deployment_config


logger = logging.getLogger(__name__)

SENSITIVE_FILE_PATTERNS = [".env", "id_rsa", "id_ed25519", ".pem", ".key"]


def _scan_obvious_secret_files() -> list[str]:
    findings: list[str] = []
    for path in PROJECT_ROOT.iterdir():
        name = path.name
        if name == ".env":
            findings.append(".env exists locally; verify it is not committed or shared.")
        if any(pattern in name for pattern in SENSITIVE_FILE_PATTERNS if pattern != ".env"):
            findings.append(f"Potential sensitive file at project root: {name}")
    return findings


def security_review() -> dict[str, Any]:
    logger.info("Deployment security review requested")
    deployment_config = get_deployment_config()
    app_config = get_app_config().get("app", {})
    secret_findings = _scan_obvious_secret_files()
    return {
        "status": "planning_required",
        "production_security_complete": False,
        "local_first_default": bool(app_config.get("local_first", True)),
        "cloud_deployment_complete": False,
        "authentication_implemented": False,
        "authorization_implemented": False,
        "security_config": deployment_config.get("security", {}),
        "secret_file_findings": secret_findings,
        "secrets_handling_notes": [
            ".env and local credentials must never be committed.",
            "Use environment variables or a future enterprise secrets manager before production use.",
            "Logs should avoid prompts, documents, or credentials that could contain sensitive data.",
        ],
        "data_privacy_notes": [
            "Raw, processed, vector, and output files are stored locally under data/.",
            "Sensitive company data should be excluded from version control and handled under a retention policy.",
            "Enterprise use requires approval for source data licensing, storage, and deletion.",
        ],
        "authentication_plan": [
            "Add organization identity provider integration before enterprise deployment.",
            "Protect FastAPI routes with authenticated sessions or bearer-token validation.",
            "Keep local developer mode separate from production auth mode.",
        ],
        "authorization_plan": [
            "Define roles such as admin, analyst, auditor, and read-only reviewer.",
            "Restrict ingestion, deletion, benchmark, and report-generation actions by role.",
            "Add document-level access controls before shared enterprise data use.",
        ],
        "audit_logging_plan": [
            "Record user, timestamp, route/action, source document IDs, output IDs, and status.",
            "Avoid storing secrets or unnecessary full prompt/document text in audit logs.",
            "Make audit logs tamper-resistant in a future enterprise environment.",
        ],
        "limitations": [
            "Production authentication is not implemented in Phase 12.",
            "No enterprise secrets manager is configured.",
            "Security architecture is planned, not certified.",
        ],
    }
