#!/usr/bin/env python3
"""Script 06 — Build ChromaDB baseline RAG collection."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rag.baseline import build_collection, query_baseline

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


def main():
    print("=" * 60)
    print("SCRIPT 06: Build Baseline RAG (ChromaDB)")
    print("=" * 60)

    print("\n--- Building collection ---")
    collection = build_collection()
    print(f"  Total chunks: {collection.count()}")

    # Sanity test
    print("\n--- Sanity query: 'uncertainty and risk management' ---")
    results = query_baseline(collection, "uncertainty and risk management", n_results=3)
    for i, r in enumerate(results):
        company = r["metadata"]["company"]
        year = r["metadata"]["year"]
        preview = r["text"][:120].replace("\n", " ")
        print(f"  [{i+1}] {company} {year}: {preview}...")

    print("\n→ CHECKPOINT 2: Review graph + RAG before query engine.")
    print("→ Next: python scripts/07_run_comparisons.py")


if __name__ == "__main__":
    main()
