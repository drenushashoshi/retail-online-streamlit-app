"""Generate demo_bad_schema.xlsx — a file with a wrong schema for the validation demo.

Intentional errors:
- the "Price" column is renamed to "Cost" (missing Price + unknown column)
- the "Country" column is missing entirely
- "Quantity" contains non-numeric text

Run with: python sample_data/make_demo_bad_schema.py
"""
from pathlib import Path

import pandas as pd

df = pd.DataFrame(
    {
        "Invoice": ["489434", "489435", "489436"],
        "StockCode": ["85048", "79323P", "22350"],
        "Description": [
            "15CM CHRISTMAS GLASS BALL 20 LIGHTS",
            "PINK CHERRY LIGHTS",
            "CAT BOWL",
        ],
        "Quantity": [12, "six", 24],
        "InvoiceDate": pd.to_datetime(
            ["2009-12-01 07:45", "2009-12-01 07:45", "2009-12-01 09:06"]
        ),
        "Cost": [6.95, 6.75, 2.55],
        "Customer ID": [13085, 13085, 13078],
    }
)

out = Path(__file__).parent / "demo_bad_schema.xlsx"
df.to_excel(out, index=False, sheet_name="Sales")
print(f"Created: {out}")
