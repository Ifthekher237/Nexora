"""Deployment readiness page for Phase 12."""

from __future__ import annotations

from typing import Any

import streamlit as st

from components import api_client
from components.layout import backend_error, empty_state, page_header, render_bullets
from components.result_cards import render_json
from components.status_cards import metric_row


NOTICE = "Nexora is local-first. This phase prepares enterprise deployment architecture but does not deploy to cloud."


@st.cache_data(ttl=20)
def _get(path: str) -> tuple[bool, dict[str, Any] | list[dict[str, Any]]]:
    return api_client.get_json(path, timeout=30)


@st.cache_data(ttl=20)
def _history(report_type: str = "") -> tuple[bool, dict[str, Any] | list[dict[str, Any]]]:
    return api_client.get_json("/deployment/reports", params={"report_type": report_type}, timeout=30)


def _clear_cache() -> None:
    _get.clear()
    _history.clear()


def _render_readiness(payload: dict[str, Any]) -> None:
    metric_row(
        {
            "Score": payload.get("readiness_score", 0),
            "Level": payload.get("readiness_level", "unknown"),
            "Status": payload.get("status", "unknown"),
            "Checks": (payload.get("summary") or {}).get("total_checks", 0),
        }
    )
    checks = payload.get("checks", [])
    if isinstance(checks, list) and checks:
        st.dataframe(checks, use_container_width=True, hide_index=True)
    render_json("Full readiness result", payload)


def _render_plan(title: str, payload: dict[str, Any]) -> None:
    st.subheader(title)
    render_json(title, payload, expanded=True)


def _reports_tab() -> None:
    report_type = st.selectbox("Report type", options=["", "deployment_readiness", "final_project_report"])
    ok, reports = _history(report_type)
    if ok and isinstance(reports, list) and reports:
        st.dataframe(reports, use_container_width=True, hide_index=True)
        ids = [report.get("report_id") for report in reports if report.get("report_id")]
        selected = st.selectbox("Saved report", options=ids or [""])
        if selected and st.button("Load deployment report"):
            detail_ok, detail = api_client.get_json(f"/deployment/reports/{selected}", timeout=30)
            if detail_ok and isinstance(detail, dict):
                render_json("Saved deployment report", detail, expanded=True)
            else:
                backend_error(detail)
    elif ok:
        empty_state("No deployment reports matched the current filter.", "Run a readiness check or generate a final report first.")
    else:
        backend_error(reports)


def render() -> None:
    page_header(
        "Deployment Readiness",
        "Reviews local enterprise-readiness, API surface, security planning, governance, observability, and final reports.",
        "Does not deploy to cloud, complete production security, or claim enterprise production readiness.",
        safety=True,
    )
    st.info(NOTICE)

    ok, status = _get("/deployment/status")
    status_payload = status if isinstance(status, dict) else {}
    if ok:
        metric_row(
            {
                "Deployment": status_payload.get("status", "unknown"),
                "Local-first": status_payload.get("local_first", False),
                "Cloud deployed": status_payload.get("actual_cloud_deployment", False),
                "Reports": status_payload.get("saved_report_count", 0),
            }
        )
    else:
        backend_error(status)

    tabs = st.tabs([
        "Status",
        "Readiness Check",
        "API Audit",
        "Security",
        "Governance",
        "Observability",
        "Final Report",
        "Reports",
        "Runbook",
    ])

    with tabs[0]:
        if ok and isinstance(status_payload, dict):
            render_json("Deployment status", status_payload, expanded=True)
        else:
            backend_error(status)

    with tabs[1]:
        st.write("Run a local readiness check. Missing files or services are reported honestly.")
        if st.button("Run readiness check", type="primary"):
            run_ok, payload = api_client.post_json("/deployment/readiness-check", {}, timeout=120)
            _clear_cache()
            if run_ok:
                st.success(f"Readiness level: {payload.get('readiness_level', 'unknown')}")
                _render_readiness(payload)
            else:
                backend_error(payload)

    with tabs[2]:
        api_ok, api_payload = _get("/deployment/api-audit")
        if api_ok and isinstance(api_payload, dict):
            metric_row({"Routes": api_payload.get("route_count", 0), "Status": api_payload.get("status", "unknown")})
            routes = api_payload.get("routes", [])
            if isinstance(routes, list):
                st.dataframe(routes, use_container_width=True, hide_index=True)
            render_json("API audit details", api_payload)
        else:
            backend_error(api_payload)

    with tabs[3]:
        sec_ok, sec_payload = _get("/deployment/security-review")
        if sec_ok and isinstance(sec_payload, dict):
            st.warning("Production security is not complete. Authentication and authorization are planned, not implemented.")
            _render_plan("Security Review", sec_payload)
        else:
            backend_error(sec_payload)

    with tabs[4]:
        gov_ok, gov_payload = _get("/deployment/governance-plan")
        if gov_ok and isinstance(gov_payload, dict):
            _render_plan("Data Governance Plan", gov_payload)
        else:
            backend_error(gov_payload)

    with tabs[5]:
        obs_ok, obs_payload = _get("/deployment/observability-plan")
        if obs_ok and isinstance(obs_payload, dict):
            _render_plan("Observability Plan", obs_payload)
        else:
            backend_error(obs_payload)

    with tabs[6]:
        st.write("Generate the recruiter/company-friendly final project report as local JSON and Markdown files.")
        if st.button("Generate final project report", type="primary"):
            report_ok, report_payload = api_client.post_json("/deployment/final-report", {}, timeout=180)
            _clear_cache()
            if report_ok:
                st.success(f"Final report generated: {report_payload.get('report_id', '')}")
                render_json("Final project report", report_payload, expanded=True)
            else:
                backend_error(report_payload)

    with tabs[7]:
        _reports_tab()

    with tabs[8]:
        runbook_ok, runbook = _get("/deployment/runbook")
        if runbook_ok and isinstance(runbook, dict):
            st.subheader("Local Production-Style Runbook")
            st.write(runbook.get("scope", ""))
            steps = runbook.get("steps", [])
            if isinstance(steps, list):
                st.dataframe(steps, use_container_width=True, hide_index=True)
            troubleshooting = runbook.get("troubleshooting", [])
            if isinstance(troubleshooting, list):
                st.subheader("Troubleshooting")
                st.dataframe(troubleshooting, use_container_width=True, hide_index=True)
            render_bullets(runbook.get("future_enterprise_notes", []))
        else:
            backend_error(runbook)
