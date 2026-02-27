import pandas as pd
from src.data_collection.fetch_analyst_data import get_recommendations_near_date

def test_get_recommendations_near_date_filters_correctly():
    """Should return recommendations within window of target date."""
    dates = pd.to_datetime(["2023-01-15", "2023-02-20", "2023-03-10", "2023-06-01"])
    df = pd.DataFrame({
        "strongBuy": [5, 6, 7, 8],
        "buy": [3, 4, 5, 6],
        "hold": [2, 2, 3, 3],
        "sell": [1, 0, 1, 0],
        "strongSell": [0, 0, 0, 0],
    }, index=dates)

    result = get_recommendations_near_date(df, "2023-02-25", window_days=30)
    assert len(result) >= 1
    assert pd.Timestamp("2023-02-20") in result.index

def test_get_recommendations_near_date_returns_empty_for_no_match():
    dates = pd.to_datetime(["2020-01-01"])
    df = pd.DataFrame({
        "strongBuy": [5], "buy": [3], "hold": [2],
        "sell": [1], "strongSell": [0],
    }, index=dates)
    result = get_recommendations_near_date(df, "2023-02-25", window_days=30)
    assert len(result) == 0

def test_get_recommendations_near_date_handles_empty_df():
    df = pd.DataFrame()
    result = get_recommendations_near_date(df, "2023-02-25")
    assert len(result) == 0
