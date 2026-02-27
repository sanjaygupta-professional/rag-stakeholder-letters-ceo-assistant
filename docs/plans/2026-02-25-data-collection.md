# Data Collection Implementation Plan (v2)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build Script 01 (data collection) and the project scaffold — downloading 6 shareholder letter PDFs, fetching market prices, analyst data, macroeconomic indicators, and synthesizing analyst narratives. Zero hard-coded business data.

**Architecture:** Modular data collection with one fetcher per data source. Each fetcher writes structured files to `data/raw/`. A central orchestrator calls all fetchers and prints a validation report. All business data lives in data files, never in Python source code.

**Tech Stack:** Python 3.10+, requests, yfinance, fredapi, pandas, pdfplumber, anthropic, python-dotenv

---

## What We're Building (Visual)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SCRIPT 01: COLLECT DATA                         │
│                                                                      │
│  DATA SOURCES (APIs)                    DATA STORE (data/raw/)       │
│  ───────────────────                    ──────────────────            │
│                                                                      │
│  berkshirehathaway.com ──PDF──►         letters/                     │
│  infosys.com ────────────PDF──►           ├── berkshire_2021.pdf     │
│                                           ├── ...6 PDFs total        │
│                                                                      │
│  yfinance ───────────────CSV──►         market/                      │
│    (BRK-B, INFY, ^GSPC, ^CNXIT)          ├── brk_b_prices.csv      │
│                                           ├── infy_prices.csv        │
│                                           ├── sp500_prices.csv       │
│                                           └── nifty_it_prices.csv    │
│                                                                      │
│  yfinance ───────────────CSV──►         analyst/                     │
│    (.recommendations, .targets)           ├── brk_b_recommendations  │
│                                           ├── brk_b_targets.csv      │
│                                           ├── infy_recommendations   │
│                                           └── infy_targets.csv       │
│                                                                      │
│  FRED API ───────────────CSV──►         macro/                       │
│    (Fed Funds, CPI, Unemployment)         ├── us_fed_funds_rate.csv  │
│                                           ├── us_cpi.csv             │
│                                           └── us_unemployment.csv    │
│                                                                      │
│  data.gov.in / RBI ─────CSV──►            ├── india_rbi_repo.csv    │
│                                           └── india_cpi.csv          │
│                                                                      │
│  Claude API ─────────────JSON──►        analyst_narratives/          │
│    (synthesized from quantitative          ├── berkshire_2021.json   │
│     data collected above)                  ├── ...6 JSONs total      │
│                                                                      │
│  COMPUTED ───────────────JSON──►        ../processed/                │
│                                           └── letter_price_snaps.json│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Data ≠ Code** — All business facts live in `data/` files. Source code is generic.
2. **One fetcher per source** — Single responsibility. Easy to test, retry, replace.
3. **Idempotent** — Every fetcher skips existing files. Safe to re-run.
4. **Provenance** — Each data file can be traced to its API source.
5. **Registry-driven** — Adding a company means adding entries to the registry, not changing fetcher code.
6. **Graceful degradation** — If an API fails, report the gap and continue.

## How This Feeds the Pipeline

```
Script 01 (THIS)          Script 02              Script 03
──────────────────        ────────────           ──────────────────
Download PDFs ─────────►  Extract text    ──►    Build Context
Fetch prices  ─────────►  from PDFs              Envelopes (JSON)
Fetch analyst data ────►                         combining ALL raw
Fetch macro data ──────►                         data into structured
Synthesize narratives ─►                         context packages
```

## Validation Strategy

| What | How | Success Criteria |
|------|-----|-----------------|
| 6 PDFs | File size + pdfplumber page count | All > 10KB, all open |
| 4 price CSVs | Row count, date range | 800+ rows, 2021-2024 |
| 2 analyst recommendation files | Has data, has dates | At least some rows |
| 2 analyst target files | Has data | At least some rows |
| 3 US macro CSVs | Row count, date range | Covers 2021-2024 |
| 2 India macro CSVs | Has data | At least some rows |
| 6 price snapshots | Realistic prices, small returns | BRK-B ~$270-400, INFY ~$15-22 |
| 6 analyst narrative JSONs | Valid JSON, has required fields | All parseable |

