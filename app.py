"""Automated sales report — Team Squirtle.

app.py only orchestrates; the logic lives in pipeline/ and slides/.
This version contains P1's slice (welcome page + uploader + validation).
The P2-P5 sections get wired up in the integration session — see the
TODO notes below.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from pipeline.validate import (
    EXPECTED_COLUMNS,
    SCHEMA_ERROR_HEADER,
    read_workbook,
    validate_extension,
    validate_workbook,
)

st.set_page_config(
    page_title="Sales Report — Squirtle",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# P1 — Welcome page: instructions, expected schema, uploader, error display
# ---------------------------------------------------------------------------

st.title("📊 Automated Monthly Sales Report")
st.caption("Team Squirtle · Dataset: Online Retail II")

st.markdown(
    """
**How it works** — three steps:

1. **Upload** the sales file in **.xlsx** format (only xlsx is accepted).
2. The app **validates the schema** — if something doesn't match, you see exactly what.
3. Scroll down to see **three slides** with the numbers, charts, and insights for decision-making.
"""
)

with st.expander("📋 Expected file schema (every sheet)", expanded=False):
    st.table(
        pd.DataFrame(
            {
                "Column": EXPECTED_COLUMNS,
                "Type": [
                    "text",
                    "text",
                    "text",
                    "number",
                    "date",
                    "number",
                    "number",
                    "text",
                ],
                "Example": [
                    "489434",
                    "85048",
                    "15CM CHRISTMAS GLASS BALL 20 LIGHTS",
                    "12",
                    "2009-12-01 07:45",
                    "6.95",
                    "13085",
                    "United Kingdom",
                ],
            }
        )
    )

uploaded = st.file_uploader(
    "Upload the sales file (.xlsx)",
    type=["xlsx"],
    accept_multiple_files=False,
    help="Only the .xlsx format is accepted. The schema must match the table above.",
)

if uploaded is None:
    st.info("⬆️ Upload an .xlsx file to generate the report.")
    st.stop()

errors = validate_extension(uploaded.name)
sheets: dict[str, pd.DataFrame] = {}

if not errors:
    with st.spinner("Reading the file..."):
        try:
            sheets = read_workbook(uploaded.getvalue())
        except Exception:
            errors = [
                "The file could not be read as xlsx — it may be corrupted "
                "or saved in a different format."
            ]
    if not errors:
        errors = validate_workbook(sheets)

if errors:
    st.error(
        f"**{SCHEMA_ERROR_HEADER}**\n\n"
        + "\n".join(f"- {e}" for e in errors)
        + "\n\nFix the file to match the schema above and try again."
    )
    st.stop()

total_rows = sum(len(df) for df in sheets.values())
st.success(
    f"✅ File validated successfully — {total_rows:,} rows "
    f"across {len(sheets)} sheet(s). Preparing the report..."
)

# ---------------------------------------------------------------------------
# Integration session (Wednesday ~16:00) — the P2-P5 steps get wired here.
# Contracts: load_and_clean(bytes) -> (df_sales, df_returns, log, errors)
#            slide_pulse(df_sales) / slide_engines(df_sales) / slide_leaks(df_sales, df_returns)
# ---------------------------------------------------------------------------

st.divider()
st.subheader("📈 Key KPIs")
st.info("🔜 P2 — KPI row with MoM deltas: Revenue, orders, items, average order value, unique customers.")

st.divider()
st.subheader("Slide 1 — Business Pulse")
st.info("🔜 P3 — monthly revenue line + MoM % + YoY %.")

st.divider()
st.subheader("Slide 2 — Revenue Engines")
st.info("🔜 P4 — top products and markets with average revenue per order.")

st.divider()
st.subheader("Slide 3 — Leaks & Key Customers")
st.info("🔜 P5 — returns, return rate %, and customer concentration.")
