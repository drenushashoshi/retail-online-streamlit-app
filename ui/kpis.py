from __future__ import annotations

import pandas as pd
import streamlit as st


def _prepare_monthly_kpis(df_sales: pd.DataFrame) -> tuple[pd.Series, pd.Series | None]:
    df = df_sales.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce", format="mixed")
    df = df.dropna(subset=["InvoiceDate"])

    if df.empty:
        raise ValueError("No valid InvoiceDate values are available for the KPI row.")

    df["month"] = df["InvoiceDate"].dt.to_period("M")

    monthly = (
        df.groupby("month")
        .agg(
            revenue=("Revenue", "sum"),
            orders=("Invoice", "nunique"),
            items=("Quantity", "sum"),
            customers=("Customer ID", lambda s: s.dropna().nunique()),
        )
        .sort_index()
    )
    monthly["aov"] = monthly["revenue"] / monthly["orders"]

    latest = monthly.iloc[-1]
    previous = monthly.iloc[-2] if len(monthly) > 1 else None
    return latest, previous


def _format_value(metric_key: str, value: float) -> str:
    if metric_key in {"revenue", "aov"}:
        return f"{value:,.2f}"
    if metric_key in {"orders", "customers"}:
        return f"{int(round(value)):,}"
    return f"{value:,.0f}"


def _format_delta(metric_key: str, latest: float, previous: float | None) -> str | None:
    if previous is None:
        return None

    change = latest - previous
    if metric_key in {"revenue", "aov"}:
        return f"{change:+,.2f} vs prev month"
    if metric_key in {"orders", "customers"}:
        return f"{int(round(change)):+,} vs prev month"
    return f"{change:+,.0f} vs prev month"


def render_kpis(df_sales: pd.DataFrame) -> None:
    if df_sales.empty:
        st.info("No sales data is available yet for the KPI row.")
        return

    try:
        latest, previous = _prepare_monthly_kpis(df_sales)
    except ValueError as exc:
        st.info(str(exc))
        return

    st.subheader("Monthly KPI Pulse")
    cols = st.columns(5)
    metrics = [
        ("Revenue", "revenue"),
        ("Orders", "orders"),
        ("Items", "items"),
        ("Average order value", "aov"),
        ("Unique customers", "customers"),
    ]

    for col, (label, key) in zip(cols, metrics):
        with col:
            st.metric(
                label=label,
                value=_format_value(key, float(latest[key])),
                delta=_format_delta(key, float(latest[key]), None if previous is None else float(previous[key])),
            )

    st.caption("Latest month vs previous month")
