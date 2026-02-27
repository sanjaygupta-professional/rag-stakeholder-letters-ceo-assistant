#!/usr/bin/env python3
"""Script 01 — Download PDFs, fetch market data, macro indicators, analyst data."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_collection.download_letters import download_all_letters
from src.data_collection.fetch_market_data import fetch_and_save_all as fetch_market
from src.data_collection.fetch_macro_data import fetch_and_save_all as fetch_macro
from src.data_collection.fetch_analyst_data import fetch_and_save_all as fetch_analyst

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("SCRIPT 01: Data Collection")
    print("=" * 60)

    # 1. Download shareholder letter PDFs
    print("\n--- Downloading PDFs ---")
    pdf_results = download_all_letters()
    pdf_ok = sum(1 for v in pdf_results.values() if v)
    print(f"  PDFs: {pdf_ok}/{len(pdf_results)} downloaded")

    # 2. Fetch market price data from yfinance
    print("\n--- Fetching market data (yfinance) ---")
    market_results = fetch_market()
    for ticker, rows in sorted(market_results.items()):
        print(f"  {ticker}: {rows} trading days")

    # 3. Fetch macro indicators (FRED + World Bank)
    print("\n--- Fetching macro indicators ---")
    macro_results = fetch_macro()
    for name, ok in sorted(macro_results.items()):
        status = "OK" if ok else "MISSING"
        print(f"  {name}: {status}")

    # 4. Fetch analyst recommendations + price targets
    print("\n--- Fetching analyst data (yfinance) ---")
    analyst_results = fetch_analyst()
    for name, ok in sorted(analyst_results.items()):
        status = "OK" if ok else "MISSING"
        print(f"  {name}: {status}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_ok = all(pdf_results.values())
    print(f"  PDFs:    {pdf_ok}/{len(pdf_results)} {'✓' if all_ok else '⚠ some failed'}")
    print(f"  Market:  {len([v for v in market_results.values() if v > 0])}/{len(market_results)} tickers")
    print(f"  Macro:   {sum(macro_results.values())}/{len(macro_results)} series")
    print(f"  Analyst: {sum(analyst_results.values())}/{len(analyst_results)} files")

    if not all_ok:
        print("\n⚠  Some PDFs failed. Check URLs or download manually.")
        print("   Berkshire: https://www.berkshirehathaway.com/letters/letters.html")
        print("   Infosys:   https://www.infosys.com/investors/reports-filings/annual-report.html")

    print("\n→ Next: python scripts/02_process_letters.py")


if __name__ == "__main__":
    main()
