#!/usr/bin/env python3
"""Script 04 — Extract themes, detect parallels, detect temporal evolution."""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_collection.letter_registry import LETTERS
from src.analysis.theme_extraction import (
    extract_and_cache, detect_parallels, detect_temporal_evolution,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

CONTEXT_PKG_DIR = "data/processed/context_packages"
THEMES_DIR = "data/themes"


def _load_context_package(letter: dict) -> dict | None:
    base = os.path.splitext(letter["output_filename"])[0]
    if letter["company"] == "Infosys":
        name = f"{base.replace('_ar', '')}_context.json"
    else:
        name = f"{base}_context.json"
    path = os.path.join(CONTEXT_PKG_DIR, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def main():
    print("=" * 60)
    print("SCRIPT 04: Theme Extraction")
    print("=" * 60)

    os.makedirs(THEMES_DIR, exist_ok=True)

    # ── Step 1: Extract themes for each letter ──────────────
    print("\n--- Extracting themes (5-7 per letter) ---")
    all_themes = {}  # {(company, year): themes_list}

    for letter in LETTERS:
        pkg = _load_context_package(letter)
        if not pkg:
            print(f"  ⚠ No context package for {letter['company']} {letter['year']}")
            continue

        letter_text = pkg["during"]["letter_text"]
        if not letter_text or len(letter_text) < 100:
            print(f"  ⚠ No letter text for {letter['company']} {letter['year']}")
            continue

        macro_summary = pkg["before"]["macro_context"].get("key_headline", "")
        themes = extract_and_cache(pkg["meta"], letter_text, macro_summary)
        all_themes[(letter["company"], letter["year"])] = themes
        print(f"  {letter['company']} {letter['year']}: {len(themes)} themes")

    # ── Step 2: Cross-company parallel detection ────────────
    print("\n--- Detecting cross-company parallels ---")
    all_parallels = []

    for year in [2021, 2022, 2023]:
        brk = all_themes.get(("Berkshire Hathaway", year), [])
        infy = all_themes.get(("Infosys", year), [])

        if not brk or not infy:
            print(f"  ⚠ Missing themes for {year}, skipping parallels")
            continue

        # Get macro context for this year from any context package
        macro = ""
        for letter in LETTERS:
            if letter["year"] == year:
                pkg = _load_context_package(letter)
                if pkg:
                    macro = pkg["before"]["macro_context"].get("key_headline", "")
                    break

        cache_path = os.path.join(THEMES_DIR, f"parallels_{year}.json")
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                parallels = json.load(f)
            print(f"  {year}: {len(parallels)} parallels (cached)")
        else:
            parallels = detect_parallels(brk, infy, year, macro)
            with open(cache_path, "w") as f:
                json.dump(parallels, f, indent=2)
            print(f"  {year}: {len(parallels)} parallels detected")

        for p in parallels:
            p["year"] = year
        all_parallels.extend(parallels)

    # Save combined parallels
    combined_path = os.path.join(THEMES_DIR, "cross_company_parallels.json")
    with open(combined_path, "w") as f:
        json.dump(all_parallels, f, indent=2)
    print(f"  Total parallels: {len(all_parallels)}")

    # ── Step 3: Temporal evolution within each company ──────
    print("\n--- Detecting temporal evolution ---")
    all_evolution = []

    for company in ["Berkshire Hathaway", "Infosys"]:
        themes_by_year = {}
        for year in [2021, 2022, 2023]:
            t = all_themes.get((company, year), [])
            if t:
                themes_by_year[year] = t

        if len(themes_by_year) < 2:
            print(f"  ⚠ {company}: insufficient years for evolution detection")
            continue

        safe_name = company.lower().replace(" ", "_")
        cache_path = os.path.join(THEMES_DIR, f"{safe_name}_evolution.json")
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                evolution = json.load(f)
            print(f"  {company}: {len(evolution)} evolutions (cached)")
        else:
            evolution = detect_temporal_evolution(themes_by_year, company)
            with open(cache_path, "w") as f:
                json.dump(evolution, f, indent=2)
            print(f"  {company}: {len(evolution)} evolutions detected")

        for e in evolution:
            e["company"] = company
        all_evolution.extend(evolution)

    evo_path = os.path.join(THEMES_DIR, "temporal_evolution.json")
    with open(evo_path, "w") as f:
        json.dump(all_evolution, f, indent=2)

    # ── Step 4: Update context packages with themes ─────────
    print("\n--- Updating context packages with themes ---")
    for letter in LETTERS:
        themes = all_themes.get((letter["company"], letter["year"]), [])
        if not themes:
            continue
        pkg = _load_context_package(letter)
        if not pkg:
            continue
        pkg["during"]["themes"] = themes

        # Write back
        base = os.path.splitext(letter["output_filename"])[0]
        if letter["company"] == "Infosys":
            name = f"{base.replace('_ar', '')}_context.json"
        else:
            name = f"{base}_context.json"
        path = os.path.join(CONTEXT_PKG_DIR, name)
        with open(path, "w") as f:
            json.dump(pkg, f, indent=2)
        print(f"  Updated {name} with {len(themes)} themes")

    # Summary
    print("\n" + "=" * 60)
    print(f"  Themes extracted: {sum(len(t) for t in all_themes.values())} across {len(all_themes)} letters")
    print(f"  Cross-company parallels: {len(all_parallels)}")
    print(f"  Temporal evolutions: {len(all_evolution)}")
    print("\n→ Next: Set up Neo4j, then run scripts/05_setup_neo4j.py")
    print("→ CHECKPOINT 2: Review themes and parallels before graph loading")


if __name__ == "__main__":
    main()
