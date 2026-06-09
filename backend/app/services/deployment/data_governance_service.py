"""Data governance planning for local-first Nexora deployment readiness."""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


def governance_plan() -> dict[str, Any]:
    logger.info("Deployment data governance plan requested")
    return {
        "status": "planning_ready",
        "raw_data_storage": {
            "path": "data/raw/",
            "notes": "Stores SEC/RSS/macro/local-upload source material. Enterprise use requires source licensing and retention review.",
        },
        "processed_data_storage": {
            "path": "data/processed/",
            "notes": "Stores extracted text and chunks derived from raw sources.",
        },
        "vector_metadata": {
            "path": "data/vector_store/metadata/vector_index.*",
            "notes": "Preserves chunk IDs, source document IDs, embedding model, vector store, and indexing status.",
        },
        "ai_output_histories": {
            "rag": "data/rag_outputs/",
            "reasoning": "data/reasoning_outputs/",
            "risk": "data/risk_outputs/",
            "explainability": "data/explainability_outputs/",
            "agents": "data/agent_outputs/",
            "performance": "data/performance_outputs/",
            "deployment": "data/deployment_outputs/",
        },
        "provenance_tracking": [
            "Ingestion records preserve document IDs, source type, URL/path, content hash, and ingestion time.",
            "Processing records connect processed documents back to source document IDs.",
            "Vector metadata connects vector IDs to processed chunks and source documents.",
            "RAG, reasoning, risk, explainability, and agent outputs preserve evidence references where available.",
        ],
        "source_attribution": [
            "Evidence-backed outputs should show source/chunk IDs.",
            "Explainability reports should be used before relying on higher-risk conclusions.",
            "Missing sources should be treated as limitations, not filled with assumptions.",
        ],
        "retention_planning": [
            "Define retention windows for raw files, processed chunks, vector indexes, and generated reports.",
            "Separate temporary test data from approved enterprise data.",
            "Document when and why benchmark or output history may be deleted.",
        ],
        "deletion_planning": [
            "Add future deletion workflows that remove raw, processed, vector, and generated-output references together.",
            "Keep audit records for deletion actions in enterprise mode.",
        ],
        "privacy_limitations": [
            "No enterprise data classification system is implemented yet.",
            "No document-level access control is implemented yet.",
            "Sensitive data should not be committed to git.",
        ],
    }
