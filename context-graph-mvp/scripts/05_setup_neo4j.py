#!/usr/bin/env python3
"""Script 05 — Create Neo4j schema and load all data."""

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
    print("SCRIPT 05: Neo4j Setup")
    print("=" * 60)

    uri = os.getenv("NEO4J_URI", "")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    if not uri or not password:
        print("\n⚠  Neo4j credentials not found in .env")
        print("\n  Option A (recommended): Neo4j Aura Free")
        print("    1. Go to https://console.neo4j.io")
        print("    2. Create Free Instance")
        print("    3. Copy URI, username, password to .env")
        print("\n  Option B: Docker")
        print("    docker run -d -p 7474:7474 -p 7687:7687 \\")
        print("      -e NEO4J_AUTH=neo4j/password neo4j:5-community")
        print("    Then set in .env:")
        print("      NEO4J_URI=bolt://localhost:7687")
        print("      NEO4J_PASSWORD=password")
        return

    from neo4j import GraphDatabase
    from src.graph.schema import create_schema, get_node_counts, get_relationship_counts
    from src.graph.loader import load_all

    print(f"\n  Connecting to {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        driver.verify_connectivity()
        print("  Connected!")
    except Exception as e:
        print(f"\n⚠  Connection failed: {e}")
        print("  Check NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env")
        return

    # Create schema
    print("\n--- Creating schema ---")
    create_schema(driver)

    # Load all data
    print("\n--- Loading data ---")
    load_all(driver)

    # Print counts
    print("\n--- Node counts ---")
    for label, count in get_node_counts(driver).items():
        print(f"  {label}: {count}")

    print("\n--- Relationship counts ---")
    for rel, count in get_relationship_counts(driver).items():
        print(f"  {rel}: {count}")

    # Quick test: run demo query 1
    print("\n--- Testing demo query 1 ---")
    from src.graph.queries import run_demo_query
    results = run_demo_query(driver, 1)
    print(f"  Query 1 returned {len(results)} rows")

    driver.close()
    print("\n→ Next: python scripts/06_build_baseline_rag.py")


if __name__ == "__main__":
    main()
