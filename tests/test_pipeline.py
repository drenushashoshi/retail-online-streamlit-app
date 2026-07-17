"""Pipeline tests — each person adds the tests for their own step.

Here: step 0 tests (validation, P1).
Run with: `python -m pytest` from the repo root.
"""
from __future__ import annotations
from pipeline.aggregate import monthly_revenue, markets_summary, top_products
from slides.engines import _build_product_insight, _build_market_insight
import pandas as pd
import pytest

from pipeline.clean import split_returns, clean_sales, load_and_clean
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

# --- clean_sales: cleaning (P3) --------------------------------------------


def test_clean_sales_filters_stockcodes_properly():
    """Verify standard codes, alphanumeric variations are kept, and administrative codes are dropped."""
    raw_data = {
        "Invoice": ["100", "200", "300", "400", "500"],
        "StockCode": [
            "85123A",  # Valid: 5 digits + suffix alpha (KEEP)
            22423,     # Valid: Pure 5-digit number (KEEP)
            "POST",    # Invalid: Administrative alpha code (DROP)
            "1234",    # Invalid: Too short (DROP)
            "M",       # Invalid: Manual entry code (DROP)
        ],
        "Price": [2.55, 10.0, 15.0, 1.0, 50.0],
        "Quantity": [6, 2, 1, 10, 1],
    }
    df = pd.DataFrame(raw_data)

    df_sales, log = clean_sales(df)

    # 3 rows should be dropped (POST, 1234, M), leaving 2 rows
    assert len(df_sales) == 2
    assert list(df_sales["StockCode"]) == ["85123A", "22423"]
    assert log[0] == ("Removed non-standard stockcodes (e.g M, D, POST)", 3)


def test_clean_sales_filters_positive_metrics_and_calculates_revenue():
    """Verify non-positive Prices or Quantities are excluded, and Revenue is correct."""
    raw_data = {
        "Invoice": ["1", "2", "3", "4", "5"],
        "StockCode": ["22423", "22423", "22423", "22423", "22423"],
        "Price": [2.0, 0.0, -1.5, 4.0, 3.5],  # 0.0 and negative should be dropped
        "Quantity": [10, 5, 2, -5, 4],       # negative should be dropped
    }
    df = pd.DataFrame(raw_data)

    df_sales, log = clean_sales(df)

    # Only row 1 (2.0 * 10) and row 5 (3.5 * 4) should pass
    assert len(df_sales) == 2
    assert list(df_sales["Revenue"]) == [20.0, 14.0]
    assert log[1] == ("Removed rows with non-positive Price or Quantity", 3)


def test_clean_sales_handles_empty_dataframe_gracefully():
    """Ensure clean_sales returns empty datasets with correct schema columns instead of crashing."""
    df_empty = pd.DataFrame(columns=["Invoice", "StockCode", "Price", "Quantity"])
    
    df_sales, log = clean_sales(df_empty)
    
    assert df_sales.empty
    assert "Revenue" in df_sales.columns
    assert log[0][1] == 0
    assert log[1][1] == 0


# --- load_and_clean: full pipeline (P3) -------------------------------------


def test_load_and_clean_handles_corrupt_bytes_without_crashing():
    """Verify that file reading exceptions log a proper error message and do not trigger a crash."""
    corrupt_bytes = b"Not a real excel workbook format"
    
    df_sales, df_returns, log, errors = load_and_clean(corrupt_bytes)
    
    assert df_sales.empty
    assert df_returns.empty
    assert len(errors) == 1
    assert "Error reading Excel file:" in errors[0]


