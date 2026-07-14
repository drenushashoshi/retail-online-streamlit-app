"""Aggregations for the slides: monthly, products/markets, returns/VIP.

Owners: P4 (part 1) + P5 (part 2) — TODO, in progress.
Contracts were agreed in the mob session; do not change signatures
without telling the team.
"""
from __future__ import annotations

import pandas as pd


def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """(P4) Monthly revenue + MoM % + YoY % for Slide 1."""
    if df.empty:
        return pd.DataFrame(columns=["Month", "Revenue", "MoM %", "YoY %"])

    df_temp = df.copy()
    
    # Make sure InvoiceDate is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df_temp["InvoiceDate"]):
        df_temp["InvoiceDate"] = pd.to_datetime(df_temp["InvoiceDate"])

    # Group by month and calculate total revenue
    df_monthly = df_temp.groupby(df_temp["InvoiceDate"].dt.to_period("M"))["Revenue"].sum().reset_index()
    df_monthly["Month"] = df_monthly["InvoiceDate"].dt.to_timestamp()
    df_monthly = df_monthly.sort_values("Month").reset_index(drop=True)

    # 1. Calculate MoM % using shift(1)
    df_monthly["Prev_Month_Rev"] = df_monthly["Revenue"].shift(1)
    df_monthly["MoM %"] = (
        (df_monthly["Revenue"] - df_monthly["Prev_Month_Rev"]) / df_monthly["Prev_Month_Rev"]
    ) * 100

    # 2. Calculate YoY % using self-merge with DateOffset(years=1)
    df_historical = df_monthly[["Month", "Revenue"]].copy()
    df_historical["Target_Year_Match"] = df_historical["Month"] + pd.DateOffset(years=1)
    df_historical = df_historical.rename(columns={"Revenue": "Prev_Year_Rev"})

    df_monthly = pd.merge(
        df_monthly,
        df_historical[["Target_Year_Match", "Prev_Year_Rev"]],
        left_on="Month",
        right_on="Target_Year_Match",
        how="left"
    ).drop(columns=["Target_Year_Match"])

    df_monthly["YoY %"] = (
        (df_monthly["Revenue"] - df_monthly["Prev_Year_Rev"]) / df_monthly["Prev_Year_Rev"]
    ) * 100

    return df_monthly[["Month", "Revenue", "MoM %", "YoY %"]]


def top_products(df: pd.DataFrame) -> pd.DataFrame:
    """(P4) Top 10 products by revenue (not by row count!)."""
    columns = ["Description", "Revenue", "Line Items"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    ranked = (
        df.groupby("Description", as_index=False)
        .agg(Revenue=("Revenue", "sum"), **{"Line Items": ("Description", "count")})
        .sort_values("Revenue", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    return ranked[columns]


def markets_summary(df: pd.DataFrame) -> pd.DataFrame:
    """(P4) Markets with average revenue per order (the 'Netherlands' effect)."""
    columns = ["Country", "Revenue", "Orders", "Avg Revenue Per Order"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    by_country = (
        df.groupby("Country", as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("Invoice", "nunique"),
        )
    )
    by_country["Avg Revenue Per Order"] = by_country["Revenue"] / by_country["Orders"]
    return (
        by_country.sort_values("Avg Revenue Per Order", ascending=False)
        .reset_index(drop=True)[columns]
    )


def returns_summary(df_sales: pd.DataFrame, df_returns: pd.DataFrame) -> pd.DataFrame:
    """(P5) Monthly returns, return rate %, most-returned products."""
    raise NotImplementedError("P5 — in progress")


def top_customers(df: pd.DataFrame) -> pd.DataFrame:
    """(P5) Top 10 customers by revenue."""
    raise NotImplementedError("P5 — in progress")


def concentration(df: pd.DataFrame) -> dict:
    """(P5) Concentration: top 5% of orders = X% of revenue."""
    raise NotImplementedError("P5 — in progress")
