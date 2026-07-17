"""Report filters: the period / country dropdowns from the plan.

The manager picks a period and a country and the KPI row plus all three
slides recompute — the slide modules stay untouched because app.py simply
hands them the already-filtered frames.

The option-building and filtering helpers are pure pandas functions so they
can be unit-tested without Streamlit.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

ALL_PERIODS = "All period"
ALL_COUNTRIES = "All countries"


def period_options(df_sales: pd.DataFrame, df_returns: pd.DataFrame) -> list[str]:
    """Years present in either frame, e.g. ['All period', '2009', '2010']."""
    years: set[int] = set()
    for df in (df_sales, df_returns):
        if not df.empty and "InvoiceDate" in df.columns:
            dates = pd.to_datetime(df["InvoiceDate"], errors="coerce").dropna()
            years.update(int(y) for y in dates.dt.year.unique())
    return [ALL_PERIODS] + [str(year) for year in sorted(years)]


def country_options(df_sales: pd.DataFrame, df_returns: pd.DataFrame) -> list[str]:
    """Countries present in either frame, alphabetical."""
    countries: set[str] = set()
    for df in (df_sales, df_returns):
        if not df.empty and "Country" in df.columns:
            countries.update(df["Country"].dropna().astype(str).unique())
    return [ALL_COUNTRIES] + sorted(countries)


def apply_filters(df: pd.DataFrame, period: str, country: str) -> pd.DataFrame:
    """Filter one frame by the selected year and country ('All ...' = keep)."""
    if df.empty:
        return df

    out = df
    if period != ALL_PERIODS and "InvoiceDate" in out.columns:
        years = pd.to_datetime(out["InvoiceDate"], errors="coerce").dt.year
        out = out[years == int(period)]
    if country != ALL_COUNTRIES and "Country" in out.columns:
        out = out[out["Country"].astype(str) == country]
    return out.copy()


def _persistent_selectbox(label: str, options: list[str], state_key: str) -> str:
    """A selectbox whose choice survives page switches.

    Widget-keyed session state is dropped by Streamlit whenever a script run
    doesn't render the widget (e.g. a slide page before any upload), so the
    choice is mirrored in a plain session key that is never cleaned up.
    """
    saved = st.session_state.get(state_key, options[0])
    index = options.index(saved) if saved in options else 0
    choice = st.selectbox(label, options, index=index)
    st.session_state[state_key] = choice
    return choice


def render_filters(
    df_sales: pd.DataFrame, df_returns: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Draw the dropdowns in the sidebar; return the filtered (sales, returns)."""
    with st.sidebar:
        st.divider()
        st.markdown("**🔎 Report filters**")
        period = _persistent_selectbox(
            "Period", period_options(df_sales, df_returns), "flt_period"
        )
        country = _persistent_selectbox(
            "Country", country_options(df_sales, df_returns), "flt_country"
        )
        if period != ALL_PERIODS or country != ALL_COUNTRIES:
            st.caption("Applied to the KPIs and all three slides.")

    return (
        apply_filters(df_sales, period, country),
        apply_filters(df_returns, period, country),
    )
