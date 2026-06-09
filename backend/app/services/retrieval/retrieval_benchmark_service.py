"""Simple retrieval benchmark runner for sanity checking search behavior."""

from __future__ import annotations

import json
from typing import Any

from backend.app.services.ingestion.metadata_service import utc_now_iso
from backend.app.services.ingestion.storage_service import project_relative_path
from backend.app.services.retrieval import retrieval_service
from backend.app.services.retrieval.retrieval_metadata_service import benchmark_results_path


DEFAULT_QUERIES = [
    "interest rate risk",
    "revenue pressure",
    "oil price impact",
]


def run_benchmark(
    queries: list[str] | None = None,
    top_k: int = 5,
    vector_store: str = "faiss",
) -> dict[str, Any]:
    selected_queries = [query for query in (queries or DEFAULT_QUERIES) if query.strip()]
    results: list[dict[str, Any]] = []

    for query in selected_queries:
        search_result = retrieval_service.search(
            query=query,
            top_k=top_k,
            vector_store=vector_store,
            filters={},
        )
        rows = search_result["results"]
        results.append(
            {
                "query": query,
                "top_result_score": rows[0]["score"] if rows else None,
                "number_of_results": len(rows),
                "result_chunk_ids": [row["chunk_id"] for row in rows],
                "timestamp": utc_now_iso(),
            }
        )

    benchmark_results_path().parent.mkdir(parents=True, exist_ok=True)
    benchmark_results_path().write_text(json.dumps(results, indent=2), encoding="utf-8")
    return {
        "status": "success",
        "results": results,
        "saved_path": project_relative_path(benchmark_results_path()),
    }