---

## Task 0: Create Project Scaffold

**Files:**
- Create: `context-graph-mvp/` full directory tree
- Create: `context-graph-mvp/requirements.txt`
- Create: `context-graph-mvp/.env.template`
- Create: `context-graph-mvp/.gitignore`
- Create: `context-graph-mvp/src/__init__.py` and sub-package `__init__.py` files

**Step 1: Create directory structure**

```bash
cd /home/sanjayegupta/projects/rag-stakeholder-letters-ceo-assistant
mkdir -p context-graph-mvp/{data/{raw/{letters,market,analyst,macro,analyst_narratives},processed/{letters,context_packages},themes},src/{data_collection,graph,analysis,rag,query_engine,demo},scripts,tests,presentation/{architecture_diagrams,demo_screenshots,graph_visualizations}}
```

**Step 2: Create requirements.txt**

```
# context-graph-mvp/requirements.txt
neo4j>=5.0.0
langchain>=0.1.0
langchain-community>=0.0.1
chromadb>=0.4.0
anthropic>=0.30.0
yfinance>=0.2.0
pdfplumber>=0.10.0
streamlit>=1.30.0
sentence-transformers>=2.0.0
python-dotenv>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
numpy>=1.24.0
pyvis>=0.3.0
fredapi>=0.5.0
pytest>=7.0.0
```

**Step 3: Create .env.template**

```
NEO4J_URI=
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=
ANTHROPIC_API_KEY=
FRED_API_KEY=
```

**Step 4: Create .gitignore**

```
.env
__pycache__/
*.pyc
data/raw/
data/processed/
data/themes/
*.egg-info/
.venv/
```

**Step 5: Create `__init__.py` files**

Empty `__init__.py` in: `src/`, `src/data_collection/`, `src/graph/`, `src/analysis/`, `src/rag/`, `src/query_engine/`, `src/demo/`

**Step 6: Commit**

```bash
git init
git add -A
git commit -m "chore: create project scaffold with directory structure and requirements"
```

---

## Task 1: Letter Metadata Registry

**Files:**
- Create: `context-graph-mvp/src/data_collection/letter_registry.py`
- Test: `context-graph-mvp/tests/test_letter_registry.py`

Pure-data module defining the 6 letters with all metadata. Every downstream module imports from here. Adding a 7th company later means adding entries here — no other code changes.

**Step 1: Write the test**

```python
# tests/test_letter_registry.py
from src.data_collection.letter_registry import LETTERS, get_letter, get_unique_tickers

def test_registry_has_six_letters():
    assert len(LETTERS) == 6

def test_berkshire_letters_have_correct_years():
    brk = [l for l in LETTERS if l["company"] == "Berkshire Hathaway"]
    years = sorted([l["year"] for l in brk])
    assert years == [2021, 2022, 2023]

def test_infosys_letters_have_correct_years():
    infy = [l for l in LETTERS if l["company"] == "Infosys"]
    years = sorted([l["year"] for l in infy])
    assert years == [2021, 2022, 2023]

def test_all_letters_have_required_fields():
    required = {"company", "ticker", "year", "fiscal_year_covered",
                "publication_date", "author", "pdf_url", "output_filename",
                "benchmark_ticker", "geography", "sector"}
    for letter in LETTERS:
        missing = required - set(letter.keys())
        assert not missing, f"{letter['company']} {letter['year']} missing: {missing}"

def test_get_letter_by_company_and_year():
    l = get_letter("Berkshire Hathaway", 2022)
    assert l["author"] == "Warren Buffett"
    assert l["publication_date"] == "2023-02-25"

def test_get_letter_returns_none_for_unknown():
    assert get_letter("Apple", 2022) is None

def test_get_unique_tickers():
    tickers = get_unique_tickers()
    assert "BRK-B" in tickers
    assert "INFY" in tickers
    assert "^GSPC" in tickers
    assert "^CNXIT" in tickers
```

**Step 2: Run test — expect FAIL**

```bash
cd context-graph-mvp && python -m pytest tests/test_letter_registry.py -v
```

**Step 3: Implement letter_registry.py**

