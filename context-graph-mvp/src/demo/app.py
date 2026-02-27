"""Streamlit demo — Context Graph for Executive Communication Intelligence."""

import json
import logging
import os
import sys

import streamlit as st

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets (cloud) first, then fall back to env vars."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)

COMPARISONS_DIR = "data/comparisons"

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Context Graph: Executive Communication Intelligence",
    page_icon="📊",
    layout="wide",
)

from src.demo.arena_style import inject_arena_css, COMPANY_COLORS, SENTIMENT_COLORS, EDGE_COLORS, PYVIS_BG, PYVIS_FONT_COLOR, ARENA
inject_arena_css()

st.title("Context Graph for Executive Communication Intelligence")
st.caption("A Knowledge Graph Approach to Shareholder Letter Analysis  |  DBA Capstone — GGU")

# ── Demo query definitions ─────────────────────────────────────────────
DEMO_QUERIES = {
    1: ("Cross-Cultural Comparison",
        "How did Buffett frame uncertainty differently than Salil Parekh during the same period?"),
    2: ("Temporal Evolution",
        "How did Buffett's narrative about market conditions evolve from 2021 to 2023?"),
    3: ("Theme Parallels",
        "What common themes appeared in both companies' letters when addressing similar economic conditions?"),
    4: ("Context → Outcome",
        "When both CEOs addressed cost or margin pressures, how did the market respond?"),
    5: ("Communication Patterns",
        "What communication patterns correlate with positive market response across both companies?"),
}


# ── Load cached results ────────────────────────────────────────────────
@st.cache_data
def load_cached_result(query_num: int) -> dict | None:
    path = os.path.join(COMPARISONS_DIR, f"query_{query_num}_results.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


# ── Connect to Neo4j (lazy) ────────────────────────────────────────────
@st.cache_resource
def get_neo4j_driver():
    uri = _get_secret("NEO4J_URI")
    password = _get_secret("NEO4J_PASSWORD")
    if not uri or not password:
        return None
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(_get_secret("NEO4J_USERNAME", "neo4j"), password))
        driver.verify_connectivity()
        return driver
    except Exception:
        return None


@st.cache_resource
def get_chromadb_collection():
    try:
        from src.rag.baseline import get_collection
        return get_collection()
    except Exception:
        return None


# ── Run live query ─────────────────────────────────────────────────────
def run_live_query(query_text: str) -> dict:
    from src.query_engine.intent import classify
    from src.query_engine.retriever import retrieve_both
    from src.query_engine.synthesizer import (
        synthesize_graph_response, synthesize_rag_response, synthesize_comparison
    )

    driver = get_neo4j_driver()
    collection = get_chromadb_collection()
    intent = classify(query_text)
    retrieval = retrieve_both(driver, collection, query_text, intent)

    graph_resp = synthesize_graph_response(retrieval["graph_results"], query_text)
    rag_resp = synthesize_rag_response(retrieval["rag_results"], query_text)
    comparison = synthesize_comparison(query_text, graph_resp, rag_resp)

    return {
        "query_text": query_text,
        "intent": intent,
        "graph_response": graph_resp,
        "rag_response": rag_resp,
        "comparison": comparison["comparison"],
    }


# ── Display side-by-side comparison ────────────────────────────────────
def display_comparison(result: dict):
    st.subheader("Side-by-Side Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Knowledge Graph Response")
        st.markdown("*Rich context: market data, themes, cross-company relationships, temporal patterns*")
        st.markdown(result.get("graph_response", "No graph response available."))

    with col2:
        st.markdown("### Baseline RAG Response")
        st.markdown("*Simple: raw text search only, no graph context*")
        st.markdown(result.get("rag_response", "No RAG response available."))

    # Comparison analysis
    st.divider()
    st.subheader("What the Graph Adds")
    st.markdown(result.get("comparison", "No comparison available."))


