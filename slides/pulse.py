"""Slide 1 — Business pulse: how did we do and what's ahead?"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pipeline.aggregate import monthly_revenue


def compute_monthly_metrics(df_sales: pd.DataFrame) -> pd.DataFrame:
    """Aggregates row-level transactions and calculates robust MoM and YoY metrics."""
    # 1. Call monthly_revenue to get the base monthly aggregates
    df_monthly = monthly_revenue(df_sales)

    if df_monthly.empty:
        return df_monthly

    # 2. Add additional columns for Year, Month_Name, and Period_Label for better visualization
    df_monthly["Year"] = df_monthly["Month"].dt.year.astype(str)
    df_monthly["Month_Name"] = df_monthly["Month"].dt.strftime("%b")
    df_monthly["Period_Label"] = df_monthly["Month"].dt.strftime("%Y - %b")

    # 3. Rename columns for clarity in the visualizations
    return df_monthly.rename(columns={
        "MoM %": "MoM_Growth_%",
        "YoY %": "YoY_Growth_%"
    })


def slide_pulse(df_sales: pd.DataFrame) -> None:
    """Main entry point called by app.py. Renders Slide 1 interactive dashboard."""
    
    # Checking if there is data to process
    if df_sales.empty:
        st.warning("⚠️ No valid sales transactions found to calculate business pulse metrics.")
        return

    # Compute aggregates dynamically
    df_monthly = compute_monthly_metrics(df_sales)

    #  Visual 1: Dual-Axis Revenue & MoM % 
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
            hovertemplate="Period: %{x}<br>Revenue: $%{y:,.2f}<extra></extra>"
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
    
    st.plotly_chart(fig_mom, use_container_width=True)

    st.divider()

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

    st.plotly_chart(fig_yoy, use_container_width=True)
