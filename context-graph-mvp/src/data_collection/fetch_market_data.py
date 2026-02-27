"""Fetch stock market data from yfinance and compute per-letter price snapshots."""

import os
import logging
from datetime import timedelta
import pandas as pd
import yfinance as yf
from src.data_collection.letter_registry import LETTERS, get_unique_tickers

logger = logging.getLogger(__name__)

START_DATE = "2021-01-01"
END_DATE = "2024-09-30"


def get_ticker_filename(ticker: str) -> str:
    """Convert a ticker symbol to a safe CSV filename."""
    safe = ticker.lower().replace("-", "_").replace("^", "").replace(".", "_")
    return f"{safe}_prices.csv"


def fetch_ticker_history(ticker: str, start: str = START_DATE, end: str = END_DATE) -> pd.DataFrame:
    """Fetch daily price history for a ticker via yfinance."""
    logger.info("Fetching %s ...", ticker)
    t = yf.Ticker(ticker)
    hist = t.history(start=start, end=end)
    if hist.empty:
        logger.warning("No data returned for %s", ticker)
    else:
        logger.info("Got %d trading days for %s", len(hist), ticker)
    return hist


def fetch_and_save_all(output_dir: str = "data/raw/market") -> dict[str, int]:
    """Fetch all unique tickers from registry and save as CSVs."""
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    tickers = get_unique_tickers()

    for ticker in sorted(tickers):
        filename = get_ticker_filename(ticker)
        outpath = os.path.join(output_dir, filename)

        if os.path.exists(outpath):
            df = pd.read_csv(outpath, index_col=0, parse_dates=True)
            logger.info("SKIP (exists): %s (%d rows)", filename, len(df))
            results[ticker] = len(df)
            continue

        hist = fetch_ticker_history(ticker)
        if not hist.empty:
            hist.to_csv(outpath)
            results[ticker] = len(hist)
        else:
            results[ticker] = 0

    return results


def find_nearest_trading_day(prices: pd.DataFrame, target_date: str) -> pd.Timestamp:
    """Find the closest trading day in the price index to a given date."""
    target = pd.Timestamp(target_date)
    idx = prices.index
    # Strip timezone info for comparison if needed
    if hasattr(idx, 'tz') and idx.tz is not None:
        idx = idx.tz_localize(None)
    if target in idx:
        return target
    diffs = abs(idx - target)
    return idx[diffs.argmin()]


def compute_letter_prices(prices: pd.DataFrame, publication_date: str) -> dict:
    """Compute price snapshot for one letter's publication date."""
    pub = pd.Timestamp(publication_date)

    date_30d_before = find_nearest_trading_day(prices, (pub - timedelta(days=30)).isoformat())
    date_on = find_nearest_trading_day(prices, pub.isoformat())
    date_7d_after = find_nearest_trading_day(prices, (pub + timedelta(days=7)).isoformat())
    date_30d_after = find_nearest_trading_day(prices, (pub + timedelta(days=30)).isoformat())

    p_30d_before = float(prices.loc[date_30d_before, "Close"])
    p_on = float(prices.loc[date_on, "Close"])
    p_7d_after = float(prices.loc[date_7d_after, "Close"])
    p_30d_after = float(prices.loc[date_30d_after, "Close"])

    return {
        "date_30d_before": str(date_30d_before.date()),
        "date_on_or_near": str(date_on.date()),
        "date_7d_after": str(date_7d_after.date()),
        "date_30d_after": str(date_30d_after.date()),
        "price_30d_before": round(p_30d_before, 2),
        "price_on_date": round(p_on, 2),
        "price_7d_after": round(p_7d_after, 2),
        "price_30d_after": round(p_30d_after, 2),
        "return_7d_pct": round((p_7d_after - p_on) / p_on * 100, 2),
        "return_30d_pct": round((p_30d_after - p_on) / p_on * 100, 2),
    }


def compute_all_letter_prices(market_dir: str = "data/raw/market") -> list[dict]:
    """For each letter in registry, compute stock + benchmark price snapshots."""
    results = []
    for letter in LETTERS:
        ticker_file = os.path.join(market_dir, get_ticker_filename(letter["ticker"]))
        bench_file = os.path.join(market_dir, get_ticker_filename(letter["benchmark_ticker"]))

        if not os.path.exists(ticker_file) or not os.path.exists(bench_file):
            logger.warning("Missing price data for %s %d", letter["company"], letter["year"])
            continue

        stock_prices = pd.read_csv(ticker_file, index_col=0)
        stock_prices.index = pd.to_datetime(stock_prices.index, utc=True).tz_localize(None)
        bench_prices = pd.read_csv(bench_file, index_col=0)
        bench_prices.index = pd.to_datetime(bench_prices.index, utc=True).tz_localize(None)

        stock_snap = compute_letter_prices(stock_prices, letter["publication_date"])
        bench_snap = compute_letter_prices(bench_prices, letter["publication_date"])

        results.append({
            "company": letter["company"],
            "year": letter["year"],
            "publication_date": letter["publication_date"],
            "stock": stock_snap,
            "benchmark": bench_snap,
            "relative_return_7d_pct": round(stock_snap["return_7d_pct"] - bench_snap["return_7d_pct"], 2),
            "relative_return_30d_pct": round(stock_snap["return_30d_pct"] - bench_snap["return_30d_pct"], 2),
        })

    return results