def test_load_and_clean_multi_sheet_deduplication_and_split():
    """Test full assembly: cross-sheet duplicates removal, parsing returns, and final cleaning."""
    import io

    # Construct an in-memory valid multisheet workbook mock
    excel_buffer = io.BytesIO()
    
    sheet1_data = {
        "Invoice": ["489434", "C489444"],  # Valid Sale, Valid Return
        "StockCode": ["21871", "21871"],
        "Price": [4.15, 4.15],
        "Quantity": [6, 1],
        "Description": ["ITEM A", "ITEM A"],
        "InvoiceDate": ["2009-12-01 07:45", "2009-12-01 07:45"],
        "Customer ID": [13085.0, 13085.0],
        "Country": ["United Kingdom", "United Kingdom"],
    }
    sheet2_data = {
        "Invoice": ["489434", "489435"],  # Cross-sheet duplicate with sheet1, and a new unique sale
        "StockCode": ["21871", "21872"],
        "Price": [4.15, 1.25],
        "Quantity": [6, 12],
        "Description": ["ITEM A", "ITEM B"],
        "InvoiceDate": ["2009-12-01 07:45", "2009-12-01 07:48"],
        "Customer ID": [13085.0, 13085.0],
        "Country": ["United Kingdom", "United Kingdom"],
    }
    
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        pd.DataFrame(sheet1_data).to_excel(writer, sheet_name="Sheet 1", index=False)
        pd.DataFrame(sheet2_data).to_excel(writer, sheet_name="Sheet 2", index=False)
        
    file_bytes = excel_buffer.getvalue()

    # Run full integrated pipeline
    df_sales, df_returns, log, errors = load_and_clean(file_bytes)

    assert len(errors) == 0
    # 4 initial rows combined -> 1 exact duplicate dropped -> 3 left.
    # Out of 3: 1 is a Cancellation return ('C'), 2 are valid sales rows.
    assert len(df_sales) == 2
    assert len(df_returns) == 1
    
    # Assert logs match expected messaging
    assert any("Initial rows from all sheets" in entry[0] for entry in log)
    assert any("Total dropped duplicate rows" in entry[0] for entry in log)
    assert any("Total rows in returns after splitting" in entry[0] for entry in log)
    assert any("Total rows in sales after cleaning as final" in entry[0] for entry in log)

# --- monthly_revenue: revenue aggregation -------------------------------------

def test_monthly_revenue_happy_path():
    # Arrange: Create 2 months of standard data exactly 1 year apart to test MoM and YoY
    data = {
        "InvoiceDate": [
            pd.Timestamp("2025-01-15"), 
            pd.Timestamp("2025-02-15"), 
            pd.Timestamp("2026-01-15")
        ],
        "Revenue": [1000.0, 1500.0, 2000.0]
    }
    df = pd.DataFrame(data)

    # Act
    result = monthly_revenue(df)

    # Assert
    assert len(result) == 3
    assert list(result.columns) == ["Month", "Revenue", "MoM %", "YoY %"]
    
    # Check Month 2 MoM calculation: ((1500 - 1000) / 1000) * 100 = 50%
    assert result.loc[1, "MoM %"] == 50.0
    
    # Check Year 2 YoY calculation: ((2000 - 1000) / 1000) * 100 = 100%
    assert result.loc[2, "YoY %"] == 100.0


def test_monthly_revenue_empty_dataframe():
    # Arrange
    df_empty = pd.DataFrame(columns=["InvoiceDate", "Revenue"])

    # Act
    result = monthly_revenue(df_empty)

    # Assert
    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert list(result.columns) == ["Month", "Revenue", "MoM %", "YoY %"]


def test_monthly_revenue_missing_columns():
    # Arrange: Missing critical calculation column
    df_broken = pd.DataFrame({"InvoiceDate": [pd.Timestamp("2025-01-15")]})

    # Act & Assert: Ensure it raises a KeyError cleanly if the pipeline contract is broken
    with pytest.raises(KeyError):
        monthly_revenue(df_broken)


# --- top_products & markets_summary: P4 aggregations ------------------------


def test_top_products_ranks_by_revenue_not_row_count():
    """A product with fewer rows but higher revenue must outrank a high-row, low-revenue product."""
    df = pd.DataFrame(
        {
            "Description": ["Bulk Lines", "Bulk Lines", "Bulk Lines", "Premium Gift"],
            "Revenue": [10.0, 10.0, 10.0, 500.0],
            "Invoice": ["A", "B", "C", "D"],
            "Country": ["United Kingdom"] * 4,
        }
    )

    result = top_products(df)

    assert len(result) == 2
    assert result.iloc[0]["Description"] == "Premium Gift"
    assert result.iloc[0]["Revenue"] == 500.0
    assert result.iloc[0]["Line Items"] == 1
    assert result.iloc[1]["Description"] == "Bulk Lines"
    assert result.iloc[1]["Revenue"] == 30.0
    assert result.iloc[1]["Line Items"] == 3


