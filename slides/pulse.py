"""Slide 1 — Business pulse: how did we do and what's ahead?"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def compute_monthly_metrics(df_sales: pd.DataFrame) -> pd.DataFrame:
    """Aggregates row-level transactions and calculates robust MoM and YoY metrics."""
    df = df_sales.copy()
    
    # Datetime conversion for reliable time-series grouping
    if not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # Floor timestamps to the first of the month for stable time-series grouping
    df["MS_Start"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()

    # Aggregate total revenue per calendar month sequence
    df_monthly = df.groupby("MS_Start", as_index=False)["Revenue"].sum()
    df_monthly = df_monthly.sort_values("MS_Start").reset_index(drop=True)

    # 1) Compute MoM % using sequential single-row shift
    df_monthly["Prev_Month_Rev"] = df_monthly["Revenue"].shift(1)
    df_monthly["MoM_Growth_%"] = (
        (df_monthly["Revenue"] - df_monthly["Prev_Month_Rev"]) / df_monthly["Prev_Month_Rev"]
    ) * 100

    # 2) Compute YoY % robustly via a self-merge on exact historical dates
    df_historical = df_monthly[["MS_Start", "Revenue"]].copy()
    df_historical["Target_Year_Match"] = df_historical["MS_Start"] + pd.DateOffset(years=1)
    df_historical = df_historical.rename(columns={"Revenue": "Prev_Year_Rev"})

    df_monthly = pd.merge(
        df_monthly,
        df_historical[["Target_Year_Match", "Prev_Year_Rev"]],
        left_on="MS_Start",
        right_on="Target_Year_Match",
        how="left"
    ).drop(columns=["Target_Year_Match"])

    df_monthly["YoY_Growth_%"] = (
        (df_monthly["Revenue"] - df_monthly["Prev_Year_Rev"]) / df_monthly["Prev_Year_Rev"]
    ) * 100

    # Human-readable visual labels
    df_monthly["Year"] = df_monthly["MS_Start"].dt.year.astype(str)
    df_monthly["Month_Name"] = df_monthly["MS_Start"].dt.strftime("%b")
    df_monthly["Period_Label"] = df_monthly["MS_Start"].dt.strftime("%Y - %b")

    return df_monthly


def slide_pulse(df_sales: pd.DataFrame) -> None:
    """Main entry point called by app.py. Renders Slide 3 interactive dashboard."""
    
    # Checking if there is data to process
    if df_sales.empty:
        st.warning("⚠️ No valid sales transactions found to calculate business pulse metrics.")
        return

    # Compute aggregates dynamically
    df_monthly = compute_monthly_metrics(df_sales)

    # --- Visual 1: Dual-Axis Revenue & MoM % ---
    st.write("")  # Add safe padding below the decision chip
    st.subheader("📊 Monthly Revenue & MoM Momentum")
    
    fig_mom = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar chart for volumes
    fig_mom.add_trace(
        go.Bar(
            x=df_monthly["Period_Label"],
            y=df_monthly["Revenue"],
            name="Revenue ($)",
            marker_color="#1f77b4",
            hovertemplate="Period: %{x}<br>Revenue: $% {y:,.2f}<extra></extra>"
        ),
        secondary_y=False
    )

    # Line chart for trajectory trend
    fig_mom.add_trace(
        go.Scatter(
            x=df_monthly["Period_Label"],
            y=df_monthly["MoM_Growth_%"],
            name="MoM Growth (%)",
            mode="lines+markers",
            line=dict(color="#ff7f0e", width=3),
            hovertemplate="Period: %{x}<br>MoM Growth: %{y:.1f}%<extra></extra>"
        ),
        secondary_y=True
    )

    fig_mom.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=30, b=10)
    )
    fig_mom.update_yaxes(title_text="Total Revenue ($)", secondary_y=False, showgrid=True)
    fig_mom.update_yaxes(title_text="MoM Growth Rate (%)", secondary_y=True, showgrid=False)
    
    st.plotly_chart(fig_mom, width="stretch")

    st.divider(width="stretch")

    # Visual 2: YoY Seasonal Trajectory Overlay 
    st.subheader("🔄 Year-over-Year (YoY) Trajectory Overlap")

    # Explicit chronological ordering sequence
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig_yoy = px.line(
        df_monthly,
        x="Month_Name",
        y="Revenue",
        color="Year",
        category_orders={"Month_Name": month_order},
        labels={"Month_Name": "Calendar Month", "Revenue": "Revenue ($)", "Year": "Fiscal Year"},
        markers=True,
        template="plotly_white"
    )

    fig_yoy.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
    )
    fig_yoy.update_yaxes(showgrid=True)

    st.plotly_chart(fig_yoy, width="stretch")
