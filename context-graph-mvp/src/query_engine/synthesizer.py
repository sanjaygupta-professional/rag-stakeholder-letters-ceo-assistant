"""Synthesize responses from graph and RAG results using the LLM."""

import json
import logging

from src.llm import call_llm

logger = logging.getLogger(__name__)


def synthesize_graph_response(graph_results: list[dict], query: str) -> str:
    """Synthesize a rich, context-aware response from graph traversal results."""
    if not graph_results:
        return "No relevant data found in the knowledge graph for this query."

    context = json.dumps(graph_results, indent=2, default=str)[:8000]

    prompt = f"""You are an expert analyst synthesizing insights from a knowledge graph about executive communication.

QUERY: {query}

GRAPH DATA (includes themes, market context, market response, cross-company parallels):
{context}

Provide a rich analytical response that:
1. Directly answers the question with specific evidence from the data
2. References specific themes, quotes, and market data
3. Highlights cross-cultural differences between US (Berkshire/Buffett) and India (Infosys/Parekh)
4. Notes temporal patterns where relevant
5. Connects communication framing to market response where data supports it

Be specific and cite data points. This is for an academic presentation on executive communication intelligence."""

    system = ("You are an expert in executive communication analysis, corporate governance, "
              "and cross-cultural business comparison. Provide analytical, evidence-based insights.")
    return call_llm(prompt, system=system, temperature=0.3)


def synthesize_rag_response(rag_chunks: list[dict], query: str) -> str:
    """Synthesize a deliberately simple response from raw text chunks only."""
    if not rag_chunks:
        return "No relevant text chunks found for this query."

    chunks_text = "\n\n---\n\n".join(
        f"[{c['metadata']['company']} {c['metadata']['year']}]\n{c['text']}"
        for c in rag_chunks
    )[:6000]

    prompt = f"""Based ONLY on the following text excerpts from shareholder letters, answer this question:

QUESTION: {query}

TEXT EXCERPTS:
{chunks_text}

Answer based strictly on what's in the text above. Do not add external knowledge about market data, analyst sentiment, or cross-company comparisons unless it's explicitly stated in the excerpts."""

    system = "You are a helpful assistant. Answer based only on the provided text excerpts."
    return call_llm(prompt, system=system, temperature=0.3)


def synthesize_comparison(query: str, graph_response: str, rag_response: str) -> dict:
    """Generate a comparison summary highlighting what graph adds over RAG."""
    prompt = f"""Compare these two responses to the same question. One comes from a Knowledge Graph with rich context (market data, themes, cross-company relationships), the other from a simple RAG system (raw text search only).

QUESTION: {query}

KNOWLEDGE GRAPH RESPONSE:
{graph_response[:3000]}

BASELINE RAG RESPONSE:
{rag_response[:3000]}

Provide a brief comparison (3-5 bullet points) highlighting:
1. What specific insights the graph response provides that RAG misses
2. What types of context (market data, cross-cultural, temporal) the graph leverages
3. Whether the graph response is more actionable for an executive audience

Return as plain text with bullet points."""

    system = "You are evaluating retrieval system quality for academic research."
    comparison_text = call_llm(prompt, system=system, temperature=0.2)

    return {
        "query": query,
        "graph_response": graph_response,
        "rag_response": rag_response,
        "comparison": comparison_text,
    }
