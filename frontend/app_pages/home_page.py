"""Home page for the Nexora Streamlit interface."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.layout import page_header
from components.status_cards import metric_row


PIPELINE = "Ingestion -> Processing -> Vector Search -> RAG -> Reasoning -> Risk Scoring -> Explainability"


def _safe_count(path: str, key: str, default: int = 0) -> int:
    ok, payload = api_client.get_json(path, timeout=8)
    if not ok or not isinstance(payload, dict):
        return default
    value = payload.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _quick_counts() -> dict[str, int]:
    rag_ok, rag_history = api_client.get_json("/rag/history", timeout=8)
    rag_count = len(rag_history) if rag_ok and isinstance(rag_history, list) else 0
    return {
        "Ingested documents": _safe_count("/ingestion/status", "ingested_documents"),
        "Processed documents": _safe_count("/processing/status", "processed_document_count"),
        "Indexed chunks": _safe_count("/retrieval/status", "indexed_chunks"),
        "Saved RAG outputs": rag_count,
        "Saved reasoning outputs": _safe_count("/reasoning/status", "saved_reasoning_outputs"),
        "Saved risk outputs": _safe_count("/risk/status", "saved_risk_outputs"),
        "Explainability reports": _safe_count("/explainability/status", "saved_reports"),
    }


def render() -> None:
    page_header(
        "Nexora Financial Intelligence Interface",
        "Provides a unified local dashboard for the full Nexora pipeline.",
        "Does not invent data, replace backend services, or provide financial advice.",
    )

    st.write(
        "Nexora is a local-first financial scenario intelligence platform. The interface below "
        "connects to the existing FastAPI backend and displays real local pipeline outputs."
    )
    st.subheader("Pipeline Overview")
    st.code(PIPELINE)

    backend_ok, backend_payload = api_client.check_backend()
    if backend_ok:
        st.success("Backend is reachable.")
        st.caption(f"Backend URL: {api_client.BACKEND_URL}")
        metric_row(_quick_counts(), columns=4)
    else:
        st.error("Backend is offline.")
        st.caption(backend_payload.get("message", "Run ./scripts/run_backend.sh"))

    st.subheader("System Capability Map")
    capabilities = [
        {"Capability": "Data ingestion", "Backend phase": "Phase 2", "Purpose": "Register SEC, RSS, macro, and local files."},
        {"Capability": "Document processing", "Backend phase": "Phase 3", "Purpose": "Clean raw records and create chunks."},
        {"Capability": "Vector search", "Backend phase": "Phase 4", "Purpose": "Retrieve ranked evidence candidates."},
        {"Capability": "RAG assistant", "Backend phase": "Phase 5", "Purpose": "Answer questions from retrieved evidence."},
        {"Capability": "Scenario reasoning", "Backend phase": "Phase 6", "Purpose": "Build cautious causal chains and exposure analysis."},
        {"Capability": "Risk scoring", "Backend phase": "Phase 7", "Purpose": "Produce evidence-backed 0-100 analytical risk scores."},
        {"Capability": "Explainability", "Backend phase": "Phase 8", "Purpose": "Audit sources, confidence, limitations, and unsupported claims."},
    ]
    st.dataframe(capabilities, use_container_width=True, hide_index=True)
