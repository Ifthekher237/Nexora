"""Status and metric display helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st


def status_badge(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        st.success(f"{label}: ready")
    else:
        st.error(f"{label}: attention needed")
    if detail:
        st.caption(detail)


def metric_row(metrics: dict[str, Any], columns: int = 4) -> None:
    cols = st.columns(columns)
    for index, (label, value) in enumerate(metrics.items()):
        with cols[index % columns]:
            st.metric(label, value)


def status_table(rows: list[dict[str, Any]]) -> None:
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No status rows are available.")
