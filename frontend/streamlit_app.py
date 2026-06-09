"""Nexora Streamlit Financial Intelligence Interface.

Phase 9 organizes the existing Phase 1-8 backend capabilities into a single
analyst-oriented local dashboard. All business logic remains in FastAPI.
"""

from __future__ import annotations

import streamlit as st

from app_pages import (
    agents_page,
    deployment_page,
    explainability_page,
    history_page,
    home_page,
    ingestion_page,
    performance_page,
    processing_page,
    rag_page,
    reasoning_page,
    retrieval_page,
    risk_page,
    system_page,
)
from components import api_client
from components.layout import SAFETY_NOTICE, apply_global_styles


PAGES = {
    "Home": home_page.render,
    "System Status": system_page.render,
    "Data Ingestion": ingestion_page.render,
    "Document Processing": processing_page.render,
    "Vector Search": retrieval_page.render,
    "RAG Assistant": rag_page.render,
    "Scenario Reasoning": reasoning_page.render,
    "Risk Scoring": risk_page.render,
    "Explainability": explainability_page.render,
    "AI Agent Collaboration": agents_page.render,
    "Performance & Scaling": performance_page.render,
    "Deployment Readiness": deployment_page.render,
    "History Explorer": history_page.render,
}


def _sidebar() -> str:
    st.sidebar.title("Nexora")
    st.sidebar.caption("Local Financial Scenario Intelligence")
    backend_ok, backend_payload = api_client.check_backend()
    if backend_ok:
        st.sidebar.success("Backend online")
    else:
        st.sidebar.error("Backend offline")
        st.sidebar.caption(backend_payload.get("message", "Run ./scripts/run_backend.sh"))
    page = st.sidebar.radio("Navigate", options=list(PAGES.keys()), index=0)
    st.sidebar.divider()
    st.sidebar.caption(SAFETY_NOTICE)
    st.sidebar.caption(f"Backend: {api_client.BACKEND_URL}")
    return page


def main() -> None:
    st.set_page_config(page_title="Nexora", page_icon=None, layout="wide")
    apply_global_styles()
    page = _sidebar()
    PAGES[page]()


if __name__ == "__main__":
    main()
