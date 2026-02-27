# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Context Graph for Executive Communication Intelligence** — a DBA capstone project (Golden Gate University, Generative AI specialization). Proves that contextual knowledge graphs outperform flat RAG for extracting executive communication intelligence from shareholder letters.

**Deadline: ~March 25, 2026.** Everything serves a live 30-minute presentation with working demo.

## Architecture

Hybrid system comparing two retrieval approaches side-by-side:

1. **Knowledge Graph** (Neo4j) — Letters embedded in "Context Envelopes" (Before/During/After market data, themes, macro conditions) with cross-company relationships
2. **Baseline RAG** (ChromaDB) — Deliberately simple vector search over raw letter text (no context enrichment)
3. **Query Engine** — Intent classification → parallel Neo4j + ChromaDB retrieval → Claude API synthesis
4. **Demo** — Streamlit app with pre-built query buttons, side-by-side comparison view, graph visualization

### Data Scope

6 shareholder letters total:
- **Berkshire Hathaway (BRK-B):** CY2021, CY2022, CY2023 letters (published Feb each year)
- **Infosys (INFY):** FY2021, FY2022, FY2023 annual report CEO letters (Salil Parekh)

Each letter wrapped in a Context Envelope: market conditions 30d before, the letter itself with extracted themes, and market response 7d/30d after.

### Neo4j Graph Schema

Nodes: `Company`, `Letter`, `Theme`, `MarketContext`, `MarketResponse`, `MacroCondition`

Key relationships:
- `(Company)-[:PUBLISHED]->(Letter)`
- `(Letter)-[:WRITTEN_DURING]->(MarketContext)`, `[:ADDRESSES_THEME]->(Theme)`, `[:TRIGGERED]->(MarketResponse)`
- `(Theme)-[:PARALLELS]->(Theme)` (cross-company, similarity_score >= 0.5)
- `(Theme)-[:EVOLVED_TO]->(Theme)` (temporal within same company)
- `(MacroCondition)-[:AFFECTED]->(Company)`, `(MarketContext)-[:SHAPED_BY]->(MacroCondition)`

### Planned Directory Structure

```
context-graph-mvp/
├── data/raw/letters/, data/raw/market/
├── data/processed/letters/, data/processed/context_packages/
├── data/themes/
├── src/data_collection/    # Download letters, fetch market/analyst data
├── src/graph/              # Neo4j schema creation and ingest
├── src/analysis/           # Theme extraction, parallel detection, sentiment
├── src/rag/                # ChromaDB baseline
├── src/query_engine/       # Hybrid retriever and synthesis
├── src/demo/               # Streamlit application
├── scripts/01-08_*.py      # Numbered execution scripts
└── presentation/           # Diagrams, screenshots, visualizations
```

## Key Dependencies

neo4j, langchain, chromadb, anthropic, yfinance, pdfplumber, streamlit, sentence-transformers (all-MiniLM-L6-v2), python-dotenv, pyvis, pandas, beautifulsoup4

## Environment Variables (.env)

```
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<password>
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

## Execution Sequence

Scripts run in order with human checkpoints:

1. `01_collect_data.py` — Download PDFs, fetch yfinance market data
2. `02_process_letters.py` — Extract text from PDFs via pdfplumber
3. `03_build_context_packages.py` — Assemble Context Envelope JSONs
4. **CHECKPOINT 1: SG reviews data quality**
5. `04_extract_themes.py` — Claude API theme extraction (5-7 themes per letter)
6. `05_setup_neo4j.py` — Create schema constraints and load all nodes/relationships
7. `06_build_baseline_rag.py` — ChromaDB with 500-token chunks, MiniLM embeddings
8. **CHECKPOINT 2: SG reviews graph and themes**
9. `07_run_comparisons.py` — Execute 5 demo queries, save results
10. `08_launch_demo.py` — Launch Streamlit app
11. **CHECKPOINT 3: SG reviews demo**

## Decision Guidelines

When making implementation choices:
1. Fewer dependencies wins
2. Easier to debug wins
3. Fail gracefully (return message, don't crash)
4. Pre-compute over real-time for demo reliability
5. If it won't appear in the demo, skip it
6. Cross-cultural comparison (US vs India) is non-negotiable in every feature

## Fallback Strategies

| If This Fails | Do This Instead |
|---|---|
| Neo4j Aura | Docker local neo4j:5-community |
| yfinance API | Hard-code data from Yahoo Finance |
| Claude API rate limits | Pre-compute themes, cache as JSON |
| LangChain GraphCypherQA | Pre-built parameterized Cypher queries |
| Streamlit visualization | Static Mermaid diagrams/screenshots |

## Critical Demo Queries (Must Work Flawlessly)

1. "How did Buffett frame uncertainty differently than Salil Parekh during the same period?"
2. "How did Buffett's narrative about market conditions evolve from 2021 to 2023?"
3. "What common themes appeared in both companies' letters when addressing similar economic conditions?"
4. "When both CEOs addressed cost or margin pressures, how did the market respond?"
5. "What communication patterns correlate with positive market response across both companies?"

## Specification Files

- `PROJECT_SPEC.md` — Single source of truth (941 lines). Contains schema definitions, prompt templates, query templates, Context Envelope JSON structure.
- `CLAUDE_CODE_KICKOFF.md` — Implementation checklist and decision guidelines.
- `images/` — Pre-built architecture diagrams (PNG + SVG) for presentation use.
