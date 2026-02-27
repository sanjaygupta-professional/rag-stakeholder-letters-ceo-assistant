"""Intent classification — maps user queries to structured intents.

For the 5 demo queries: hardcoded pattern matching (reliable).
For free-text: LLM-based classification (flexible).
"""

import logging
import re

logger = logging.getLogger(__name__)

# Demo query texts (canonical forms)
DEMO_QUERIES = {
    1: "How did Buffett frame uncertainty differently than Salil Parekh during the same period?",
    2: "How did Buffett's narrative about market conditions evolve from 2021 to 2023?",
    3: "What common themes appeared in both companies' letters when addressing similar economic conditions?",
    4: "When both CEOs addressed cost or margin pressures, how did the market respond?",
    5: "What communication patterns correlate with positive market response across both companies?",
}

# Pattern-based intent detection for known demo queries
_PATTERNS = [
    (1, r"(?i)(buffett|warren).*(parekh|salil|infosys).*(uncertainty|differently|frame|compare)"),
    (1, r"(?i)(cross.?cultural|compare.*ceo|different.*frame)"),
    (2, r"(?i)(buffett|berkshire).*(evolv|narrative|chang).*(2021|2022|2023|over time|year)"),
    (2, r"(?i)(temporal|evolution|over.*years|narrative.*shift)"),
    (3, r"(?i)(common.*theme|parallel|both.*compan|similar.*theme|shared.*theme)"),
    (3, r"(?i)(same.*economic|similar.*condition|shared.*macro)"),
    (4, r"(?i)(cost|margin|pressur|efficien).*(market.*respond|stock.*react|market.*react)"),
    (4, r"(?i)(market.*respond|outcome).*(cost|margin|pressur)"),
    (5, r"(?i)(pattern|communicat).*(positive.*market|market.*positive|correlat)"),
    (5, r"(?i)(what.*pattern|positive.*respon|successful.*communicat)"),
]


def classify_demo_query(query: str) -> int | None:
    """Check if query matches a known demo pattern. Returns query number (1-5) or None."""
    # Exact match check
    for num, demo_text in DEMO_QUERIES.items():
        if query.strip().lower() == demo_text.lower():
            return num

    # Pattern match
    for num, pattern in _PATTERNS:
        if re.search(pattern, query):
            logger.info("Pattern-matched to demo query %d", num)
            return num

    return None


def classify_free_text(query: str) -> dict:
    """Classify a free-text query using the LLM. Returns structured intent."""
    from src.llm import call_llm_json

    prompt = f"""Classify this question about executive communication / shareholder letters.

QUESTION: {query}

Return a JSON object with:
- "query_type": one of "cross_cultural_comparison", "temporal_evolution", "theme_parallel", "context_outcome", "communication_pattern", "general"
- "companies": list of company names mentioned (from: "Berkshire Hathaway", "Infosys", or both)
- "years": list of years mentioned (from: 2021, 2022, 2023), or empty for all years
- "themes": list of theme keywords the query is about (e.g., "uncertainty", "cost", "digital")
- "comparison_requested": true if the user wants a graph-vs-RAG comparison

Return ONLY valid JSON."""

    try:
        return call_llm_json(prompt, temperature=0.0)
    except Exception as e:
        logger.warning("Intent classification failed: %s", e)
        return {
            "query_type": "general",
            "companies": ["Berkshire Hathaway", "Infosys"],
            "years": [],
            "themes": [],
            "comparison_requested": True,
        }


def classify(query: str) -> dict:
    """Full intent classification — demo pattern match first, then LLM fallback."""
    demo_num = classify_demo_query(query)
    if demo_num is not None:
        return {
            "demo_query_number": demo_num,
            "query_type": ["cross_cultural_comparison", "temporal_evolution",
                           "theme_parallel", "context_outcome",
                           "communication_pattern"][demo_num - 1],
            "original_query": query,
            "is_demo_query": True,
        }

    intent = classify_free_text(query)
    intent["original_query"] = query
    intent["is_demo_query"] = False
    return intent
