import pandas as pd
from src.data_collection.fetch_market_data import (
    find_nearest_trading_day,
    compute_letter_prices,
    get_ticker_filename,
)

def test_get_ticker_filename():
    assert get_ticker_filename("BRK-B") == "brk_b_prices.csv"
    assert get_ticker_filename("^GSPC") == "gspc_prices.csv"
    assert get_ticker_filename("INFY") == "infy_prices.csv"

def test_find_nearest_trading_day_exact_match():
    dates = pd.DatetimeIndex(["2023-02-24", "2023-02-25", "2023-02-27"])
    prices = pd.DataFrame({"Close": [100, 101, 102]}, index=dates)
    result = find_nearest_trading_day(prices, "2023-02-25")
    assert result == pd.Timestamp("2023-02-25")

def test_find_nearest_trading_day_weekend():
    dates = pd.DatetimeIndex(["2023-02-24", "2023-02-27"])
    prices = pd.DataFrame({"Close": [100, 102]}, index=dates)
    result = find_nearest_trading_day(prices, "2023-02-25")
    assert result in [pd.Timestamp("2023-02-24"), pd.Timestamp("2023-02-27")]

def test_compute_letter_prices_structure():
    dates = pd.bdate_range("2023-01-01", "2023-04-30")
    prices = pd.DataFrame({"Close": range(len(dates))}, index=dates)
    result = compute_letter_prices(prices, "2023-02-25")
    expected_keys = {
        "price_30d_before", "price_on_date", "price_7d_after",
        "price_30d_after", "return_7d_pct", "return_30d_pct",
        "date_30d_before", "date_on_or_near", "date_7d_after", "date_30d_after",
    }
    assert expected_keys.issubset(set(result.keys()))

def test_compute_letter_prices_constant_returns_zero():
    dates = pd.bdate_range("2023-01-01", "2023-04-30")
    prices = pd.DataFrame({"Close": [100.0] * len(dates)}, index=dates)
    result = compute_letter_prices(prices, "2023-02-25")
    assert result["return_7d_pct"] == 0.0
    assert result["return_30d_pct"] == 0.0
