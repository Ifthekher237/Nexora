"""Document processing page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.layout import backend_error, empty_state, page_header
from components.status_cards import metric_row


def render() -> None:
    page_header(
        "Document Processing",
        "Converts raw ingested records into cleaned documents and chunk metadata.",
        "Does not create embeddings or perform semantic search; use Vector Search for that.",
    )

    tabs = st.tabs(["Status", "Run Processing", "Index & Chunks"])
    with tabs[0]:
        status_ok, status = api_client.get_json("/processing/status")
        summary_ok, summary = api_client.get_json("/processing/summary")
        if status_ok and isinstance(status, dict):
            metric_row(
                {
                    "Processed documents": status.get("processed_document_count", 0),
                    "Chunks": status.get("chunk_count", 0),
                    "Failed": status.get("failed_document_count", 0),
                    "Status": status.get("status", "unknown"),
                }
            )
        else:
            backend_error(status)
        if summary_ok:
            st.subheader("Processing Summary")
            st.json(summary)

    with tabs[1]:
        st.subheader("Batch Processing")
        cols = st.columns(4)
        with cols[0]:
            limit = st.number_input("Limit", min_value=1, max_value=50, value=5, step=1)
        with cols[1]:
            source = st.text_input("Source type", value="")
        with cols[2]:
            ticker = st.text_input("Ticker", value="")
        with cols[3]:
            doc_type = st.text_input("Document type", value="")
        reprocess = st.checkbox("Reprocess existing documents", value=False)
        if st.button("Run batch processing", key="run_processing"):
            ok, payload = api_client.post_json(
                "/processing/run",
                {
                    "limit": int(limit),
                    "source_type": source or None,
                    "ticker": ticker or None,
                    "document_type": doc_type or None,
                    "reprocess": reprocess,
                },
                timeout=240,
            )
            st.success(payload.get("message", "Processing request finished.")) if ok else st.error(payload.get("message", "Processing failed."))
            st.json(payload)

        st.subheader("Process One Document")
        document_id = st.text_input("Source document ID", value="")
        single_reprocess = st.checkbox("Reprocess selected document", value=False)
        if st.button("Process selected document", key="process_one"):
            if not document_id.strip():
                st.error("Enter a source document ID first.")
            else:
                ok, payload = api_client.post_json(
                    f"/processing/document/{document_id.strip()}?reprocess={str(single_reprocess).lower()}",
                    {},
                    timeout=180,
                )
                st.success(payload.get("message", "Document processed.")) if ok else st.error(payload.get("message", "Processing failed."))
                st.json(payload)

    with tabs[2]:
        cols = st.columns(5)
        with cols[0]:
            source = st.text_input("Source", value="", key="proc_filter_source")
        with cols[1]:
            ticker = st.text_input("Ticker", value="", key="proc_filter_ticker")
        with cols[2]:
            doc_type = st.text_input("Doc type", value="", key="proc_filter_doc")
        with cols[3]:
            status = st.text_input("Status", value="", key="proc_filter_status")
        with cols[4]:
            market = st.text_input("Market", value="", key="proc_filter_market")
        ok, records = api_client.get_json(
            "/processing/documents",
            params={
                "source_type": source,
                "ticker": ticker,
                "document_type": doc_type,
                "processing_status": status,
                "market": market,
            },
        )
        if ok and isinstance(records, list) and records:
            st.dataframe(records, use_container_width=True, hide_index=True)
            processed_ids = [record.get("processed_document_id") for record in records if record.get("processed_document_id")]
            selected = st.selectbox("Processed document ID", options=processed_ids or [""])
            if selected and st.button("Load chunks"):
                chunks_ok, chunks = api_client.get_json(f"/processing/chunks/{selected}", timeout=20)
                if chunks_ok:
                    st.dataframe(chunks, use_container_width=True, hide_index=True)
                else:
                    backend_error(chunks)
        elif ok:
            empty_state("No processed documents matched the current filters.", "Run processing first or clear filters.")
        else:
            backend_error(records)
