#!/usr/bin/env python3
"""Script 03 — Assemble Context Envelope JSONs (before/during/after) for each letter."""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.data_collection.letter_registry import LETTERS
from src.data_collection.fetch_market_data import get_ticker_filename
from src.data_collection.fetch_macro_data import get_macro_snapshot_for_date

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Hardcoded macro fallback for the 6 known publication dates ──────────
# Sources: FRED, RBI, public records. Used when FRED API key unavailable.
MACRO_FALLBACK = {
    "2021-07-01": {  # Infosys FY2021 AR
        "us_fed_funds_rate": 0.08,
        "us_cpi_yoy_pct": 5.4,
        "india_rbi_repo_rate": 4.0,
        "india_cpi_yoy_pct": 6.3,
        "key_headline": "Post-COVID recovery accelerating. US inflation emerging at 5.4%. "
                        "India second COVID wave subsiding. Digital acceleration boosting IT demand.",
        "us_context": "Near-zero rates, massive fiscal stimulus, labor market recovering",
        "india_context": "Second COVID wave aftermath, IT services boom, attrition beginning",
        "global_context": "Vaccine rollout uneven, supply chain disruptions emerging, chip shortage",
    },
    "2022-02-26": {  # Berkshire 2021 letter
        "us_fed_funds_rate": 0.08,
        "us_cpi_yoy_pct": 7.9,
        "india_rbi_repo_rate": 4.0,
        "india_cpi_yoy_pct": 6.1,
        "key_headline": "US inflation surging to 40-year high at 7.9%. Fed signaling imminent rate hikes. "
                        "Russia-Ukraine tensions escalating.",
        "us_context": "Inflation surging, rate hikes imminent, post-COVID boom, supply chain crisis",
        "india_context": "IT boom continuing, attrition peaking, strong deal pipeline",
        "global_context": "Russia-Ukraine war imminent, energy prices rising, supply chain crisis peaks",
    },
    "2022-07-01": {  # Infosys FY2022 AR
        "us_fed_funds_rate": 1.58,
        "us_cpi_yoy_pct": 9.1,
        "india_rbi_repo_rate": 4.9,
        "india_cpi_yoy_pct": 7.0,
        "key_headline": "US inflation at 9.1% — 40-year peak. Aggressive Fed rate hikes underway. "
                        "India IT facing peak attrition crisis with 25%+ rates.",
        "us_context": "Aggressive rate hikes begun, inflation at 40-year peak, recession fears emerging",
        "india_context": "Peak IT attrition crisis (25%+), strong demand but margin pressure, rupee weakening",
        "global_context": "Ukraine war ongoing, energy crisis in Europe, global food prices spiking",
    },
    "2023-02-25": {  # Berkshire 2022 letter
        "us_fed_funds_rate": 4.57,
        "us_cpi_yoy_pct": 6.0,
        "india_rbi_repo_rate": 6.5,
        "india_cpi_yoy_pct": 6.4,
        "key_headline": "Fed funds at 4.57% after aggressive hikes. Inflation declining from peak. "
                        "Banking stress emerging (SVB pre-collapse).",
        "us_context": "Rate hikes slowing, inflation declining from peak, banking stress emerging",
        "india_context": "RBI tightening, IT demand moderating, attrition normalizing",
        "global_context": "China reopening, energy prices stabilizing, recession fears persist",
    },
    "2023-07-01": {  # Infosys FY2023 AR
        "us_fed_funds_rate": 5.08,
        "us_cpi_yoy_pct": 3.0,
        "india_rbi_repo_rate": 6.5,
        "india_cpi_yoy_pct": 4.8,
        "key_headline": "US inflation declining to 3%. Peak rates at 5.08%. AI narrative exploding "
                        "post-ChatGPT. IT services demand softening.",
        "us_context": "Peak rates, inflation declining, SVB collapse aftermath, AI boom narrative",
        "india_context": "IT demand slowdown, AI narrative emerging, large deal wins but margin focus",
        "global_context": "AI/ChatGPT revolution, US banking crisis contained, China recovery disappoints",
    },
    "2024-02-24": {  # Berkshire 2023 letter
        "us_fed_funds_rate": 5.33,
        "us_cpi_yoy_pct": 3.1,
        "india_rbi_repo_rate": 6.5,
        "india_cpi_yoy_pct": 5.1,
        "key_headline": "Fed holding at 5.33%, rate cuts expected in 2024. Charlie Munger passed Nov 2023. "
                        "AI reshaping investment landscape.",
        "us_context": "Rate cuts anticipated, soft landing narrative, AI investment boom, Munger tribute",
        "india_context": "IT sector recovery signs, AI services demand, margin improvement",
        "global_context": "Rate cut expectations, AI investment surge, geopolitical tensions (Middle East)",
    },
}