def test_top_products_returns_top_10_only():
    descriptions = [f"Product {idx}" for idx in range(12)]
    df = pd.DataFrame(
        {
            "Description": descriptions,
            "Revenue": [float(100 - idx) for idx in range(12)],
            "Invoice": descriptions,
            "Country": ["United Kingdom"] * 12,
        }
    )

    result = top_products(df)

    assert len(result) == 10
    assert result.iloc[0]["Description"] == "Product 0"
    assert result.iloc[0]["Revenue"] == 100.0


def test_top_products_empty_dataframe():
    df_empty = pd.DataFrame(columns=["Description", "Revenue", "Invoice", "Country"])

    result = top_products(df_empty)

    assert result.empty
    assert list(result.columns) == ["Description", "Revenue", "Line Items"]


def test_markets_summary_calculates_avg_revenue_per_order():
    df = pd.DataFrame(
        {
            "Country": ["Netherlands", "Netherlands", "United Kingdom", "United Kingdom"],
            "Invoice": ["NL-1", "NL-1", "UK-1", "UK-2"],
            "Revenue": [1000.0, 500.0, 80.0, 120.0],
            "Description": ["A", "B", "C", "D"],
        }
    )

    result = markets_summary(df)

    netherlands = result.loc[result["Country"] == "Netherlands"].iloc[0]
    united_kingdom = result.loc[result["Country"] == "United Kingdom"].iloc[0]

    assert netherlands["Orders"] == 1
    assert netherlands["Revenue"] == 1500.0
    assert netherlands["Avg Revenue Per Order"] == 1500.0
    assert united_kingdom["Orders"] == 2
    assert united_kingdom["Avg Revenue Per Order"] == 100.0
    assert result.iloc[0]["Country"] == "Netherlands"


def test_markets_summary_empty_dataframe():
    df_empty = pd.DataFrame(columns=["Country", "Invoice", "Revenue", "Description"])

    result = markets_summary(df_empty)

    assert result.empty
    assert list(result.columns) == ["Country", "Revenue", "Orders", "Avg Revenue Per Order"]


def test_build_product_insight_same_leader_returns_no_false_claim():
    df = pd.DataFrame(
        {
            "Description": ["MUG", "DESK"],
            "Revenue": [1500.0, 900.0],
            "Line Items": [3, 1],
        }
    )
    result = _build_product_insight(df, total_revenue=2400.0)

    assert "despite only" not in result
    assert "leads on both revenue and line items (3)" in result


def test_build_product_insight_diverging_leaders_states_comparison():
    df = pd.DataFrame(
        {
            "Description": ["Premium Gift", "Bulk Lines"],
            "Revenue": [500.0, 30.0],
            "Line Items": [1, 3],
        }
    )
    result = _build_product_insight(df, total_revenue=530.0)

    assert "outsells **Bulk Lines**" in result
    assert "3 vs 1" in result


def test_build_market_insight_baseline_equals_top_market():
    df = pd.DataFrame(
        {
            "Country": ["Germany", "Luxembourg"],
            "Revenue": [10000.0, 500.0],
            "Orders": [50, 1],
            "Avg Revenue Per Order": [200.0, 500.0],
        }
    )
    result = _build_market_insight(df)

    assert "is both the largest market by revenue" in result
    assert "Germany" in result


def test_markets_summary_excludes_low_order_countries_below_threshold():
    df = pd.DataFrame(
        {
            "Country": ["Germany"] * 6 + ["Luxembourg"] * 2,
            "Invoice": [f"DE-{i}" for i in range(6)] + ["LUX-1", "LUX-2"],
            "Revenue": [100.0] * 6 + [5000.0, 100.0],
            "Description": ["A"] * 8,
        }
    )

    result = markets_summary(df)

    assert "Luxembourg" not in result["Country"].tolist()
    assert "Germany" in result["Country"].tolist()
    # --- P5 task tests (returns_summary & top_customers) -------------------------

