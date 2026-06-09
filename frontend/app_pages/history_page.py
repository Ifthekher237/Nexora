"""Unified history explorer page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.evidence_cards import render_sources
from components.layout import backend_error, empty_state, page_header
from components.result_cards import render_confidence, render_json, render_limitations


HISTORY_TYPES = {
    "RAG": {
        "list_path": "/rag/history",
        "detail_path": "/rag/history/{id}",
        "id_key": "response_id",
        "filters": ["status", "confidence_level", "ticker", "model"],
    },
    "Reasoning": {
        "list_path": "/reasoning/history",
        "detail_path": "/reasoning/history/{id}",
        "id_key": "reasoning_id",
        "filters": ["status", "confidence_level", "ticker", "market", "scenario_type"],
    },
    "Risk": {
        "list_path": "/risk/history",
        "detail_path": "/risk/history/{id}",
        "id_key": "risk_id",
        "filters": ["status", "confidence_level", "ticker", "market", "scenario_type", "risk_level"],
    },
    "Explainability": {
        "list_path": "/explainability/history",
        "detail_path": "/explainability/history/{id}",
        "id_key": "explainability_id",
        "filters": ["status", "target_type", "coverage_level"],
    },
}


def _filters(history_type: str) -> dict[str, str | None]:
    config = HISTORY_TYPES[history_type]
    values: dict[str, str | None] = {}
    cols = st.columns(min(4, len(config["filters"])))
    for index, name in enumerate(config["filters"]):
        with cols[index % len(cols)]:
            if name in {"confidence_level", "coverage_level"}:
                options = ["", "low", "medium", "high"]
                values[name] = st.selectbox(name.replace("_", " ").title(), options=options, key=f"hist_{history_type}_{name}") or None
            elif name == "target_type":
                values[name] = st.selectbox("Target Type", options=["", "risk", "reasoning", "rag"], key=f"hist_{history_type}_{name}") or None
            else:
                values[name] = st.text_input(name.replace("_", " ").title(), value="", key=f"hist_{history_type}_{name}") or None
    return values


def _render_detail(history_type: str, detail: dict[str, object]) -> None:
    if history_type == "RAG":
        st.markdown(detail.get("answer", ""))
        render_confidence(detail.get("confidence"))
        render_sources(detail.get("sources", []), title="Sources")
    elif history_type == "Reasoning":
        st.markdown(detail.get("direct_answer", ""))
        render_confidence(detail.get("confidence"))
        if detail.get("causal_chain"):
            st.dataframe(detail.get("causal_chain", []), use_container_width=True, hide_index=True)
        render_sources(detail.get("evidence_map", []), title="Evidence Map")
    elif history_type == "Risk":
        st.metric("Overall Risk Score", detail.get("overall_risk_score", 0))
        st.write(detail.get("explanation", ""))
        render_confidence(detail.get("confidence"))
        render_json("Score breakdown", detail.get("score_breakdown", {}), expanded=True)
    else:
        st.metric("Explainability Score", detail.get("explainability_score", 0.0))
        render_sources(detail.get("expanded_citations", []), title="Expanded Citations")
        if detail.get("unsupported_claims"):
            st.dataframe(detail.get("unsupported_claims", []), use_container_width=True, hide_index=True)
    render_limitations(detail.get("limitations"))
    render_json("Full record JSON", detail)


def render() -> None:
    page_header(
        "History Explorer",
        "Loads saved RAG, reasoning, risk, and explainability records from local history endpoints.",
        "Does not create new outputs; use the workflow pages for generation.",
    )

    history_type = st.selectbox("History type", options=list(HISTORY_TYPES.keys()))
    filters = _filters(history_type)
    config = HISTORY_TYPES[history_type]
    ok, records = api_client.get_json(config["list_path"], params=filters, timeout=20)
    if ok and isinstance(records, list) and records:
        st.dataframe(records, use_container_width=True, hide_index=True)
        ids = [record.get(config["id_key"]) for record in records if record.get(config["id_key"])]
        selected = st.selectbox("Record ID", options=ids or [""])
        if selected and st.button("Inspect selected record"):
            detail_ok, detail = api_client.get_json(config["detail_path"].format(id=selected), timeout=20)
            if detail_ok and isinstance(detail, dict):
                _render_detail(history_type, detail)
            else:
                backend_error(detail)
    elif ok:
        empty_state(f"No {history_type.lower()} history records matched the current filters.")
    else:
        backend_error(records)
