"""Pipeline steps 1-4: data cleaning.

Owners: P2 (part 1) + P3 (part 2) — TODO, in progress.
Contracts were agreed in the mob session; do not change signatures
without telling the team.
"""
from __future__ import annotations

import pandas as pd
import io
import streamlit as st


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


@st.cache_data(
    show_spinner="Processing Excel file.. Please wait"
)

def load_and_clean(file_bytes: bytes):
    """(P3) Full pipeline with @st.cache_data: bytes -> (df_sales, df_returns, log, errors)."""

    errors = []
    log = []

    # Read all sheets using calamine engine for speed
    try:
        sheet_dict = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, engine="calamine")
    except Exception as e:
        errors.append(f"Error reading Excel file: {e}")
        return pd.DataFrame(), pd.DataFrame(), log, errors

    # Combine all sheets into a single DataFrame
    df_raw = pd.concat(sheet_dict.values(), ignore_index=True)
    log.append(("Initial rows from all sheets", len(df_raw)))

    #Standardize column names by stripping whitespace and drop duplicates
    df_raw.columns = df_raw.columns.str.strip()

    #Standardize identifier types to prevent mixed-type mismatches (e.g str vs int64) across different sheets
    if "Invoice" in df_raw.columns:
        df_raw["Invoice"] = df_raw["Invoice"].astype(str).str.strip()
    if "StockCode" in df_raw.columns:
        df_raw["StockCode"] = df_raw["StockCode"].astype(str).str.strip()

    #Dropping duplicates and logging the number of rows dropped
    len_before_dedup = len(df_raw)
    df_raw = df_raw.drop_duplicates()
    log.append(("Total dropped duplicate rows", len_before_dedup - len(df_raw)))

    # Split returns based on P2 logic
    df_sales_raw, df_returns = split_returns(df_raw)
    log.append(("Total rows in returns after splitting", len(df_returns)))

    # Final sales cleaning and logging 
    df_sales, sales_cleaning_log = clean_sales(df_sales_raw)
    log.extend(sales_cleaning_log)
    log.append(("Total rows in sales after cleaning as final", len(df_sales)))

    return df_sales, df_returns, log, errors




