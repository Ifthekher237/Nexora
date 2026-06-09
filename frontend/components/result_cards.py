"""Result rendering helpers for RAG, reasoning, risk, and explainability pages."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from components.layout import render_bullets


def render_confidence(confidence: dict[str, Any] | None) -> None:
    if not confidence:
        st.info("No confidence object was returned.")
        return
    cols = st.columns(3)
    with cols[0]:
        st.metric("Confidence", confidence.get("level", "unknown"))
    with cols[1]:
        st.metric("Confidence Score", confidence.get("score", 0.0))
    with cols[2]:
        st.write(confidence.get("reason") or confidence.get("explanation") or "")


def render_limitations(limitations: list[Any] | None) -> None:
    if not limitations:
        return
    with st.expander("Limitations", expanded=True):
        render_bullets(limitations)


def render_validation_warnings(warnings: list[Any] | None) -> None:
    if not warnings:
        return
    with st.expander("Validation warnings", expanded=False):
        render_bullets(warnings)


def render_json(label: str, payload: Any, *, expanded: bool = False) -> None:
    with st.expander(label, expanded=expanded):
        st.json(payload)


def render_score_bar(label: str, value: float, maximum: float = 100.0) -> None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    st.write(f"{label}: {numeric:g}")
    st.progress(max(0.0, min(1.0, numeric / maximum)))


def render_simple_table(data: list[dict[str, Any]] | dict[str, Any], empty_message: str) -> None:
    if isinstance(data, dict):
        rows = [{"metric": key, "value": value} for key, value in data.items()]
    else:
        rows = data
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)
