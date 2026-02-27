"""Hybrid retriever — runs Neo4j graph queries and ChromaDB vector search."""

import json
import logging

logger = logging.getLogger(__name__)


def retrieve_graph(driver, intent: dict) -> list[dict]:
    """Execute the appropriate Cypher query based on intent."""
    from src.graph.queries import run_demo_query, DEMO_QUERIES

    if intent.get("is_demo_query"):
        query_num = intent["demo_query_number"]
        return run_demo_query(driver, query_num)

    # For free-text queries, pick the closest demo query by type
    type_to_query = {
        "cross_cultural_comparison": 1,
        "temporal_evolution": 2,
        "theme_parallel": 3,
        "context_outcome": 4,
        "communication_pattern": 5,
    }
    query_num = type_to_query.get(intent.get("query_type"), 1)

    # Override params based on intent
    q = DEMO_QUERIES[query_num]
    params = dict(q["params"])
    companies = intent.get("companies", [])
    if query_num == 2 and companies:
        params["company"] = companies[0]

    with driver.session() as session:
        result = session.run(q["cypher"], **params)
        return [dict(record) for record in result]


def retrieve_rag(collection, query: str, n_results: int = 5) -> list[dict]:
    """Simple vector search — the baseline."""
    from src.rag.baseline import query_baseline
    return query_baseline(collection, query, n_results=n_results)


def retrieve_both(driver, collection, query: str, intent: dict) -> dict:
    """Run both retrievers and return combined results."""
    graph_results = []
    rag_results = []

    # Graph retrieval
    try:
        if driver:
            graph_results = retrieve_graph(driver, intent)
            logger.info("Graph: %d results", len(graph_results))
    except Exception as e:
        logger.warning("Graph retrieval failed: %s", e)

    # RAG retrieval
    try:
        if collection:
            rag_results = retrieve_rag(collection, query)
            logger.info("RAG: %d chunks", len(rag_results))
    except Exception as e:
        logger.warning("RAG retrieval failed: %s", e)

    return {
        "query": query,
        "intent": intent,
        "graph_results": _serialize(graph_results),
        "rag_results": rag_results,
    }


def _serialize(results: list) -> list:
    """Make Neo4j results JSON-serializable."""
    serialized = []
    for record in results:
        row = {}
        for key, value in record.items():
            if hasattr(value, "items"):
                row[key] = dict(value)
            elif isinstance(value, list):
                row[key] = [dict(v) if hasattr(v, "items") else v for v in value]
            else:
                row[key] = value
        serialized.append(row)
    return serialized
