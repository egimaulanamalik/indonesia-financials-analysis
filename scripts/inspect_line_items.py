"""
inspect_line_items.py

Before designing the PostgreSQL schema, we need to know how consistent
(or inconsistent) yfinance's line item naming is across our 5 companies.

Why this matters: Tableau dashboards work best off a small set of
standardized metrics (Total Revenue, Net Income, Total Assets, etc.).
If those core metrics exist under different names per company (or are
missing for some), we need to know NOW -- before writing SQL -- so we
can build a mapping/standardization step rather than discovering broken
charts later in Tableau.

This script answers three questions:
  1. Which line items appear for ALL 5 companies? (safe to use directly)
  2. Which line items appear for only SOME companies? (sector-specific,
     e.g. "Net Interest Income" only for banks)
  3. Do the core metrics we care about for the dashboard actually exist
     everywhere, and under what exact name?
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")

# Core metrics we plan to anchor the dashboard around. Listed as
# lowercase substrings so we can fuzzy-match against actual line_item
# text, since exact naming may vary slightly.
CORE_METRICS_TO_CHECK = [
    "total revenue",
    "net income",
    "total assets",
    "total liabilities",
    "total equity",
    "operating income",
    "operating expense",
]


def inspect_file(filename: str, label: str):
    path = DATA_DIR / filename
    if not path.exists():
        print(f"[{label}] File not found: {path}")
        return

    df = pd.read_csv(path)
    print(f"\n{'=' * 70}")
    print(f"{label}  ({filename})")
    print(f"{'=' * 70}")
    print(f"Total rows: {len(df)}  |  Companies: {df['ticker'].nunique()}")

    # Build a map: line_item -> set of tickers that have it
    item_to_tickers = df.groupby("line_item")["ticker"].apply(set)
    all_tickers = set(df["ticker"].unique())
    n_companies = len(all_tickers)

    shared_by_all = [item for item, tickers in item_to_tickers.items()
                      if len(tickers) == n_companies]
    partial = [item for item, tickers in item_to_tickers.items()
               if len(tickers) < n_companies]

    print(f"\nLine items present in ALL {n_companies} companies: {len(shared_by_all)}")
    print(f"Line items present in SOME companies only: {len(partial)}")

    if partial:
        print("\n--- Company-specific line items (top 15) ---")
        # Sort by how few companies have them (most specific first)
        partial_sorted = sorted(partial, key=lambda x: len(item_to_tickers[x]))
        for item in partial_sorted[:15]:
            tickers = item_to_tickers[item]
            print(f"  '{item}' -> only in: {sorted(tickers)}")

    print("\n--- Checking core dashboard metrics ---")
    for metric in CORE_METRICS_TO_CHECK:
        matches = [item for item in df["line_item"].unique()
                   if metric in item.lower()]
        if matches:
            for m in matches:
                tickers_with_m = item_to_tickers[m]
                missing = all_tickers - tickers_with_m
                status = "ALL companies" if not missing else f"MISSING for {sorted(missing)}"
                print(f"  '{m}' -> {status}")
        else:
            print(f"  '{metric}' -> NOT FOUND under this name in any company")


def main():
    inspect_file("income_statement_raw.csv", "INCOME STATEMENT")
    inspect_file("balance_sheet_raw.csv", "BALANCE SHEET")
    inspect_file("cashflow_raw.csv", "CASH FLOW")


if __name__ == "__main__":
    main()