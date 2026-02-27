"""Pre-built parameterized Cypher queries for the 5 demo scenarios.

No dynamic Cypher generation — reliability over flexibility for a live demo.
"""

# ── Query 1: Cross-Cultural Comparison ─────────────────────────────────
# "How did Buffett frame uncertainty differently than Salil Parekh?"
QUERY_1_CROSS_CULTURAL = """
MATCH (c1:Company {name: 'Berkshire Hathaway'})-[:PUBLISHED]->(l1:Letter)
MATCH (c2:Company {name: 'Infosys'})-[:PUBLISHED]->(l2:Letter)
WHERE l1.year = l2.year
MATCH (l1)-[:ADDRESSES_THEME]->(t1:Theme)
MATCH (l2)-[:ADDRESSES_THEME]->(t2:Theme)
MATCH (l1)-[:WRITTEN_DURING]->(mc1:MarketContext)
MATCH (l2)-[:WRITTEN_DURING]->(mc2:MarketContext)
MATCH (l1)-[:TRIGGERED]->(mr1:MarketResponse)
MATCH (l2)-[:TRIGGERED]->(mr2:MarketResponse)
OPTIONAL MATCH (t1)-[p:PARALLELS]->(t2)
RETURN l1.year AS year,
       l1.author AS brk_author, l2.author AS infy_author,
       collect(DISTINCT {label: t1.label, sentiment: t1.sentiment_polarity,
                         confidence: t1.confidence_level, quote: t1.key_quote}) AS brk_themes,
       collect(DISTINCT {label: t2.label, sentiment: t2.sentiment_polarity,
                         confidence: t2.confidence_level, quote: t2.key_quote}) AS infy_themes,
       mc1 {.pre_letter_sentiment, .key_analyst_concerns} AS brk_context,
       mc2 {.pre_letter_sentiment, .key_analyst_concerns} AS infy_context,
       mr1 {.stock_change_7d_pct, .stock_change_30d_pct, .relative_return_7d} AS brk_response,
       mr2 {.stock_change_7d_pct, .stock_change_30d_pct, .relative_return_7d} AS infy_response,
       collect(DISTINCT {score: p.similarity_score, desc: p.parallel_description,
                         cultural_diff: p.cultural_difference}) AS parallels
ORDER BY year
"""

# ── Query 2: Temporal Evolution ────────────────────────────────────────
# "How did Buffett's narrative evolve from 2021 to 2023?"
QUERY_2_TEMPORAL = """
MATCH (c:Company {name: $company})-[:PUBLISHED]->(l:Letter)
MATCH (l)-[:ADDRESSES_THEME]->(t:Theme)
MATCH (l)-[:WRITTEN_DURING]->(mc:MarketContext)
MATCH (l)-[:TRIGGERED]->(mr:MarketResponse)
OPTIONAL MATCH (t)-[e:EVOLVED_TO]->(t2:Theme)
RETURN l.year AS year,
       l.publication_date AS pub_date,
       l.word_count AS word_count,
       collect(DISTINCT {label: t.label, sentiment: t.sentiment_polarity,
                         temporal: t.temporal_orientation, confidence: t.confidence_level,
                         quote: t.key_quote}) AS themes,
       mc {.pre_letter_sentiment, .stock_price_on_date} AS context,
       mr {.stock_change_7d_pct, .stock_change_30d_pct, .relative_return_7d} AS response,
       collect(DISTINCT {to_label: t2.label, to_year: t2.year,
                         evolution: e.evolution_description, driver: e.driver}) AS evolutions
ORDER BY year
"""

# ── Query 3: Theme Parallel Detection ──────────────────────────────────
# "What common themes appeared in both companies' letters?"
QUERY_3_PARALLELS = """
MATCH (t1:Theme)-[p:PARALLELS]->(t2:Theme)
MATCH (l1:Letter)-[:ADDRESSES_THEME]->(t1)
MATCH (l2:Letter)-[:ADDRESSES_THEME]->(t2)
MATCH (l1)-[:WRITTEN_DURING]->(mc1:MarketContext)-[:SHAPED_BY]->(macro:MacroCondition)
RETURN t1.year AS year,
       t1.label AS brk_theme, t2.label AS infy_theme,
       p.similarity_score AS similarity,
       p.parallel_description AS description,
       p.cultural_difference AS cultural_diff,
       p.shared_driver AS driver,
       t1.sentiment_polarity AS brk_sentiment,
       t2.sentiment_polarity AS infy_sentiment,
       t1.confidence_level AS brk_confidence,
       t2.confidence_level AS infy_confidence,
       collect(DISTINCT macro.key_factors) AS macro_factors
ORDER BY year, similarity DESC
"""

