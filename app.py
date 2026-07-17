"""Automated sales report — Team Squirtle.

app.py only orchestrates — every page lives in its own module and is
reached with the sidebar buttons:
- ui/welcome.py      (P1) Overview & Upload: validation + file status
- slides/pulse.py    (P3) Business Pulse
- slides/engines.py  (P4) Revenue Engines
- slides/leaks.py    (P5) Leaks & Key Customers

The slide pages already call the real contracts — as soon as
load_and_clean() (P2+P3) and the slide_*() functions are implemented,
the slides light up without touching this file.
"""
from __future__ import annotations

import streamlit as st

from pipeline.clean import load_and_clean
from slides import slide_engines, slide_leaks, slide_pulse
from ui.filters import render_filters
from ui.kpis import render_kpis
from ui.sidebar import render_sidebar
from ui.theme import ACCENTS, inject_css
from ui.welcome import render_home

st.set_page_config(
    page_title="Sales Report — Squirtle",
    page_icon="📊",
    layout="wide",
)

_SLIDES = {
    "pulse": (
        "💓 Business Pulse",
        "How did we do — and what's coming? Monthly revenue with MoM % and YoY %.",
        "Decides: stock & staffing for next month",
        lambda data: slide_pulse(data[0]),
    ),
    "engines": (
        "🚀 Revenue Engines",
        "What's driving the month? Top products by revenue and the highest-value markets.",
        "Decides: what to promote & who gets VIP treatment",
        lambda data: slide_engines(data[0]),
    ),
    "leaks": (
        "🔍 Leaks & Key Customers",
        "Where is money leaking? Returns, return rate % and customer concentration.",
        "Decides: what to investigate & who to call",
        lambda data: slide_leaks(data[0], data[1]),
    ),
}


def _render_slide_page(key: str) -> None:
    title, description, decision, render = _SLIDES[key]
    st.title(title)
    st.caption(description)
    st.markdown(
        f'<span class="decision-chip" style="--accent:{ACCENTS[key]}">🎯 {decision}</span>',
        unsafe_allow_html=True,
    )

    if "file_bytes" not in st.session_state:
        st.info("⬅️ Upload and validate the sales file on **Overview & Upload** first.")
        return

    try:
        df_sales, df_returns, log, errors = load_and_clean(st.session_state["file_bytes"])
        df_sales, df_returns = render_filters(df_sales, df_returns)
        render((df_sales, df_returns))
    except NotImplementedError as todo:
        st.markdown(
            '<div class="ph-card"><div class="ph-emoji">🏗️</div>'
            '<div class="ph-title">This slide is on its way</div>'
            f'<div class="ph-text">{description}</div>'
            f'<span class="owner-chip">{todo}</span></div>',
            unsafe_allow_html=True,
        )


inject_css()
page = render_sidebar()

if page == "home":
    render_home()
    # P2's KPI row — shown once a valid file is loaded
    if "file_bytes" in st.session_state:
        try:
            df_sales, df_returns, log, _ = load_and_clean(st.session_state["file_bytes"])
            df_sales, df_returns = render_filters(df_sales, df_returns)
            st.divider()
            render_kpis(df_sales)
        except NotImplementedError:
            pass  # pipeline not complete yet — KPIs appear when it is
else:
    _render_slide_page(page)
