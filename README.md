# Retail Online — Automated Reporting (Streamlit) 🐢

Team Squirtle's Streamlit app that automates the Project_1_EDA analyses
(Online Retail II) into a monthly report for the **sales manager**: upload
the sales xlsx, the app validates the schema and generates **three slides**
with numbers, interactive charts, and insights computed from the data.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests:

```bash
python -m pytest
```

## Expected file schema (every sheet)

| Column | Type |
|---|---|
| Invoice | text |
| StockCode | text |
| Description | text |
| Quantity | number |
| InvoiceDate | date |
| Price | number |
| Customer ID | number |
| Country | text |

A file that doesn't match the schema is rejected with a clear message —
try it with `sample_data/demo_bad_schema.xlsx`.

## Structure

```
├── app.py                  # main UI — orchestration only
├── pipeline/
│   ├── validate.py         # step 0: schema validation (P1)
│   ├── clean.py            # steps 1-4: duplicates, returns split, filters, Revenue (P2+P3)
│   └── aggregate.py        # aggregations for the slides (P4+P5)
├── slides/
│   ├── pulse.py            # Slide 1 — business pulse (P3)
│   ├── engines.py          # Slide 2 — revenue engines (P4)
│   └── leaks.py            # Slide 3 — leaks & key customers (P5)
├── tests/test_pipeline.py  # each person adds tests for their own step
└── sample_data/            # demo samples (the full 45MB file does NOT go in the repo)
```

## Workflow

- `main` is protected — every change lands via **PR + 1 review**
  (round-robin: P1→P2→P3→P4→P5→P1).
- Everyone works on their own branch `name/part` (e.g. `drenusha/validate`).
- Streamlit Cloud auto-deploys from `main`.

Accuracy check with the original file: **1,003,214 sales rows + 19,104 return rows**.
