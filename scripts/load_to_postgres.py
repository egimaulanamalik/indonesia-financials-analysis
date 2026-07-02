"""
load_to_postgres.py

Loads the three raw CSVs (income statement, balance sheet, cash flow)
into the PostgreSQL `financial_statements` table, and populates the
`companies` and `core_metrics` reference tables.

Why we derive `companies` and `core_metrics` here instead of typing them
by hand in SQL: the ticker/company_name pairs and the "universal" line
items were both DISCOVERED programmatically in earlier steps (the
extraction script and the inspection script). Deriving them here keeps
the pipeline self-consistent -- if you add a 6th company later, this
script picks it up automatically instead of needing a manual SQL edit.
"""

import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

DATA_DIR = Path("data/raw")

# ---- DATABASE CONNECTION ----
# Why these specific connection details: matches the DBeaver connection
# you already set up -- local Homebrew Postgres, your Mac username as
# the DB user, no password (trust auth), default port 5432.
DB_USER = "egi"          # <-- change this if your Mac username differs
DB_NAME = "indonesia_financials"
DB_HOST = "localhost"
DB_PORT = "5432"

engine = create_engine(f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# These are the universal line items we found in Step 5 (the inspection
# script): present under the EXACT SAME name across all 5 companies.
# Mapped to a clean category label for easier filtering in Tableau.
CORE_METRICS_MAP = {
    "Total Revenue": "revenue",
    "Net Income": "net_income",
    "Total Assets": "total_assets",
    "Total Liabilities Net Minority Interest": "total_liabilities",
    "Total Equity Gross Minority Interest": "total_equity",
    "Operating Expense": "operating_expense",
}


def load_companies():
    """
    Build the companies table from whatever (ticker, company_name) pairs
    appear in the raw CSVs -- not hand-typed, so it stays accurate even
    if tickers are added/removed later.
    """
    frames = []
    for fname in ["income_statement_raw.csv", "balance_sheet_raw.csv", "cashflow_raw.csv"]:
        path = DATA_DIR / fname
        if path.exists():
            df = pd.read_csv(path, usecols=["ticker", "company_name"])
            frames.append(df)

    all_companies = pd.concat(frames, ignore_index=True).drop_duplicates()
    all_companies["sector"] = None  # filled in manually below

    # Why a manual sector mapping here rather than pulling it from
    # yfinance: yfinance's sector/industry labels are inconsistent in
    # granularity (and require an extra API call per ticker). Since we
    # only have 5 companies, hand-labeling sector is faster and more
    # reliable than adding another fragile API dependency.
    sector_map = {
        "BBCA.JK": "Banking",
        "BMRI.JK": "Banking",
        "TLKM.JK": "Telecommunications",
        "ICBP.JK": "Consumer Goods",
        "GOTO.JK": "Technology",
    }
    all_companies["sector"] = all_companies["ticker"].map(sector_map)

    all_companies.to_sql(
        "companies", engine, if_exists="append", index=False,
        method="multi"
    )
    print(f"Loaded {len(all_companies)} companies.")


def load_core_metrics():
    """
    Populate the core_metrics lookup table from the CORE_METRICS_MAP
    defined above. This table is what Tableau will join against to
    filter down to universal, cross-company-comparable KPIs.
    """
    df = pd.DataFrame(
        list(CORE_METRICS_MAP.items()),
        columns=["line_item", "metric_category"]
    )
    df.to_sql("core_metrics", engine, if_exists="append", index=False)
    print(f"Loaded {len(df)} core metric mappings.")


def load_statement(filename: str, statement_type: str):
    """
    Loads one raw CSV into financial_statements, tagging each row with
    its statement_type ('income', 'balance', 'cashflow').
    """
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  SKIPPED (not found): {filename}")
        return

    df = pd.read_csv(path)
    df["statement_type"] = statement_type

    # Keep only the columns financial_statements actually has.
    # company_name is dropped here because it now lives in `companies`
    # -- this IS the normalization payoff from Step 7.
    df = df[["ticker", "statement_type", "line_item", "period", "value"]]

    # Why dropna on value: yfinance occasionally returns NaN for a
    # line item in a period where it genuinely wasn't reported (not
    # every company reports every line item every year). Loading NaN
    # into a NUMERIC column would either fail or insert nulls that
    # complicate every downstream SUM/AVG; dropping them here is
    # cleaner since a missing fact is different from a zero fact.
    before = len(df)
    df = df.dropna(subset=["value"])
    dropped = before - len(df)

    df.to_sql(
        "financial_statements", engine, if_exists="append", index=False,
        method="multi", chunksize=500
    )
    print(f"  Loaded {len(df)} rows from {filename} "
          f"(dropped {dropped} NaN rows).")


def main():
    print("--- Loading companies ---")
    load_companies()

    print("\n--- Loading core_metrics ---")
    load_core_metrics()

    print("\n--- Loading financial_statements ---")
    load_statement("income_statement_raw.csv", "income")
    load_statement("balance_sheet_raw.csv", "balance")
    load_statement("cashflow_raw.csv", "cashflow")

    print("\n--- DONE ---")


if __name__ == "__main__":
    main()