"""Pydantic schemas for Nexora financial data ingestion."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SECIngestionRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=12)
    company_name: str = Field(default="", max_length=200)
    limit: int = Field(default=5, ge=1)


class RSSIngestionRequest(BaseModel):
    feed_name: str = Field(..., min_length=1, max_length=120)
    limit: int = Field(default=10, ge=1)


class LocalFileIngestionRequest(BaseModel):
    file_path: str = Field(..., min_length=1)
    source_type: str = Field(default="local_uploads")
    company_name: str = Field(default="", max_length=200)
    ticker: str = Field(default="", max_length=12)
    market: str = Field(default="", max_length=40)
    document_type: str = Field(..., min_length=1, max_length=80)
    period: str = Field(default="", max_length=40)
    title: Optional[str] = Field(default=None, max_length=300)
    notes: str = Field(default="", max_length=800)


class MacroDatasetIngestionRequest(BaseModel):
    file_path: str = Field(..., min_length=1)
    source_name: str = Field(default="Manual macro dataset", max_length=200)
    title: Optional[str] = Field(default=None, max_length=300)
    period: str = Field(default="", max_length=40)
    notes: str = Field(default="", max_length=800)


class DocumentMetadata(BaseModel):
    document_id: str
    source_type: str
    source_name: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    document_type: str
    title: str
    source_url: str = ""
    local_path: str = ""
    file_format: str = ""
    ingested_at: str
    published_at: str = ""
    period: str = ""
    status: str
    error_message: str = ""
    content_hash: str
    notes: str = ""


class IngestionResult(BaseModel):
    status: str
    source_type: str
    message: str
    documents_found: int = 0
    documents_saved: int = 0
    duplicates_skipped: int = 0
    errors: list[str] = []
    documents: list[DocumentMetadata] = []


class IngestionStatus(BaseModel):
    status: str
    available_source_modules: list[str]
    storage_paths: dict[str, str]
    metadata_index: dict[str, object]
    ingested_documents: int


class IngestionSummary(BaseModel):
    total_documents: int
    documents_by_source_type: dict[str, int]
    documents_by_status: dict[str, int]
    latest_ingestion_time: str
    top_companies: dict[str, int]
    top_tickers: dict[str, int]
