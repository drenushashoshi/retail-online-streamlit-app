"""Generate demo_sales.xlsx — a ~10k-row sample of Online Retail II for a fast demo.

Whole invoices are sampled (never single rows) so order-level numbers —
average order value, concentration, returns — stay meaningful. Sampling is
stratified per month and per sale/return so every month keeps both sales
and some C-invoices, and the raw rows are kept as-is (non-standard
stockcodes, negative quantities, ...) so the cleaning pipeline has real
work to do in the demo.

Run with:  python sample_data/make_demo_sales.py [path\\to\\online_retail_II.xlsx]
(the original 45MB file is NOT in the repo — see .gitignore)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

TARGET_ROWS = 10_000
SEED = 42

source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("online_retail_II.xlsx")
if not source.exists():
    sys.exit(f"Source file not found: {source} — pass the path to online_retail_II.xlsx")

print(f"Reading {source} ...")
try:
    sheets = pd.read_excel(source, sheet_name=None, engine="calamine")
except ImportError:
    sheets = pd.read_excel(source, sheet_name=None, engine="openpyxl")

total_rows = sum(len(df) for df in sheets.values())
sampled_sheets: dict[str, pd.DataFrame] = {}

for sheet_name, df in sheets.items():
    target_sheet_rows = TARGET_ROWS * len(df) / total_rows

    work = df.copy()
    work["_month"] = pd.to_datetime(work["InvoiceDate"], errors="coerce").dt.to_period("M")
    work["_is_return"] = work["Invoice"].astype(str).str.startswith("C")

    # Keep only real-product return lines (5-digit stockcodes) in the returns
    # pool — otherwise a single giant fee/adjustment row (e.g. AMAZON FEE)
    # dominates the small sample and distorts the Slide 3 return-rate story.
    # Sales rows keep their messy codes so the cleaning step has work to do.
    is_adjustment = work["_is_return"] & ~work["StockCode"].astype(str).str.match(r"^\d{5}")
    work = work[~is_adjustment]
    df = df[~is_adjustment]

    rows_per_invoice = len(work) / work["Invoice"].nunique()
    invoice_frac = min(1.0, target_sheet_rows / rows_per_invoice / work["Invoice"].nunique())

    keep_invoices: list = []
    for (_, _), group in work.groupby(["_month", "_is_return"]):
        invoices = group["Invoice"].drop_duplicates()
        n = max(1, round(len(invoices) * invoice_frac))
        keep_invoices.extend(invoices.sample(n=n, random_state=SEED).tolist())

    sampled = df[work["Invoice"].isin(keep_invoices)]
    sampled_sheets[sheet_name] = sampled
    print(f"  {sheet_name}: {len(sampled):,} rows from {len(df):,}")

out = Path(__file__).parent / "demo_sales.xlsx"
with pd.ExcelWriter(out, engine="openpyxl") as writer:
    for sheet_name, df in sampled_sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"Created: {out} ({sum(len(df) for df in sampled_sheets.values()):,} rows)")
