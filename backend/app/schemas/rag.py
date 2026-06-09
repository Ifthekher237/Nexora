"""Pydantic schemas for Nexora's evidence-grounded RAG pipeline."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RAGFilters(BaseModel):
    ticker: Optional[str] = None
    source_type: Optional[str] = None
    document_type: Optional[str] = None
    market: Optional[str] = None
    section_hint: Optional[str] = None


class RAGAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1)
    model: Optional[str] = None
    vector_store: str = Field(default="faiss")
    filters: RAGFilters = Field(default_factory=RAGFilters)


class RAGConfidence(BaseModel):
    level: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class RAGSource(BaseModel):
    rank: int
    score: float
    chunk_id: str
    source_document_id: str = ""
    processed_document_id: str = ""
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    document_type: str = ""
    source_type: str = ""
    published_at: str = ""
    source_url: str = ""
    section_hint: str = ""
    evidence_text: str = ""


class RAGRetrievalSummary(BaseModel):
    results_found: int
    evidence_used: int
    min_score: float


class RAGAskResponse(BaseModel):
    response_id: str
    question: str
    answer: str
    model: str
    query_type: str
    confidence: RAGConfidence
    sources: list[RAGSource]
    retrieval_summary: RAGRetrievalSummary
    limitations: list[str]
    status: str
    created_at: str
    filters: RAGFilters = Field(default_factory=RAGFilters)
    error_message: str = ""


class RAGHistoryItem(BaseModel):
    response_id: str
    created_at: str
    question: str
    model: str
    ticker: str = ""
    confidence_level: str
    confidence_score: float
    source_count: int
    status: str
    response_path: str
    error_message: str = ""


class RAGEvidenceOnlyRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1)
    vector_store: str = Field(default="faiss")
    filters: RAGFilters = Field(default_factory=RAGFilters)


class RAGEvidenceOnlyResponse(BaseModel):
    question: str
    query_type: str
    evidence_context: str
    sources: list[RAGSource]
    retrieval_summary: RAGRetrievalSummary
    limitations: list[str]
    status: str


class RAGStatus(BaseModel):
    status: str
    default_model: str
    fallback_model: str
    default_top_k: int
    max_top_k: int
    min_retrieval_score: float
    require_citations: bool
    save_rag_outputs: bool
    response_output_dir: str
    response_index_csv: str
    response_index_json: str
    retrieval_status: dict[str, object]
    ollama_running: bool
    installed_models: list[str]
