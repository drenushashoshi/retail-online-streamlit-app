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

    # 1. Group by Year-Month
    df_monthly = df.groupby(df["InvoiceDate"].dt.to_period("M"))["Revenue"].sum().reset_index()
    df_monthly["Month"] = df_monthly["InvoiceDate"].dt.to_timestamp()
    df_monthly = df_monthly.sort_values("Month").reset_index(drop=True)

    # 2. Calculate Month-over-Month % changes
    df_monthly["MoM %"] = df_monthly["Revenue"].pct_change() * 100

    # 3. Calculate Year-over-Year % changes (shifting by 12 months)
    df_monthly["YoY %"] = df_monthly["Revenue"].pct_change(periods=12) * 100

    return df_monthly[["Month", "Revenue", "MoM %", "YoY %"]]


def top_products(df: pd.DataFrame) -> pd.DataFrame:
    """(P4) Top 10 products by revenue (not by row count!)."""
    raise NotImplementedError("P4 — in progress")


def markets_summary(df: pd.DataFrame) -> pd.DataFrame:
    """(P4) Markets with average revenue per order (the 'Netherlands' effect)."""
    raise NotImplementedError("P4 — in progress")


def returns_summary(df_sales: pd.DataFrame, df_returns: pd.DataFrame) -> pd.DataFrame:
    """(P5) Monthly returns, return rate %, most-returned products."""
    raise NotImplementedError("P5 — in progress")


def top_customers(df: pd.DataFrame) -> pd.DataFrame:
    """(P5) Top 10 customers by revenue."""
    raise NotImplementedError("P5 — in progress")


def concentration(df: pd.DataFrame) -> dict:
    """(P5) Concentration: top 5% of orders = X% of revenue."""
    raise NotImplementedError("P5 — in progress")
