"""Pydantic schemas for Nexora's Explainability & Evidence Layer."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ExplainLatestRequest(BaseModel):
    target_type: str = Field(..., pattern="^(risk|reasoning|rag)$")


class EvidenceCoverage(BaseModel):
    level: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    sources_used: int = 0
    unique_documents: int = 0
    average_retrieval_score: float = 0.0
    company_specific_evidence: bool = False
    relevant_document_types: bool = False


class ExpandedCitation(BaseModel):
    source_number: str
    chunk_id: str = "unknown"
    source_document_id: str = "unknown"
    processed_document_id: str = "unknown"
    company_name: str = "unknown"
    ticker: str = "unknown"
    market: str = "unknown"
    document_type: str = "unknown"
    source_type: str = "unknown"
    published_date: str = "unknown"
    retrieval_score: float = 0.0
    chunk_text_excerpt: str = "unknown"
    source_url: str = "unknown"
    citation_usage_count: int = 0
    missing_fields: list[str] = Field(default_factory=list)


class EvidenceRankingItem(BaseModel):
    rank: int
    evidence_id: str
    score: float = Field(ge=0.0, le=1.0)
    rank_reason: str
    source_summary: str
    score_components: dict[str, float] = Field(default_factory=dict)


class DocumentAttributionItem(BaseModel):
    source_document_id: str
    company_name: str = "unknown"
    ticker: str = "unknown"
    document_type: str = "unknown"
    source_type: str = "unknown"
    published_date: str = "unknown"
    evidence_chunk_count: int = 0
    average_retrieval_score: float = 0.0
    supported_items: list[str] = Field(default_factory=list)


class UnsupportedClaimItem(BaseModel):
    claim: str
    issue_type: str
    severity: str
    suggested_fix: str


class ConfidenceExplanation(BaseModel):
    level: str = "unknown"
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str
    factors: list[str] = Field(default_factory=list)
    distinction: str


class ExplainabilityHistoryItem(BaseModel):
    explainability_id: str
    created_at: str
    target_type: str
    target_id: str
    coverage_level: str
    coverage_score: float
    explainability_score: float
    status: str
    report_path: str
    error_message: str = ""


class ExplainabilityReportResponse(BaseModel):
    explainability_id: str
    target_type: str
    target_id: str
    explainability_score: float = Field(ge=0.0, le=1.0)
    evidence_coverage: EvidenceCoverage
    expanded_citations: list[ExpandedCitation] = Field(default_factory=list)
    evidence_ranking: list[EvidenceRankingItem] = Field(default_factory=list)
    score_explanation: str = ""
    confidence_explanation: ConfidenceExplanation
    reasoning_trace: dict[str, object] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    unsupported_claims: list[UnsupportedClaimItem] = Field(default_factory=list)
    document_attribution: list[DocumentAttributionItem] = Field(default_factory=list)
    recommendation: str
    validation_warnings: list[str] = Field(default_factory=list)
    report: dict[str, object] = Field(default_factory=dict)
    status: str
    created_at: str
    error_message: str = ""


class ExplainabilityStatus(BaseModel):
    status: str
    saved_reports: int
    rag_history_available: bool
    reasoning_history_available: bool
    risk_history_available: bool
    output_storage: dict[str, object]
    config_status: dict[str, object]


class ExplainabilityHistoryFilters(BaseModel):
    target_type: Optional[str] = None
    status: Optional[str] = None
    coverage_level: Optional[str] = None
