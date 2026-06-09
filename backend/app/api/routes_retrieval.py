"""API routes for Nexora vector search and retrieval."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.app.schemas.retrieval import (
    BenchmarkRequest,
    BenchmarkResponse,
    BuildIndexRequest,
    BuildIndexResponse,
    RetrievalStatus,
    RetrievalSummary,
    SearchRequest,
    SearchResponse,
    VectorMetadata,
)
from backend.app.services.retrieval import (
    retrieval_benchmark_service,
    retrieval_service,
    vector_store_manager,
)
from backend.app.services.retrieval.embedding_service import EmbeddingServiceError
from backend.app.services.retrieval.faiss_store import FaissStoreError
from backend.app.services.retrieval.vector_store_manager import VectorStoreManagerError


router = APIRouter(tags=["retrieval"])


def _error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@router.get("/retrieval/status", response_model=RetrievalStatus)
def get_retrieval_status() -> dict[str, object]:
    return vector_store_manager.retrieval_system_status()


@router.post("/retrieval/index/build", response_model=BuildIndexResponse)
def post_build_index(request: BuildIndexRequest) -> dict[str, object] | JSONResponse:
    try:
        return vector_store_manager.build_vector_index(
            limit=request.limit,
            vector_store=request.vector_store,
            rebuild=request.rebuild,
        )
    except (EmbeddingServiceError, FaissStoreError, VectorStoreManagerError) as exc:
        return _error_response(str(exc), status_code=503)


@router.post("/retrieval/search", response_model=SearchResponse)
def post_retrieval_search(request: SearchRequest) -> dict[str, object] | JSONResponse:
    try:
        return retrieval_service.search(
            query=request.query,
            top_k=request.top_k,
            vector_store=request.vector_store,
            filters=request.filters.model_dump(),
        )
    except (EmbeddingServiceError, FaissStoreError, VectorStoreManagerError, ValueError) as exc:
        return _error_response(str(exc), status_code=400)


@router.get("/retrieval/index", response_model=list[VectorMetadata])
def get_retrieval_index(
    ticker: Optional[str] = Query(default=None),
    source_type: Optional[str] = Query(default=None),
    document_type: Optional[str] = Query(default=None),
    market: Optional[str] = Query(default=None),
    section_hint: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> list[dict[str, str]]:
    return retrieval_service.index_metadata(
        {
            "ticker": ticker,
            "source_type": source_type,
            "document_type": document_type,
            "market": market,
            "section_hint": section_hint,
            "status": status,
        }
    )


@router.get("/retrieval/summary", response_model=RetrievalSummary)
def get_retrieval_summary() -> dict[str, object]:
    return retrieval_service.summary()


@router.post("/retrieval/benchmark", response_model=BenchmarkResponse)
def post_retrieval_benchmark(request: BenchmarkRequest) -> dict[str, object] | JSONResponse:
    try:
        return retrieval_benchmark_service.run_benchmark(
            queries=request.queries,
            top_k=request.top_k,
            vector_store=request.vector_store,
        )
    except (EmbeddingServiceError, FaissStoreError, VectorStoreManagerError, ValueError) as exc:
        return _error_response(str(exc), status_code=400)
