"""Slide 1 — Business pulse: how did we do and what's ahead?"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from pipeline.aggregate import monthly_revenue

PULSE_ACCENT = "#2a78d6"
PULSE_SUPPORT = "#86b6ef"
PULSE_MOM = "#4a3aa7"


def compute_monthly_metrics(df_sales: pd.DataFrame) -> pd.DataFrame:
    """Aggregates row-level transactions and calculates robust MoM and YoY metrics."""
    df_monthly = monthly_revenue(df_sales)

    if df_monthly.empty:
        return df_monthly

    df_monthly["Year"] = df_monthly["Month"].dt.year.astype(str)
    df_monthly["Month_Name"] = df_monthly["Month"].dt.strftime("%b")
    df_monthly["Period_Label"] = df_monthly["Month"].dt.strftime("%Y - %b")

    return df_monthly.rename(columns={"MoM %": "MoM_Growth_%", "YoY %": "YoY_Growth_%"})


def _format_metric_currency(value: float) -> str:
    if abs(value) >= 10_000:
        return f"£{value / 1000:,.1f}k"
    return f"£{value:,.2f}"


def _format_metric_percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1f}%"


def _format_delta_percent(value: float | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    return f"{value:+.1f}%"


def _build_revenue_insight(latest_month: pd.Series) -> str:
    month_label = f"{latest_month['Month']:%b %Y}"
    revenue_text = _format_metric_currency(float(latest_month["Revenue"]))
    summary = f"Revenue in **{month_label}** was **{revenue_text}**"

    comparisons: list[str] = []
    if pd.notna(latest_month["MoM_Growth_%"]):
        comparisons.append(f"{latest_month['MoM_Growth_%']:+.1f}% vs the previous month")
    if pd.notna(latest_month["YoY_Growth_%"]):
        comparisons.append(f"{latest_month['YoY_Growth_%']:+.1f}% vs the same month last year")

    if not comparisons:
        return f"{summary}. No prior month or year benchmark is available yet."

    return f"{summary} — " + " and ".join(comparisons) + "."


def slide_pulse(df_sales: pd.DataFrame) -> None:
    """Main entry point called by app.py. Renders Slide 1 interactive dashboard."""
    if df_sales.empty:
        st.warning("⚠️ No valid sales transactions found to calculate business pulse metrics.")
        return

    df_monthly = compute_monthly_metrics(df_sales)
    if df_monthly.empty:
        st.info("No monthly revenue data is available yet.")
        return

    latest_month = df_monthly.iloc[-1]

    st.write("")
    st.subheader("This Month at a Glance")
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric(
            "Latest-month revenue",
            _format_metric_currency(float(latest_month["Revenue"])),
            delta=_format_delta_percent(latest_month["MoM_Growth_%"]),
        )
    with metric_cols[1]:
        st.metric(
            "MoM %",
            _format_metric_percent(latest_month["MoM_Growth_%"]),
            delta=_format_delta_percent(latest_month["MoM_Growth_%"]),
        )
    with metric_cols[2]:
        st.metric(
            "YoY %",
            _format_metric_percent(latest_month["YoY_Growth_%"]),
            delta=_format_delta_percent(latest_month["YoY_Growth_%"]),
        )

    st.markdown(_build_revenue_insight(latest_month))
    st.divider()

    st.subheader("📊 Monthly Revenue & MoM Momentum")
    fig_mom = make_subplots(specs=[[{"secondary_y": True}]])
    fig_mom.add_trace(
        go.Bar(
            x=df_monthly["Period_Label"],
            y=df_monthly["Revenue"],
            name="Revenue (£)",
            marker_color=PULSE_ACCENT,
            hovertemplate="Period: %{x}<br>Revenue: £%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig_mom.add_trace(
        go.Scatter(
            x=df_monthly["Period_Label"],
            y=df_monthly["MoM_Growth_%"],
            name="MoM Growth (%)",
            mode="lines+markers",
            line=dict(color=PULSE_MOM, width=3),
            hovertemplate="Period: %{x}<br>MoM Growth: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig_mom.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    fig_mom.update_yaxes(
        title_text="Total Revenue (£)",
        secondary_y=False,
        showgrid=True,
        tickprefix="£",
    )
    fig_mom.update_yaxes(title_text="MoM Growth Rate (%)", secondary_y=True, showgrid=False)

    st.plotly_chart(fig_mom, use_container_width=True)

    st.divider()

    st.subheader("🔄 Year-over-Year (YoY) Trajectory Overlap")
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    years = sorted(df_monthly["Year"].unique())
    color_map = {year: PULSE_SUPPORT for year in years}
    if years:
        color_map[years[-1]] = PULSE_ACCENT

    fig_yoy = px.line(
        df_monthly,
        x="Month_Name",
        y="Revenue",
        color="Year",
        category_orders={"Month_Name": month_order},
        labels={"Month_Name": "Calendar Month", "Revenue": "Revenue (£)", "Year": "Fiscal Year"},
        markers=True,
        template="plotly_white",
        color_discrete_map=color_map,
    )

    fig_yoy.update_traces(hovertemplate="Month: %{x}<br>Revenue: £%{y:,.2f}<extra>%{fullData.name}</extra>")
    fig_yoy.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
    )
    fig_yoy.update_yaxes(showgrid=True, tickprefix="£")

    st.plotly_chart(fig_yoy, use_container_width=True)