```python
# src/data_collection/letter_registry.py
"""
Central registry of all shareholder letters with metadata.

This is the ONLY place letter metadata is defined. All fetchers,
processors, and analysis modules reference this registry.

To add a new company/year: add an entry to LETTERS. No other code changes needed.
"""

LETTERS = [
    {
        "company": "Berkshire Hathaway",
        "ticker": "BRK-B",
        "year": 2021,
        "fiscal_year_covered": "CY2021",
        "publication_date": "2022-02-26",
        "author": "Warren Buffett",
        "pdf_url": "https://www.berkshirehathaway.com/letters/2021ltr.pdf",
        "output_filename": "berkshire_2021.pdf",
        "benchmark_ticker": "^GSPC",
        "geography": "US",
        "sector": "Diversified Conglomerate",
    },
    {
        "company": "Berkshire Hathaway",
        "ticker": "BRK-B",
        "year": 2022,
        "fiscal_year_covered": "CY2022",
        "publication_date": "2023-02-25",
        "author": "Warren Buffett",
        "pdf_url": "https://www.berkshirehathaway.com/letters/2022ltr.pdf",
        "output_filename": "berkshire_2022.pdf",
        "benchmark_ticker": "^GSPC",
        "geography": "US",
        "sector": "Diversified Conglomerate",
    },
    {
        "company": "Berkshire Hathaway",
        "ticker": "BRK-B",
        "year": 2023,
        "fiscal_year_covered": "CY2023",
        "publication_date": "2024-02-24",
        "author": "Warren Buffett",
        "pdf_url": "https://www.berkshirehathaway.com/letters/2023ltr.pdf",
        "output_filename": "berkshire_2023.pdf",
        "benchmark_ticker": "^GSPC",
        "geography": "US",
        "sector": "Diversified Conglomerate",
    },
    {
        "company": "Infosys",
        "ticker": "INFY",
        "year": 2021,
        "fiscal_year_covered": "FY2021 (Apr 2020 - Mar 2021)",
        "publication_date": "2021-07-01",
        "author": "Salil Parekh",
        "pdf_url": "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-21.pdf",
        "output_filename": "infosys_fy2021_ar.pdf",
        "benchmark_ticker": "^CNXIT",
        "geography": "India",
        "sector": "IT Services",
    },
    {
        "company": "Infosys",
        "ticker": "INFY",
        "year": 2022,
        "fiscal_year_covered": "FY2022 (Apr 2021 - Mar 2022)",
        "publication_date": "2022-07-01",
        "author": "Salil Parekh",
        "pdf_url": "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-22.pdf",
        "output_filename": "infosys_fy2022_ar.pdf",
        "benchmark_ticker": "^CNXIT",
        "geography": "India",
        "sector": "IT Services",
    },
    {
        "company": "Infosys",
        "ticker": "INFY",
        "year": 2023,
        "fiscal_year_covered": "FY2023 (Apr 2022 - Mar 2023)",
        "publication_date": "2023-07-01",
        "author": "Salil Parekh",
        "pdf_url": "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-23.pdf",
        "output_filename": "infosys_fy2023_ar.pdf",
        "benchmark_ticker": "^CNXIT",
        "geography": "India",
        "sector": "IT Services",
    },
]


def get_letter(company: str, year: int) -> dict | None:
    """Look up a letter by company name and coverage year."""
    for letter in LETTERS:
        if letter["company"] == company and letter["year"] == year:
            return letter
    return None


def get_unique_tickers() -> set[str]:
    """Return all unique stock + benchmark tickers from the registry."""
    tickers = set()
    for letter in LETTERS:
        tickers.add(letter["ticker"])
        tickers.add(letter["benchmark_ticker"])
    return tickers
```

**Step 4: Run test — expect PASS**

**Step 5: Commit**

```bash
git add src/data_collection/letter_registry.py tests/test_letter_registry.py
git commit -m "feat: add letter metadata registry with 6 letters"
```

---

## Task 2: PDF Downloader

**Files:**
- Create: `context-graph-mvp/src/data_collection/download_letters.py`
- Test: `context-graph-mvp/tests/test_download_letters.py`

Downloads PDFs from URLs defined in the registry. Idempotent (skips existing). Validates each file is a real PDF.

**Step 1: Write the test**

