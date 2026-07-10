"""Pipeline steps 1-4: data cleaning.

Owners: P2 (part 1) + P3 (part 2) — TODO, in progress.
Contracts were agreed in the mob session; do not change signatures
without telling the team.
"""
from __future__ import annotations

import pandas as pd


def split_returns(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(P2) Strip column names, drop duplicates, split C-invoices.

    Returns (sales_raw, returns). Returned invoices are NOT dropped —
    Slide 3 needs them!
    """
    raise NotImplementedError("P2 — in progress")


def clean_sales(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    """(P3) StockCode ^\\d{5} filter, Price>0 & Qty>0, Revenue column.

    Returns (df_sales, cleaning_log) where the log is [(step, rows_removed)].
    """
    raise NotImplementedError("P3 — in progress")


def load_and_clean(file_bytes: bytes):
    """(P3) Full pipeline with @st.cache_data: bytes -> (df_sales, df_returns, log, errors)."""
    raise NotImplementedError("P3 — in progress")