def _load_csv_safe(path: str) -> pd.DataFrame | None:
    """Load a CSV as DataFrame, or return None if file missing."""
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0)
        # Try to parse index as datetime
        try:
            df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
        except Exception:
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                pass  # Leave as-is if not date-parseable
        return df
    return None


def _load_json_safe(path: str) -> dict | list | None:
    """Load a JSON file, or return None if file missing."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def _get_analyst_summary(ticker: str, pub_date: str, analyst_dir: str) -> dict:
    """Build analyst summary from saved data."""
    safe = ticker.lower().replace("-", "_").replace(".", "_")
    recs_path = os.path.join(analyst_dir, f"{safe}_recommendations.csv")
    targets_path = os.path.join(analyst_dir, f"{safe}_targets.json")

    result = {"analyst_recommendations": None, "analyst_consensus_eps": None,
              "pre_letter_sentiment": "neutral", "key_analyst_concerns": ""}

    # Recommendations — use most recent period (yfinance saves relative periods, not dates)
    recs_df = _load_csv_safe(recs_path)
    if recs_df is not None and not recs_df.empty:
        # Use the first row (most recent period "0m")
        row = recs_df.iloc[0]
        buy_total = int(row.get("strongBuy", 0) or 0) + int(row.get("buy", 0) or 0)
        sell_total = int(row.get("sell", 0) or 0) + int(row.get("strongSell", 0) or 0)
        hold_total = int(row.get("hold", 0) or 0)
        result["analyst_recommendations"] = {"buy": buy_total, "hold": hold_total, "sell": sell_total}
        if buy_total > sell_total + hold_total:
            result["pre_letter_sentiment"] = "bullish"
        elif sell_total > buy_total:
            result["pre_letter_sentiment"] = "bearish"

    # Price targets
    targets = _load_json_safe(targets_path)
    if targets and "targetMeanPrice" in targets:
        result["analyst_consensus_eps"] = targets.get("targetMeanPrice")

    return result


def build_context_package(letter: dict, price_snapshots: list, macro_dir: str,
                          analyst_dir: str, text_dir: str) -> dict:
    """Assemble a single Context Envelope JSON for one letter."""
    company = letter["company"]
    year = letter["year"]
    pub_date = letter["publication_date"]

    # Find price snapshot for this letter
    snap = None
    for s in price_snapshots:
        if s["company"] == company and s["year"] == year:
            snap = s
            break

    # Load letter text
    base = os.path.splitext(letter["output_filename"])[0]
    if company == "Infosys":
        txt_name = f"{base.replace('_ar', '')}_ceo.txt"
    else:
        txt_name = f"{base}.txt"
    txt_path = os.path.join(text_dir, txt_name)
    letter_text = ""
    if os.path.exists(txt_path):
        with open(txt_path, encoding="utf-8") as f:
            letter_text = f.read()

    # Macro context — try API data first, fall back to hardcoded
    fed_df = _load_csv_safe(os.path.join(macro_dir, "us_fed_funds_rate.csv"))
    cpi_df = _load_csv_safe(os.path.join(macro_dir, "us_cpi.csv"))
    india_repo_df = _load_csv_safe(os.path.join(macro_dir, "india_rbi_repo.csv"))
    india_cpi_df = _load_csv_safe(os.path.join(macro_dir, "india_cpi.csv"))

    macro_api = get_macro_snapshot_for_date(pub_date, fed_df, cpi_df, india_repo_df, india_cpi_df)

    # Use hardcoded fallback for any missing values
    fallback = MACRO_FALLBACK.get(pub_date, {})
    macro_context = {
        "us_fed_rate": f"{macro_api.get('us_fed_funds_rate') or fallback.get('us_fed_funds_rate', 'N/A')}%",
        "us_inflation_rate": f"{macro_api.get('us_cpi_yoy_pct') or fallback.get('us_cpi_yoy_pct', 'N/A')}%",
        "india_rbi_repo_rate": f"{macro_api.get('india_rbi_repo_rate') or fallback.get('india_rbi_repo_rate', 'N/A')}%",
        "india_cpi_yoy_pct": f"{macro_api.get('india_cpi_yoy_pct') or fallback.get('india_cpi_yoy_pct', 'N/A')}%",
        "key_headline": fallback.get("key_headline", ""),
        "us_context": fallback.get("us_context", ""),
        "india_context": fallback.get("india_context", ""),
        "global_context": fallback.get("global_context", ""),
    }

    # Analyst context
    analyst = _get_analyst_summary(letter["ticker"], pub_date, analyst_dir)

    # Build the envelope
    package = {
        "meta": {
            "company": company,
            "company_ticker": letter["ticker"],
            "letter_year": year,
            "fiscal_year_covered": letter["fiscal_year_covered"],
            "publication_date": pub_date,
            "author": letter["author"],
            "letter_type": "annual_shareholder_letter" if company == "Berkshire Hathaway" else "annual_report_ceo_letter",
            "geography": letter["geography"],
            "sector": letter["sector"],
        },
        "before": {
            "stock_price_30d_before": snap["stock"]["price_30d_before"] if snap else None,
            "stock_price_on_publication": snap["stock"]["price_on_date"] if snap else None,
            "stock_30d_return_pct": snap["stock"]["return_30d_pct"] if snap else None,
            "benchmark_index": "S&P 500" if letter["geography"] == "US" else "Nifty IT",
            "benchmark_30d_return_pct": snap["benchmark"]["return_30d_pct"] if snap else None,
            "relative_return_30d_pct": snap["relative_return_30d_pct"] if snap else None,
            **analyst,
            "macro_context": macro_context,
        },
        "during": {
            "letter_text": letter_text,
            "word_count": len(letter_text.split()) if letter_text else 0,
            "overall_sentiment_score": None,  # filled by theme extraction
            "forward_looking_ratio": None,    # filled by theme extraction
            "themes": [],                     # filled by script 04
            "key_quotes": [],                 # filled by theme extraction
        },
        "after": {
            "stock_change_7d_pct": snap["stock"]["return_7d_pct"] if snap else None,
            "stock_change_30d_pct": snap["stock"]["return_30d_pct"] if snap else None,
            "benchmark_change_7d_pct": snap["benchmark"]["return_7d_pct"] if snap else None,
            "benchmark_change_30d_pct": snap["benchmark"]["return_30d_pct"] if snap else None,
            "relative_return_7d_pct": snap["relative_return_7d_pct"] if snap else None,
            "relative_return_30d_pct": snap["relative_return_30d_pct"] if snap else None,
            "post_letter_analyst_reaction": "",  # could be filled manually
            "sentiment_shift": "unchanged",
        },
    }
    return package


def main():
    print("=" * 60)
    print("SCRIPT 03: Build Context Packages")
    print("=" * 60)

    # Load price snapshots
    snap_path = "data/processed/letter_price_snapshots.json"
    price_snapshots = _load_json_safe(snap_path) or []
    if not price_snapshots:
        logger.warning("No price snapshots found at %s — run script 02 first", snap_path)

    output_dir = "data/processed/context_packages"
    os.makedirs(output_dir, exist_ok=True)

    for letter in LETTERS:
        company = letter["company"]
        year = letter["year"]

        # Output filename
        base = os.path.splitext(letter["output_filename"])[0]
        if company == "Infosys":
            out_name = f"{base.replace('_ar', '')}_context.json"
        else:
            out_name = f"{base}_context.json"
        out_path = os.path.join(output_dir, out_name)

        package = build_context_package(
            letter, price_snapshots,
            macro_dir="data/raw/macro",
            analyst_dir="data/raw/analyst",
            text_dir="data/processed/letters",
        )

        with open(out_path, "w") as f:
            json.dump(package, f, indent=2)

        wc = package["during"]["word_count"]
        has_before = package["before"]["stock_price_on_publication"] is not None
        print(f"  {company} {year}: {wc} words, before={'✓' if has_before else '✗'}, "
              f"macro={'✓' if package['before']['macro_context']['key_headline'] else '✗'}")

    # Summary
    print(f"\n  Saved {len(LETTERS)} context packages to {output_dir}/")
    print("\n→ CHECKPOINT 1: Review data quality before proceeding.")
    print("  - Check word counts (Berkshire ~3000-5000, Infosys CEO ~1000-3000)")
    print("  - Verify macro context accuracy")
    print("  - Verify price snapshots make sense")
    print("\n→ Next: python scripts/04_extract_themes.py")


if __name__ == "__main__":
    main()