```python
# tests/test_download_letters.py
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.data_collection.download_letters import download_pdf

def test_download_pdf_saves_file():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.content = b"%PDF-1.4 fake pdf content here"
    fake_response.raise_for_status = MagicMock()

    with tempfile.TemporaryDirectory() as tmpdir:
        outpath = os.path.join(tmpdir, "test.pdf")
        with patch("requests.get", return_value=fake_response):
            result = download_pdf("https://example.com/test.pdf", outpath)
        assert result is True
        assert os.path.exists(outpath)

def test_download_pdf_returns_false_on_failure():
    with patch("requests.get", side_effect=Exception("Network error")):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_pdf("https://example.com/bad.pdf",
                                  os.path.join(tmpdir, "bad.pdf"))
            assert result is False

def test_download_pdf_skips_existing(tmp_path):
    outpath = tmp_path / "exists.pdf"
    outpath.write_bytes(b"%PDF-1.4 already here" + b"x" * 2000)
    with patch("requests.get") as mock_get:
        result = download_pdf("https://example.com/x.pdf", str(outpath))
        assert result is True
        mock_get.assert_not_called()
```

**Step 2: Run test — expect FAIL**

**Step 3: Implement download_letters.py**

```python
# src/data_collection/download_letters.py
"""Download shareholder letter PDFs to data/raw/letters/."""

import os
import logging
import requests
from src.data_collection.letter_registry import LETTERS

logger = logging.getLogger(__name__)


def download_pdf(url: str, output_path: str, timeout: int = 60) -> bool:
    """Download a single PDF. Skips if file already exists and is > 1KB."""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        logger.info("SKIP (exists): %s", os.path.basename(output_path))
        return True

    try:
        logger.info("Downloading: %s", url)
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)

        size_kb = len(resp.content) / 1024
        logger.info("Saved: %s (%.0f KB)", os.path.basename(output_path), size_kb)
        return True

    except Exception as e:
        logger.error("FAILED: %s — %s", os.path.basename(output_path), e)
        return False


def download_all_letters(output_dir: str = "data/raw/letters") -> dict[str, bool]:
    """Download all letter PDFs from registry. Returns {filename: success}."""
    results = {}
    for letter in LETTERS:
        filename = letter["output_filename"]
        output_path = os.path.join(output_dir, filename)
        results[filename] = download_pdf(letter["pdf_url"], output_path)

    succeeded = sum(1 for v in results.values() if v)
    logger.info("PDFs: %d/%d downloaded successfully", succeeded, len(results))
    return results
```

**Step 4: Run test — expect PASS**

**Step 5: Commit**

```bash
git add src/data_collection/download_letters.py tests/test_download_letters.py
git commit -m "feat: add PDF downloader with skip-existing and graceful failure"
```

---

## Task 3: Market Data Fetcher

**Files:**
- Create: `context-graph-mvp/src/data_collection/fetch_market_data.py`
- Test: `context-graph-mvp/tests/test_fetch_market_data.py`

Fetches daily stock prices for all tickers from the registry via yfinance. Computes per-letter price snapshots (30d before → pub date → 7d after → 30d after).

**Step 1: Write the test**

```python
# tests/test_fetch_market_data.py
import pandas as pd
from src.data_collection.fetch_market_data import (
    find_nearest_trading_day,
    compute_letter_prices,
)

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
    }
    assert expected_keys.issubset(set(result.keys()))

def test_compute_letter_prices_constant_returns_zero():
    dates = pd.bdate_range("2023-01-01", "2023-04-30")
    prices = pd.DataFrame({"Close": [100.0] * len(dates)}, index=dates)
    result = compute_letter_prices(prices, "2023-02-25")
    assert result["return_7d_pct"] == 0.0
    assert result["return_30d_pct"] == 0.0
```

**Step 2: Run test — expect FAIL**

**Step 3: Implement** (same as previous plan — `fetch_market_data.py` with `fetch_and_save_all`, `compute_letter_prices`, `compute_all_letter_prices`). Tickers are derived from the registry via `get_unique_tickers()`, not hard-coded in the fetcher.

**Step 4: Run test — expect PASS**

**Step 5: Commit**

---

## Task 4: Analyst Data Fetcher

