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
try it with `sample_data/demo_bad_schema.xlsx`. For a fast demo with valid
data use `sample_data/demo_sales.xlsx` (~8.6k rows sampled from the full
dataset, whole invoices, returns included).

## Report filters

Once a file is loaded, the sidebar shows two dropdowns — **Period** (year)
and **Country** — that recompute the KPI row and all three slides,
including every chart and every insight sentence.

## Structure

```
├── app.py                  # main UI — orchestration only
├── ui/
│   ├── welcome.py          # Overview & Upload page: instructions, schema, uploader (P1)
│   ├── sidebar.py          # sidebar navigation buttons + file status (P1)
│   ├── filters.py          # period / country dropdowns applied to KPIs + slides
│   ├── kpis.py             # monthly KPI row with MoM deltas (P2)
│   └── theme.py            # shared CSS look & feel (P1)
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

Accuracy check with the original file: **1,003,214 sales rows + 19,104 return
rows** (verified against `online_retail_II.xlsx` — matches the notebook).
