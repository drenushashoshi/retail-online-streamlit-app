"""Slide 2 — Revenue engines: which products and markets are making the month?

Owner: P4 — Jetmir.
MUST: top 10 products by revenue + markets with average revenue per order.
BONUS: "movers" — products with the biggest rise/fall vs the previous month.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from pipeline.aggregate import markets_summary, top_products

ACCENT = "#1baf7a"


def compute_product_movers(df_sales: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Products with the largest revenue change vs the previous month."""
    columns = ["Description", "Previous Revenue", "Current Revenue", "Change", "Change %"]
    if df_sales.empty:
        return pd.DataFrame(columns=columns)

    df = df_sales.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    df["Month"] = df["InvoiceDate"].dt.to_period("M")
    monthly = (
        df.groupby(["Month", "Description"], as_index=False)["Revenue"]
        .sum()
        .sort_values("Month")
    )

    months = monthly["Month"].drop_duplicates().tolist()
    if len(months) < 2:
        return pd.DataFrame(columns=columns)

    prev_month, curr_month = months[-2], months[-1]
    prev = monthly[monthly["Month"] == prev_month].rename(
        columns={"Revenue": "Previous Revenue"}
    )[["Description", "Previous Revenue"]]
    curr = monthly[monthly["Month"] == curr_month].rename(
        columns={"Revenue": "Current Revenue"}
    )[["Description", "Current Revenue"]]

    movers = curr.merge(prev, on="Description", how="outer").fillna(0)
    movers["Change"] = movers["Current Revenue"] - movers["Previous Revenue"]
    movers["Change %"] = (
        movers["Change"] / movers["Previous Revenue"].replace(0, pd.NA)
    ) * 100

    movers = movers.reindex(movers["Change"].abs().sort_values(ascending=False).index)
    return movers.head(top_n).reset_index(drop=True)[columns]


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _build_product_insight(df_products: pd.DataFrame, total_revenue: float) -> str:
    if df_products.empty or total_revenue <= 0:
        return "Upload more sales rows to surface product-level revenue drivers."

    leader = df_products.iloc[0]
    share = (leader["Revenue"] / total_revenue) * 100
    return (
        f"**{leader['Description']}** leads with {_format_currency(leader['Revenue'])} "
        f"({share:.1f}% of total revenue). "
        f"It ranks #1 by revenue despite only {int(leader['Line Items'])} line items — "
        "revenue beats raw row count."
    )


def _build_market_insight(df_markets: pd.DataFrame) -> str:
    if df_markets.empty:
        return "No country breakdown is available yet."

    top_market = df_markets.iloc[0]
    if len(df_markets) == 1:
        return (
            f"**{top_market['Country']}** averages "
            f"{_format_currency(top_market['Avg Revenue Per Order'])} per order."
        )

    baseline = df_markets.iloc[-1]
    uplift = (
        (top_market["Avg Revenue Per Order"] / baseline["Avg Revenue Per Order"]) - 1
    ) * 100
    return (
        f"**{top_market['Country']}** averages "
        f"{_format_currency(top_market['Avg Revenue Per Order'])} per order "
        f"({uplift:+.0f}% vs {baseline['Country']}) — fewer orders, higher ticket size "
        "(the wholesale / Netherlands effect)."
    )


def slide_engines(df_sales: pd.DataFrame) -> None:
    """Render Slide 2 in Streamlit."""
    if df_sales.empty:
        st.warning("⚠️ No valid sales transactions found to calculate revenue engines.")
        return

    df_products = top_products(df_sales)
    df_markets = markets_summary(df_sales)
    df_movers = compute_product_movers(df_sales)
    total_revenue = float(df_sales["Revenue"].sum())

    st.write("")
    st.subheader("🏆 Revenue Drivers at a Glance")

    metric_cols = st.columns(3)
    with metric_cols[0]:
        top_product_rev = float(df_products.iloc[0]["Revenue"]) if not df_products.empty else 0.0
        st.metric("Top product revenue", _format_currency(top_product_rev))
    with metric_cols[1]:
        top_market_aov = (
            float(df_markets.iloc[0]["Avg Revenue Per Order"]) if not df_markets.empty else 0.0
        )
        st.metric("Highest avg order value", _format_currency(top_market_aov))
    with metric_cols[2]:
        active_markets = int(df_markets["Country"].nunique()) if not df_markets.empty else 0
        st.metric("Active markets", f"{active_markets:,}")

    st.markdown(_build_product_insight(df_products, total_revenue))
    st.markdown(_build_market_insight(df_markets))

    st.divider()

    st.subheader("📦 Top 10 Products by Revenue")
    if df_products.empty:
        st.info("No product revenue to chart yet.")
    else:
        fig_products = px.bar(
            df_products.sort_values("Revenue"),
            x="Revenue",
            y="Description",
            orientation="h",
            labels={"Revenue": "Revenue ($)", "Description": "Product"},
            color_discrete_sequence=[ACCENT],
            template="plotly_white",
        )
        fig_products.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_products, use_container_width=True)

    st.divider()

    st.subheader("🌍 Markets by Average Revenue per Order")
    if df_markets.empty:
        st.info("No market breakdown to chart yet.")
    else:
        top_markets = df_markets.head(10).sort_values("Avg Revenue Per Order")
        fig_markets = px.bar(
            top_markets,
            x="Avg Revenue Per Order",
            y="Country",
            orientation="h",
            labels={
                "Avg Revenue Per Order": "Avg revenue / order ($)",
                "Country": "Country",
            },
            color_discrete_sequence=[ACCENT],
            template="plotly_white",
            hover_data={"Revenue": ":,.2f", "Orders": True},
        )
        fig_markets.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_markets, use_container_width=True)

    if not df_movers.empty:
        st.divider()
        st.subheader("🚀 Monthly Movers (vs previous month)")
        st.caption("Products with the biggest revenue swing month over month.")
        st.dataframe(
            df_movers.style.format(
                {
                    "Previous Revenue": "${:,.2f}",
                    "Current Revenue": "${:,.2f}",
                    "Change": "${:+,.2f}",
                    "Change %": "{:+.1f}%",
                },
                na_rep="—",
            ),
            use_container_width=True,
            hide_index=True,
        )
