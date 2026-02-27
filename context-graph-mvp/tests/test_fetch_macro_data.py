import pandas as pd
from src.data_collection.fetch_macro_data import get_macro_snapshot_for_date

def test_get_macro_snapshot_for_date_structure():
    """Snapshot should have US and India sections."""
    dates = pd.date_range("2020-01-01", "2024-06-30", freq="MS")
    fed_funds = pd.DataFrame({"value": [0.25] * len(dates)}, index=dates)
    us_cpi = pd.DataFrame({"value": [260.0 + i * 0.5 for i in range(len(dates))]}, index=dates)

    snapshot = get_macro_snapshot_for_date(
        target_date="2023-02-25",
        fed_funds_df=fed_funds,
        us_cpi_df=us_cpi,
        india_repo_df=None,
        india_cpi_df=None,
    )
    assert "us_fed_funds_rate" in snapshot
    assert "us_cpi_yoy_pct" in snapshot
    assert snapshot["us_fed_funds_rate"] == 0.25

def test_get_macro_snapshot_handles_missing_india_data():
    """Should return None for India fields when data unavailable."""
    dates = pd.date_range("2020-01-01", "2024-06-30", freq="MS")
    fed_funds = pd.DataFrame({"value": [4.5] * len(dates)}, index=dates)
    us_cpi = pd.DataFrame({"value": [300.0] * len(dates)}, index=dates)

    snapshot = get_macro_snapshot_for_date(
        target_date="2023-02-25",
        fed_funds_df=fed_funds,
        us_cpi_df=us_cpi,
        india_repo_df=None,
        india_cpi_df=None,
    )
    assert snapshot["india_rbi_repo_rate"] is None

def test_get_macro_snapshot_cpi_yoy_is_percentage():
    """CPI YoY should be a percentage change."""
    dates = pd.date_range("2020-01-01", "2024-06-30", freq="MS")
    # CPI goes from 100 to 110 over a year = 10% inflation
    cpi_values = [100.0 + (i / len(dates)) * 50 for i in range(len(dates))]
    us_cpi = pd.DataFrame({"value": cpi_values}, index=dates)
    fed_funds = pd.DataFrame({"value": [2.0] * len(dates)}, index=dates)

    snapshot = get_macro_snapshot_for_date(
        target_date="2023-02-25",
        fed_funds_df=fed_funds,
        us_cpi_df=us_cpi,
        india_repo_df=None,
        india_cpi_df=None,
    )
    # Should be a reasonable percentage, not a raw number
    assert snapshot["us_cpi_yoy_pct"] is not None
    assert -20 < snapshot["us_cpi_yoy_pct"] < 50  # Sanity bounds
