"""Pydantic schemas for Nexora's AI Agent Collaboration System."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AgentFilters(BaseModel):
    source_type: Optional[str] = None
    document_type: Optional[str] = None
    section_hint: Optional[str] = None


class AgentConfidence(BaseModel):
    level: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class AgentEvidenceItem(BaseModel):
    source_number: str
    chunk_id: str = ""
    source_document_id: str = ""
    processed_document_id: str = ""
    relevance: str
    score: float = 0.0
    evidence_text: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    agent_name: str
    agent_key: str
    status: str
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    evidence_used: list[AgentEvidenceItem] = Field(default_factory=list)
    confidence: AgentConfidence
    limitations: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    details: dict[str, object] = Field(default_factory=dict)


class CollaborationSummary(BaseModel):
    combined_view: str
    key_agreements: list[str] = Field(default_factory=list)
    key_uncertainties: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)


class AgentWorkflowRequest(BaseModel):
    scenario: str = Field(..., min_length=1)
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    market: Optional[str] = None
    top_k: int = Field(default=8, ge=1)
    model: Optional[str] = None
    agents: list[str] = Field(default_factory=list)
    vector_store: str = "faiss"
    filters: AgentFilters = Field(default_factory=AgentFilters)


class SingleAgentRequest(BaseModel):
    agent_name: str
    scenario: str = Field(..., min_length=1)
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    market: Optional[str] = None
    top_k: int = Field(default=8, ge=1)
    model: Optional[str] = None
    vector_store: str = "faiss"
    filters: AgentFilters = Field(default_factory=AgentFilters)


class AgentWorkflowResponse(BaseModel):
    agent_run_id: str
    scenario: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    agents_run: list[str]
    agent_outputs: list[AgentOutput]
    collaboration_summary: CollaborationSummary
    overall_confidence: AgentConfidence
    limitations: list[str]
    not_financial_advice: bool = True
    status: str
    created_at: str
    model: str = ""
    error_message: str = ""


class AgentHistoryItem(BaseModel):
    agent_run_id: str
    created_at: str
    scenario: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    agents_run: str = ""
    overall_confidence_level: str
    overall_confidence_score: float
    status: str
    response_path: str
    error_message: str = ""


class AvailableAgentDescription(BaseModel):
    agent_name: str
    agent_key: str
    description: str


class AgentStatus(BaseModel):
    status: str
    enabled_agents: list[str]
    rag_available: bool
    reasoning_available: bool
    risk_available: bool
    explainability_available: bool
    saved_agent_runs: int
    output_storage: dict[str, object]
    config_status: dict[str, object]
