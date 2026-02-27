#!/usr/bin/env python3
"""Script 02 — Extract text from PDFs and compute price snapshots."""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_collection.extract_text import extract_all_letters
from src.data_collection.fetch_market_data import compute_all_letter_prices

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("SCRIPT 02: Process Letters")
    print("=" * 60)

    # 1. Extract text from PDFs
    print("\n--- Extracting text from PDFs ---")
    text_results = extract_all_letters()
    for name, wc in sorted(text_results.items()):
        status = f"{wc} words" if wc > 0 else "FAILED"
        print(f"  {name}: {status}")

    # 2. Compute price snapshots for each letter
    print("\n--- Computing price snapshots ---")
    price_snapshots = compute_all_letter_prices()

    out_dir = "data/processed"
    os.makedirs(out_dir, exist_ok=True)
    snap_path = os.path.join(out_dir, "letter_price_snapshots.json")
    with open(snap_path, "w") as f:
        json.dump(price_snapshots, f, indent=2)
    print(f"  Saved {len(price_snapshots)} price snapshots to {snap_path}")

    for snap in price_snapshots:
        print(f"  {snap['company']} {snap['year']}: "
              f"7d={snap['stock']['return_7d_pct']:+.1f}% "
              f"30d={snap['stock']['return_30d_pct']:+.1f}% "
              f"(rel 7d={snap['relative_return_7d_pct']:+.1f}%)")

    # Summary
    print("\n" + "=" * 60)
    extracted = sum(1 for wc in text_results.values() if wc > 0)
    print(f"  Texts extracted: {extracted}/{len(text_results)}")
    print(f"  Price snapshots: {len(price_snapshots)}")

    if extracted < 6:
        print("\n⚠  Some extractions failed. Check PDFs in data/raw/letters/")
        print("   Infosys page ranges may need adjustment in extract_text.py")

    print("\n→ Next: python scripts/03_build_context_packages.py")


if __name__ == "__main__":
    main()
