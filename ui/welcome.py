"""Overview & Upload page: hero, decision cards, expected schema, uploader.

Owner: P1 (Drenusha)

`render_home()` draws the landing page. On a successful upload it stores the
validated data in st.session_state so the slide pages (and the sidebar
status) can use it:
    st.session_state["file_bytes"] — raw xlsx bytes for load_and_clean()
    st.session_state["sheets"]     — validated {sheet_name: DataFrame}
    st.session_state["valid_file"] — {"name", "rows", "sheets"} for the sidebar
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
from ui.theme import ACCENTS

_DECISION_CARDS = [
    (
        "pulse",
        "💓",
        "How did we do?",
        "Monthly revenue trend with MoM % and YoY % vs last year.",
        "Stock and staffing for next month.",
    ),
    (
        "engines",
        "🚀",
        "What's driving the month?",
        "Top products by revenue and top-value markets.",
        "What to promote, and who is VIP.",
    ),
    (
        "leaks",
        "🔍",
        "Where is money leaking?",
        "Returns, return rate % and revenue concentration.",
        "What to investigate, who to call.",
    ),
]


def render_home() -> None:
    """Render the Overview & Upload page."""
    st.markdown(
        '<div class="hero-title">Automated Monthly Sales Report</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-sub">Upload the month\'s sales file and get a decision-ready '
        "report in seconds — three slides, three decisions, zero spreadsheets.</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(3, gap="medium")
    for col, (key, emoji, question, see, decision) in zip(cols, _DECISION_CARDS):
        with col:
            st.markdown(
                f'<div class="dec-card" style="--accent:{ACCENTS[key]}">'
                f'<span class="dec-emoji">{emoji}</span>'
                f'<div class="dec-q">{question}</div>'
                f'<div class="dec-see">{see}</div>'
                f'<div class="dec-label">You decide</div>'
                f'<div class="dec-text">{decision}</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Open slide →", key=f"open_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

    st.write("")

    with st.expander("📋 What should the file look like? (expected schema)"):
        st.dataframe(
            pd.DataFrame(
                {
                    "Column": EXPECTED_COLUMNS,
                    "Type": ["text", "text", "text", "number", "date", "number", "number", "text"],
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
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Every sheet in the workbook must have exactly these columns.")

    uploaded = st.file_uploader(
        "**Upload the sales file (.xlsx)**",
        type=["xlsx"],
        accept_multiple_files=False,
        help="Only the .xlsx format is accepted. The schema must match the table above.",
    )

    if uploaded is None:
        # The uploader widget forgets its file when the manager visits a slide
        # page and comes back — but the validated data is still in session
        # state, so the summary (metrics + peek) must not disappear with it.
        file_info = st.session_state.get("valid_file")
        sheets = st.session_state.get("sheets")
        if file_info and sheets:
            _render_loaded_summary(
                f'📄 **{file_info["name"]}** is loaded — open the slides from the sidebar. '
                "Upload a new file any time to refresh the report.",
                sheets,
            )
        else:
            st.info("⬆️ Upload an .xlsx file to generate the report.")
        return

    raw = uploaded.getvalue()

    # Same file already validated this session (e.g. a filter change reran the
    # page) — reuse the stored sheets instead of re-reading a possibly-45MB file.
    already_validated = (
        st.session_state.get("file_bytes") == raw and "sheets" in st.session_state
    )

    errors = [] if already_validated else validate_extension(uploaded.name)
    sheets: dict[str, pd.DataFrame] = st.session_state.get("sheets", {}) if already_validated else {}

    if not errors and not already_validated:
        with st.spinner("Reading the file..."):
            try:
                sheets = read_workbook(raw)
            except Exception:
                errors = [
                    "The file could not be read as xlsx — it may be corrupted "
                    "or saved in a different format."
                ]
        if not errors:
            errors = validate_workbook(sheets)

    if errors:
        # A rejected file must not leave a stale report active. Clear any
        # previously loaded file so the KPI row, slides, and sidebar reset to
        # the empty state instead of silently showing the old file's data.
        had_stale = any(
            key in st.session_state for key in ("file_bytes", "sheets", "valid_file")
        )
        for stale_key in ("file_bytes", "sheets", "valid_file"):
            st.session_state.pop(stale_key, None)

        # The sidebar is drawn before this page runs, so it still shows the old
        # file — rerun once so it resets too. The rerun re-enters here, errors
        # again with clean state (had_stale now False), and stops.
        if had_stale:
            st.rerun()

        st.error(
            f"**{SCHEMA_ERROR_HEADER}**\n\n"
            + "\n".join(f"- {e}" for e in errors)
            + "\n\nFix the file to match the schema above and try again."
        )
        return

    total_rows = sum(len(df) for df in sheets.values())
    st.session_state["file_bytes"] = raw
    st.session_state["sheets"] = sheets
    st.session_state["valid_file"] = {
        "name": uploaded.name,
        "rows": total_rows,
        "sheets": len(sheets),
    }

    # First run with a new file: the sidebar (already drawn) still shows the old
    # status — rerun once so it updates. The rerun is cheap: already_validated
    # short-circuits the re-read above.
    if not already_validated:
        st.rerun()

    _render_loaded_summary(
        f"✅ **{uploaded.name}** validated successfully — your report is ready.", sheets
    )


def _render_loaded_summary(message: str, sheets: dict[str, pd.DataFrame]) -> None:
    """Success message + file metrics + first-rows peek for a loaded file."""
    st.success(message)

    total_rows = sum(len(df) for df in sheets.values())
    m1, m2, m3 = st.columns(3)
    m1.metric("Rows of sales data", f"{total_rows:,}")
    m2.metric("Period covered", _period_covered(sheets))
    m3.metric("Markets", _market_count(sheets))

    # PyArrow mismatch-type issues can occur if we don't enforce strict types on the preview DataFrame.
    with st.expander(":eyes: Peek at the first rows"):
        preview = next(iter(sheets.values())).head(5).copy()
        
        # Standardize preview column headers to ensure strict matching
        preview.columns = preview.columns.str.strip()
        
        # 1. Cast generic text columns to strict strings (Stops Arrow from type guessing)
        text_cols = ["Invoice", "StockCode", "Description", "Country"]
        for col in text_cols:
            if col in preview.columns:
                preview[col] = preview[col].astype(str).str.strip()
        
        # 2. Enforce Datetime format safely
        if "InvoiceDate" in preview.columns:
            preview["InvoiceDate"] = pd.to_datetime(preview["InvoiceDate"], errors="coerce")
            
        # 3. Enforce Numeric Floats safely
        if "Price" in preview.columns:
            preview["Price"] = pd.to_numeric(preview["Price"], errors="coerce").astype("float64")
            
        # 4. Enforce Nullable Integers (Converts 13085.0 -> 13085, handles missing data)
        nullable_int_cols = ["Quantity", "Customer ID"]
        for col in nullable_int_cols:
            if col in preview.columns:
                preview[col] = pd.to_numeric(preview[col], errors="coerce").astype("Int64")

        st.dataframe(preview, hide_index=True, use_container_width=True)
    # --------------------------------------------

    st.info("⬅️ Open the three slides from the sidebar — or with the buttons above.")


def _period_covered(sheets: dict[str, pd.DataFrame]) -> str:
    """'Dec 2009 – Dec 2011' across all sheets; '—' if dates can't be read."""
    try:
        dates = pd.concat(
            [pd.to_datetime(df["InvoiceDate"], errors="coerce", format="mixed") for df in sheets.values()]
        ).dropna()
        if dates.empty:
            return "—"
        # Short year ('Dec 09') — the full form clips inside st.metric at 3 columns
        return f"{dates.min():%b %y} – {dates.max():%b %y}"
    except Exception:
        return "—"


def _market_count(sheets: dict[str, pd.DataFrame]) -> str:
    try:
        countries = pd.concat([df["Country"] for df in sheets.values()]).dropna()
        return f"{countries.nunique()}"
    except Exception:
        return "—"