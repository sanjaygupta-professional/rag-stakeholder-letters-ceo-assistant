"""Pipeline View — animated walkthrough of the query processing pipeline.

Shows the audience exactly what happens under the hood:
intent classification, graph traversal vs vector search, LLM synthesis.
Uses cached results — no live API calls during the demo.
"""

import json
import time

import streamlit as st
import streamlit.components.v1 as components


# ── Helper: get the regex pattern that matched a demo query ───────────
def _get_pattern_for_demo(query_num: int) -> str | None:
    """Return the first regex pattern from intent.py that maps to this demo query."""
    from src.query_engine.intent import _PATTERNS
    for num, pattern in _PATTERNS:
        if num == query_num:
            return pattern
    return None


# ── Helper: get Cypher query text for a demo query ───────────────────
def _get_cypher_for_query(query_num: int) -> tuple[str, dict]:
    """Return (cypher_text, params) for a demo query number."""
    from src.graph.queries import DEMO_QUERIES as GQ
    q = GQ.get(query_num, GQ[1])
    return q["cypher"].strip(), q["params"]


# ── Helper: describe the graph traversal path ────────────────────────
_TRAVERSAL_DESCRIPTIONS = {
    1: "Company --> Letter (same year, both companies) --> Theme, MarketContext, MarketResponse + PARALLELS cross-links",
    2: "Company --> Letter (ordered by year) --> Theme --> EVOLVED_TO + MarketContext, MarketResponse",
    3: "Theme -[PARALLELS]-> Theme + backing Letters --> MarketContext -[SHAPED_BY]-> MacroCondition",
    4: "Letter --> Theme (filtered: cost/margin/efficiency) + Company, MarketContext, MarketResponse",
    5: "Letter -[TRIGGERED]-> MarketResponse (filtered: positive 7d) + Company, Theme, MarketContext",
}


def _describe_traversal(query_num: int) -> str:
    return _TRAVERSAL_DESCRIPTIONS.get(query_num, "Company --> Letter --> Theme + context nodes")