**Files:**
- Create: `context-graph-mvp/src/data_collection/fetch_analyst_data.py`
- Test: `context-graph-mvp/tests/test_fetch_analyst_data.py`

Fetches analyst recommendations (buy/hold/sell over time) and price targets from yfinance for each company ticker. Saves as CSVs.

**Step 1: Write the test**

```python
# tests/test_fetch_analyst_data.py
import pandas as pd
from unittest.mock import patch, MagicMock
from src.data_collection.fetch_analyst_data import (
    fetch_recommendations,
    get_recommendations_near_date,
)

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
    # Should include Feb 20 (5 days before) but not Jan 15 (41 days before)
    assert len(result) >= 1
    assert result.index[0] == pd.Timestamp("2023-02-20")

def test_get_recommendations_near_date_returns_empty_for_no_match():
    dates = pd.to_datetime(["2020-01-01"])
    df = pd.DataFrame({
        "strongBuy": [5], "buy": [3], "hold": [2],
        "sell": [1], "strongSell": [0],
    }, index=dates)
    result = get_recommendations_near_date(df, "2023-02-25", window_days=30)
    assert len(result) == 0
```

**Step 2: Run test — expect FAIL**

**Step 3: Implement fetch_analyst_data.py**

```python
# src/data_collection/fetch_analyst_data.py
"""Fetch analyst recommendations and price targets from yfinance."""

import os
import logging
from datetime import timedelta
import pandas as pd
import yfinance as yf
from src.data_collection.letter_registry import LETTERS

logger = logging.getLogger(__name__)


def fetch_recommendations(ticker: str) -> pd.DataFrame:
    """Fetch analyst recommendation history for a ticker."""
    t = yf.Ticker(ticker)
    try:
        recs = t.recommendations
        if recs is not None and not recs.empty:
            logger.info("%s: got %d recommendation periods", ticker, len(recs))
            return recs
    except Exception as e:
        logger.warning("%s recommendations failed: %s", ticker, e)
    return pd.DataFrame()


def fetch_price_targets(ticker: str) -> dict:
    """Fetch analyst price target summary for a ticker."""
    t = yf.Ticker(ticker)
    try:
        targets = t.analyst_price_targets
        if targets is not None:
            logger.info("%s: got price targets", ticker)
            return dict(targets) if not isinstance(targets, dict) else targets
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
        else:
            recs = fetch_recommendations(ticker)
            if not recs.empty:
                recs.to_csv(recs_path)
            results[f"{ticker}_recommendations"] = not recs.empty

        # Price targets
        targets_path = os.path.join(output_dir, f"{safe_name}_targets.json")
        if os.path.exists(targets_path):
            logger.info("SKIP (exists): %s", os.path.basename(targets_path))
        else:
            import json
            targets = fetch_price_targets(ticker)
            if targets:
                with open(targets_path, "w") as f:
                    json.dump(targets, f, indent=2, default=str)
            results[f"{ticker}_targets"] = bool(targets)

    return results
```

**Step 4: Run test — expect PASS**

**Step 5: Commit**

```bash
git add src/data_collection/fetch_analyst_data.py tests/test_fetch_analyst_data.py
git commit -m "feat: add analyst data fetcher (recommendations + price targets)"
```

---

## Task 5: Macroeconomic Data Fetcher

**Files:**
- Create: `context-graph-mvp/src/data_collection/fetch_macro_data.py`
- Test: `context-graph-mvp/tests/test_fetch_macro_data.py`

Fetches US macro data from FRED API (Fed Funds Rate, CPI, Unemployment). Fetches India data from RBI/data.gov.in or falls back to World Bank API. All stored as time-series CSVs.

**Step 1: Write the test**

```python
# tests/test_fetch_macro_data.py
import pandas as pd
from src.data_collection.fetch_macro_data import (
    get_macro_snapshot_for_date,
)

def test_get_macro_snapshot_for_date_structure():
    """Snapshot should have US and India sections."""
    # Create fake macro data
    dates = pd.date_range("2020-01-01", "2024-06-30", freq="MS")
    fed_funds = pd.DataFrame({"value": [0.25] * len(dates)}, index=dates)
    us_cpi = pd.DataFrame({"value": [260.0 + i*0.5 for i in range(len(dates))]}, index=dates)

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
```

