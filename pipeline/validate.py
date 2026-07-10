"""Pipeline step 0: file and schema validation.

Owner: P1 (Drenusha) — in progress.
"""
from __future__ import annotations

import pandas as pd

# Expected schema — the same for every sheet of the xlsx (Online Retail II)
EXPECTED_COLUMNS = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
]


def validate_workbook(sheets: dict[str, pd.DataFrame]) -> list[str]:
    """Validate the schema of every sheet. Returns a list of errors; empty = valid."""
    raise NotImplementedError("P1 — in progress")
