"""Pydantic schemas for Nexora's financial reasoning engine."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReasoningFilters(BaseModel):
    source_type: Optional[str] = None
    document_type: Optional[str] = None
    section_hint: Optional[str] = None


class ScenarioAnalysisRequest(BaseModel):
    scenario: str = Field(..., min_length=1)
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    market: Optional[str] = None
    top_k: int = Field(default=8, ge=1)
    model: Optional[str] = None
    vector_store: str = Field(default="faiss")
    filters: ReasoningFilters = Field(default_factory=ReasoningFilters)


class ParsedScenario(BaseModel):
    scenario_type: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    macro_trigger: str = ""
    sector_trigger: str = ""
    key_risk_keywords: list[str] = Field(default_factory=list)
    time_horizon: str = ""
    numerical_shock: str = ""


class CausalChainStep(BaseModel):
    step: int
    cause: str
    effect: str
    evidence_strength: str
    supporting_sources: list[str] = Field(default_factory=list)
    uncertainty: str


class FinancialExposureAnalysis(BaseModel):
    operational_exposure: str
    macro_exposure: str
    sector_exposure: str
    company_specific_exposure: str


class EvidenceMapItem(BaseModel):
    source_number: str
    chunk_id: str
    source_document_id: str = ""
    relevance: str
    used_for: str
    score: float = 0.0
    evidence_text: str = ""


class ReasoningConfidence(BaseModel):
    level: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class ScenarioAnalysisResponse(BaseModel):
    reasoning_id: str
    scenario: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    scenario_type: str
    direct_answer: str
    causal_chain: list[CausalChainStep]
    financial_exposure_analysis: FinancialExposureAnalysis
    evidence_map: list[EvidenceMapItem]
    confidence: ReasoningConfidence
    limitations: list[str]
    validation_warnings: list[str] = Field(default_factory=list)
    not_financial_advice: bool = True
    status: str
    created_at: str
    model: str
    error_message: str = ""


class ReasoningHistoryItem(BaseModel):
    reasoning_id: str
    created_at: str
    scenario: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    scenario_type: str
    model: str
    confidence_level: str
    confidence_score: float
    status: str
    response_path: str
    error_message: str = ""


class CausalChainOnlyResponse(BaseModel):
    scenario: str
    scenario_type: str
    causal_chain: list[CausalChainStep]
    status: str


class EvidenceMapResponse(BaseModel):
    scenario: str
    scenario_type: str
    evidence_map: list[EvidenceMapItem]
    retrieval_summary: dict[str, object]
    limitations: list[str]
    status: str


class ReasoningStatus(BaseModel):
    status: str
    rag_available: bool
    retrieval_available: bool
    ollama_running: bool
    installed_models: list[str]
    saved_reasoning_outputs: int
    default_model: str
    fallback_model: str
    default_top_k: int
    max_top_k: int
    min_evidence_score: float
    output_storage: dict[str, object]
