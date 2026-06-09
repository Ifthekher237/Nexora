"""Risk scoring page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.charts import bar_chart_from_mapping
from components.layout import backend_error, empty_state, page_header
from components.result_cards import (
    render_confidence,
    render_json,
    render_limitations,
    render_score_bar,
    render_simple_table,
    render_validation_warnings,
)
from components.status_cards import metric_row


def render() -> None:
    page_header(
        "Risk Scoring",
        "Generates evidence-backed analytical 0-100 risk scores from Phase 6 reasoning.",
        "Does not predict prices, certify outcomes, or provide investment advice.",
        safety=True,
    )
    st.info("Risk score and confidence are different. A higher risk estimate can still have low evidence confidence.")

    status_ok, status = api_client.get_json("/risk/status", timeout=12)
    status_payload = status if isinstance(status, dict) else {}
    if status_ok:
        metric_row(
            {
                "Risk engine": status_payload.get("status", "unknown"),
                "Reasoning": "available" if status_payload.get("reasoning_available") else "unavailable",
                "Retrieval": "available" if status_payload.get("retrieval_available") else "unavailable",
                "Saved scores": status_payload.get("saved_risk_outputs", 0),
            }
        )
    else:
        backend_error(status)

    tabs = st.tabs(["Score Scenario", "History"])
    with tabs[0]:
        scenario = st.text_area("Scenario", value="What financial risks could appear if interest rates rise?", height=100)
        cols = st.columns(3)
        with cols[0]:
            company = st.text_input("Company name", value="")
        with cols[1]:
            ticker = st.text_input("Ticker", value="")
        with cols[2]:
            market = st.text_input("Market", value="")
        cols = st.columns(3)
        with cols[0]:
            model = st.text_input("Model", value="llama3.1:8b")
        with cols[1]:
            top_k = st.number_input("Top K", min_value=1, max_value=12, value=5)
        with cols[2]:
            vector_store = st.selectbox("Vector store", options=["faiss", "chroma"])
        fcols = st.columns(3)
        with fcols[0]:
            source_type = st.text_input("Source type filter", value="")
        with fcols[1]:
            document_type = st.text_input("Document type filter", value="")
        with fcols[2]:
            section_hint = st.text_input("Section hint filter", value="")

        if st.button("Run risk scoring", type="primary"):
            ok, payload = api_client.post_json(
                "/risk/score-scenario",
                {
                    "scenario": scenario,
                    "company_name": company or None,
                    "ticker": ticker or None,
                    "market": market or None,
                    "top_k": int(top_k),
                    "model": model or None,
                    "vector_store": vector_store,
                    "filters": {
                        "source_type": source_type or None,
                        "document_type": document_type or None,
                        "section_hint": section_hint or None,
                    },
                },
                timeout=420,
            )
            if ok:
                st.success(f"Risk scoring status: {payload.get('status', 'unknown')}")
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Overall Risk Score", payload.get("overall_risk_score", 0))
                    render_score_bar("Risk score", payload.get("overall_risk_score", 0))
                with cols[1]:
                    st.metric("Risk Level", payload.get("overall_risk_level", "unknown"))
                with cols[2]:
                    render_confidence(payload.get("confidence"))
                if payload.get("score_breakdown"):
                    bar_chart_from_mapping(payload.get("score_breakdown", {}), "Score Breakdown")
                    render_json("Score breakdown JSON", payload.get("score_breakdown", {}))
                render_simple_table(payload.get("risk_drivers", []), "No risk drivers were returned.")
                render_json("Evidence summary", payload.get("evidence_summary", {}), expanded=True)
                st.subheader("Explanation")
                st.write(payload.get("explanation", ""))
                render_validation_warnings(payload.get("validation_warnings"))
                render_limitations(payload.get("limitations"))
                render_json("Full risk response", payload)
            else:
                backend_error(payload)

    with tabs[1]:
        cols = st.columns(6)
        with cols[0]:
            ticker = st.text_input("Ticker", value="", key="risk_hist_ticker")
        with cols[1]:
            market = st.text_input("Market", value="", key="risk_hist_market")
        with cols[2]:
            scenario_type = st.text_input("Scenario type", value="", key="risk_hist_type")
        with cols[3]:
            risk_level = st.text_input("Risk level", value="", key="risk_hist_level")
        with cols[4]:
            confidence = st.selectbox("Confidence", options=["", "low", "medium", "high"], key="risk_hist_conf")
        with cols[5]:
            status_filter = st.text_input("Status", value="", key="risk_hist_status")
        ok, records = api_client.get_json(
            "/risk/history",
            params={
                "ticker": ticker,
                "market": market,
                "scenario_type": scenario_type,
                "risk_level": risk_level,
                "confidence_level": confidence,
                "status": status_filter,
            },
        )
        if ok and isinstance(records, list) and records:
            st.dataframe(records, use_container_width=True, hide_index=True)
            ids = [record.get("risk_id") for record in records if record.get("risk_id")]
            selected = st.selectbox("Saved risk score", options=ids or [""])
            if selected and st.button("Load risk score"):
                detail_ok, detail = api_client.get_json(f"/risk/history/{selected}", timeout=20)
                if detail_ok and isinstance(detail, dict):
                    st.metric("Overall Risk Score", detail.get("overall_risk_score", 0))
                    st.write(detail.get("explanation", ""))
                    render_confidence(detail.get("confidence"))
                    render_json("Saved risk JSON", detail)
                else:
                    backend_error(detail)
        elif ok:
            empty_state("No saved risk outputs matched the current filters.", "Run risk scoring first.")
        else:
            backend_error(records)
