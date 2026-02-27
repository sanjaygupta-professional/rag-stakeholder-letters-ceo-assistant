# CLAUDE CODE: Day 1 Kickoff Instructions

## Read First
Before doing ANYTHING, read `PROJECT_SPEC.md` in full. That is your bible for this project.

## Your Role
You are the implementation engine for this project. SG (the project owner) will review your work at defined checkpoints. Between checkpoints, you have full autonomy to make implementation decisions, BUT you should prefer simplicity and reliability over elegance.

## Immediate Setup Tasks (Do These First)

### 1. Create Project Scaffold
```bash
mkdir -p context-graph-mvp/{data/{raw/{letters,market},processed/{letters,context_packages},themes},src/{data_collection,graph,analysis,rag,query_engine,demo},scripts,presentation/{architecture_diagrams,demo_screenshots,graph_visualizations}}
cd context-graph-mvp
```

### 2. Create requirements.txt
```
neo4j>=5.0.0
langchain>=0.1.0
langchain-community>=0.0.1
chromadb>=0.4.0
anthropic>=0.30.0
yfinance>=0.2.0
pdfplumber>=0.10.0
streamlit>=1.30.0
sentence-transformers>=2.0.0
python-dotenv>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
numpy>=1.24.0
pyvis>=0.3.0
```

### 3. Create .env template
```
NEO4J_URI=
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=
ANTHROPIC_API_KEY=
```

**STOP HERE and ask SG:**
- "Do you want Neo4j Aura (cloud) or Docker (local)? I recommend Aura Free Tier."
- "Please provide your Anthropic API key (or confirm it's in your environment)."
- "Please provide Neo4j credentials once the instance is created."

### 4. Once Credentials Are Set, Execute Scripts In Order

The execution sequence is:
1. `scripts/01_collect_data.py` — Downloads letters, fetches market data
2. `scripts/02_process_letters.py` — Extracts text from PDFs
3. `scripts/03_build_context_packages.py` — Assembles context JSON files
4. **>>> CHECKPOINT 1: SG reviews data quality <<<**
5. `scripts/04_extract_themes.py` — Claude API theme extraction
6. `scripts/05_setup_neo4j.py` — Creates schema and loads all data
7. `scripts/06_build_baseline_rag.py` — Sets up ChromaDB
8. **>>> CHECKPOINT 2: SG reviews graph and themes <<<**
9. `scripts/07_run_comparisons.py` — Executes demo queries through both systems
10. `scripts/08_launch_demo.py` — Starts Streamlit
11. **>>> CHECKPOINT 3: SG reviews demo <<<**

## Decision Guidelines

When you need to make a technical decision:
1. **Choose the approach with fewer dependencies**
2. **Choose the approach that's easier to debug**
3. **Choose the approach that fails gracefully** (returns a message instead of crashing)
4. **Pre-compute over real-time** whenever possible for demo reliability
5. **If it won't appear in the demo, skip it**

## Key Dates
- Today: February 24, 2026
- Data collection must be complete by: March 3
- Graph + themes must be ready by: March 10
- Demo must be working by: March 18
- Presentation: approximately March 25

## Critical Reminders
- The side-by-side RAG vs. Graph comparison is THE most important feature
- Cross-cultural analysis (US vs. India) is mandatory — the academic advisor requires it
- Pre-built demo query buttons are essential for a smooth live demo
- Always have a fallback (cached results, screenshots) for every live element
