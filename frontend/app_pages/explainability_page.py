"""Explainability and evidence page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.evidence_cards import render_evidence_ranking, render_sources
from components.layout import backend_error, empty_state, page_header
from components.result_cards import render_json, render_limitations, render_score_bar
from components.status_cards import metric_row


def _render_report(report: dict[str, object]) -> None:
    cols = st.columns(3)
    with cols[0]:
        st.metric("Explainability Score", report.get("explainability_score", 0.0))
        render_score_bar("Explainability score", float(report.get("explainability_score", 0.0)) * 100)
    coverage = report.get("evidence_coverage", {}) if isinstance(report.get("evidence_coverage"), dict) else {}
    with cols[1]:
        st.metric("Coverage", coverage.get("level", "unknown"))
    with cols[2]:
        st.metric("Coverage Score", coverage.get("score", 0.0))

    st.info(report.get("recommendation", "Use this audit cautiously."))
    if coverage:
        render_json("Evidence coverage", coverage, expanded=True)
    confidence = report.get("confidence_explanation", {})
    if isinstance(confidence, dict):
        with st.expander("Confidence explanation", expanded=True):
            st.write(confidence.get("explanation", ""))
            for factor in confidence.get("factors", []):
                st.write(f"- {factor}")
            st.caption(confidence.get("distinction", ""))

    render_sources(report.get("expanded_citations", []), title="Expanded Citations")
    render_evidence_ranking(report.get("evidence_ranking", []))
    trace = report.get("reasoning_trace", {})
    if isinstance(trace, dict) and trace.get("causal_chain_steps"):
        st.subheader("Reasoning Trace")
        st.dataframe(trace.get("causal_chain_steps", []), use_container_width=True, hide_index=True)
    render_json("Reasoning trace details", trace)
    if report.get("document_attribution"):
        st.subheader("Document Attribution")
        st.dataframe(report.get("document_attribution", []), use_container_width=True, hide_index=True)
    if report.get("unsupported_claims"):
        st.subheader("Unsupported Claim Warnings")
        st.dataframe(report.get("unsupported_claims", []), use_container_width=True, hide_index=True)
    else:
        st.success("No unsupported-claim warnings were returned.")
    render_limitations(report.get("limitations"))
    render_json("Full explainability report", report)


def render() -> None:
    page_header(
        "Explainability & Evidence",
        "Audits saved RAG, reasoning, and risk outputs for evidence support and trustworthiness.",
        "Does not generate new financial recommendations or invent citations.",
        safety=True,
    )
    st.write("This page helps answer: Why did Nexora produce this result? Can I trust the evidence? What is missing?")

    status_ok, status = api_client.get_json("/explainability/status", timeout=12)
    status_payload = status if isinstance(status, dict) else {}
    if status_ok:
        metric_row(
            {
                "Explainability": status_payload.get("status", "unknown"),
                "Saved reports": status_payload.get("saved_reports", 0),
                "RAG history": "available" if status_payload.get("rag_history_available") else "missing",
                "Risk history": "available" if status_payload.get("risk_history_available") else "missing",
            }
        )
    else:
        backend_error(status)

    tabs = st.tabs(["Explain Output", "History"])
    with tabs[0]:
        target_type = st.selectbox("Target type", options=["risk", "reasoning", "rag"])
        target_id = st.text_input("Specific output ID", value="")
        cols = st.columns(2)
        with cols[0]:
            if st.button("Explain latest output", type="primary"):
                ok, payload = api_client.post_json("/explainability/explain-latest", {"target_type": target_type}, timeout=120)
                if ok:
                    st.success(f"Report saved for {payload.get('target_id')}.")
                    _render_report(payload)
                else:
                    backend_error(payload)
        with cols[1]:
            if st.button("Explain specific ID"):
                if not target_id.strip():
                    st.error("Enter a saved output ID first.")
                else:
                    path = {
                        "risk": f"/explainability/explain-risk/{target_id.strip()}",
                        "reasoning": f"/explainability/explain-reasoning/{target_id.strip()}",
                        "rag": f"/explainability/explain-rag/{target_id.strip()}",
                    }[target_type]
                    ok, payload = api_client.post_json(path, {}, timeout=120)
                    if ok:
                        st.success(f"Report saved for {payload.get('target_id')}.")
                        _render_report(payload)
                    else:
                        backend_error(payload)

    with tabs[1]:
        cols = st.columns(3)
        with cols[0]:
            target_filter = st.selectbox("Target type filter", options=["", "risk", "reasoning", "rag"])
        with cols[1]:
            status_filter = st.text_input("Status", value="")
        with cols[2]:
            coverage = st.selectbox("Coverage", options=["", "low", "medium", "high"])
        ok, records = api_client.get_json(
            "/explainability/history",
            params={"target_type": target_filter, "status": status_filter, "coverage_level": coverage},
        )
        if ok and isinstance(records, list) and records:
            st.dataframe(records, use_container_width=True, hide_index=True)
            ids = [record.get("explainability_id") for record in records if record.get("explainability_id")]
            selected = st.selectbox("Explainability report", options=ids or [""])
            if selected and st.button("Load explainability report"):
                detail_ok, detail = api_client.get_json(f"/explainability/history/{selected}", timeout=20)
                if detail_ok and isinstance(detail, dict):
                    _render_report(detail)
                else:
                    backend_error(detail)
        elif ok:
            empty_state("No explainability reports matched the current filters.", "Explain a saved output first.")
        else:
            backend_error(records)
