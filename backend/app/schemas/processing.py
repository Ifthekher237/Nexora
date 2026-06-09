"""Pydantic schemas for the Nexora document processing pipeline."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProcessingRunRequest(BaseModel):
    limit: int = Field(default=10, ge=1)
    source_type: Optional[str] = None
    ticker: Optional[str] = None
    document_type: Optional[str] = None
    reprocess: bool = False


class ProcessedDocumentMetadata(BaseModel):
    processed_document_id: str
    source_document_id: str
    source_type: str
    source_name: str
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    document_type: str
    source_local_path: str
    processed_text_path: str = ""
    chunk_file_path: str = ""
    file_format: str
    processing_status: str
    processing_error: str = ""
    processed_at: str
    published_at: str = ""
    period: str = ""
    text_length: int = 0
    word_count: int = 0
    chunk_count: int = 0
    language: str = "en"
    detected_document_category: str = "unknown"
    content_hash: str = ""
    notes: str = ""


class ChunkMetadata(BaseModel):
    chunk_id: str
    processed_document_id: str
    source_document_id: str
    chunk_index: int
    chunk_text: str
    chunk_word_count: int
    chunk_char_count: int
    company_name: str = ""
    ticker: str = ""
    market: str = ""
    document_type: str = ""
    source_type: str = ""
    published_at: str = ""
    period: str = ""
    section_hint: str = "unknown"
    created_at: str


class SingleProcessingResponse(BaseModel):
    status: str
    message: str
    document: Optional[ProcessedDocumentMetadata] = None
    chunks_created: int = 0
    errors: list[str] = []


class BatchProcessingResponse(BaseModel):
    status: str
    message: str
    documents_selected: int
    documents_processed: int
    documents_skipped: int
    documents_failed: int
    chunks_created: int
    errors: list[str] = []
    documents: list[ProcessedDocumentMetadata] = []


class ProcessingStatus(BaseModel):
    status: str
    processed_document_count: int
    chunk_count: int
    failed_document_count: int
    processing_storage_paths: dict[str, str]
    config_status: str


class ProcessingSummary(BaseModel):
    total_processed_documents: int
    total_chunks: int
    documents_by_source_type: dict[str, int]
    documents_by_document_type: dict[str, int]
    documents_by_processing_status: dict[str, int]
    latest_processed_time: str
