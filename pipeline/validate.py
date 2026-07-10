"""Pipeline step 0: file and schema validation.

Owner: P1 (Drenusha)

Rules:
- only the .xlsx format is accepted
- every sheet of the workbook must have exactly the expected schema columns
- Quantity and Price must be numeric, InvoiceDate must be a date
- error messages are shown to the manager as-is, so they must be clear
"""
from __future__ import annotations

import io

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

NUMERIC_COLUMNS = ["Quantity", "Price"]
DATE_COLUMNS = ["InvoiceDate"]

SCHEMA_ERROR_HEADER = "This file does not match the expected columns / schema."


def validate_extension(filename: str) -> list[str]:
    """Return an error if the file is not .xlsx (empty list = OK)."""
    if not str(filename).lower().endswith(".xlsx"):
        return [
            f'Only the .xlsx format is accepted — the file "{filename}" is not xlsx.'
        ]
    return []


def read_workbook(file_bytes: bytes) -> dict[str, pd.DataFrame]:
    """Read every sheet of the workbook as {sheet_name: DataFrame}.

    Tries the fast `calamine` engine (45MB file -> seconds); if it is
    missing, falls back to `openpyxl`.
    """
    try:
        return pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, engine="calamine")
    except ImportError:
        return pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, engine="openpyxl")


def validate_workbook(sheets: dict[str, pd.DataFrame]) -> list[str]:
    """Validate the schema of every sheet. Returns a list of errors; empty = valid."""
    if not sheets:
        return ["The file does not contain any sheet with data."]

    errors: list[str] = []
    for sheet_name, df in sheets.items():
        errors.extend(_validate_sheet(sheet_name, df))
    return errors


def _validate_sheet(sheet_name: str, df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    # Column names are compared without surrounding whitespace — clean.py
    # strips them later, so they must not fail validation here.
    actual = [str(c).strip() for c in df.columns]

    missing = [c for c in EXPECTED_COLUMNS if c not in actual]
    extra = [c for c in actual if c not in EXPECTED_COLUMNS]

    if missing:
        errors.append(
            f'Sheet "{sheet_name}": missing expected columns: {", ".join(missing)}.'
        )
    if extra:
        errors.append(
            f'Sheet "{sheet_name}": unknown columns outside the schema: {", ".join(extra)}.'
        )

    if df.empty:
        errors.append(f'Sheet "{sheet_name}": contains no data rows.')

    # Types are only checked for columns that exist
    df = df.copy()
    df.columns = actual

    for col in NUMERIC_COLUMNS:
        if col in df.columns and not _is_numeric(df[col]):
            example = _first_bad_numeric(df[col])
            errors.append(
                f'Sheet "{sheet_name}": column "{col}" must be numeric, '
                f'but contains non-numeric values (e.g. "{example}").'
            )

    for col in DATE_COLUMNS:
        if col in df.columns and not _is_datetime(df[col]):
            example = _first_bad_datetime(df[col])
            errors.append(
                f'Sheet "{sheet_name}": column "{col}" must be a date, '
                f'but contains values that cannot be read as dates (e.g. "{example}").'
            )

    return errors


def _is_numeric(series: pd.Series) -> bool:
    """True if the column is numeric or every non-empty value converts to a number."""
    if pd.api.types.is_numeric_dtype(series):
        return True
    converted = pd.to_numeric(series.dropna(), errors="coerce")
    return not converted.isna().any()


def _first_bad_numeric(series: pd.Series):
    values = series.dropna()
    converted = pd.to_numeric(values, errors="coerce")
    bad = values[converted.isna()]
    return bad.iloc[0] if len(bad) else values.iloc[0]


def _is_datetime(series: pd.Series) -> bool:
    """True if the column is datetime or every non-empty value parses as a date."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if pd.api.types.is_numeric_dtype(series):
        return False  # plain numbers are not accepted as dates
    converted = pd.to_datetime(series.dropna(), errors="coerce", format="mixed")
    return not converted.isna().any()


def _first_bad_datetime(series: pd.Series):
    values = series.dropna()
    if pd.api.types.is_numeric_dtype(values):
        return values.iloc[0]
    converted = pd.to_datetime(values, errors="coerce", format="mixed")
    bad = values[converted.isna()]
    return bad.iloc[0] if len(bad) else values.iloc[0]
