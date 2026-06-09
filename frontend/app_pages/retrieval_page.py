"""Vector search and retrieval page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.evidence_cards import render_sources
from components.layout import backend_error, empty_state, page_header
from components.status_cards import metric_row


def _filters(prefix: str) -> dict[str, str | None]:
    cols = st.columns(5)
    with cols[0]:
        ticker = st.text_input("Ticker", value="", key=f"{prefix}_ticker")
    with cols[1]:
        source = st.text_input("Source type", value="", key=f"{prefix}_source")
    with cols[2]:
        doc_type = st.text_input("Document type", value="", key=f"{prefix}_doc")
    with cols[3]:
        market = st.text_input("Market", value="", key=f"{prefix}_market")
    with cols[4]:
        section = st.text_input("Section hint", value="", key=f"{prefix}_section")
    return {
        "ticker": ticker or None,
        "source_type": source or None,
        "document_type": doc_type or None,
        "market": market or None,
        "section_hint": section or None,
    }


def render() -> None:
    page_header(
        "Vector Search & Retrieval",
        "Builds and searches the local vector index for ranked evidence candidates.",
        "Does not generate final answers; use the RAG Assistant after retrieval.",
    )

    tabs = st.tabs(["Status", "Build Index", "Search", "Index", "Benchmark"])
    with tabs[0]:
        status_ok, status = api_client.get_json("/retrieval/status", timeout=15)
        summary_ok, summary = api_client.get_json("/retrieval/summary", timeout=15)
        if status_ok and isinstance(status, dict):
            metric_row(
                {
                    "Retrieval": status.get("status", "unknown"),
                    "Indexed chunks": status.get("indexed_chunks", 0),
                    "Embedding model": status.get("embedding_model_status", {}).get("default_model", "unknown"),
                    "FAISS": "ready" if status.get("faiss_index_status", {}).get("index_exists") else "missing",
                }
            )
            with st.expander("Retrieval status details", expanded=False):
                st.json(status)
        else:
            backend_error(status)
        if summary_ok:
            st.subheader("Retrieval Summary")
            st.json(summary)

    with tabs[1]:
        cols = st.columns(3)
        with cols[0]:
            store = st.selectbox("Vector store", options=["faiss", "chroma"])
        with cols[1]:
            limit = st.number_input("Chunk limit", min_value=1, max_value=500, value=100, step=1)
        with cols[2]:
            rebuild = st.checkbox("Rebuild selected store", value=False)
        if st.button("Build vector index", key="build_vector"):
            ok, payload = api_client.post_json(
                "/retrieval/index/build",
                {"limit": int(limit), "vector_store": store, "rebuild": rebuild},
                timeout=600,
            )
            st.success(payload.get("status", "Index build completed.")) if ok else st.error(payload.get("message", "Index build failed."))
            st.json(payload)

    with tabs[2]:
        query = st.text_input("Search query", value="financial risk")
        cols = st.columns(2)
        with cols[0]:
            store = st.selectbox("Store", options=["faiss", "chroma"], key="search_store")
        with cols[1]:
            top_k = st.number_input("Top K", min_value=1, max_value=20, value=5, step=1, key="search_top_k")
        filters = _filters("retrieval_search")
        if st.button("Search vectors", key="search_vectors"):
            ok, payload = api_client.post_json(
                "/retrieval/search",
                {"query": query, "top_k": int(top_k), "vector_store": store, "filters": filters},
                timeout=120,
            )
            if ok:
                results = payload.get("results", [])
                st.success(f"Retrieved {len(results)} evidence candidate(s).")
                render_sources(results, title="Ranked Evidence Candidates")
            else:
                backend_error(payload)

    with tabs[3]:
        filters = _filters("retrieval_index")
        status_filter = st.text_input("Status", value="", key="retrieval_index_status")
        ok, records = api_client.get_json("/retrieval/index", params={**filters, "status": status_filter}, timeout=20)
        if ok and isinstance(records, list) and records:
            st.dataframe(records, use_container_width=True, hide_index=True)
        elif ok:
            empty_state("No vector metadata records matched the current filters.", "Build the vector index first if it is empty.")
        else:
            backend_error(records)

    with tabs[4]:
        queries = st.text_area("Benchmark queries, one per line", value="interest rate risk\nrevenue pressure\noil price impact")
        cols = st.columns(2)
        with cols[0]:
            store = st.selectbox("Benchmark store", options=["faiss", "chroma"], key="bench_store")
        with cols[1]:
            top_k = st.number_input("Benchmark Top K", min_value=1, max_value=20, value=5, step=1)
        if st.button("Run retrieval benchmark", key="benchmark_retrieval"):
            query_list = [line.strip() for line in queries.splitlines() if line.strip()]
            ok, payload = api_client.post_json(
                "/retrieval/benchmark",
                {"queries": query_list, "top_k": int(top_k), "vector_store": store},
                timeout=240,
            )
            st.success("Benchmark completed.") if ok else st.error(payload.get("message", "Benchmark failed."))
            st.json(payload)
