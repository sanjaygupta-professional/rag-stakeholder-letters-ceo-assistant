"""Fetch macroeconomic indicators from FRED API and World Bank API."""

import os
import logging
from datetime import timedelta
import pandas as pd

logger = logging.getLogger(__name__)

FRED_SERIES = {
    "us_fed_funds_rate": "FEDFUNDS",
    "us_cpi": "CPIAUCSL",
    "us_unemployment": "UNRATE",
}

START_DATE = "2020-01-01"
END_DATE = "2024-09-30"


def fetch_fred_series(series_id: str, api_key: str,
                      start: str = START_DATE, end: str = END_DATE) -> pd.DataFrame:
    """Fetch a single FRED time series."""
    try:
        from fredapi import Fred
        fred = Fred(api_key=api_key)
        data = fred.get_series(series_id, observation_start=start, observation_end=end)
        df = data.to_frame(name="value")
        logger.info("FRED %s: got %d observations", series_id, len(df))
        return df
    except Exception as e:
        logger.error("FRED %s failed: %s", series_id, e)
        return pd.DataFrame()


def fetch_india_rbi_repo(start: str = START_DATE, end: str = END_DATE) -> pd.DataFrame:
    """Fetch India RBI Repo Rate from World Bank API."""
    try:
        import requests
        url = (
            f"https://api.worldbank.org/v2/country/IND/indicator/FR.INR.RINR"
            f"?date={start[:4]}:{end[:4]}&format=json&per_page=100"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if len(data) > 1 and data[1]:
            records = [
                {"date": r["date"], "value": r["value"]}
                for r in data[1] if r["value"] is not None
            ]
            if records:
                df = pd.DataFrame(records)
                df["date"] = pd.to_datetime(df["date"], format="%Y")
                df = df.set_index("date").sort_index()
                logger.info("India RBI: got %d observations", len(df))
                return df
    except Exception as e:
        logger.warning("India RBI fetch failed: %s", e)
    return pd.DataFrame()


def fetch_india_cpi(start: str = START_DATE, end: str = END_DATE) -> pd.DataFrame:
    """Fetch India CPI YoY from World Bank API."""
    try:
        import requests
        url = (
            f"https://api.worldbank.org/v2/country/IND/indicator/FP.CPI.TOTL.ZG"
            f"?date={start[:4]}:{end[:4]}&format=json&per_page=100"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if len(data) > 1 and data[1]:
            records = [
                {"date": r["date"], "value": r["value"]}
                for r in data[1] if r["value"] is not None
            ]
            if records:
                df = pd.DataFrame(records)
                df["date"] = pd.to_datetime(df["date"], format="%Y")
                df = df.set_index("date").sort_index()
                logger.info("India CPI: got %d observations", len(df))
                return df
    except Exception as e:
        logger.warning("India CPI fetch failed: %s", e)
    return pd.DataFrame()


def fetch_and_save_all(output_dir: str = "data/raw/macro", fred_api_key: str = "") -> dict[str, bool]:
    """Fetch all macro indicators and save as CSVs."""
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    if not fred_api_key:
        from dotenv import load_dotenv
        load_dotenv()
        fred_api_key = os.getenv("FRED_API_KEY", "")

    if fred_api_key:
        for name, series_id in FRED_SERIES.items():
            path = os.path.join(output_dir, f"{name}.csv")
            if os.path.exists(path):
                logger.info("SKIP (exists): %s", name)
                results[name] = True
                continue
            df = fetch_fred_series(series_id, fred_api_key)
            if not df.empty:
                df.to_csv(path)
                results[name] = True
            else:
                results[name] = False
    else:
        logger.warning("No FRED_API_KEY — skipping US macro data. "
                       "Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html")
        for name in FRED_SERIES:
            results[name] = False

    for name, fetcher in [("india_rbi_repo", fetch_india_rbi_repo),
                          ("india_cpi", fetch_india_cpi)]:
        path = os.path.join(output_dir, f"{name}.csv")
        if os.path.exists(path):
            logger.info("SKIP (exists): %s", name)
            results[name] = True
            continue
        df = fetcher()
        if not df.empty:
            df.to_csv(path)
            results[name] = True
        else:
            results[name] = False

    return results


def get_macro_snapshot_for_date(
    target_date: str,
    fed_funds_df: pd.DataFrame | None,
    us_cpi_df: pd.DataFrame | None,
    india_repo_df: pd.DataFrame | None,
    india_cpi_df: pd.DataFrame | None,
) -> dict:
    """Get the macro indicator values nearest to a target date."""
    target = pd.Timestamp(target_date)

    def nearest_value(df, t):
        if df is None or df.empty:
            return None
        diffs = abs(df.index - t)
        return float(df.iloc[diffs.argmin()]["value"])

    us_ff = nearest_value(fed_funds_df, target)
    us_cpi_val = nearest_value(us_cpi_df, target)

    us_cpi_yoy = None
    if us_cpi_df is not None and not us_cpi_df.empty and us_cpi_val is not None:
        year_ago = target - timedelta(days=365)
        cpi_year_ago = nearest_value(us_cpi_df, year_ago)
        if cpi_year_ago and cpi_year_ago > 0:
            us_cpi_yoy = round((us_cpi_val - cpi_year_ago) / cpi_year_ago * 100, 1)

    return {
        "date": target_date,
        "us_fed_funds_rate": us_ff,
        "us_cpi_index": us_cpi_val,
        "us_cpi_yoy_pct": us_cpi_yoy,
        "india_rbi_repo_rate": nearest_value(india_repo_df, target),
        "india_cpi_yoy_pct": nearest_value(india_cpi_df, target),
    }
