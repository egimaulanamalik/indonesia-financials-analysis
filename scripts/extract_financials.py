"""
extract_financials.py

Pulls annual financial statements (Income Statement, Balance Sheet, Cash Flow)
for a set of Indonesian public companies using yfinance, and saves each
statement type as a single combined CSV (all companies stacked together).

Why stacked CSVs instead of one file per company?
Because the next step is loading into PostgreSQL, and a single "long" table
per statement type (with a company_ticker column) is much easier to load
and query than 15 separate small files. This mirrors how real data
pipelines consolidate multiple sources into a common schema.
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
import time

# ---- CONFIG ----
# Why these 5: a cross-sector mix (2 banks, telecom, consumer goods, tech)
# chosen to support comparative analysis (mature vs growth, sector vs sector)
# rather than 5 companies that all behave the same way.
TICKERS = {
    "BBCA.JK": "Bank Central Asia",
    "BMRI.JK": "Bank Mandiri",
    "TLKM.JK": "Telkom Indonesia",
    "ICBP.JK": "Indofood CBP",
    "GOTO.JK": "GoTo Gojek Tokopedia",
}

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_statement(ticker_obj, statement_type: str) -> pd.DataFrame:
    """
    Fetches one statement type from yfinance and returns it reshaped
    so that each row is one (line_item, period) pair rather than the
    wide year-as-column format yfinance returns by default.

    Why reshape to long format here, not later in SQL?
    Because yfinance's row labels (line item names) are NOT guaranteed
    to be identical across companies (e.g. a bank may have "Net Interest
    Income" while a consumer goods company won't). Reshaping in pandas
    lets us inspect and standardize names before they ever hit the database,
    which is much easier to fix in Python than in SQL.
    """
    if statement_type == "income":
        df = ticker_obj.financials
    elif statement_type == "balance":
        df = ticker_obj.balance_sheet
    elif statement_type == "cashflow":
        df = ticker_obj.cashflow
    else:
        raise ValueError(f"Unknown statement type: {statement_type}")

    if df is None or df.empty:
        return pd.DataFrame()

    # yfinance gives wide format: rows = line items, columns = period dates.
    # We use .stack() rather than reset_index()+melt() to reshape to long
    # format. Why: pandas 3.0 introduced a regression where melt() raises
    # "'Series' object has no attribute 'columns'" on certain DataFrame
    # shapes (this bit us during development). .stack() achieves the same
    # long-format reshape without going through melt's internal concat path,
    # so it works correctly on both pandas 2.x and 3.x.
    df = df.copy()
    df.index.name = "line_item"
    df.columns.name = "period"
    long_df = df.stack().reset_index(name="value")
    return long_df


def main():
    all_income = []
    all_balance = []
    all_cashflow = []
    failures = []

    for ticker_symbol, company_name in TICKERS.items():
        print(f"Fetching {ticker_symbol} ({company_name})...")
        try:
            t = yf.Ticker(ticker_symbol)

            income_df = fetch_statement(t, "income")
            balance_df = fetch_statement(t, "balance")
            cashflow_df = fetch_statement(t, "cashflow")

            for df in (income_df, balance_df, cashflow_df):
                if not df.empty:
                    df["ticker"] = ticker_symbol
                    df["company_name"] = company_name

            if income_df.empty and balance_df.empty and cashflow_df.empty:
                failures.append(ticker_symbol)
                print(f"  WARNING: no data returned for {ticker_symbol}")
            else:
                all_income.append(income_df)
                all_balance.append(balance_df)
                all_cashflow.append(cashflow_df)
                print(f"  OK - income: {len(income_df)} rows, "
                      f"balance: {len(balance_df)} rows, "
                      f"cashflow: {len(cashflow_df)} rows")

            # Why sleep here: Yahoo Finance is not an official paid API,
            # it's the free public endpoint yfinance scrapes. Hammering it
            # with rapid-fire requests increases the chance of a temporary
            # rate-limit block. A short pause between companies is cheap
            # insurance against that.
            time.sleep(1.5)

        except Exception as e:
            print(f"  ERROR fetching {ticker_symbol}: {e}")
            failures.append(ticker_symbol)

    # Combine all companies into one file per statement type
    if all_income:
        pd.concat(all_income, ignore_index=True).to_csv(
            OUTPUT_DIR / "income_statement_raw.csv", index=False
        )
    if all_balance:
        pd.concat(all_balance, ignore_index=True).to_csv(
            OUTPUT_DIR / "balance_sheet_raw.csv", index=False
        )
    if all_cashflow:
        pd.concat(all_cashflow, ignore_index=True).to_csv(
            OUTPUT_DIR / "cashflow_raw.csv", index=False
        )

    print("\n--- DONE ---")
    print(f"Saved files to {OUTPUT_DIR.resolve()}")
    if failures:
        print(f"Companies with issues: {failures}")
        print("If GOTO.JK failed or returned partial data, that's expected -- "
              "it's a newer listing with a shorter financial history. "
              "We'll handle that gap explicitly in the next step, not hide it.")


if __name__ == "__main__":
    main()