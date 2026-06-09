"""Pydantic schemas for Nexora's risk scoring engine."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RiskFilters(BaseModel):
    source_type: Optional[str] = None
    document_type: Optional[str] = None
    section_hint: Optional[str] = None


class RiskScoringRequest(BaseModel):
    scenario: str = Field(..., min_length=1)
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    market: Optional[str] = None
    top_k: int = Field(default=8, ge=1)
    model: Optional[str] = None
    vector_store: str = Field(default="faiss")
    filters: RiskFilters = Field(default_factory=RiskFilters)


class RiskConfidence(BaseModel):
    level: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class ScoreBreakdown(BaseModel):
    evidence_strength_score: int = Field(ge=0, le=100)
    exposure_score: int = Field(ge=0, le=100)
    vulnerability_score: int = Field(ge=0, le=100)
    operational_risk_score: int = Field(ge=0, le=100)
    macro_risk_score: int = Field(ge=0, le=100)
    sector_risk_score: int = Field(ge=0, le=100)
    company_specific_risk_score: int = Field(ge=0, le=100)


class RiskDriver(BaseModel):
    driver: str
    score_impact: str
    supporting_sources: list[str] = Field(default_factory=list)
    explanation: str


class EvidenceSummary(BaseModel):
    sources_used: int
    unique_documents: int
    average_retrieval_score: float
    top_retrieval_score: float = 0.0
    supported_chain_steps: int
    source_diversity: float = Field(ge=0.0, le=1.0)


class RiskScoringResponse(BaseModel):
    risk_id: str
    source_reasoning_id: str = ""
    scenario: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    scenario_type: str
    overall_risk_score: int = Field(ge=0, le=100)
    overall_risk_level: str
    confidence: RiskConfidence
    score_breakdown: ScoreBreakdown
    risk_drivers: list[RiskDriver]
    evidence_summary: EvidenceSummary
    explanation: str
    limitations: list[str]
    validation_warnings: list[str] = Field(default_factory=list)
    not_financial_advice: bool = True
    status: str
    created_at: str
    model: str = ""
    error_message: str = ""


class RiskHistoryItem(BaseModel):
    risk_id: str
    created_at: str
    scenario: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    scenario_type: str
    overall_risk_score: int
    overall_risk_level: str
    confidence_level: str
    confidence_score: float
    status: str
    response_path: str
    error_message: str = ""


class ExplainScoreRequest(BaseModel):
    risk_id: Optional[str] = None
    risk_payload: Optional[dict[str, object]] = None


class ExplainScoreResponse(BaseModel):
    risk_id: str = ""
    explanation: str
    limitations: list[str]
    status: str


class RiskStatus(BaseModel):
    status: str
    reasoning_available: bool
    rag_available: bool
    retrieval_available: bool
    saved_risk_outputs: int
    scoring_config_status: dict[str, object]
    output_storage: dict[str, object]
