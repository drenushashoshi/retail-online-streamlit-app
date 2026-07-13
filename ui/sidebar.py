"""Sidebar: brand, slide navigation buttons, loaded-file status.

Owner: P1 (Drenusha)

`render_sidebar()` returns the key of the page the manager selected.
"""
from __future__ import annotations

import streamlit as st

PAGES = [
    ("home", "🏠", "Overview & Upload"),
    ("pulse", "💓", "1 · Business Pulse"),
    ("engines", "🚀", "2 · Revenue Engines"),
    ("leaks", "🔍", "3 · Leaks & Key Customers"),
]


def render_sidebar() -> str:
    if "page" not in st.session_state:
        st.session_state.page = "home"

    with st.sidebar:
        st.markdown('<div class="sb-brand">📊 Sales Report</div>', unsafe_allow_html=True)
        st.caption("Team Squirtle · Online Retail II")
        st.divider()

        for key, emoji, label in PAGES:
            active = st.session_state.page == key
            if st.button(
                f"{emoji} {label}",
                key=f"nav_{key}",
                width="stretch",
                type="primary" if active else "secondary",
            ):
                st.session_state.page = key
                st.rerun()

        st.divider()

        file_info = st.session_state.get("valid_file")
        if file_info:
            st.markdown(
                f'<div class="sb-file">✅ <b>{file_info["name"]}</b><br>'
                f'{file_info["rows"]:,} rows · {file_info["sheets"]} sheet(s)</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No file loaded yet — start on Overview & Upload.")

    return st.session_state.page
