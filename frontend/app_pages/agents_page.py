"""AI agent collaboration page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from components import api_client
from components.evidence_cards import render_sources
from components.layout import backend_error, empty_state, page_header, render_bullets
from components.result_cards import render_confidence, render_json, render_limitations, render_validation_warnings
from components.status_cards import metric_row


DEFAULT_SCENARIO = "What financial risks could appear if interest rates rise?"


def _agent_options(available: list[dict[str, Any]]) -> tuple[list[str], dict[str, str]]:
    keys = [str(agent.get("agent_key", "")) for agent in available if agent.get("agent_key")]
    labels = {
        str(agent.get("agent_key")): f"{agent.get('agent_name', agent.get('agent_key'))} ({agent.get('agent_key')})"
        for agent in available
        if agent.get("agent_key")
    }
    return keys, labels


def _filters(prefix: str) -> dict[str, str | None]:
    cols = st.columns(3)
    with cols[0]:
        source_type = st.text_input("Source type filter", value="", key=f"{prefix}_source_type")
    with cols[1]:
        document_type = st.text_input("Document type filter", value="", key=f"{prefix}_document_type")
    with cols[2]:
        section_hint = st.text_input("Section hint filter", value="", key=f"{prefix}_section_hint")
    return {
        "source_type": source_type or None,
        "document_type": document_type or None,
        "section_hint": section_hint or None,
    }


def _request_inputs(prefix: str, scenario_value: str = DEFAULT_SCENARIO) -> dict[str, Any]:
    scenario = st.text_area("Scenario", value=scenario_value, height=100, key=f"{prefix}_scenario")
    cols = st.columns(3)
    with cols[0]:
        company_name = st.text_input("Company name", value="", key=f"{prefix}_company")
    with cols[1]:
        ticker = st.text_input("Ticker", value="", key=f"{prefix}_ticker")
    with cols[2]:
        market = st.text_input("Market", value="", key=f"{prefix}_market")
    cols = st.columns(3)
    with cols[0]:
        top_k = st.number_input("Top K", min_value=1, max_value=12, value=5, key=f"{prefix}_top_k")
    with cols[1]:
        model = st.text_input("Model", value="llama3.1:8b", key=f"{prefix}_model")
    with cols[2]:
        vector_store = st.selectbox("Vector store", options=["faiss", "chroma"], key=f"{prefix}_vector_store")
    filters = _filters(prefix)
    return {
        "scenario": scenario,
        "company_name": company_name or None,
        "ticker": ticker or None,
        "market": market or None,
        "top_k": int(top_k),
        "model": model or None,
        "vector_store": vector_store,
        "filters": filters,
    }


def _render_summary(summary: dict[str, Any]) -> None:
    st.subheader("Collaboration Summary")
    st.write(summary.get("combined_view", ""))
    cols = st.columns(2)
    with cols[0]:
        st.write("Key agreements")
        render_bullets(summary.get("key_agreements", []) or ["None reported."])
        st.write("Evidence gaps")
        render_bullets(summary.get("evidence_gaps", []) or ["None reported."])
    with cols[1]:
        st.write("Key uncertainties")
        render_bullets(summary.get("key_uncertainties", []) or ["None reported."])
        st.write("Recommended next steps")
        render_bullets(summary.get("recommended_next_steps", []) or ["Review cited evidence."])


def _render_agent_output(output: dict[str, Any], *, expanded: bool = False) -> None:
    label = f"{output.get('agent_name', output.get('agent_key', 'Agent'))} - {output.get('status', 'unknown')}"
    with st.expander(label, expanded=expanded):
        st.write(output.get("summary", ""))
        render_confidence(output.get("confidence"))
        findings = output.get("key_findings", [])
        if findings:
            st.write("Key findings")
            render_bullets(findings)
        render_sources(output.get("evidence_used", []), title="Evidence Used")
        render_validation_warnings(output.get("validation_warnings"))
        render_limitations(output.get("limitations"))
        details = output.get("details", {})
        if details:
            render_json("Agent details", details)


def _render_workflow_response(payload: dict[str, Any]) -> None:
    metric_row(
        {
            "Workflow status": payload.get("status", "unknown"),
            "Run ID": payload.get("agent_run_id", ""),
            "Agents run": len(payload.get("agent_outputs", [])),
            "Model": payload.get("model", ""),
        }
    )
    render_confidence(payload.get("overall_confidence"))
    _render_summary(payload.get("collaboration_summary", {}))
    st.subheader("Agent Outputs")
    for index, output in enumerate(payload.get("agent_outputs", [])):
        if isinstance(output, dict):
            _render_agent_output(output, expanded=index == 0)
    render_limitations(payload.get("limitations"))
    render_json("Full agent workflow response", payload)


def _run_workflow_tab(available: list[dict[str, Any]]) -> None:
    request_payload = _request_inputs("workflow")
    keys, labels = _agent_options(available)
    selected_agents = st.multiselect(
        "Agents",
        options=keys,
        default=keys,
        format_func=lambda key: labels.get(key, key),
    )
    if st.button("Run agent workflow", type="primary"):
        request_payload["agents"] = selected_agents
        ok, payload = api_client.post_json("/agents/run-workflow", request_payload, timeout=420)
        if ok:
            st.success(f"Agent workflow status: {payload.get('status', 'unknown')}")
            _render_workflow_response(payload)
        else:
            backend_error(payload)


def _run_single_tab(available: list[dict[str, Any]]) -> None:
    request_payload = _request_inputs("single")
    keys, labels = _agent_options(available)
    if not keys:
        empty_state("No agents are available.", "Check /agents/status.")
        return
    agent_key = st.selectbox("Agent", options=keys, format_func=lambda key: labels.get(key, key))
    if st.button("Run selected agent", type="primary"):
        request_payload["agent_name"] = agent_key
        ok, payload = api_client.post_json("/agents/run-single", request_payload, timeout=240)
        if ok:
            st.success(f"Agent run status: {payload.get('status', 'unknown')}")
            _render_workflow_response(payload)
        else:
            backend_error(payload)


def _history_tab() -> None:
    cols = st.columns(4)
    with cols[0]:
        status_filter = st.text_input("Status", value="", key="agent_hist_status")
    with cols[1]:
        ticker = st.text_input("Ticker", value="", key="agent_hist_ticker")
    with cols[2]:
        agent_name = st.text_input("Agent key", value="", key="agent_hist_agent")
    with cols[3]:
        confidence = st.selectbox("Confidence", options=["", "low", "medium", "high"], key="agent_hist_conf")
    ok, records = api_client.get_json(
        "/agents/history",
        params={
            "status": status_filter,
            "ticker": ticker,
            "agent_name": agent_name,
            "confidence_level": confidence,
        },
        timeout=20,
    )
    if ok and isinstance(records, list) and records:
        st.dataframe(records, use_container_width=True, hide_index=True)
        ids = [record.get("agent_run_id") for record in records if record.get("agent_run_id")]
        selected = st.selectbox("Saved agent run", options=ids or [""])
        if selected and st.button("Load agent run"):
            detail_ok, detail = api_client.get_json(f"/agents/history/{selected}", timeout=30)
            if detail_ok and isinstance(detail, dict):
                _render_workflow_response(detail)
            else:
                backend_error(detail)
    elif ok:
        empty_state("No saved agent runs matched the current filters.", "Run an agent workflow first.")
    else:
        backend_error(records)


def render() -> None:
    page_header(
        "AI Agent Collaboration",
        "Coordinates local evidence-grounded agents for macro, company, sector, news, and risk propagation analysis.",
        "Does not browse the web, fake agent output, provide investment advice, or predict stock prices.",
        safety=True,
    )

    status_ok, status = api_client.get_json("/agents/status", timeout=20)
    status_payload = status if isinstance(status, dict) else {}
    if status_ok:
        metric_row(
            {
                "Agents": status_payload.get("status", "unknown"),
                "Enabled agents": len(status_payload.get("enabled_agents", [])),
                "RAG": "available" if status_payload.get("rag_available") else "unavailable",
                "Saved runs": status_payload.get("saved_agent_runs", 0),
            }
        )
    else:
        backend_error(status)

    available_ok, available_payload = api_client.get_json("/agents/available", timeout=20)
    available = available_payload if available_ok and isinstance(available_payload, list) else []
    if available:
        with st.expander("Available agents", expanded=False):
            st.dataframe(available, use_container_width=True, hide_index=True)
    elif not available_ok:
        backend_error(available_payload)

    tabs = st.tabs(["Run Workflow", "Single Agent", "History"])
    with tabs[0]:
        _run_workflow_tab(available)
    with tabs[1]:
        _run_single_tab(available)
    with tabs[2]:
        _history_tab()