# ── Graph visualization ────────────────────────────────────────────────
def show_graph_visualization():
    driver = get_neo4j_driver()
    if not driver:
        st.info("Neo4j not connected — graph visualization unavailable.")
        return

    try:
        from pyvis.network import Network
        import tempfile

        net = Network(height="500px", width="100%", bgcolor=PYVIS_BG,
                      font_color=PYVIS_FONT_COLOR, directed=True)

        # Fetch graph structure
        with driver.session() as session:
            result = session.run("""
                MATCH (c:Company)-[:PUBLISHED]->(l:Letter)-[:ADDRESSES_THEME]->(t:Theme)
                RETURN c.name AS company, l.year AS year, l.letter_id AS lid,
                       t.label AS theme, t.theme_id AS tid, t.sentiment_polarity AS sentiment
                LIMIT 100
            """)

            for record in result:
                company = record["company"]
                lid = record["lid"]
                tid = record["tid"]
                year = record["year"]
                theme = record["theme"]

                color = COMPANY_COLORS.get(company, ARENA["warm_gray"])
                net.add_node(company, label=company, color=color, size=30, shape="diamond")
                net.add_node(lid, label=f"{company[:3]} {year}", color=color, size=20)
                sentiment = record["sentiment"] or "neutral"
                net.add_node(tid, label=theme[:25],
                             color=SENTIMENT_COLORS.get(sentiment, ARENA["warm_gray"]),
                             size=15)
                net.add_edge(company, lid, label="PUBLISHED")
                net.add_edge(lid, tid, label="THEME")

            # Add PARALLELS edges
            result2 = session.run("""
                MATCH (t1:Theme)-[p:PARALLELS]->(t2:Theme)
                RETURN t1.theme_id AS from_id, t2.theme_id AS to_id,
                       p.similarity_score AS score
            """)
            for record in result2:
                net.add_edge(record["from_id"], record["to_id"],
                             label=f"PARALLEL ({record['score']:.1f})",
                             color=EDGE_COLORS["PARALLELS"], dashes=True)

        # Render
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            net.save_graph(f.name)
            with open(f.name) as html:
                st.components.v1.html(html.read(), height=520, scrolling=True)
            os.unlink(f.name)

    except Exception as e:
        st.warning(f"Graph visualization error: {e}")


# ── Main app layout ───────────────────────────────────────────────────
# Sidebar: system status
with st.sidebar:
    st.header("System Status")
    driver = get_neo4j_driver()
    collection = get_chromadb_collection()

    st.markdown(f"- Neo4j: {'Connected' if driver else 'Not connected'}")
    st.markdown(f"- ChromaDB: {collection.count() if collection else 0} chunks")

    cached_count = sum(1 for i in range(1, 6) if load_cached_result(i))
    st.markdown(f"- Cached results: {cached_count}/5 queries")

    st.divider()
    st.header("About")
    st.markdown("""
    **Thesis:** Contextual knowledge graphs outperform flat RAG for extracting
    executive communication intelligence from shareholder letters.

    **Data:** 6 letters (Berkshire Hathaway + Infosys, 2021-2023)

    **Approach:** Side-by-side comparison of Knowledge Graph vs baseline RAG
    on identical queries.
    """)

# Pre-built demo queries
st.subheader("Pre-Built Demo Queries")
cols = st.columns(5)
selected_demo = None

for i, (num, (label, _)) in enumerate(DEMO_QUERIES.items()):
    with cols[i]:
        if st.button(label, key=f"demo_{num}", use_container_width=True):
            selected_demo = num

# Free-text input
st.divider()
free_text = st.text_input("Or ask your own question:",
                          placeholder="e.g., How did both CEOs discuss digital transformation?")

# View toggle
view = st.radio("View:", ["Side-by-Side", "Pipeline View", "Graph Only", "RAG Only", "Graph Visualization"],
                horizontal=True)

st.divider()

# ── Execute query ──────────────────────────────────────────────────────
result = None

if selected_demo:
    # Try cached first
    result = load_cached_result(selected_demo)
    if not result:
        with st.spinner(f"Running query {selected_demo}..."):
            query_text = DEMO_QUERIES[selected_demo][1]
            result = run_live_query(query_text)
    st.info(f"**Query {selected_demo}:** {DEMO_QUERIES[selected_demo][1]}")

elif free_text:
    with st.spinner("Processing query..."):
        result = run_live_query(free_text)

# ── Display results ───────────────────────────────────────────────────
if result:
    if view == "Side-by-Side":
        display_comparison(result)
    elif view == "Pipeline View":
        from src.demo.pipeline_view import render_pipeline
        render_pipeline(result, selected_demo)
    elif view == "Graph Only":
        st.subheader("Knowledge Graph Response")
        st.markdown(result.get("graph_response", "No graph response."))
    elif view == "RAG Only":
        st.subheader("Baseline RAG Response")
        st.markdown(result.get("rag_response", "No RAG response."))
    elif view == "Graph Visualization":
        show_graph_visualization()
elif view == "Graph Visualization":
    show_graph_visualization()
else:
    st.info("Select a demo query above or type your own question to get started.")
