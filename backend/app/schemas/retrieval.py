"""Pydantic schemas for Nexora vector retrieval."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RetrievalFilters(BaseModel):
    ticker: Optional[str] = None
    source_type: Optional[str] = None
    document_type: Optional[str] = None
    market: Optional[str] = None
    section_hint: Optional[str] = None


class BuildIndexRequest(BaseModel):
    limit: int = Field(default=100, ge=1)
    vector_store: str = Field(default="faiss")
    rebuild: bool = False


class BuildIndexResponse(BaseModel):
    status: str
    vector_store: str
    embedding_model: str
    chunks_found: int
    chunks_indexed: int
    duplicates_skipped: int
    errors: list[str] = []


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1)
    vector_store: str = Field(default="faiss")
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


class SearchResult(BaseModel):
    rank: int
    score: float
    chunk_id: str
    chunk_text: str
    metadata: dict[str, object]


class SearchResponse(BaseModel):
    query: str
    top_k: int
    results: list[SearchResult]


class VectorMetadata(BaseModel):
    vector_id: str
    chunk_id: str
    processed_document_id: str
    source_document_id: str
    chunk_index: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    document_type: str = ""
    source_type: str = ""
    published_at: str = ""
    period: str = ""
    section_hint: str = ""
    embedding_model: str
    embedding_dimension: str
    vector_store: str
    indexed_at: str
    chunk_word_count: str
    chunk_char_count: str
    source_chunk_file: str
    status: str
    error_message: str = ""


class RetrievalStatus(BaseModel):
    status: str
    embedding_model_status: dict[str, object]
    vector_store_availability: dict[str, object]
    indexed_chunks: int
    faiss_index_status: dict[str, object]
    chroma_status: dict[str, object]
    metadata_index_status: dict[str, object]


class RetrievalSummary(BaseModel):
    total_indexed_chunks: int
    indexed_chunks_by_source_type: dict[str, int]
    indexed_chunks_by_ticker: dict[str, int]
    indexed_chunks_by_document_type: dict[str, int]
    embedding_model_used: str
    vector_stores_available: list[str]
    latest_indexing_time: str


class BenchmarkRequest(BaseModel):
    queries: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1)
    vector_store: str = Field(default="faiss")


class BenchmarkResponse(BaseModel):
    status: str
    results: list[dict[str, object]]
    saved_path: str
