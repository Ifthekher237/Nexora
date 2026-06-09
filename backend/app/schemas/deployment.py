"""Pydantic schemas for Phase 12 deployment readiness."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReadinessCheckItem(BaseModel):
    name: str
    status: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ReadinessResponse(BaseModel):
    report_type: str = "deployment_readiness"
    report_id: str = ""
    created_at: str
    status: str
    readiness_score: float
    readiness_level: str
    summary: dict[str, object]
    checks: list[ReadinessCheckItem]
    environment_review: dict[str, object]
    local_first: bool
    cloud_ready_planning_only: bool
    actual_cloud_deployment: bool
    limitations: list[str] = Field(default_factory=list)
    json_path: str = ""
    markdown_path: str = ""
    saved: bool = False
    error_message: str = ""


class APIAuditItem(BaseModel):
    path: str
    methods: list[str]
    group: str
    tags: list[str] = Field(default_factory=list)
    purpose: str
    readiness_note: str


class APIAuditResponse(BaseModel):
    status: str
    route_count: int = 0
    routes: list[APIAuditItem] = Field(default_factory=list)
    groups: dict[str, object] = Field(default_factory=dict)
    missing_expected_groups: list[str] = Field(default_factory=list)
    error_message: str = ""


class SecurityReviewResponse(BaseModel):
    status: str
    production_security_complete: bool
    local_first_default: bool
    cloud_deployment_complete: bool
    authentication_implemented: bool
    authorization_implemented: bool
    security_config: dict[str, object]
    secret_file_findings: list[str]
    secrets_handling_notes: list[str]
    data_privacy_notes: list[str]
    authentication_plan: list[str]
    authorization_plan: list[str]
    audit_logging_plan: list[str]
    limitations: list[str]


class GovernancePlanResponse(BaseModel):
    status: str
    raw_data_storage: dict[str, object]
    processed_data_storage: dict[str, object]
    vector_metadata: dict[str, object]
    ai_output_histories: dict[str, object]
    provenance_tracking: list[str]
    source_attribution: list[str]
    retention_planning: list[str]
    deletion_planning: list[str]
    privacy_limitations: list[str]


class ObservabilityPlanResponse(BaseModel):
    status: str
    current_observability: dict[str, object]
    future_observability: list[str]
    dashboard_metrics: list[str]
    limitations: list[str]


class FinalReportResponse(BaseModel):
    report_type: str
    report_id: str = ""
    created_at: str
    status: str
    completed_phases: list[str]
    project_summary: str
    system_capabilities: list[str]
    apis: dict[str, object]
    data_pipeline: str
    model_runtime_layer: str
    evidence_retrieval_layer: str
    reasoning_risk_explainability_layer: str
    performance_readiness: str
    deployment_readiness: dict[str, object]
    security_review: dict[str, object]
    data_governance: dict[str, object]
    observability_plan: dict[str, object]
    technical_architecture: str
    ai_llm_stack: str
    evidence_grounding: str
    advanced_layers: str
    known_limitations: list[str]
    future_enterprise_steps: list[str]
    readiness_score: float
    readiness_level: str
    saved: bool = False
    json_path: str = ""
    markdown_path: str = ""
    error_message: str = ""


class DeploymentReportHistoryItem(BaseModel):
    report_id: str
    created_at: str
    report_type: str
    readiness_score: str | float = ""
    readiness_level: str = ""
    status: str
    json_path: str
    markdown_path: str = ""
    error_message: str = ""


class DeploymentStatusResponse(BaseModel):
    status: str
    local_first: bool
    cloud_ready_planning_only: bool
    actual_cloud_deployment: bool
    required_reports_available: bool
    latest_readiness_report: dict[str, object] | None = None
    latest_report: dict[str, object] | None = None
    saved_report_count: int
    config_status: dict[str, object]
