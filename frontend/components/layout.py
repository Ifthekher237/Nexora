"""Shared layout primitives for the Nexora Streamlit interface."""

from __future__ import annotations

from typing import Iterable

import streamlit as st


SAFETY_NOTICE = (
    "Nexora provides evidence-backed financial analysis support. It does not provide "
    "financial advice, trading recommendations, or stock price predictions."
)


def apply_global_styles() -> None:
    """Keep the interface restrained and analyst-oriented."""

    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.25rem; padding-bottom: 3rem;}
        div[data-testid="stMetric"] {
            border: 1px solid #d9dee8;
            border-radius: 8px;
            padding: 0.85rem 0.95rem;
            background: #ffffff;
        }
        .nexora-page-note {
            border-left: 4px solid #476582;
            padding: 0.75rem 1rem;
            background: #f6f8fb;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, does: str, does_not: str, *, safety: bool = False) -> None:
    """Render a consistent page header with scope and non-scope."""

    st.title(title)
    st.markdown(
        f"""
        <div class="nexora-page-note">
        <strong>What this page does:</strong> {does}<br>
        <strong>What this page does not do:</strong> {does_not}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if safety:
        st.warning(SAFETY_NOTICE)


def backend_error(payload: dict[str, object] | object) -> None:
    """Show a clear backend failure with a next step."""

    message = "Backend is not reachable. Please run ./scripts/run_backend.sh"
    detail = ""
    if isinstance(payload, dict):
        message = str(payload.get("message") or message)
        detail = str(payload.get("detail") or "")
    st.error(message)
    if detail:
        st.caption(detail)


def empty_state(message: str, next_step: str | None = None) -> None:
    st.info(message)
    if next_step:
        st.caption(next_step)


def render_key_value_grid(items: dict[str, object], columns: int = 3) -> None:
    cols = st.columns(columns)
    for index, (label, value) in enumerate(items.items()):
        with cols[index % columns]:
            st.metric(label, value)


def render_bullets(items: Iterable[object]) -> None:
    for item in items:
        st.write(f"- {item}")