**Step 2: Run test — expect FAIL**

**Step 3: Implement fetch_macro_data.py**

```python
# src/data_collection/fetch_macro_data.py
"""Fetch macroeconomic indicators from FRED API and Indian data sources."""

import os
import logging
from datetime import timedelta
import pandas as pd

logger = logging.getLogger(__name__)

# FRED series IDs
FRED_SERIES = {
    "us_fed_funds_rate": "FEDFUNDS",       # Effective Federal Funds Rate (monthly)
    "us_cpi": "CPIAUCSL",                  # Consumer Price Index (monthly, seasonally adj)
    "us_unemployment": "UNRATE",            # Unemployment Rate (monthly)
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
    """Fetch India RBI Repo Rate. Tries World Bank API as source."""
    try:
        import requests
        # World Bank indicator for India policy rate
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

        logger.warning("India RBI: no data from World Bank, will try fallback")
    except Exception as e:
        logger.warning("India RBI fetch failed: %s", e)

    return pd.DataFrame()


def fetch_india_cpi(start: str = START_DATE, end: str = END_DATE) -> pd.DataFrame:
    """Fetch India CPI from World Bank API."""
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

    # US data from FRED
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

    # India data
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

    def nearest_value(df, target):
        if df is None or df.empty:
            return None
        diffs = abs(df.index - target)
        nearest_idx = diffs.argmin()
        return float(df.iloc[nearest_idx]["value"])

    us_ff = nearest_value(fed_funds_df, target)
    us_cpi_val = nearest_value(us_cpi_df, target)

    # Compute YoY CPI change
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
```

**Step 4: Run test — expect PASS**

**Step 5: Commit**

```bash
git add src/data_collection/fetch_macro_data.py tests/test_fetch_macro_data.py
git commit -m "feat: add macro data fetcher (FRED + World Bank APIs)"
```

---

## Task 6: Analyst Narrative Synthesizer

**Files:**
- Create: `context-graph-mvp/src/data_collection/synthesize_analyst_narratives.py`
- Test: `context-graph-mvp/tests/test_synthesize_narratives.py`

Uses Claude API to synthesize structured analyst narratives from the quantitative data already collected (prices, recommendations, macro indicators). This is NOT hard-coding — it's LLM synthesis from real data, stored as auditable JSON files with the prompt included.

**Step 1: Write the test**

```python
# tests/test_synthesize_narratives.py
from src.data_collection.synthesize_analyst_narratives import (
    build_synthesis_prompt,
    parse_narrative_response,
)

def test_build_synthesis_prompt_includes_all_context():
    prompt = build_synthesis_prompt(
        company="Berkshire Hathaway",
        year=2022,
        publication_date="2023-02-25",
        stock_snapshot={"price_30d_before": 300, "price_on_date": 310,
                        "return_7d_pct": 1.2, "return_30d_pct": -2.5},
        benchmark_snapshot={"return_7d_pct": 0.5, "return_30d_pct": -1.0},
        recommendations={"buy": 5, "hold": 3, "sell": 0},
        macro_snapshot={"us_fed_funds_rate": 4.5, "us_cpi_yoy_pct": 6.4},
    )
    assert "Berkshire Hathaway" in prompt
    assert "2023-02-25" in prompt
    assert "4.5" in prompt

def test_parse_narrative_response_extracts_fields():
    raw = '''{
        "pre_letter_sentiment": "bullish",
        "key_analyst_concerns": "Focus on cash deployment. Succession questions.",
        "post_letter_reaction": "Analysts praised capital allocation discipline.",
        "sentiment_shift": "unchanged"
    }'''
    result = parse_narrative_response(raw)
    assert result["pre_letter_sentiment"] == "bullish"
    assert "cash deployment" in result["key_analyst_concerns"]
```

**Step 2: Run test — expect FAIL**

**Step 3: Implement synthesize_analyst_narratives.py**

