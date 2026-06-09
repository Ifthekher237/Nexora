"""Evidence-grounded RAG assistant page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.evidence_cards import render_sources
from components.layout import backend_error, empty_state, page_header
from components.result_cards import render_confidence, render_json, render_limitations
from components.status_cards import metric_row


def _rag_filters(prefix: str) -> dict[str, str | None]:
    cols = st.columns(5)
    with cols[0]:
        ticker = st.text_input("Ticker", value="", key=f"{prefix}_ticker")
    with cols[1]:
        source_type = st.text_input("Source type", value="", key=f"{prefix}_source")
    with cols[2]:
        document_type = st.text_input("Document type", value="", key=f"{prefix}_doc")
    with cols[3]:
        market = st.text_input("Market", value="", key=f"{prefix}_market")
    with cols[4]:
        section_hint = st.text_input("Section hint", value="", key=f"{prefix}_section")
    return {
        "ticker": ticker or None,
        "source_type": source_type or None,
        "document_type": document_type or None,
        "market": market or None,
        "section_hint": section_hint or None,
    }


def _model_options(status: dict[str, object]) -> list[str]:
    default = str(status.get("default_model") or "llama3.1:8b")
    models = [model for model in status.get("installed_models", []) if model]
    if default not in models:
        models.insert(0, default)
    fallback = status.get("fallback_model")
    if fallback and fallback not in models:
        models.append(str(fallback))
    return models or [default]


def render() -> None:
    page_header(
        "Financial RAG Assistant",
        "Answers financial questions using retrieved local evidence and saved source citations.",
        "Does not provide investment advice, buy/sell calls, or stock price predictions.",
        safety=True,
    )

    status_ok, status = api_client.get_json("/rag/status", timeout=12)
    status_payload = status if isinstance(status, dict) else {}
    if status_ok:
        metric_row(
            {
                "RAG": status_payload.get("status", "unknown"),
                "Default model": status_payload.get("default_model", "unknown"),
                "Min retrieval score": status_payload.get("min_retrieval_score", "unknown"),
                "Ollama": "running" if status_payload.get("ollama_running") else "offline",
            }
        )
    else:
        backend_error(status)

    tabs = st.tabs(["Ask", "Evidence Only", "History"])
    with tabs[0]:
        question = st.text_area("Question", value="What financial risks are mentioned in the available documents?", height=100)
        cols = st.columns(3)
        with cols[0]:
            model = st.selectbox("Model", options=_model_options(status_payload))
        with cols[1]:
            top_k = st.number_input(
                "Top K",
                min_value=1,
                max_value=int(status_payload.get("max_top_k", 10) or 10),
                value=min(int(status_payload.get("default_top_k", 5) or 5), 10),
                step=1,
            )
        with cols[2]:
            vector_store = st.selectbox("Vector store", options=["faiss", "chroma"])
        filters = _rag_filters("rag_ask")

        if st.button("Ask RAG", type="primary"):
            if not question.strip():
                st.error("Enter a question first.")
            else:
                ok, payload = api_client.post_json(
                    "/rag/ask",
                    {
                        "question": question,
                        "top_k": int(top_k),
                        "model": model,
                        "vector_store": vector_store,
                        "filters": filters,
                    },
                    timeout=300,
                )
                if ok:
                    st.success(f"RAG status: {payload.get('status', 'unknown')}")
                    st.markdown(payload.get("answer", ""))
                    render_confidence(payload.get("confidence"))
                    render_sources(payload.get("sources", []), title="Sources Used")
                    render_limitations(payload.get("limitations"))
                    render_json("Full RAG response", payload)
                else:
                    backend_error(payload)

    with tabs[1]:
        question = st.text_area("Evidence question", value="What financial risks are mentioned in the available documents?", height=90)
        cols = st.columns(3)
        with cols[0]:
            top_k = st.number_input("Top K", min_value=1, max_value=20, value=5, step=1, key="rag_evidence_top_k")
        with cols[1]:
            vector_store = st.selectbox("Vector store", options=["faiss", "chroma"], key="rag_evidence_store")
        filters = _rag_filters("rag_evidence")
        if st.button("Run evidence-only retrieval"):
            ok, payload = api_client.post_json(
                "/rag/evidence-only",
                {"question": question, "top_k": int(top_k), "vector_store": vector_store, "filters": filters},
                timeout=120,
            )
            if ok:
                st.success(f"Evidence status: {payload.get('status', 'unknown')}")
                render_json("Retrieval summary", payload.get("retrieval_summary", {}), expanded=True)
                st.text_area("Evidence context", value=payload.get("evidence_context", ""), height=260, disabled=True)
                render_sources(payload.get("sources", []), title="Evidence Candidates")
                render_limitations(payload.get("limitations"))
            else:
                backend_error(payload)

    with tabs[2]:
        cols = st.columns(4)
        with cols[0]:
            ticker = st.text_input("Ticker", value="", key="rag_hist_ticker")
        with cols[1]:
            model_filter = st.text_input("Model", value="", key="rag_hist_model")
        with cols[2]:
            confidence = st.selectbox("Confidence", options=["", "low", "medium", "high"], key="rag_hist_conf")
        with cols[3]:
            status_filter = st.text_input("Status", value="", key="rag_hist_status")
        ok, records = api_client.get_json(
            "/rag/history",
            params={"ticker": ticker, "model": model_filter, "confidence_level": confidence, "status": status_filter},
        )
        if ok and isinstance(records, list) and records:
            st.dataframe(records, use_container_width=True, hide_index=True)
            response_ids = [record.get("response_id") for record in records if record.get("response_id")]
            selected = st.selectbox("Saved RAG response", options=response_ids or [""])
            if selected and st.button("Load RAG response"):
                detail_ok, detail = api_client.get_json(f"/rag/history/{selected}", timeout=20)
                if detail_ok and isinstance(detail, dict):
                    st.markdown(detail.get("answer", ""))
                    render_confidence(detail.get("confidence"))
                    render_sources(detail.get("sources", []), title="Saved Sources")
                    render_json("Saved RAG JSON", detail)
                else:
                    backend_error(detail)
        elif ok:
            empty_state("No saved RAG responses matched the current filters.", "Ask a RAG question first.")
        else:
            backend_error(records)
