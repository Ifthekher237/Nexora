"""API routes for Nexora Phase 12 enterprise deployment planning."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.deployment import (
    APIAuditResponse,
    DeploymentReportHistoryItem,
    DeploymentStatusResponse,
    FinalReportResponse,
    GovernancePlanResponse,
    ObservabilityPlanResponse,
    ReadinessResponse,
    SecurityReviewResponse,
)
from backend.app.services.deployment import (
    api_audit_service,
    data_governance_service,
    deployment_readiness_service,
    final_report_service,
    observability_plan_service,
    production_runbook_service,
    security_review_service,
)


router = APIRouter(tags=["deployment"])


@router.get("/deployment/status", response_model=DeploymentStatusResponse)
def get_deployment_status() -> dict[str, object]:
    return deployment_readiness_service.deployment_status()


@router.post("/deployment/readiness-check", response_model=ReadinessResponse)
def post_readiness_check() -> dict[str, object]:
    return deployment_readiness_service.run_readiness_check(save=True)


@router.get("/deployment/api-audit", response_model=APIAuditResponse)
def get_api_audit() -> dict[str, object]:
    return api_audit_service.audit_api_routes()


@router.get("/deployment/security-review", response_model=SecurityReviewResponse)
def get_security_review() -> dict[str, object]:
    return security_review_service.security_review()


@router.get("/deployment/governance-plan", response_model=GovernancePlanResponse)
def get_governance_plan() -> dict[str, object]:
    return data_governance_service.governance_plan()


@router.get("/deployment/observability-plan", response_model=ObservabilityPlanResponse)
def get_observability_plan() -> dict[str, object]:
    return observability_plan_service.observability_plan()


@router.get("/deployment/runbook")
def get_runbook() -> dict[str, object]:
    return production_runbook_service.production_runbook()


@router.post("/deployment/final-report", response_model=FinalReportResponse)
def post_final_report() -> dict[str, object]:
    return final_report_service.generate_final_project_report()


@router.get("/deployment/reports", response_model=list[DeploymentReportHistoryItem])
def get_reports(report_type: Optional[str] = Query(default=None)) -> list[dict[str, object]]:
    try:
        return final_report_service.read_history({"report_type": report_type})
    except final_report_service.DeploymentReportStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/deployment/reports/{report_id}")
def get_report(report_id: str) -> dict[str, object]:
    try:
        report = final_report_service.read_report(report_id)
    except final_report_service.DeploymentReportStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if report is None:
        raise HTTPException(status_code=404, detail=f"Deployment report not found: {report_id}")
    return report
