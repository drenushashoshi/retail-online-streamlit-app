"""Pipeline tests — each person adds the tests for their own step.

Here: step 0 tests (validation, P1).
Run with: `python -m pytest` from the repo root.
"""
from __future__ import annotations

import pandas as pd

from pipeline.clean import split_returns
from pipeline.validate import (
    EXPECTED_COLUMNS,
    validate_extension,
    validate_workbook,
)


def make_valid_df() -> pd.DataFrame:
    """A small sheet that respects the Online Retail II schema."""
    return pd.DataFrame(
        {
            "Invoice": ["489434", "C489449"],
            "StockCode": ["85048", "22350"],
            "Description": ["15CM CHRISTMAS GLASS BALL", "CAT BOWL"],
            "Quantity": [12, -2],
            "InvoiceDate": pd.to_datetime(["2009-12-01 07:45", "2009-12-01 10:33"]),
            "Price": [6.95, 2.55],
            "Customer ID": [13085.0, 14237.0],
            "Country": ["United Kingdom", "United Kingdom"],
        }
    )


# --- validate_extension -----------------------------------------------------


def test_extension_xlsx_accepted():
    assert validate_extension("sales_june.xlsx") == []


def test_extension_uppercase_xlsx_accepted():
    assert validate_extension("SALES.XLSX") == []


def test_extension_csv_rejected():
    errors = validate_extension("sales.csv")
    assert len(errors) == 1
    assert ".xlsx" in errors[0]


# --- validate_workbook: schema ----------------------------------------------


def test_valid_schema_returns_empty_list():
    assert validate_workbook({"Year 2009-2010": make_valid_df()}) == []


def test_empty_workbook_rejected():
    errors = validate_workbook({})
    assert len(errors) == 1


def test_missing_column_reported_by_name():
    df = make_valid_df().drop(columns=["Country"])
    errors = validate_workbook({"Sheet1": df})
    assert any("Country" in e and "missing" in e for e in errors)


def test_unknown_column_reported():
    df = make_valid_df().rename(columns={"Price": "Cost"})
    errors = validate_workbook({"Sheet1": df})
    assert any("Price" in e for e in errors)  # Price is missing
    assert any("Cost" in e for e in errors)  # Cost is outside the schema


def test_surrounding_whitespace_in_column_names_tolerated():
    df = make_valid_df().rename(columns={"Price": " Price "})
    assert validate_workbook({"Sheet1": df}) == []


def test_empty_sheet_reported():
    df = make_valid_df().iloc[0:0]
    errors = validate_workbook({"Sheet1": df})
    assert any("no data rows" in e for e in errors)


def test_every_sheet_is_checked():
    good = make_valid_df()
    bad = make_valid_df().drop(columns=["Invoice"])
    errors = validate_workbook({"Year 2009-2010": good, "Year 2010-2011": bad})
    assert any("Year 2010-2011" in e for e in errors)
    assert not any("Year 2009-2010" in e for e in errors)


# --- validate_workbook: types -----------------------------------------------


def test_non_numeric_quantity_rejected():
    df = make_valid_df()
    df["Quantity"] = ["twelve", "two"]
    errors = validate_workbook({"Sheet1": df})
    assert any("Quantity" in e and "numeric" in e for e in errors)


def test_non_numeric_price_rejected():
    df = make_valid_df()
    df["Price"] = ["6,95 EUR", "2,55 EUR"]
    errors = validate_workbook({"Sheet1": df})
    assert any("Price" in e and "numeric" in e for e in errors)


def test_numbers_stored_as_text_accepted():
    # Excel sometimes stores numbers as text — if they convert, they are valid
    df = make_valid_df()
    df["Quantity"] = ["12", "-2"]
    assert validate_workbook({"Sheet1": df}) == []


def test_non_date_invoicedate_rejected():
    df = make_valid_df()
    df["InvoiceDate"] = ["yesterday", "today"]
    errors = validate_workbook({"Sheet1": df})
    assert any("InvoiceDate" in e and "date" in e for e in errors)


def test_numeric_invoicedate_rejected():
    df = make_valid_df()
    df["InvoiceDate"] = [42.0, 43.5]
    errors = validate_workbook({"Sheet1": df})
    assert any("InvoiceDate" in e for e in errors)


def test_expected_schema_has_8_columns():
    assert len(EXPECTED_COLUMNS) == 8


# --- split_returns: cleaning (P2) ------------------------------------------


def test_split_returns_strips_column_whitespace():
    df = make_valid_df().rename(columns={"Invoice": " Invoice ", "Country": " Country "})

    sales_raw, returns = split_returns(df)

    assert "Invoice" in sales_raw.columns
    assert "Country" in sales_raw.columns
    assert " Invoice " not in sales_raw.columns
    assert " Country " not in sales_raw.columns
    assert "Invoice" in returns.columns


def test_split_returns_drops_exact_duplicates_before_split():
    df = pd.concat([make_valid_df(), make_valid_df()], ignore_index=True)

    sales_raw, returns = split_returns(df)

    assert len(sales_raw) == 1
    assert len(returns) == 1


def test_split_returns_preserves_total_rows_after_duplicate_removal():
    df = pd.concat([make_valid_df(), make_valid_df(), make_valid_df().iloc[[0]]], ignore_index=True)
    df_after_duplicates_removed = df.copy().drop_duplicates()

    sales_raw, df_returns = split_returns(df)

    assert len(sales_raw) + len(df_returns) == len(df_after_duplicates_removed)


def test_split_returns_moves_c_invoices_to_returns_dataframe():
    sales_raw, df_returns = split_returns(make_valid_df())

    assert sales_raw["Invoice"].tolist() == ["489434"]
    assert df_returns["Invoice"].tolist() == ["C489449"]


def test_split_returns_keeps_non_c_invoices_as_sales():
    df = make_valid_df()
    df["Invoice"] = ["489434", "489435"]

    sales_raw, returns = split_returns(df)

    assert sales_raw["Invoice"].tolist() == ["489434", "489435"]
    assert returns.empty


def test_split_returns_numeric_invoice_values_do_not_crash():
    df = make_valid_df()
    df["Invoice"] = [489434, 489435]

    sales_raw, returns = split_returns(df)

    assert sales_raw["Invoice"].tolist() == [489434, 489435]
    assert returns.empty


def test_split_returns_missing_invoice_column_raises_clear_valueerror():
    df = make_valid_df().drop(columns=["Invoice"])

    try:
        split_returns(df)
        assert False, "Expected ValueError for missing Invoice column"
    except ValueError as exc:
        assert 'Missing required column: "Invoice".' == str(exc)


def test_split_returns_empty_dataframe_returns_empty_sales_and_returns():
    df = make_valid_df().iloc[0:0]

    sales_raw, returns = split_returns(df)

    assert sales_raw.empty
    assert returns.empty
    assert sales_raw.columns.tolist() == EXPECTED_COLUMNS
    assert returns.columns.tolist() == EXPECTED_COLUMNS
