"""Simple built-in Streamlit chart helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def bar_chart_from_mapping(mapping: dict[str, Any], title: str) -> None:
    rows = []
    for label, value in mapping.items():
        try:
            rows.append({"component": label, "score": float(value)})
        except (TypeError, ValueError):
            continue
    if not rows:
        return
    st.subheader(title)
    frame = pd.DataFrame(rows).set_index("component")
    st.bar_chart(frame)
