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
from ui.filters import ALL_PERIODS, apply_filters, render_filters
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
        period, country = render_filters(df_sales, df_returns)

        # The year filter must skip Business Pulse: its MoM/YoY comparisons need
        # the prior year's rows, which filtering to a single year would remove.
        # Country still applies. Every other slide gets the full filter.
        slide_period = ALL_PERIODS if key == "pulse" else period
        df_sales = apply_filters(df_sales, slide_period, country)
        df_returns = apply_filters(df_returns, slide_period, country)

        # Shared empty-data guard: a valid but non-overlapping filter combo
        # (e.g. a country that only traded in a different year) yields no rows.
        # Stop here with one clear message instead of letting a slide render
        # "the top 5% (0 orders) bring in 0.00% of revenue".
        if df_sales.empty:
            st.info(
                "No sales match the current filters — adjust the period or "
                "country in the sidebar."
            )
            return

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
            period, country = render_filters(df_sales, df_returns)
            df_sales = apply_filters(df_sales, period, country)
            st.divider()
            render_kpis(df_sales)
        except NotImplementedError:
            pass  # pipeline not complete yet — KPIs appear when it is
else:
    _render_slide_page(page)