# ── Query 4: Context-to-Outcome ────────────────────────────────────────
# "When both CEOs addressed cost/margin pressures, how did the market respond?"
QUERY_4_CONTEXT_OUTCOME = """
MATCH (l:Letter)-[:ADDRESSES_THEME]->(t:Theme)
WHERE t.label =~ '(?i).*(cost|margin|efficiency|profitab|expense|pricing).*'
   OR t.description =~ '(?i).*(cost|margin|efficiency|profitab|expense|pricing).*'
MATCH (c:Company)-[:PUBLISHED]->(l)
MATCH (l)-[:WRITTEN_DURING]->(mc:MarketContext)
MATCH (l)-[:TRIGGERED]->(mr:MarketResponse)
RETURN c.name AS company,
       l.year AS year,
       t.label AS theme,
       t.description AS theme_desc,
       t.sentiment_polarity AS sentiment,
       t.confidence_level AS confidence,
       t.key_quote AS quote,
       mc.pre_letter_sentiment AS pre_sentiment,
       mr.stock_change_7d_pct AS stock_7d,
       mr.stock_change_30d_pct AS stock_30d,
       mr.relative_return_7d AS rel_return_7d,
       mr.relative_return_30d AS rel_return_30d,
       mr.sentiment_shift AS sentiment_shift
ORDER BY company, year
"""

# ── Query 5: Communication Patterns with Positive Market Response ──────
# "What communication patterns correlate with positive market response?"
QUERY_5_PATTERNS = """
MATCH (l:Letter)-[:TRIGGERED]->(mr:MarketResponse)
WHERE mr.stock_change_7d_pct > 0
MATCH (c:Company)-[:PUBLISHED]->(l)
MATCH (l)-[:ADDRESSES_THEME]->(t:Theme)
MATCH (l)-[:WRITTEN_DURING]->(mc:MarketContext)
RETURN c.name AS company,
       l.year AS year,
       l.author AS author,
       mr.stock_change_7d_pct AS stock_7d,
       mr.relative_return_7d AS rel_return_7d,
       mc.pre_letter_sentiment AS pre_sentiment,
       collect({label: t.label, sentiment: t.sentiment_polarity,
                temporal: t.temporal_orientation, confidence: t.confidence_level,
                ccr: t.cross_cultural_relevance}) AS themes
ORDER BY mr.stock_change_7d_pct DESC
"""

# ── Graph Visualization Query ──────────────────────────────────────────
# Returns a subgraph for pyvis rendering
QUERY_VISUALIZATION = """
MATCH (c:Company)-[:PUBLISHED]->(l:Letter)-[:ADDRESSES_THEME]->(t:Theme)
OPTIONAL MATCH (t)-[p:PARALLELS]->(t2:Theme)
OPTIONAL MATCH (t)-[e:EVOLVED_TO]->(t3:Theme)
OPTIONAL MATCH (l)-[:WRITTEN_DURING]->(mc:MarketContext)
OPTIONAL MATCH (l)-[:TRIGGERED]->(mr:MarketResponse)
RETURN c, l, t, t2, t3, mc, mr, p, e
"""

# Map demo query numbers to their Cypher + parameters
DEMO_QUERIES = {
    1: {"cypher": QUERY_1_CROSS_CULTURAL, "params": {}},
    2: {"cypher": QUERY_2_TEMPORAL, "params": {"company": "Berkshire Hathaway"}},
    3: {"cypher": QUERY_3_PARALLELS, "params": {}},
    4: {"cypher": QUERY_4_CONTEXT_OUTCOME, "params": {}},
    5: {"cypher": QUERY_5_PATTERNS, "params": {}},
}


def run_demo_query(driver, query_number: int) -> list[dict]:
    """Execute a pre-built demo query and return results as list of dicts."""
    if query_number not in DEMO_QUERIES:
        raise ValueError(f"Unknown demo query: {query_number}. Valid: 1-5")

    q = DEMO_QUERIES[query_number]
    with driver.session() as session:
        result = session.run(q["cypher"], **q["params"])
        return [dict(record) for record in result]
