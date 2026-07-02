"""
debug_yfinance.py

A minimal diagnostic script. Before re-running the full pipeline, we need
to see exactly what yfinance is returning for ONE ticker, with nothing
hidden by try/except blocks. This isolates whether the problem is:
  (a) yfinance/Yahoo backend issue (likely, based on the error pattern)
  (b) something about Indonesian .JK tickers specifically
  (c) a version/environment issue on this machine
"""

import yfinance as yf
import pandas as pd

print("yfinance version:", yf.__version__)
print("pandas version:", pd.__version__)
print()

ticker = yf.Ticker("BBCA.JK")

print("--- Raw .financials ---")
fin = ticker.financials
print("Type:", type(fin))
print("Value:", fin)
print()

print("--- Raw .income_stmt (newer yfinance attribute name) ---")
try:
    inc = ticker.income_stmt
    print("Type:", type(inc))
    print(inc)
except Exception as e:
    print("Error:", e)
print()

print("--- Trying a well-known US ticker for comparison: AAPL ---")
aapl = yf.Ticker("AAPL")
aapl_fin = aapl.financials
print("Type:", type(aapl_fin))
print("Empty?:", aapl_fin.empty if hasattr(aapl_fin, "empty") else "N/A (not a DataFrame)")