```python
# src/data_collection/synthesize_analyst_narratives.py
"""Synthesize analyst narratives from quantitative data using Claude API.

Each narrative is generated from real collected data (prices, recommendations,
macro indicators) — not invented. The prompt and all input data are stored
alongside the output for full auditability.
"""

import os
import json
import logging
from anthropic import Anthropic
from src.data_collection.letter_registry import LETTERS

logger = logging.getLogger(__name__)


def build_synthesis_prompt(
    company: str,
    year: int,
    publication_date: str,
    stock_snapshot: dict,
    benchmark_snapshot: dict,
    recommendations: dict | None,
    macro_snapshot: dict,
) -> str:
    """Build the prompt for Claude to synthesize an analyst narrative."""
    return f"""You are a financial analyst summarizing the market context around a CEO shareholder letter publication.

COMPANY: {company}
LETTER YEAR: {year}
PUBLICATION DATE: {publication_date}

STOCK PRICE DATA (30 days before → publication → 7d/30d after):
- Price 30d before: ${stock_snapshot.get('price_30d_before', 'N/A')}
- Price on publication: ${stock_snapshot.get('price_on_date', 'N/A')}
- 7-day return: {stock_snapshot.get('return_7d_pct', 'N/A')}%
- 30-day return: {stock_snapshot.get('return_30d_pct', 'N/A')}%

BENCHMARK COMPARISON:
- Benchmark 7-day return: {benchmark_snapshot.get('return_7d_pct', 'N/A')}%
- Benchmark 30-day return: {benchmark_snapshot.get('return_30d_pct', 'N/A')}%

ANALYST RECOMMENDATIONS (nearest to publication date):
{json.dumps(recommendations, indent=2) if recommendations else 'Not available'}

MACROECONOMIC CONTEXT:
{json.dumps(macro_snapshot, indent=2)}

Based on this quantitative data and your knowledge of market conditions at that time, provide:

1. "pre_letter_sentiment": Overall analyst sentiment BEFORE the letter — one of "bullish", "neutral", "bearish"
2. "key_analyst_concerns": 2-3 sentences summarizing what analysts and investors were focused on before this letter was published
3. "post_letter_reaction": 2-3 sentences summarizing likely market/analyst reaction after the letter, based on the stock price movement data
4. "sentiment_shift": How sentiment changed after the letter — one of "improved", "unchanged", "deteriorated"
5. "macro_narrative": 2-3 sentences describing the macroeconomic backdrop at the time of publication

Return as a JSON object with exactly these 5 keys."""


def parse_narrative_response(raw_text: str) -> dict:
    """Parse Claude's JSON response into a narrative dict."""
    # Strip markdown code fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


def synthesize_narrative(
    company: str,
    year: int,
    publication_date: str,
    stock_snapshot: dict,
    benchmark_snapshot: dict,
    recommendations: dict | None,
    macro_snapshot: dict,
    api_key: str = "",
) -> dict:
    """Synthesize a single analyst narrative and return the full auditable record."""
    prompt = build_synthesis_prompt(
        company, year, publication_date,
        stock_snapshot, benchmark_snapshot, recommendations, macro_snapshot,
    )

    if not api_key:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY", "")

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_response = response.content[0].text
    narrative = parse_narrative_response(raw_response)

    # Return full auditable record
    return {
        "company": company,
        "year": year,
        "publication_date": publication_date,
        "input_data": {
            "stock_snapshot": stock_snapshot,
            "benchmark_snapshot": benchmark_snapshot,
            "recommendations": recommendations,
            "macro_snapshot": macro_snapshot,
        },
        "prompt": prompt,
        "raw_response": raw_response,
        "narrative": narrative,
    }


def synthesize_all(
    price_snapshots: list[dict],
    macro_snapshots: dict,
    analyst_dir: str = "data/raw/analyst",
    output_dir: str = "data/raw/analyst_narratives",
) -> dict[str, bool]:
    """Synthesize narratives for all 6 letters."""
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    for letter in LETTERS:
        key = f"{letter['company'].lower().replace(' ', '_')}_{letter['year']}"
        outpath = os.path.join(output_dir, f"{key}.json")

        if os.path.exists(outpath):
            logger.info("SKIP (exists): %s", key)
            results[key] = True
            continue

        # Find matching price snapshot
        snap = next(
            (s for s in price_snapshots
             if s["company"] == letter["company"] and s["year"] == letter["year"]),
            None,
        )
        if not snap:
            logger.warning("No price snapshot for %s %d — skipping", letter["company"], letter["year"])
            results[key] = False
            continue

        # Load analyst recommendations if available
        recs = _load_recommendations_near_date(analyst_dir, letter)

        # Get macro snapshot for this date
        macro = macro_snapshots.get(letter["publication_date"], {})

        try:
            record = synthesize_narrative(
                company=letter["company"],
                year=letter["year"],
                publication_date=letter["publication_date"],
                stock_snapshot=snap["stock"],
                benchmark_snapshot=snap["benchmark"],
                recommendations=recs,
                macro_snapshot=macro,
            )
            with open(outpath, "w") as f:
                json.dump(record, f, indent=2)
            logger.info("Synthesized narrative: %s", key)
            results[key] = True
        except Exception as e:
            logger.error("Failed to synthesize %s: %s", key, e)
            results[key] = False

    return results


def _load_recommendations_near_date(analyst_dir: str, letter: dict) -> dict | None:
    """Load recommendation counts nearest to a letter's publication date."""
    import pandas as pd
    from src.data_collection.fetch_analyst_data import get_recommendations_near_date

    safe_name = letter["ticker"].lower().replace("-", "_").replace(".", "_")
    recs_path = os.path.join(analyst_dir, f"{safe_name}_recommendations.csv")

    if not os.path.exists(recs_path):
        return None

    try:
        df = pd.read_csv(recs_path, index_col=0, parse_dates=True)
        nearby = get_recommendations_near_date(df, letter["publication_date"])
        if not nearby.empty:
            latest = nearby.iloc[-1]
            return {col: int(latest[col]) for col in nearby.columns if col != "period"}
    except Exception as e:
        logger.warning("Could not load recommendations for %s: %s", letter["ticker"], e)

    return None
```

