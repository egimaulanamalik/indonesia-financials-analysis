# Comparative Analysis of Selected Indonesian Listed Companies (2022–2025)

A end-to-end data analytics portfolio project covering financial statement analysis of 5 major Indonesian public companies across Banking, Telecommunications, Consumer Goods, and Technology sectors.

**[View Live Tableau Dashboard →](https://public.tableau.com/app/profile/muhammad.egi.maulana.malik/viz/ComparativeAnalysisofSelectedIndonesianListedCompanies2022-2025/Overview)**

---

## Companies Analysed

| Ticker | Company | Sector |
|--------|---------|--------|
| BBCA.JK | Bank Central Asia | Banking |
| BMRI.JK | Bank Mandiri | Banking |
| TLKM.JK | Telkom Indonesia | Telecommunications |
| ICBP.JK | Indofood CBP | Consumer Goods |
| GOTO.JK | GoTo Gojek Tokopedia | Technology |

---

## Project Architecture

```
Data Source (Yahoo Finance)
        ↓
Python ETL Pipeline (yfinance + pandas)
        ↓
Raw CSVs (data/raw/)
        ↓
PostgreSQL Database (indonesia_financials)
        ↓
SQL View (tableau_financials)
        ↓
Tableau Dashboard (Tableau Public)
```

---

## Dashboard Overview

The published dashboard contains 4 analytical views:

- **Revenue & Net Income Trend** — 4-year trend lines for all 5 companies, showing GOTO's path from deep losses (-90T IDR in 2022) to near-breakeven by 2025
- **Total Assets Comparison** — Balance sheet snapshot showing the structural size difference between banking and non-banking sectors
- **Capital Structure** — Stacked bar showing Liabilities vs. Equity mix per company, highlighting the distinct capital profiles of banks vs. tech/consumer companies
- **Profitability Margin** — Dual-axis combo chart (Revenue bars + Net Margin % line) with interactive company selector

---

## Technical Stack

| Layer | Tool |
|-------|------|
| Data Extraction | Python, yfinance, pandas |
| Storage (Raw) | CSV files |
| Database | PostgreSQL 16 |
| Data Modelling | SQL (views, normalised schema) |
| Visualisation | Tableau Desktop / Tableau Public |
| Version Control | Git, GitHub |

---

## Key Design Decisions

**Why long/normalized format for the database:**
Financial statement line items are not standardised across sectors (banks report Net Interest Income; consumer companies don't). Storing data in long format `(ticker, statement_type, line_item, period, value)` accommodates structural differences between companies without forcing NULL-heavy wide tables.

**Why a `core_metrics` lookup table:**
The inspection step revealed that only 6 line items exist under identical names across all 5 companies (Total Revenue, Net Income, Total Assets, Total Liabilities, Total Equity, Operating Expense). A lookup table tags these universal metrics with clean category labels, enabling Tableau to filter between "cross-company comparable" and "sector-specific" views from one data source.

**Why `LEFT JOIN` for the Tableau view:**
Using `LEFT JOIN core_metrics` (rather than `INNER JOIN`) preserves all 3,076 rows from `financial_statements` — including company-specific line items not in the core metrics list — while adding a boolean `is_core_metric` flag. A regular inner join would have silently dropped ~97% of the data.

---

## Repository Structure

```
├── data/
│   └── raw/
│       ├── income_statement_raw.csv
│       ├── balance_sheet_raw.csv
│       └── cashflow_raw.csv
├── scripts/
│   ├── extract_financials.py     # Pulls data from Yahoo Finance via yfinance
│   ├── inspect_line_items.py     # Audits line item consistency across companies
│   └── load_to_postgres.py       # Loads CSVs into PostgreSQL
├── sql/
│   ├── 01_create_tables.sql      # Schema: companies, financial_statements, core_metrics
│   └── 03_create_tableau_view.sql # Joined view used as Tableau data source
├── requirements.txt
└── README.md
```

---

## How to Reproduce

### Prerequisites
- Python 3.9+
- PostgreSQL 16
- Tableau Desktop (or Tableau Public)

### Setup

```bash
# Clone the repo
git clone https://github.com/egimaulanamalik/indonesia-financials-analysis.git
cd indonesia-financials-analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create PostgreSQL database
createdb indonesia_financials

# Run SQL schema
psql indonesia_financials -f sql/01_create_tables.sql

# Extract data
python scripts/extract_financials.py

# Inspect line items (optional)
python scripts/inspect_line_items.py

# Load to PostgreSQL
python scripts/load_to_postgres.py

# Run view
psql indonesia_financials -f sql/03_create_tableau_view.sql
```

Then connect Tableau Desktop to `localhost:5432 / indonesia_financials` and open the `tableau_financials` view.

---

## Key Findings

- **Banking sector dominance:** BBCA and BMRI hold Total Assets of 1,587T and 2,830T IDR respectively — roughly 10–60x larger than non-banking peers, reflecting the structural nature of bank balance sheets (customer deposits count as liabilities).
- **GOTO's profitability trajectory:** GoTo Gojek Tokopedia recorded a Net Margin of -611% in 2023, improving to near-breakeven by 2025 — the clearest illustration of a growth-stage tech company's path to profitability in this dataset.
- **Stable incumbents:** BBCA, TLKM, and ICBP all show consistent revenue growth and positive net margins throughout 2022–2025, reflecting their established market positions.

---

## Data Source

Financial statements sourced from Yahoo Finance via the [yfinance](https://github.com/ranaroussi/yfinance) Python library. All figures in IDR (Indonesian Rupiah), reported annually.

---

*Note:*

*1. yfinance is an unofficial Yahoo Finance data client. Data should be verified against IDX filings (idx.co.id) for production use.*

*2. Built as part of a data analytics portfolio targeting Finance or Data Analyst roles.*