def test_returns_summary_handles_no_revenue_column():
    # Mock data where df_returns lacks a Revenue column initially
    sales_df = pd.DataFrame({
        "InvoiceDate": [pd.Timestamp("2026-01-15"), pd.Timestamp("2026-01-20")],
        "Revenue": [1000.0, 500.0]
    })
    returns_df = pd.DataFrame({
        "InvoiceDate": [pd.Timestamp("2026-01-18")],
        "Price": [12.75],
        "Quantity": [-2],
        "Description": ["REGENCY CAKESTAND"]
    })

    from pipeline.aggregate import returns_summary
    result = returns_summary(sales_df, returns_df)

    assert len(result) == 1
    assert "Return Rate %" in result.columns
    # Returned Revenue should be absolute value: 12.75 * 2 = 25.5
    assert result.iloc[0]["Returned Revenue"] == 25.5
    # Return Rate %: (25.5 / 1500) * 100 = 1.7%
    assert round(result.iloc[0]["Return Rate %"], 2) == 1.70
    assert result.iloc[0]["Most Returned Product"] == "REGENCY CAKESTAND"


def test_top_customers_returns_sorted_descending():
    df = pd.DataFrame({
        "Customer ID": [12345.0, 12345.0, 67890.0, 99999.0],
        "Revenue": [100.0, 200.0, 500.0, 50.0]
    })

    from pipeline.aggregate import top_customers
    result = top_customers(df)

    assert len(result) == 3
    # Top should be Customer 67890 (Revenue 500.0)
    assert result.iloc[0]["Customer ID"] == "67890"
    assert result.iloc[0]["Revenue"] == 500.0
    # Second should be Customer 12345 (Revenue 300.0)
    assert result.iloc[1]["Customer ID"] == "12345"
    assert result.iloc[1]["Revenue"] == 300.0


# --- report filters: period / country dropdowns ------------------------------


def make_filter_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Invoice": ["1", "2", "3", "4"],
            "InvoiceDate": pd.to_datetime(
                ["2010-03-01", "2010-07-15", "2011-01-10", "2011-06-20"]
            ),
            "Country": ["United Kingdom", "France", "France", "Germany"],
            "Revenue": [10.0, 20.0, 30.0, 40.0],
        }
    )


def test_period_options_lists_years_from_both_frames():
    from ui.filters import ALL_PERIODS, period_options

    sales = make_filter_df()
    returns = make_filter_df().assign(InvoiceDate=pd.to_datetime(["2009-12-05"] * 4))

    options = period_options(sales, returns)

    assert options == [ALL_PERIODS, "2009", "2010", "2011"]


def test_country_options_sorted_with_all_first():
    from ui.filters import ALL_COUNTRIES, country_options

    options = country_options(make_filter_df(), make_filter_df().iloc[0:0])

    assert options[0] == ALL_COUNTRIES
    assert options[1:] == ["France", "Germany", "United Kingdom"]


def test_apply_filters_by_year():
    from ui.filters import ALL_COUNTRIES, apply_filters

    result = apply_filters(make_filter_df(), "2010", ALL_COUNTRIES)

    assert result["Invoice"].tolist() == ["1", "2"]


def test_apply_filters_by_country():
    from ui.filters import ALL_PERIODS, apply_filters

    result = apply_filters(make_filter_df(), ALL_PERIODS, "France")

    assert result["Invoice"].tolist() == ["2", "3"]


def test_apply_filters_year_and_country_combined():
    from ui.filters import apply_filters

    result = apply_filters(make_filter_df(), "2011", "France")

    assert result["Invoice"].tolist() == ["3"]


def test_apply_filters_all_selections_keep_everything():
    from ui.filters import ALL_COUNTRIES, ALL_PERIODS, apply_filters

    df = make_filter_df()
    result = apply_filters(df, ALL_PERIODS, ALL_COUNTRIES)

    assert len(result) == len(df)


def test_apply_filters_empty_frame_passthrough():
    from ui.filters import apply_filters

    df_empty = make_filter_df().iloc[0:0]
    result = apply_filters(df_empty, "2010", "France")

    assert result.empty