"""Pipeline steps 1-4: data cleaning.

Owners: P2 (part 1) + P3 (part 2) — TODO, in progress.
Contracts were agreed in the mob session; do not change signatures
without telling the team.
"""
from __future__ import annotations

import pandas as pd


def split_returns(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(P2) Strip column names, drop duplicates, split C-invoices.

    Returns (sales_raw, df_returns). Returned invoices are NOT dropped —
    Slide 3 needs them!
    """
    if "Invoice" not in [str(col).strip() for col in df.columns]:
        raise ValueError('Missing required column: "Invoice".')

    if df.empty:
        empty = df.copy()
        empty.columns = [str(col).strip() for col in empty.columns]
        return empty.copy(), empty.copy()

    cleaned = df.copy()
    cleaned.columns = [str(col).strip() for col in cleaned.columns]
    cleaned = cleaned.drop_duplicates()

    invoice_series = cleaned["Invoice"]
    is_return = invoice_series.map(lambda value: str(value).startswith("C"))

    sales_raw = cleaned.loc[~is_return].copy()
    df_returns = cleaned.loc[is_return].copy()
    return sales_raw, df_returns


def clean_sales(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, int]]]:

    """(P3) StockCode ^\\d{5} filter, Price>0 & Qty>0, Revenue column.

    Returns (df_sales, cleaning_log) where the log is [(step, rows_removed)].

    """
    cleaning_log = []
    df_sales = df.copy()
    initial_rows = len(df_sales)

    # Casting to string to prevent regex conversion errors
    df_sales["StockCode"] = df_sales["StockCode"].astype(str).str.strip()

    # Keep only 5-digit standard stockcodes (e.g. 85123A is non-standard, M, D, POST are non-standard)
    mask_stockcode = df_sales["StockCode"].str.match(r"^\d{5}", na=False)

    # df_sales Dataframe with TRUE (allows to pass through) for rows with standard stockcodes and FALSE(completely dropped) for non-standard stockcodes, appending the changes into the cleaning_log list with the number of rows removed in this step.

    df_sales = df_sales[mask_stockcode]
    rows_after_stock = len(df_sales)
    cleaning_log.append(
        (
            "Removed non-standard stockcodes (e.g M, D, POST)",

            initial_rows - rows_after_stock
        )
    )
    # Keep only positive prices and quantities
    df_sales = df_sales[
        (df_sales["Price"] > 0) & (df_sales["Quantity"] > 0)
    ]

    # Appending the changes into the cleaning_log list with the number of rows removed in this step.
    rows_after_metrics = len(df_sales)
    cleaning_log.append(
        (
            "Removed rows with non-positive Price or Quantity",

            rows_after_stock - rows_after_metrics
        )
    )

    # Revenue calculation
    df_sales["Revenue"] = df_sales["Price"] * df_sales["Quantity"]

    return df_sales, cleaning_log


def load_and_clean(file_bytes: bytes):
    """(P3) Full pipeline with @st.cache_data: bytes -> (df_sales, df_returns, log, errors)."""
    raise NotImplementedError("P3 — in progress")
