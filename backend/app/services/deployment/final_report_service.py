"""Deployment readiness and final project report storage/generation."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.app.core.config import PROJECT_ROOT, get_deployment_config
from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ingestion.storage_service import project_relative_path, safe_filename


logger = logging.getLogger(__name__)

INDEX_FIELDS = [
    "report_id",
    "created_at",
    "report_type",
    "readiness_score",
    "readiness_level",
    "status",
    "json_path",
    "markdown_path",
    "error_message",
]

PHASES = [
    "Phase 1: Core infrastructure foundation",
    "Phase 2: Financial Data Ingestion Engine",
    "Phase 3: Document Processing Pipeline",
    "Phase 4: Vector Database & Retrieval System",
    "Phase 5: Core Financial RAG Pipeline",
    "Phase 6: Financial Reasoning Engine",
    "Phase 7: Risk Scoring Engine",
    "Phase 8: Explainability & Evidence Layer",
    "Phase 9: Streamlit Financial Intelligence Interface",
    "Phase 10: AI Agent Collaboration System",
    "Phase 11: Performance Optimization & Scaling",
    "Phase 12: Enterprise Deployment Architecture",
]


class DeploymentReportStorageError(RuntimeError):
    """Raised when deployment report storage cannot be read or written."""


def _config() -> dict[str, Any]:
    return get_deployment_config().get("deployment", {})


def output_dir() -> Path:
    return PROJECT_ROOT / _config().get("output_dir", "data/deployment_outputs/reports")


def index_csv_path() -> Path:
    return PROJECT_ROOT / _config().get("index_csv", "data/deployment_outputs/deployment_readiness_index.csv")


def index_json_path() -> Path:
    return PROJECT_ROOT / _config().get("index_json", "data/deployment_outputs/deployment_readiness_index.json")


def ensure_storage() -> None:
    output_dir().mkdir(parents=True, exist_ok=True)
    index_csv_path().parent.mkdir(parents=True, exist_ok=True)
    if not index_csv_path().exists():
        with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=INDEX_FIELDS).writeheader()
    if not index_json_path().exists():
        index_json_path().write_text("[]", encoding="utf-8")


def generate_report_id(report_type: str, payload: Any) -> str:
    timestamp = utc_now_iso().replace("+00:00", "Z").replace(":", "").replace("-", "")
    digest = hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:8]
    return safe_filename(f"DEPLOY_{timestamp}_{report_type}_{digest}_{uuid4().hex[:8]}")


def _read_index() -> list[dict[str, Any]]:
    ensure_storage()
    try:
        data = json.loads(index_json_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DeploymentReportStorageError(f"Deployment index JSON is malformed: {exc}") from exc
    if not isinstance(data, list):
        raise DeploymentReportStorageError("Deployment index JSON must contain a list.")
    return [record for record in data if isinstance(record, dict)]


def _write_index(records: list[dict[str, Any]]) -> None:
    normalized = [
        {field: "" if record.get(field) is None else str(record.get(field, "")) for field in INDEX_FIELDS}
        for record in records
    ]
    with index_csv_path().open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(normalized)
    index_json_path().write_text(json.dumps(normalized, indent=2), encoding="utf-8")


def _index_record(report: dict[str, Any], json_path: Path, markdown_path: Path | None) -> dict[str, Any]:
    return {
        "report_id": report.get("report_id", ""),
        "created_at": report.get("created_at", ""),
        "report_type": report.get("report_type", ""),
        "readiness_score": report.get("readiness_score", ""),
        "readiness_level": report.get("readiness_level", ""),
        "status": report.get("status", ""),
        "json_path": project_relative_path(json_path),
        "markdown_path": project_relative_path(markdown_path) if markdown_path else "",
        "error_message": report.get("error_message", ""),
    }


def save_deployment_report(report: dict[str, Any], markdown: str = "") -> dict[str, Any]:
    ensure_storage()
    report_type = str(report.get("report_type", "deployment_report"))
    report_id = str(report.get("report_id") or generate_report_id(report_type, report))
    report["report_id"] = report_id
    report.setdefault("created_at", utc_now_iso())
    json_path = output_dir() / f"{safe_filename(report_id)}.json"
    markdown_path = output_dir() / f"{safe_filename(report_id)}.md" if markdown else None
    try:
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
        if markdown_path:
            markdown_path.write_text(markdown, encoding="utf-8")
        records = [record for record in _read_index() if record.get("report_id") != report_id]
        records.append(_index_record(report, json_path, markdown_path))
        _write_index(records)
    except OSError as exc:
        raise DeploymentReportStorageError(f"Could not save deployment report: {exc}") from exc
    logger.info("Deployment report saved | report_id=%s | type=%s", report_id, report_type)
    return {
        "saved": True,
        "report_id": report_id,
        "json_path": project_relative_path(json_path),
        "markdown_path": project_relative_path(markdown_path) if markdown_path else "",
    }


def read_history(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    records = _read_index()
    filters = filters or {}
    report_type = filters.get("report_type")
    if report_type:
        records = [record for record in records if str(record.get("report_type", "")).lower() == report_type.lower()]
    return sorted(records, key=lambda item: item.get("created_at", ""), reverse=True)


def read_report(report_id: str) -> dict[str, Any] | None:
    clean = report_id.strip()
    for record in _read_index():
        if record.get("report_id") != clean:
            continue
        path = PROJECT_ROOT / str(record.get("json_path", ""))
        if not path.exists():
            raise DeploymentReportStorageError(f"Deployment report body is missing for {clean}.")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DeploymentReportStorageError(f"Deployment report is malformed: {exc}") from exc
        return data if isinstance(data, dict) else None
    return None


def output_count() -> int:
    return len(_read_index())


def latest_report(report_type: str | None = None) -> dict[str, Any] | None:
    records = read_history({"report_type": report_type} if report_type else {})
    if not records:
        return None
    return records[0]


def _markdown_report(report: dict[str, Any]) -> str:
    readiness = report.get("deployment_readiness", {})
    capabilities = report.get("system_capabilities", [])
    limitations = report.get("known_limitations", [])
    future = report.get("future_enterprise_steps", [])
    lines = [
        "# Nexora Final Project Report",
        "",
        "Nexora is a local-first Financial Scenario Intelligence Engine that combines ingestion, document processing, vector retrieval, RAG, reasoning, risk scoring, explainability, multi-agent workflows, performance monitoring, and enterprise deployment planning.",
        "",
        "## Completed Phases",
        *[f"- {phase}" for phase in report.get("completed_phases", PHASES)],
        "",
        "## System Capabilities",
        *[f"- {item}" for item in capabilities],
        "",
        "## Technical Architecture",
        report.get("technical_architecture", ""),
        "",
        "## AI / LLM Stack",
        report.get("ai_llm_stack", ""),
        "",
        "## Evidence-Grounded Reasoning",
        report.get("evidence_grounding", ""),
        "",
        "## Risk, Explainability, Agents, and Performance",
        report.get("advanced_layers", ""),
        "",
        "## Deployment Readiness",
        f"- Score: {readiness.get('readiness_score', 'unknown')}",
        f"- Level: {readiness.get('readiness_level', 'unknown')}",
        "- Phase 12 prepares enterprise deployment architecture but does not deploy to cloud.",
        "",
        "## Known Limitations",
        *[f"- {item}" for item in limitations],
        "",
        "## Future Enterprise Deployment Path",
        *[f"- {item}" for item in future],
        "",
        "Nexora does not provide investment advice, trading recommendations, or stock price predictions.",
    ]
    return "\n".join(lines) + "\n"


def generate_final_project_report() -> dict[str, Any]:
    logger.info("Final project report generation started")
    from backend.app.services.deployment import (
        api_audit_service,
        data_governance_service,
        deployment_readiness_service,
        observability_plan_service,
        security_review_service,
    )

    readiness = deployment_readiness_service.run_readiness_check(save=False)
    api_audit = api_audit_service.audit_api_routes()
    security = security_review_service.security_review()
    governance = data_governance_service.governance_plan()
    observability = observability_plan_service.observability_plan()
    report = {
        "report_type": "final_project_report",
        "created_at": utc_now_iso(),
        "status": "success",
        "completed_phases": PHASES,
        "project_summary": "Nexora is a local-first AI-powered Financial Scenario Intelligence Engine for evidence-backed financial scenario analysis.",
        "system_capabilities": [
            "Financial data ingestion from SEC, RSS, macro, and local files.",
            "Document processing, chunking, metadata enrichment, and vector indexing.",
            "Semantic retrieval with FAISS/Chroma support.",
            "Evidence-grounded RAG, scenario reasoning, risk scoring, and explainability.",
            "Multi-agent collaboration across macro, company, sector, news, and risk propagation views.",
            "Performance monitoring, caching, resource inspection, and benchmark history.",
            "Enterprise deployment architecture planning and final readiness reporting.",
        ],
        "apis": {"route_count": api_audit.get("route_count", 0), "groups": api_audit.get("groups", {})},
        "data_pipeline": "Raw data is registered under data/raw, processed under data/processed, embedded into vector stores, and connected to output histories through source IDs and chunk IDs.",
        "model_runtime_layer": "Local Ollama is the intended LLM runtime; no OpenAI API or paid model API is required.",
        "evidence_retrieval_layer": "FAISS/Chroma vector retrieval returns cited chunks and metadata used by RAG, reasoning, risk, explainability, and agents.",
        "reasoning_risk_explainability_layer": "Nexora separates evidence-supported reasoning, risk scoring, and explainability audits with saved histories and limitations.",
        "performance_readiness": "Phase 11 adds cache stats, latency tracking, resource monitoring, and real benchmark reports.",
        "deployment_readiness": readiness,
        "security_review": security,
        "data_governance": governance,
        "observability_plan": observability,
        "technical_architecture": "FastAPI backend services, Streamlit frontend pages, YAML configuration, local file indexes, vector stores, and modular phase-specific services.",
        "ai_llm_stack": "Local Ollama runtime with configured model registry, sentence-transformer embeddings, FAISS/Chroma vector systems, and evidence-first generation safeguards.",
        "evidence_grounding": "Outputs preserve source references and limitations; missing evidence is reported instead of invented.",
        "advanced_layers": "Risk scoring, explainability, agent collaboration, performance benchmarking, and deployment readiness provide portfolio-grade project depth.",
        "known_limitations": [
            "No real cloud deployment is implemented.",
            "No production authentication or authorization is implemented yet.",
            "No enterprise secrets manager is configured.",
            "No Docker/Kubernetes deployment is required or implemented.",
            "Local performance depends on Mac hardware, local models, and data volume.",
            "Enterprise use requires security review, data governance approval, and legal/source licensing review.",
        ],
        "future_enterprise_steps": [
            "Add authentication and authorization.",
            "Add secrets management and production audit logging.",
            "Define retention/deletion workflows and document-level access controls.",
            "Create optional container/cloud deployment artifacts after architecture approval.",
            "Add production observability, alerting, and incident response.",
        ],
        "readiness_score": readiness.get("readiness_score", 0),
        "readiness_level": readiness.get("readiness_level", "early"),
        "error_message": "",
    }
    markdown = _markdown_report(report)
    save_info = save_deployment_report(report, markdown=markdown)
    report.update(save_info)
    logger.info("Final project report generation completed | report_id=%s", report.get("report_id"))
    return report
