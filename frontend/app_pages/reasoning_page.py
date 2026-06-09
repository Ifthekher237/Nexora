"""Financial scenario reasoning page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.evidence_cards import render_sources
from components.layout import backend_error, empty_state, page_header
from components.result_cards import render_confidence, render_json, render_limitations, render_validation_warnings
from components.status_cards import metric_row


def _reasoning_filters(prefix: str) -> dict[str, str | None]:
    cols = st.columns(3)
    with cols[0]:
        source_type = st.text_input("Source type", value="", key=f"{prefix}_source")
    with cols[1]:
        document_type = st.text_input("Document type", value="", key=f"{prefix}_doc")
    with cols[2]:
        section_hint = st.text_input("Section hint", value="", key=f"{prefix}_section")
    return {"source_type": source_type or None, "document_type": document_type or None, "section_hint": section_hint or None}


def _models(status: dict[str, object]) -> list[str]:
    default = str(status.get("default_model") or "llama3.1:8b")
    options = [model for model in status.get("installed_models", []) if model]
    if default not in options:
        options.insert(0, default)
    fallback = status.get("fallback_model")
    if fallback and fallback not in options:
        options.append(str(fallback))
    return options or [default]


def render() -> None:
    page_header(
        "Scenario Reasoning",
        "Runs evidence-grounded scenario analysis with causal chains, exposure analysis, and evidence maps.",
        "Does not produce final risk scores or investment recommendations.",
        safety=True,
    )

    status_ok, status = api_client.get_json("/reasoning/status", timeout=12)
    status_payload = status if isinstance(status, dict) else {}
    if status_ok:
        metric_row(
            {
                "Reasoning": status_payload.get("status", "unknown"),
                "RAG": "available" if status_payload.get("rag_available") else "unavailable",
                "Retrieval": "available" if status_payload.get("retrieval_available") else "unavailable",
                "Saved outputs": status_payload.get("saved_reasoning_outputs", 0),
            }
        )
    else:
        backend_error(status)

    tabs = st.tabs(["Analyze Scenario", "Causal Chain", "Evidence Map", "History"])
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
            model = st.selectbox("Model", options=_models(status_payload), key="reasoning_model")
        with cols[1]:
            top_k = st.number_input("Top K", min_value=1, max_value=int(status_payload.get("max_top_k", 12) or 12), value=5)
        with cols[2]:
            vector_store = st.selectbox("Vector store", options=["faiss", "chroma"], key="reasoning_store")
        filters = _reasoning_filters("reasoning")
        if st.button("Run scenario analysis", type="primary"):
            ok, payload = api_client.post_json(
                "/reasoning/analyze-scenario",
                {
                    "scenario": scenario,
                    "company_name": company or None,
                    "ticker": ticker or None,
                    "market": market or None,
                    "top_k": int(top_k),
                    "model": model,
                    "vector_store": vector_store,
                    "filters": filters,
                },
                timeout=360,
            )
            if ok:
                st.success(f"Reasoning status: {payload.get('status', 'unknown')}")
                st.markdown(payload.get("direct_answer", ""))
                render_confidence(payload.get("confidence"))
                if payload.get("causal_chain"):
                    st.subheader("Causal Chain")
                    st.dataframe(payload.get("causal_chain", []), use_container_width=True, hide_index=True)
                if payload.get("financial_exposure_analysis"):
                    render_json("Financial exposure analysis", payload.get("financial_exposure_analysis"), expanded=True)
                render_sources(payload.get("evidence_map", []), title="Evidence Map")
                render_validation_warnings(payload.get("validation_warnings"))
                render_limitations(payload.get("limitations"))
                render_json("Full reasoning response", payload)
            else:
                backend_error(payload)

    with tabs[1]:
        scenario = st.text_area("Scenario for causal chain", value="What happens if oil prices rise by 25%?", height=90)
        if st.button("Generate causal chain"):
            ok, payload = api_client.post_json("/reasoning/causal-chain", {"scenario": scenario, "top_k": 1, "filters": {}}, timeout=60)
            if ok:
                st.success(f"Scenario type: {payload.get('scenario_type', 'unknown')}")
                st.dataframe(payload.get("causal_chain", []), use_container_width=True, hide_index=True)
            else:
                backend_error(payload)

    with tabs[2]:
        scenario = st.text_area("Scenario for evidence map", value="What financial risks could appear if interest rates rise?", height=90)
        top_k = st.number_input("Top K", min_value=1, max_value=12, value=5, key="map_top_k")
        filters = _reasoning_filters("map")
        if st.button("Build evidence map"):
            ok, payload = api_client.post_json(
                "/reasoning/evidence-map",
                {"scenario": scenario, "top_k": int(top_k), "filters": filters},
                timeout=120,
            )
            if ok:
                render_json("Retrieval summary", payload.get("retrieval_summary", {}), expanded=True)
                render_sources(payload.get("evidence_map", []), title="Evidence Map")
                render_limitations(payload.get("limitations"))
            else:
                backend_error(payload)

    with tabs[3]:
        cols = st.columns(5)
        with cols[0]:
            ticker = st.text_input("Ticker", value="", key="reason_hist_ticker")
        with cols[1]:
            market = st.text_input("Market", value="", key="reason_hist_market")
        with cols[2]:
            scenario_type = st.text_input("Scenario type", value="", key="reason_hist_type")
        with cols[3]:
            confidence = st.selectbox("Confidence", options=["", "low", "medium", "high"], key="reason_hist_conf")
        with cols[4]:
            status_filter = st.text_input("Status", value="", key="reason_hist_status")
        ok, records = api_client.get_json(
            "/reasoning/history",
            params={
                "ticker": ticker,
                "market": market,
                "scenario_type": scenario_type,
                "confidence_level": confidence,
                "status": status_filter,
            },
        )
        if ok and isinstance(records, list) and records:
            st.dataframe(records, use_container_width=True, hide_index=True)
            ids = [record.get("reasoning_id") for record in records if record.get("reasoning_id")]
            selected = st.selectbox("Saved reasoning output", options=ids or [""])
            if selected and st.button("Load reasoning output"):
                detail_ok, detail = api_client.get_json(f"/reasoning/history/{selected}", timeout=20)
                if detail_ok and isinstance(detail, dict):
                    st.markdown(detail.get("direct_answer", ""))
                    render_confidence(detail.get("confidence"))
                    render_sources(detail.get("evidence_map", []), title="Saved Evidence Map")
                    render_json("Saved reasoning JSON", detail)
                else:
                    backend_error(detail)
        elif ok:
            empty_state("No saved reasoning outputs matched the current filters.", "Run scenario analysis first.")
        else:
            backend_error(records)
