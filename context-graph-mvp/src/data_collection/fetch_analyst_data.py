"""Fetch analyst recommendations and price targets from yfinance."""

import os
import json
import logging
from datetime import timedelta
import pandas as pd
import yfinance as yf
from src.data_collection.letter_registry import LETTERS

logger = logging.getLogger(__name__)


def fetch_recommendations(ticker: str) -> pd.DataFrame:
    """Fetch analyst recommendation history for a ticker."""
    try:
        t = yf.Ticker(ticker)
        recs = t.recommendations
        if recs is not None and not recs.empty:
            logger.info("%s: got %d recommendation periods", ticker, len(recs))
            return recs
    except Exception as e:
        logger.warning("%s recommendations failed: %s", ticker, e)
    return pd.DataFrame()


def fetch_price_targets(ticker: str) -> dict:
    """Fetch analyst price target summary for a ticker."""
    try:
        t = yf.Ticker(ticker)
        targets = t.analyst_price_targets
        if targets is not None:
            logger.info("%s: got price targets", ticker)
            if isinstance(targets, dict):
                return targets
            return dict(targets)
    except Exception as e:
        logger.warning("%s price targets failed: %s", ticker, e)
    return {}


def get_recommendations_near_date(
    recs_df: pd.DataFrame, target_date: str, window_days: int = 30
) -> pd.DataFrame:
    """Filter recommendations to those within window_days before target_date."""
    if recs_df.empty:
        return recs_df
    target = pd.Timestamp(target_date)
    start = target - timedelta(days=window_days)
    mask = (recs_df.index >= start) & (recs_df.index <= target)
    return recs_df.loc[mask]


def fetch_and_save_all(output_dir: str = "data/raw/analyst") -> dict[str, bool]:
    """Fetch analyst data for all company tickers in the registry."""
    os.makedirs(output_dir, exist_ok=True)
    company_tickers = {l["ticker"] for l in LETTERS}
    results = {}

    for ticker in sorted(company_tickers):
        safe_name = ticker.lower().replace("-", "_").replace(".", "_")

        # Recommendations
        recs_path = os.path.join(output_dir, f"{safe_name}_recommendations.csv")
        if os.path.exists(recs_path):
            logger.info("SKIP (exists): %s", os.path.basename(recs_path))
            results[f"{ticker}_recommendations"] = True
        else:
            recs = fetch_recommendations(ticker)
            if not recs.empty:
                recs.to_csv(recs_path)
                results[f"{ticker}_recommendations"] = True
            else:
                results[f"{ticker}_recommendations"] = False

        # Price targets
        targets_path = os.path.join(output_dir, f"{safe_name}_targets.json")
        if os.path.exists(targets_path):
            logger.info("SKIP (exists): %s", os.path.basename(targets_path))
            results[f"{ticker}_targets"] = True
        else:
            targets = fetch_price_targets(ticker)
            if targets:
                with open(targets_path, "w") as f:
                    json.dump(targets, f, indent=2, default=str)
                results[f"{ticker}_targets"] = True
            else:
                results[f"{ticker}_targets"] = False

    return results
