#!/usr/bin/env python3
"""Script 07 — Run all 5 demo queries through both systems and cache results."""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("SCRIPT 07: Run Comparisons")
    print("=" * 60)

    output_dir = "data/comparisons"
    os.makedirs(output_dir, exist_ok=True)

    # Connect to Neo4j
    driver = None
    uri = os.getenv("NEO4J_URI", "")
    if uri and os.getenv("NEO4J_PASSWORD"):
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(os.getenv("NEO4J_USERNAME", "neo4j"),
                                                  os.getenv("NEO4J_PASSWORD")))
        try:
            driver.verify_connectivity()
            print("  Neo4j: connected")
        except Exception as e:
            print(f"  Neo4j: connection failed ({e}), will use cached data")
            driver = None
    else:
        print("  Neo4j: no credentials, will skip graph queries")

    # Load ChromaDB
    collection = None
    try:
        from src.rag.baseline import get_collection
        collection = get_collection()
        print(f"  ChromaDB: {collection.count()} chunks")
    except Exception as e:
        print(f"  ChromaDB: not available ({e})")

    from src.query_engine.intent import classify, DEMO_QUERIES
    from src.query_engine.retriever import retrieve_both
    from src.query_engine.synthesizer import (
        synthesize_graph_response, synthesize_rag_response, synthesize_comparison
    )

    for num, query_text in DEMO_QUERIES.items():
        print(f"\n--- Query {num}: {query_text[:60]}... ---")

        cache_path = os.path.join(output_dir, f"query_{num}_results.json")
        if os.path.exists(cache_path):
            print(f"  SKIP (cached): {cache_path}")
            continue

        intent = classify(query_text)
        retrieval = retrieve_both(driver, collection, query_text, intent)

        # Synthesize responses
        graph_resp = synthesize_graph_response(retrieval["graph_results"], query_text)
        rag_resp = synthesize_rag_response(retrieval["rag_results"], query_text)
        comparison = synthesize_comparison(query_text, graph_resp, rag_resp)

        # Save full results
        result = {
            "query_number": num,
            "query_text": query_text,
            "intent": intent,
            "graph_response": graph_resp,
            "rag_response": rag_resp,
            "comparison": comparison["comparison"],
            "graph_results_raw": retrieval["graph_results"],
            "rag_results_raw": [{"text": r["text"][:200], "metadata": r["metadata"]}
                                for r in retrieval["rag_results"]],
        }
        with open(cache_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  Saved: {cache_path}")
        print(f"  Graph response: {len(graph_resp)} chars")
        print(f"  RAG response:   {len(rag_resp)} chars")

    if driver:
        driver.close()

    print("\n" + "=" * 60)
    print("  All 5 comparisons complete.")
    print("→ Next: python scripts/08_launch_demo.py")
    print("→ CHECKPOINT 3: Review comparisons before demo")


if __name__ == "__main__":
    main()