**Step 4: Run test — expect PASS**

**Step 5: Commit**

```bash
git add src/data_collection/synthesize_analyst_narratives.py tests/test_synthesize_narratives.py
git commit -m "feat: add analyst narrative synthesizer with full auditability"
```

---

## Task 7: Script 01 — Full Orchestrator + Validation Report

**Files:**
- Create: `context-graph-mvp/scripts/01_collect_data.py`

The top-level script. Calls all fetchers in dependency order, prints comprehensive validation.

**Step 1: Implement** — Orchestrator calls:
1. `download_all_letters()` → PDFs
2. `fetch_market_data.fetch_and_save_all()` → price CSVs
3. `fetch_analyst_data.fetch_and_save_all()` → recommendation CSVs
4. `fetch_macro_data.fetch_and_save_all()` → macro CSVs
5. `compute_all_letter_prices()` → price snapshots JSON
6. `compute_macro_snapshots()` → macro snapshots per letter
7. `synthesize_all()` → analyst narrative JSONs
8. Print validation report covering ALL data

**Step 2: Run E2E**

```bash
python scripts/01_collect_data.py
```

**Step 3: Commit**

---

## Task 8: Install Dependencies and Run End-to-End

**Step 1:** Create venv, install requirements
**Step 2:** Set up `.env` with API keys (FRED + Anthropic)
**Step 3:** Run all tests
**Step 4:** Run Script 01 for real
**Step 5:** Review validation report with SG

---

## Summary of Deliverables

| Task | Module | Data Source | Output |
|------|--------|-------------|--------|
| 0 | scaffold | — | Project structure |
| 1 | `letter_registry.py` | — | Registry of 6 letters |
| 2 | `download_letters.py` | HTTP | 6 PDFs |
| 3 | `fetch_market_data.py` | yfinance | 4 price CSVs + snapshots |
| 4 | `fetch_analyst_data.py` | yfinance | Recommendations + targets |
| 5 | `fetch_macro_data.py` | FRED + World Bank | Macro indicator CSVs |
| 6 | `synthesize_analyst_narratives.py` | Claude API | 6 narrative JSONs |
| 7 | `01_collect_data.py` | orchestrator | Validation report |
| 8 | — | — | E2E run + SG review |

## Environment Variables Required

```
ANTHROPIC_API_KEY=sk-ant-...   # For narrative synthesis
FRED_API_KEY=...               # Free at https://fred.stlouisfed.org/docs/api/api_key.html
```
