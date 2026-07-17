"""Slide 3 — Leaks & key customers: returns and concentration.

Owner: P5
MUST: returns per month + return rate % + top 5 most-returned products;
concentration (top 5% of orders = X% of revenue) + top 10 customers.
BONUS: "customers to call this month" table.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from pipeline.aggregate import concentration, returns_summary, top_customers

ACCENT = "#eda100"  # Leaks slide accent (see ui/theme.py)


def _with_returned_value(df_returns: pd.DataFrame) -> pd.DataFrame:
    """df_returns with an absolute 'Returned Value' column.

    split_returns output has no Revenue column (only df_sales gets one in
    clean_sales), so compute it here before taking the absolute value.
    """
    df = df_returns.copy()
    if "Revenue" not in df.columns:
        df["Revenue"] = df["Price"] * df["Quantity"]
    df["Returned Value"] = df["Revenue"].abs()
    return df


def slide_leaks(df_sales: pd.DataFrame, df_returns: pd.DataFrame) -> None:
    """Render Slide 3 in Streamlit."""
    # 1. Aggregations
    ret_summary = returns_summary(df_sales, df_returns)
    top_custs = top_customers(df_sales)
    con_stats = concentration(df_sales)

    # 2. MUST: concentration (top 5% of orders)
    pct = con_stats.get("percentage", 0.0)
    order_count = con_stats.get("top_order_count", 0)

    st.subheader("Order Concentration")
    st.metric(label="Revenue share of the top 5% of orders", value=f"{pct:.2f}%")
    st.write(
        f"The business depends on a small group of orders: the **top 5%** "
        f"({order_count} orders) bring in **{pct:.2f}%** of all revenue."
    )

    # 3. MUST: monthly returns chart — the visual that exposes return spikes
    st.subheader("Monthly Returned Value")
    if ret_summary.empty or ret_summary["Returned Revenue"].sum() <= 0:
        st.info("No returned value to chart in this period.")
    else:
        fig_returns = px.bar(
            ret_summary,
            x="Month",
            y="Returned Revenue",
            labels={"Month": "Month", "Returned Revenue": "Returned value (£)"},
            color_discrete_sequence=[ACCENT],
            template="plotly_white",
            hover_data={"Return Rate %": ":.2f", "Most Returned Product": True},
        )
        fig_returns.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        fig_returns.update_xaxes(dtick="M1", tickformat="%b %Y")
        st.plotly_chart(fig_returns, use_container_width=True)

        peak = ret_summary.loc[ret_summary["Returned Revenue"].idxmax()]
        st.markdown(
            f"Returns peaked in **{peak['Month']:%b %Y}** — **£{peak['Returned Revenue']:,.2f}** returned "
            f"({peak['Return Rate %']:.2f}% of that month's sales), led by **{peak['Most Returned Product']}**. "
            "A returns spike that doesn't match a sales peak is worth investigating."
        )

    st.divider()

    # 4. Returns detail on the left, key customers on the right
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Returns & Return Rate %")
        st.dataframe(
            ret_summary.style.format(
                {
                    "Month": lambda m: f"{m:%b %Y}",
                    "Returned Revenue": "£{:,.2f}",
                    "Return Rate %": "{:.2f}%",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Top 5 Most-Returned Products")
        if df_returns.empty:
            st.info("No returns in this period.")
        else:
            top_returned = (
                _with_returned_value(df_returns)
                .groupby("Description")["Returned Value"]
                .sum()
                .reset_index()
                .sort_values("Returned Value", ascending=False)
                .head(5)
            )
            st.dataframe(
                top_returned.style.format({"Returned Value": "£{:,.2f}"}),
                use_container_width=True,
                hide_index=True,
            )

    with col2:
        st.subheader("Top 10 Customers by Revenue")
        st.dataframe(
            top_custs.style.format({"Revenue": "£{:,.2f}"}),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("📞 Customers to Call (Bonus)")
        if df_returns.empty:
            st.info("No returns.")
        else:
            df_ret = _with_returned_value(df_returns)
            if "Customer ID" not in df_ret.columns:
                st.info('The "Customer ID" column is missing.')
            else:
                df_ret = df_ret.dropna(subset=["Customer ID"])
                df_ret["Customer ID"] = (
                    df_ret["Customer ID"].astype(float).astype(int).astype(str)
                )
                call_list = (
                    df_ret.groupby("Customer ID")["Returned Value"]
                    .sum()
                    .reset_index()
                    .sort_values("Returned Value", ascending=False)
                    .head(5)
                    .rename(columns={"Returned Value": "Total Returned Value"})
                )
                st.dataframe(
                    call_list.style.format({"Total Returned Value": "£{:,.2f}"}),
                    use_container_width=True,
                    hide_index=True,
                )
