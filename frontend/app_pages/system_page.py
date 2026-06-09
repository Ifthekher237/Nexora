"""System status page."""

from __future__ import annotations

import streamlit as st

from components import api_client
from components.layout import backend_error, page_header
from components.status_cards import metric_row, status_table


STATUS_ENDPOINTS = [
    ("Backend health", "/health"),
    ("System details", "/health/system"),
    ("Ingestion", "/ingestion/status"),
    ("Processing", "/processing/status"),
    ("Retrieval", "/retrieval/status"),
    ("RAG", "/rag/status"),
    ("Reasoning", "/reasoning/status"),
    ("Risk", "/risk/status"),
    ("Explainability", "/explainability/status"),
]


def render() -> None:
    page_header(
        "System Status",
        "Checks backend, Ollama, retrieval, and saved-output availability.",
        "Does not repair missing services automatically.",
    )

    rows = []
    payloads: dict[str, object] = {}
    for label, path in STATUS_ENDPOINTS:
        ok, payload = api_client.get_json(path, timeout=12)
        status = payload.get("status", "error") if isinstance(payload, dict) else "error"
        rows.append(
            {
                "Service": label,
                "Endpoint": path,
                "Reachable": ok,
                "Reported status": status,
                "Message": payload.get("message", "") if isinstance(payload, dict) else "",
            }
        )
        payloads[label] = payload

    status_table(rows)

    retrieval = payloads.get("Retrieval", {}) if isinstance(payloads.get("Retrieval"), dict) else {}
    rag = payloads.get("RAG", {}) if isinstance(payloads.get("RAG"), dict) else {}
    reasoning = payloads.get("Reasoning", {}) if isinstance(payloads.get("Reasoning"), dict) else {}
    risk = payloads.get("Risk", {}) if isinstance(payloads.get("Risk"), dict) else {}
    explain = payloads.get("Explainability", {}) if isinstance(payloads.get("Explainability"), dict) else {}
    metric_row(
        {
            "Indexed chunks": retrieval.get("indexed_chunks", 0),
            "Ollama for RAG": "running" if rag.get("ollama_running") else "offline",
            "Saved reasoning": reasoning.get("saved_reasoning_outputs", 0),
            "Saved risks": risk.get("saved_risk_outputs", 0),
            "Explainability reports": explain.get("saved_reports", 0),
        },
        columns=5,
    )

    ollama_ok, ollama_payload = api_client.check_ollama()
    if ollama_ok:
        models = [item.get("name") for item in ollama_payload.get("models", []) if item.get("name")]
        st.success(f"Ollama is reachable at {api_client.OLLAMA_URL}.")
        st.code("\n".join(models) if models else "No local models reported.")
    else:
        backend_error(ollama_payload)

    with st.expander("Raw status payloads", expanded=False):
        st.json(payloads)