# ── Helper: safe truncation for JSON display ─────────────────────────
def _truncate_json(obj, max_chars: int = 1200) -> str:
    text = json.dumps(obj, indent=2, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n  ... (truncated)"


# ── Query type labels ────────────────────────────────────────────────
_QUERY_TYPE_LABELS = {
    "cross_cultural_comparison": "Cross-Cultural Comparison",
    "temporal_evolution": "Temporal Evolution",
    "theme_parallel": "Theme Parallel Detection",
    "context_outcome": "Context-to-Outcome Analysis",
    "communication_pattern": "Communication Pattern Mining",
    "general": "General Query",
}


# ── Mermaid architecture diagram ─────────────────────────────────────
_MERMAID_HTML = """<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({startOnLoad:true, theme:'base',
  themeVariables:{fontSize:'15px', fontFamily:'Inter, sans-serif',
    primaryColor:'#DDEFEF', lineColor:'#898584'}});
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    const svg = document.querySelector('.mermaid svg');
    if (svg) { svg.style.width = '100%'; svg.style.maxWidth = '100%'; }
  }, 200);
});
</script>
<style>
  body{margin:0;padding:8px 0;background:#F7F6F5;overflow:hidden;}
  .mermaid{text-align:center;}
  .mermaid svg{width:100% !important;max-width:100% !important;height:auto !important;}
</style>
</head><body>
<pre class="mermaid">
%%{init:{'flowchart':{'nodeSpacing':25,'rankSpacing':60,'useMaxWidth':true}}}%%
graph LR
    Q["Query"] --> IC["Intent\nClassifier"]
    IC -->|"Cypher"| KG["Knowledge Graph\n(Neo4j)"]
    IC -->|"Embed"| RAG["Vector Search\n(ChromaDB)"]
    KG --> S1["LLM Synthesis\n(Graph)"]
    RAG --> S2["LLM Synthesis\n(RAG)"]
    S1 --> CMP["Compare"]
    S2 --> CMP
    CMP --> OUT["Results"]

    style Q fill:#DDEFEF,stroke:#487265,color:#292C33,stroke-width:1px
    style IC fill:#F3F1EF,stroke:#BC976A,color:#292C33,stroke-width:1px
    style KG fill:#DDEFEF,stroke:#487265,color:#292C33,stroke-width:1px
    style RAG fill:#F3F1EF,stroke:#BC976A,color:#292C33,stroke-width:1px
    style S1 fill:#DDEFEF,stroke:#487265,color:#292C33,stroke-width:1px
    style S2 fill:#F3F1EF,stroke:#BC976A,color:#292C33,stroke-width:1px
    style CMP fill:#ffffff,stroke:#D9D9D9,color:#292C33,stroke-width:1px
    style OUT fill:#DDEFEF,stroke:#487265,color:#292C33,stroke-width:1px
</pre>
</body></html>"""


# ── Main render function ─────────────────────────────────────────────
def render_pipeline(result: dict, demo_num: int | None):
    """Render the animated pipeline view for a query result.

    Args:
        result: Cached query result dict (from query_N_results.json).
        demo_num: Demo query number (1-5) or None for free-text.
    """
    st.subheader("Pipeline View: How the System Processes Your Query")
    components.html(_MERMAID_HTML, height=300)

    intent = result.get("intent", {})
    query_text = result.get("query_text", intent.get("original_query", ""))
    is_demo = intent.get("is_demo_query", demo_num is not None)
    query_num = intent.get("demo_query_number", demo_num)

    # ── Stage 1: User Query ──────────────────────────────────────────
    with st.status("Stage 1: Receiving query...", expanded=True) as s1:
        st.markdown(f"> **{query_text}**")
        if is_demo and query_num:
            st.caption(f"Matched demo query #{query_num}")
        s1.update(label="Stage 1: User Query", state="complete")

    # ── Stage 2: Intent Classification ───────────────────────────────
    with st.status("Stage 2: Classifying intent...", expanded=True) as s2:
        time.sleep(0.5)

        query_type = intent.get("query_type", "general")
        type_label = _QUERY_TYPE_LABELS.get(query_type, query_type)

        if is_demo and query_num:
            pattern = _get_pattern_for_demo(query_num)
            st.markdown("**Method:** Pattern matching (deterministic)")
            if pattern:
                st.code(pattern, language="regex")
            st.markdown(f"**Classified as:** `{type_label}`")
        else:
            st.markdown("**Method:** LLM-based classification (flexible)")
            st.markdown(f"**Classified as:** `{type_label}`")
            companies = intent.get("companies", [])
            if companies:
                st.markdown(f"**Companies:** {', '.join(companies)}")

        s2.update(label=f"Stage 2: Intent = {type_label}", state="complete")

    # ── Stage 3: Dual Retrieval ──────────────────────────────────────
    with st.status("Stage 3: Retrieving from both systems...", expanded=True) as s3:
        time.sleep(1.0)

        col_kg, col_rag = st.columns(2)

        with col_kg:
            st.markdown("#### Knowledge Graph (Neo4j)")
            if query_num:
                cypher_text, params = _get_cypher_for_query(query_num)
                st.markdown(f"**Traversal path:**  \n`{_describe_traversal(query_num)}`")
                with st.expander("Cypher query", expanded=False):
                    st.code(cypher_text, language="cypher")
                if params:
                    st.caption(f"Parameters: `{params}`")

                raw = result.get("graph_results_raw", [])
                st.metric("Records returned", len(raw))
                if raw:
                    with st.expander("Sample record", expanded=False):
                        st.code(_truncate_json(raw[0]), language="json")
            else:
                st.markdown("Mapped to closest demo query by type")

        with col_rag:
            st.markdown("#### Baseline RAG (ChromaDB)")
            st.markdown("**Embedding model:** `all-MiniLM-L6-v2` (384-dim)")
            st.code(
                'collection.query(\n'
                f'    query_texts=["{query_text[:60]}..."],\n'
                '    n_results=5\n'
                ')',
                language="python",
            )
            rag_raw = result.get("rag_results_raw", [])
            st.metric("Chunks retrieved", len(rag_raw) if rag_raw else 5)
            if rag_raw:
                with st.expander("Sample chunk", expanded=False):
                    sample = rag_raw[0] if rag_raw else {}
                    meta = sample.get("metadata", {})
                    st.caption(f"{meta.get('company', '?')} {meta.get('year', '?')}")
                    st.text(sample.get("text", "")[:300] + "...")

        s3.update(label="Stage 3: Dual Retrieval Complete", state="complete")

    # ── Stage 4: LLM Synthesis ───────────────────────────────────────
    with st.status("Stage 4: LLM synthesis (3 calls)...", expanded=True) as s4:
        time.sleep(0.5)

        # Call 1: Graph response
        st.markdown("**Call 1 — Graph Response**")
        st.caption(
            "System: *Expert in executive communication analysis, corporate governance, "
            "and cross-cultural business comparison.*"
        )
        graph_resp = result.get("graph_response", "")
        st.caption(f"Data payload: ~{len(json.dumps(result.get('graph_results_raw', []), default=str)):,} chars | "
                   f"Response: ~{len(graph_resp):,} chars")
        time.sleep(0.5)

        # Call 2: RAG response
        st.markdown("**Call 2 — RAG Response**")
        st.caption("System: *Helpful assistant. Answer based only on provided text excerpts.*")
        rag_resp = result.get("rag_response", "")
        st.caption(f"Response: ~{len(rag_resp):,} chars")
        time.sleep(0.5)

        # Call 3: Comparison
        st.markdown("**Call 3 — Comparison Evaluation**")
        st.caption("System: *Evaluating retrieval system quality for academic research.*")
        comparison = result.get("comparison", "")
        st.caption(f"Both responses fed in | Output: ~{len(comparison):,} chars")

        s4.update(label="Stage 4: LLM Synthesis (3 calls complete)", state="complete")

    # ── Stage 5: Results Preview ─────────────────────────────────────
    with st.status("Stage 5: Assembling results...", expanded=True) as s5:
        col_g, col_r = st.columns(2)

        with col_g:
            st.markdown("**Graph Response Preview**")
            preview = graph_resp[:500] + ("..." if len(graph_resp) > 500 else "")
            st.markdown(preview)

        with col_r:
            st.markdown("**RAG Response Preview**")
            preview = rag_resp[:500] + ("..." if len(rag_resp) > 500 else "")
            st.markdown(preview)

        st.info("Switch to **Side-by-Side** view for the full responses and comparison analysis.")
        s5.update(label="Stage 5: Results Ready", state="complete")
