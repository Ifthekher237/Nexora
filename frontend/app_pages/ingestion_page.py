"""Financial data ingestion page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.layout import backend_error, empty_state, page_header


def _show_result(ok: bool, payload: dict[str, object]) -> None:
    if ok:
        st.success(payload.get("message", payload.get("status", "Request completed.")))
    else:
        st.error(payload.get("message", "Request failed."))
    st.json(payload)


def render() -> None:
    page_header(
        "Financial Data Ingestion",
        "Registers real SEC, RSS, macro, and local-file sources for the local knowledge base.",
        "Does not parse documents or generate embeddings; those happen in later pages.",
    )

    tabs = st.tabs(["Status", "Run Ingestion", "Index"])

    with tabs[0]:
        status_ok, status = api_client.get_json("/ingestion/status")
        summary_ok, summary = api_client.get_json("/ingestion/summary")
        sources_ok, sources = api_client.get_json("/ingestion/sources")
        if status_ok and isinstance(status, dict):
            st.metric("Ingested documents", status.get("ingested_documents", 0))
            with st.expander("Storage paths", expanded=False):
                st.json(status.get("storage_paths", {}))
        else:
            backend_error(status)
        if summary_ok:
            st.subheader("Ingestion Summary")
            st.json(summary)
        if sources_ok:
            with st.expander("Configured Sources", expanded=False):
                st.json(sources)

    with tabs[1]:
        sec_tab, rss_tab, local_tab, macro_tab = st.tabs(["SEC", "RSS", "Local File", "Macro CSV"])
        with sec_tab:
            ticker = st.text_input("Ticker", value="AAPL", key="sec_ticker")
            company = st.text_input("Company name", value="Apple Inc.", key="sec_company")
            limit = st.number_input("Limit", min_value=1, max_value=10, value=3, step=1, key="sec_limit")
            if st.button("Run SEC ingestion", key="run_sec"):
                ok, payload = api_client.post_json(
                    "/ingestion/sec/company",
                    {"ticker": ticker, "company_name": company, "limit": int(limit)},
                    timeout=120,
                )
                _show_result(ok, payload)

        with rss_tab:
            source_ok, source_payload = api_client.get_json("/ingestion/sources")
            feed_names = []
            if source_ok and isinstance(source_payload, dict):
                feed_names = [
                    feed.get("name")
                    for feed in source_payload.get("sources", {}).get("rss", {}).get("feeds", [])
                    if feed.get("name")
                ]
            feed = st.selectbox("Configured feed", options=feed_names or ["Yahoo Finance"], key="rss_feed")
            limit = st.number_input("Items", min_value=1, max_value=10, value=5, step=1, key="rss_limit")
            if st.button("Run RSS ingestion", key="run_rss"):
                ok, payload = api_client.post_json("/ingestion/rss", {"feed_name": feed, "limit": int(limit)}, timeout=120)
                _show_result(ok, payload)

        with local_tab:
            file_path = st.text_input("Local file path", value="data/external/sample_annual_report.pdf")
            cols = st.columns(3)
            with cols[0]:
                source_type = st.selectbox("Source type", options=["local_uploads", "asx"])
                ticker = st.text_input("Ticker", value="QAN", key="local_ticker")
            with cols[1]:
                company = st.text_input("Company", value="Qantas Airways", key="local_company")
                market = st.text_input("Market", value="ASX", key="local_market")
            with cols[2]:
                doc_type = st.text_input("Document type", value="annual_report")
                period = st.text_input("Period", value="2024")
            if st.button("Register local file", key="register_local"):
                ok, payload = api_client.post_json(
                    "/ingestion/local-file",
                    {
                        "file_path": file_path,
                        "source_type": source_type,
                        "company_name": company,
                        "ticker": ticker,
                        "market": market,
                        "document_type": doc_type,
                        "period": period,
                    },
                    timeout=120,
                )
                _show_result(ok, payload)

        with macro_tab:
            file_path = st.text_input("Macro CSV path", value="data/external/macro.csv")
            source_name = st.text_input("Source name", value="Manual macro dataset")
            if st.button("Register macro CSV", key="register_macro"):
                ok, payload = api_client.post_json(
                    "/ingestion/macro/local-csv",
                    {"file_path": file_path, "source_name": source_name},
                    timeout=120,
                )
                _show_result(ok, payload)

    with tabs[2]:
        cols = st.columns(4)
        with cols[0]:
            source_type = st.text_input("Source type filter", value="")
        with cols[1]:
            ticker = st.text_input("Ticker filter", value="")
        with cols[2]:
            doc_type = st.text_input("Document type filter", value="")
        with cols[3]:
            status = st.text_input("Status filter", value="")
        ok, records = api_client.get_json(
            "/ingestion/documents",
            params={"source_type": source_type, "ticker": ticker, "document_type": doc_type, "status": status},
        )
        if ok and isinstance(records, list) and records:
            st.dataframe(records, use_container_width=True, hide_index=True)
        elif ok:
            empty_state("No ingestion records matched the current filters.", "Run ingestion or clear filters.")
        else:
            backend_error(records)
