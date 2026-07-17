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


def markets_summary(df: pd.DataFrame, min_orders: int = 5) -> pd.DataFrame:
    """(P4) Markets with average revenue per order (the 'Netherlands' effect).

    Markets with fewer than min_orders orders are left out of the ranking so a single
    fluke order cannot crown a country as the highest-value market. If no market clears
    the bar (small file), every market is kept rather than showing nothing.
    """
    columns = ["Country", "Revenue", "Orders", "Avg Revenue Per Order"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    by_country = (
        df.groupby("Country", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Orders=("Invoice", "nunique"))
    )
    by_country["Avg Revenue Per Order"] = by_country["Revenue"] / by_country["Orders"]

    ranked = by_country[by_country["Orders"] >= min_orders]
    if ranked.empty:
        ranked = by_country

    return (
        ranked.sort_values("Avg Revenue Per Order", ascending=False)
        .reset_index(drop=True)[columns]
    )


def returns_summary(df_sales: pd.DataFrame, df_returns: pd.DataFrame) -> pd.DataFrame:
    """(P5) Monthly returns, return rate %, most-returned products."""
    df_sales = df_sales.copy()
    df_returns = df_returns.copy()

    # df_returns comes straight from split_returns and has NO Revenue column
    # (only df_sales gets Revenue in clean_sales) — compute it here.
    if "Revenue" not in df_returns.columns:
        df_returns["Revenue"] = df_returns["Price"] * df_returns["Quantity"]

    df_sales["Month"] = pd.to_datetime(df_sales["InvoiceDate"]).dt.to_period("M").dt.to_timestamp()
    df_returns["Month"] = pd.to_datetime(df_returns["InvoiceDate"]).dt.to_period("M").dt.to_timestamp()

    # Take absolute value before grouping (not valid directly on groupby object)
    df_returns["Revenue_Abs"] = df_returns["Revenue"].abs()

    sales_m = df_sales.groupby("Month")["Revenue"].sum().to_frame("Sales")
    returns_m = df_returns.groupby("Month")["Revenue_Abs"].sum().to_frame("Returned Revenue")

    # replace(0, pd.NA) avoids 'inf' values when a month has returns but no sales
    merged = sales_m.join(returns_m, how="outer").fillna(0).reset_index()
    merged["Return Rate %"] = (
        merged["Returned Revenue"] / merged["Sales"].replace(0, pd.NA)
    ).fillna(0) * 100

    # Find top returned product per month
    top_idx = df_returns.groupby(["Month", "Description"])["Revenue_Abs"].sum().groupby("Month").idxmax()
    most_returned = {month: desc for month, desc in top_idx.values} if not top_idx.empty else {}
    merged["Most Returned Product"] = merged["Month"].map(most_returned).fillna("None")

    return merged[["Month", "Returned Revenue", "Return Rate %", "Most Returned Product"]]


def top_customers(df: pd.DataFrame) -> pd.DataFrame:
    """(P5) Top 10 customers by revenue."""
    # Column has a space: "Customer ID"
    df_clean = df.dropna(subset=["Customer ID"])
    ranked = df_clean.groupby("Customer ID")["Revenue"].sum().reset_index()
    ranked = ranked.sort_values("Revenue", ascending=False).head(10).reset_index(drop=True)
    ranked["Customer ID"] = ranked["Customer ID"].astype(float).astype(int).astype(str)
    return ranked[["Customer ID", "Revenue"]]


def concentration(df: pd.DataFrame) -> dict:
    """(P5) Concentration: top 5% of orders = X% of revenue."""
    if df.empty or "Revenue" not in df.columns:
        return {"percentage": 0.0, "top_order_count": 0}

    # Group by Invoice to get cumulative revenue per order
    order_revenue = df.groupby("Invoice")["Revenue"].sum().sort_values(ascending=False)
    total_rev = order_revenue.sum()
    if total_rev <= 0:
        return {"percentage": 0.0, "top_order_count": 0}

    # Determine top 5% of orders (minimum 1 order)
    n_orders = len(order_revenue)
    top_5_count = max(1, int(round(n_orders * 0.05)))
    
    top_5_rev = order_revenue.head(top_5_count).sum()
    pct = (top_5_rev / total_rev) * 100

    return {"percentage": pct, "top_order_count": top_5_count}