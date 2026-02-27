# Context Graph for Executive Communication Intelligence
## Complete MVP Project Specification for Claude Code

**Version:** 1.0
**Date:** February 24, 2026
**Owner:** SG (Sanjay Gupta)
**Purpose:** This document is the single source of truth for Claude Code to plan and execute the full MVP build. It contains everything needed: project context, academic thesis, technical architecture, data sources, schema definitions, implementation steps, validation checkpoints, and demo requirements.

---

## 1. PROJECT CONTEXT

### 1.1 What This Is
A hybrid Knowledge Graph + RAG application that analyzes CEO/shareholder letters alongside their surrounding business context (analyst expectations, market conditions, market response) to extract actionable executive communication intelligence.

### 1.2 Why It Exists
This is SG's DBA capstone project at Golden Gate University (Doctor of Business Administration in Generative AI and Agentic AI, Module 3). The deliverable is a **live presentation and demo** — no written paper required.

### 1.3 The Academic Thesis
> "Contextual knowledge graphs outperform flat document retrieval (RAG) for extracting actionable executive communication intelligence from shareholder letters, because the relationships between business context, communication framing, and market response are fundamentally graph-structured."

**To prove this thesis, the MVP must:**
1. Build a knowledge graph with letters embedded in contextual envelopes (before-during-after)
2. Build a baseline RAG system over the same letter texts (without graph context)
3. Run identical queries through both systems
4. Demonstrate that the knowledge graph approach produces richer, more actionable insights
5. Show cross-cultural patterns between US and Indian executive communication

### 1.4 Timeline
**4 weeks total. Deadline: approximately March 25, 2026.**
- Week 1 (Feb 25 - Mar 3): Data collection + Neo4j setup
- Week 2 (Mar 4 - Mar 10): Graph population + theme extraction + baseline RAG
- Week 3 (Mar 11 - Mar 18): Query engine + Streamlit demo + comparison runs
- Week 4 (Mar 19 - Mar 25): Presentation build + rehearsal + contingency

### 1.5 Owner's Technical Profile
- Has Claude Code set up and working
- Python comfortable, API-experienced
- Conceptually familiar with graph databases, has NOT built with Neo4j before
- Will be human-in-the-loop for validation; Claude Code drives all implementation
- 25+ years enterprise IT experience; currently Enterprise Agility Coach at Accenture

---

## 2. SCOPE BOUNDARIES

### 2.1 In Scope (MVP)
- **2 companies:** Berkshire Hathaway (US) and Infosys (India)
- **3 years per company:** FY2021, FY2022, FY2023 = **6 letter-context packages total**
- **Knowledge graph** in Neo4j with full schema
- **Baseline RAG** in ChromaDB for comparison
- **Hybrid query engine** (natural language → graph traversal + vector search → Claude synthesis)
- **Streamlit demo interface** with RAG vs. Graph comparison toggle
- **5 pre-built demo queries** that showcase cross-cultural and temporal analysis
- **Presentation-ready** graph visualizations

### 2.2 Out of Scope (Future Work / Mentioned in Presentation Only)
- More than 2 companies
- Automated data pipeline (data is manually curated for MVP)
- Predictive analysis
- Letter drafting assistance
- Production deployment
- User authentication or multi-tenancy

### 2.3 Critical Note on Infosys
Infosys follows an Indian fiscal year (April to March). So:
- "FY2021" = April 2020 - March 2021 (annual report published ~mid-2021)
- "FY2022" = April 2021 - March 2022 (annual report published ~mid-2022)
- "FY2023" = April 2022 - March 2023 (annual report published ~mid-2023)

Berkshire Hathaway follows calendar year. Annual letter published in February of the following year:
- "2021 letter" = covers CY2021, published February 2022
- "2022 letter" = covers CY2022, published February 2023
- "2023 letter" = covers CY2023, published February 2024

**For cross-cultural comparison, align by calendar year of the letter's PUBLICATION, not the fiscal year it covers.** This ensures both letters are discussing similar macro conditions.

---

## 3. DATA ARCHITECTURE

### 3.1 The Context Envelope Model (Core Differentiator)
Each letter exists inside a "context envelope" with three temporal layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT ENVELOPE                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   BEFORE     │  │   DURING     │  │     AFTER        │   │
│  │              │  │              │  │                  │   │
│  │ • Analyst    │  │ • Full text  │  │ • Stock price    │   │
│  │   consensus  │──│   of letter  │──│   change (7d,    │   │
│  │ • Stock      │  │ • Extracted  │  │   30d)           │   │
│  │   trajectory │  │   themes     │  │ • Analyst        │   │
│  │ • Macro      │  │ • Sentiment  │  │   reactions      │   │
│  │   conditions │  │ • Framing    │  │ • Sentiment      │   │
│  │ • Sector     │  │   strategy   │  │   shift          │   │
│  │   headwinds  │  │ • Cultural   │  │                  │   │
│  │              │  │   patterns   │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Companies and Data Periods

#### Berkshire Hathaway (BRK.A / BRK.B)
| Letter Year | Covers FY | Published | Key Context |
|---|---|---|---|
| 2021 | CY2020 | Feb 27, 2021 | COVID recovery, stimulus, market rally |
| 2022 | CY2021 | Feb 26, 2022 | Post-COVID boom, inflation emerging, supply chain |
| 2023 | CY2022 | Feb 25, 2023 | Rate hikes, inflation peak, energy crisis, Charlie Munger tribute |

**Note:** The 2023 letter (covering CY2022) also addresses Charlie Munger's passing (Nov 28, 2023). The letter published Feb 24, 2024 covering CY2023 is technically the "2024 letter" — use the 2021, 2022, 2023 letters as defined above.

**CORRECTION / CLARIFICATION:**
- Buffett's letter published Feb 2021 covers fiscal year 2020
- Buffett's letter published Feb 2022 covers fiscal year 2021
- Buffett's letter published Feb 2023 covers fiscal year 2022
- Buffett's letter published Feb 2024 covers fiscal year 2023 (this one includes Munger tribute)

**For the MVP, use the letters published in Feb 2022, Feb 2023, and Feb 2024.** These cover FY2021, FY2022, and FY2023 respectively, giving us the richest recent period.

#### Infosys (INFY / 500209.BO)
| Letter/Report | Covers FY | Published Approx | Key Context |
|---|---|---|---|
| FY2021 Annual Report | Apr 2020 - Mar 2021 | June-July 2021 | COVID digital acceleration, attrition beginning |
| FY2022 Annual Report | Apr 2021 - Mar 2022 | June-July 2022 | Peak attrition crisis, strong growth, margin pressure |
| FY2023 Annual Report | Apr 2022 - Mar 2023 | June-July 2023 | Demand slowdown, AI narrative emerging, deal wins |

**Infosys letters to extract:**
- Chairman's Letter (Nandan Nilekani) — strategic vision, governance
- CEO's Letter (Salil Parekh) — operational strategy, market positioning
- For the MVP, focus primarily on the **CEO's letter (Salil Parekh)** for consistency with single-CEO comparison to Buffett. Chairman's letter is secondary context.

---

## 4. DATA SOURCES (Specific URLs and Methods)

### 4.1 Shareholder Letters

#### Berkshire Hathaway Letters
- **Source:** https://www.berkshirehathaway.com/letters/letters.html
- **Format:** PDF files, one per year
- **Direct URLs:**
  - 2021 letter (published Feb 2022): https://www.berkshirehathaway.com/letters/2021ltr.pdf
  - 2022 letter (published Feb 2023): https://www.berkshirehathaway.com/letters/2022ltr.pdf
  - 2023 letter (published Feb 2024): https://www.berkshirehathaway.com/letters/2023ltr.pdf
- **Extraction method:** Download PDFs, extract text using PyPDF2 or pdfplumber

#### Infosys Annual Reports
- **Source:** https://www.infosys.com/investors/reports-filings/annual-report.html
- **Format:** PDF annual reports (large documents; CEO letter is a specific section)
- **Direct URLs:**
  - FY2021: https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-21.pdf
  - FY2022: https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-22.pdf
  - FY2023: https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-23.pdf
- **Extraction method:** Download PDFs, extract CEO letter section (typically pages 8-15 of annual report). Use pdfplumber with page range extraction.
- **Alternative:** Also available on https://www.annualreports.com/Company/infosys-limited

### 4.2 Market Data (Automated via yfinance)

```python
# Install: pip install yfinance
import yfinance as yf

# Berkshire Hathaway
brk = yf.Ticker("BRK-B")  # Use BRK-B for more granular price data
brk_history = brk.history(start="2021-01-01", end="2024-06-30")

# Infosys (NSE India)
infy = yf.Ticker("INFY")  # US-listed ADR (easier to compare)
# OR for NSE: yf.Ticker("INFY.NS")
infy_history = infy.history(start="2021-01-01", end="2024-06-30")

# S&P 500 benchmark
sp500 = yf.Ticker("^GSPC")
sp500_history = sp500.history(start="2021-01-01", end="2024-06-30")

# Nifty IT Index (for Infosys benchmark)
nifty_it = yf.Ticker("^CNXIT")
nifty_it_history = nifty_it.history(start="2021-01-01", end="2024-06-30")
```

**For each letter, extract:**
- Stock price 30 days BEFORE publication date
- Stock price on publication date
- Stock price 7 days AFTER publication date
- Stock price 30 days AFTER publication date
- Calculate: 7-day return, 30-day return, relative to benchmark

### 4.3 Analyst Data (Web-Scraped / Manual)

#### Berkshire Hathaway
- **Seeking Alpha:** Search for BRK.A/BRK.B articles within 2 weeks before each letter publication
  - URL pattern: https://seekingalpha.com/symbol/BRK.B/analysis
  - Look for: analyst estimates, earnings expectations, sentiment
- **Yahoo Finance:** Analyst recommendations and estimates
  - `brk.recommendations` via yfinance
  - `brk.analyst_price_targets` via yfinance

#### Infosys
- **Seeking Alpha:** https://seekingalpha.com/symbol/INFY/analysis
- **Moneycontrol:** https://www.moneycontrol.com/india/stockpricequote/computers-software/infosys/IT (analyst ratings section)
- **Trendlyne:** https://trendlyne.com/equity/953/INFY/infosys-limited/ (analyst estimates)
- **Yahoo Finance India:** `yf.Ticker("INFY.NS").recommendations`

#### What to Capture Per Letter
For each letter period, create a structured analyst context with:
1. **Consensus EPS estimate** (pre-results) — from yfinance or Seeking Alpha
2. **Number of Buy/Hold/Sell recommendations** — from yfinance
3. **Key analyst themes/concerns** (2-3 bullet points, manually extracted from 1-2 articles)
4. **Post-letter analyst reaction summary** (2-3 bullet points from articles published within 1 week after)

### 4.4 Macroeconomic Context (Pre-Curated Reference Data)

This data is well-known and can be hard-coded as reference context. Claude Code should populate this based on known economic conditions:

| Year | US Context | India Context | Global Context |
|---|---|---|---|
| 2021 (covers 2020) | COVID stimulus, near-zero rates, market recovery | COVID second wave, digital acceleration | Vaccine rollout, supply chain disruption begins |
| 2022 (covers 2021) | Inflation emerging, rate hike signals, crypto boom | IT boom, attrition crisis, strong demand | Supply chain crisis peaks, chip shortage |
| 2023 (covers 2022) | Aggressive rate hikes, inflation 9%+, energy crisis | Rupee depreciation, demand moderation | Ukraine war, energy shock, recession fears |

**For each letter, capture:**
- US Federal Funds Rate at time of letter
- India RBI Repo Rate at time of letter
- Key macro headline (1-2 sentences)
- Sector-specific headwind (1-2 sentences)

---

## 5. KNOWLEDGE GRAPH SCHEMA (Neo4j)

### 5.1 Node Types

```cypher
// Company
CREATE CONSTRAINT company_name IF NOT EXISTS
FOR (c:Company) REQUIRE c.name IS UNIQUE;

// Node properties:
// Company: name, sector, geography, market_cap_category, stock_ticker, index_benchmark

// Letter
// Properties: company_name, year, fiscal_year_covered, publication_date, author,
//             full_text, letter_type (annual/quarterly), word_count,
//             overall_sentiment_score (-1 to 1), forward_looking_ratio (0 to 1)

// Theme
// Properties: label, description, sentiment_polarity (positive/negative/mixed),
//             temporal_orientation (backward_looking/forward_looking/both),
//             confidence_level (definitive/hedged/aspirational),
//             key_quote (short excerpt, <50 words)

// MarketContext (BEFORE the letter)
// Properties: company_name, year, stock_price_30d_before, stock_price_on_date,
//             index_benchmark_30d_before, index_benchmark_on_date,
//             analyst_consensus_eps, analyst_buy_count, analyst_hold_count,
//             analyst_sell_count, pre_letter_sentiment (bullish/neutral/bearish),
//             key_analyst_concerns (text, 2-3 sentences)

// MarketResponse (AFTER the letter)
// Properties: company_name, year, stock_change_7d_pct, stock_change_30d_pct,
//             benchmark_change_7d_pct, benchmark_change_30d_pct,
//             relative_return_7d, relative_return_30d,
//             post_letter_analyst_reaction (text, 2-3 sentences),
//             sentiment_shift (improved/unchanged/deteriorated)

// MacroCondition (shared context that affects both companies)
// Properties: year, region (US/India/Global), interest_rate,
//             key_factors (text array), industry_headwinds (text),
//             market_sentiment (risk_on/cautious/risk_off)
```

### 5.2 Relationship Types

```cypher
// Core relationships
(Company)-[:PUBLISHED]->(Letter)
(Letter)-[:WRITTEN_DURING]->(MarketContext)
(Letter)-[:ADDRESSES_THEME]->(Theme)
(Letter)-[:TRIGGERED]->(MarketResponse)
(MarketContext)-[:SHAPED_BY]->(MacroCondition)

// Cross-company relationships (KEY FOR THESIS)
(Theme)-[:PARALLELS {similarity_score: float, same_year: boolean}]->(Theme)
// Links themes across companies in the same year
// e.g., Buffett's "inflation framing" PARALLELS Parekh's "margin pressure framing" in 2022

// Temporal relationships (KEY FOR PATTERN ANALYSIS)
(Theme)-[:EVOLVED_TO {years_gap: int}]->(Theme)
// Links same company's theme across years
// e.g., Buffett's "COVID uncertainty" 2021 EVOLVED_TO "inflation uncertainty" 2022

// Contextual influence
(MacroCondition)-[:AFFECTED]->(Company)
// Shows how the same macro condition influenced different companies differently
```

### 5.3 Schema Visual Summary

```
                    ┌─────────────┐
                    │   Company   │
                    └──────┬──────┘
                           │ PUBLISHED
                           ▼
┌──────────────┐    ┌─────────────┐    ┌────────────────┐
│ MarketContext │◄───│   Letter    │───►│ MarketResponse │
│   (BEFORE)   │    └──────┬──────┘    │    (AFTER)     │
└──────┬───────┘           │           └────────────────┘
       │                   │ ADDRESSES_THEME
       │ SHAPED_BY         ▼
       │            ┌─────────────┐
       │            │    Theme    │◄──── PARALLELS (cross-company)
       │            └──────┬──────┘      EVOLVED_TO (temporal)
       ▼                   │
┌──────────────┐           │
│MacroCondition│───────────┘
│  (US/India/  │    AFFECTED
│   Global)    │
└──────────────┘
```

---

## 6. BASELINE RAG SYSTEM (For Comparison)

### 6.1 Purpose
The baseline RAG exists ONLY to demonstrate what you lose without graph context. It should be deliberately simple.

### 6.2 Architecture
- **Vector Store:** ChromaDB (lightweight, Python-native, easy to set up)
- **Embeddings:** OpenAI `text-embedding-3-small` or Anthropic embeddings via VoyageAI
  - Fallback: `sentence-transformers/all-MiniLM-L6-v2` (free, local, good enough for demo)
- **Chunking:** Split each letter into ~500 token chunks with 100 token overlap
- **Query:** Simple semantic similarity search, top-5 chunks, feed to Claude for synthesis

### 6.3 What It Should NOT Have
- No graph context
- No market data
- No analyst sentiment
- No temporal relationships
- No cross-company linking
- Just raw letter text → vector search → synthesis

This deliberate poverty of context is what makes the comparison compelling.

---

## 7. QUERY ENGINE (Hybrid Pipeline)

### 7.1 Query Flow

```
USER QUESTION (natural language)
       │
       ▼
┌──────────────────────┐
│  INTENT CLASSIFIER   │ ← Claude API
│  Determines:         │
│  • Query type        │
│  • Companies needed  │
│  • Years needed      │
│  • Themes relevant   │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌──────────┐
│ Neo4j   │ │ ChromaDB │
│ Graph   │ │ Vector   │
│Traversal│ │ Search   │
└────┬────┘ └────┬─────┘
     │           │
     ▼           ▼
┌──────────────────────┐
│  CONTEXT ASSEMBLER   │
│  Merges:             │
│  • Graph nodes/edges │
│  • Relevant text     │
│  • Market data       │
│  • Theme labels      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  INSIGHT SYNTHESIZER │ ← Claude API
│  Produces:           │
│  • Comparative analysis│
│  • Pattern insights  │
│  • Cross-cultural    │
│    observations      │
│  • Actionable advice │
└──────────────────────┘
```

### 7.2 Pre-Built Demo Queries (Must Work Flawlessly)

These 5 queries are the ones SG will run during the live demo. They must be tested extensively.

**Query 1: Cross-Cultural Comparison (FLAGSHIP)**
> "How did Buffett frame uncertainty differently than Salil Parekh at Infosys during the same period?"

Expected graph traversal:
- Retrieve Letter nodes for both companies, same year
- Retrieve associated Theme nodes where label contains "uncertainty" or "risk"
- Retrieve MarketContext for both (what pressures they were under)
- Retrieve MarketResponse for both (how market reacted)
- Compare framing strategies

**Query 2: Temporal Evolution**
> "How did Buffett's narrative about market conditions evolve from 2021 to 2023?"

Expected graph traversal:
- Retrieve all Letter nodes for Berkshire (2021, 2022, 2023)
- Follow EVOLVED_TO edges between Theme nodes
- Show how themes shifted year over year
- Include MarketContext change as explanatory factor

**Query 3: Theme Parallel Detection**
> "What common themes appeared in both companies' letters when addressing similar economic conditions?"

Expected graph traversal:
- Retrieve Theme nodes linked to both companies
- Follow PARALLELS edges
- Include MacroCondition nodes to show shared context
- Highlight cultural differences in how same themes are framed

**Query 4: Context-to-Outcome Analysis**
> "When both CEOs addressed cost or margin pressures, how did the market respond?"

Expected graph traversal:
- Find Theme nodes with labels related to "cost", "margin", "efficiency", "profitability"
- Retrieve associated MarketResponse nodes
- Compare market reactions across companies
- Include MarketContext to control for different starting conditions

**Query 5: Communication Pattern Extraction**
> "What communication patterns correlate with positive market response across both companies?"

Expected graph traversal:
- Retrieve MarketResponse nodes where stock_change_7d_pct > 0
- Trace back to associated Letter and Theme nodes
- Identify common Theme characteristics (sentiment, temporal_orientation, confidence_level)
- Generate pattern summary

### 7.3 Comparison Display
For at least Query 1 and Query 5, the demo MUST show side-by-side:
- **Left panel:** Knowledge Graph response (rich, contextual, comparative)
- **Right panel:** Baseline RAG response (flat, text-only, no context)

This visual comparison IS the thesis proof.

---

## 8. THEME EXTRACTION (Claude API)

### 8.1 Theme Extraction Prompt Template

For each letter, send to Claude API with this prompt:

```
You are analyzing a CEO shareholder letter for a knowledge graph about executive communication patterns.

LETTER CONTEXT:
- Company: {company_name}
- Author: {author_name}
- Year: {year}
- Fiscal Year Covered: {fiscal_year}
- Key Macro Conditions: {macro_context_summary}

LETTER TEXT:
{full_letter_text}

Extract exactly 5-7 themes from this letter. For each theme, provide:

1. **label**: A concise theme label (2-5 words, e.g., "Digital Transformation Imperative", "Capital Allocation Discipline", "Talent Retention Crisis")

2. **description**: One sentence describing this theme as it appears in the letter

3. **sentiment_polarity**: One of: "positive", "negative", "mixed"

4. **temporal_orientation**: One of:
   - "backward_looking" (discussing past performance, explaining what happened)
   - "forward_looking" (setting vision, making commitments, predicting)
   - "both" (connecting past to future)

5. **confidence_level**: One of:
   - "definitive" (strong, certain language: "we will", "we achieved")
   - "hedged" (cautious language: "we expect", "we believe", "we hope")
   - "aspirational" (vision language: "we aim to", "our ambition is")

6. **key_quote**: A single sentence (under 30 words) from the letter that best captures this theme

7. **cross_cultural_relevance**: Rate 1-5 how likely this theme would appear in both US and Indian corporate letters (5 = universal business theme, 1 = culturally specific)

Return as JSON array.
```

### 8.2 Parallel Detection Prompt

After extracting themes for all letters, run cross-company parallel detection:

```
You are identifying thematic parallels between CEO letters from different companies and cultures.

BERKSHIRE HATHAWAY THEMES ({year}):
{berkshire_themes_json}

INFOSYS THEMES ({year}):
{infosys_themes_json}

SHARED MACRO CONTEXT:
{macro_context_for_year}

For each meaningful thematic parallel between the two companies:

1. **berkshire_theme_label**: The Berkshire theme
2. **infosys_theme_label**: The Infosys theme
3. **similarity_score**: 0.0 to 1.0 (how similar the themes are)
4. **parallel_description**: One sentence describing the parallel
5. **cultural_difference**: How the same theme is framed differently due to cultural/market context
6. **shared_driver**: What external factor drove both companies to address this theme

Return as JSON array. Only include parallels with similarity_score >= 0.5.
```

---

## 9. TECH STACK

### 9.1 Core Dependencies

```
# Python packages
neo4j==5.x          # Neo4j Python driver
langchain>=0.1.0    # Query orchestration
langchain-community # Neo4j integration
chromadb==0.4.x     # Vector store for baseline RAG
anthropic>=0.30.0   # Claude API for synthesis and theme extraction
yfinance>=0.2.0     # Market data
pdfplumber>=0.10.0  # PDF text extraction
streamlit>=1.30.0   # Demo UI
sentence-transformers>=2.0  # Local embeddings (fallback)
python-dotenv       # Environment variables
neomodel             # Optional: OGM for Neo4j (if needed)
requests            # Web scraping
beautifulsoup4      # HTML parsing for analyst data
pandas              # Data manipulation
numpy               # Numerical operations
```

### 9.2 Neo4j Setup

**Option A: Neo4j Aura Free Tier (RECOMMENDED for simplicity)**
- URL: https://neo4j.com/cloud/platform/aura-graph-database/
- Free tier: 1 instance, 200K nodes, 400K relationships (MORE than enough)
- Zero local setup, cloud-hosted
- Connection: `neo4j+s://<instance>.databases.neo4j.io`
- Requires creating account and saving credentials

**Option B: Local Neo4j via Docker**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5-community
```
- Access Neo4j Browser at http://localhost:7474
- Bolt connection: bolt://localhost:7687

**Use Option A unless there are connectivity issues. Option B is the fallback.**

### 9.3 Environment Variables Required

```env
# .env file
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # or bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

ANTHROPIC_API_KEY=sk-ant-xxxxx  # Claude API for synthesis
OPENAI_API_KEY=sk-xxxxx         # Optional: for OpenAI embeddings

# If using sentence-transformers locally, no key needed
```

### 9.4 Project Directory Structure

```
context-graph-mvp/
├── .env                          # Environment variables (gitignored)
├── README.md                     # Project overview
├── requirements.txt              # Python dependencies
├── PROJECT_SPEC.md              # This file (reference)
│
├── data/
│   ├── raw/
│   │   ├── letters/
│   │   │   ├── berkshire_2021.pdf
│   │   │   ├── berkshire_2022.pdf
│   │   │   ├── berkshire_2023.pdf
│   │   │   ├── infosys_fy2021_ar.pdf
│   │   │   ├── infosys_fy2022_ar.pdf
│   │   │   └── infosys_fy2023_ar.pdf
│   │   └── market/
│   │       └── (auto-generated CSVs from yfinance)
│   │
│   ├── processed/
│   │   ├── letters/
│   │   │   ├── berkshire_2021.txt      # Extracted text
│   │   │   ├── berkshire_2022.txt
│   │   │   ├── berkshire_2023.txt
│   │   │   ├── infosys_fy2021_ceo.txt  # CEO section only
│   │   │   ├── infosys_fy2022_ceo.txt
│   │   │   └── infosys_fy2023_ceo.txt
│   │   └── context_packages/
│   │       ├── berkshire_2021_context.json
│   │       ├── berkshire_2022_context.json
│   │       ├── berkshire_2023_context.json
│   │       ├── infosys_fy2021_context.json
│   │       ├── infosys_fy2022_context.json
│   │       └── infosys_fy2023_context.json
│   │
│   └── themes/
│       ├── berkshire_2021_themes.json
│       ├── berkshire_2022_themes.json
│       ├── berkshire_2023_themes.json
│       ├── infosys_fy2021_themes.json
│       ├── infosys_fy2022_themes.json
│       ├── infosys_fy2023_themes.json
│       └── cross_company_parallels.json
│
├── src/
│   ├── __init__.py
│   ├── data_collection/
│   │   ├── __init__.py
│   │   ├── download_letters.py      # Download PDFs
│   │   ├── extract_text.py          # PDF to text
│   │   ├── fetch_market_data.py     # yfinance data collection
│   │   └── fetch_analyst_data.py    # Analyst sentiment collection
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── schema.py               # Neo4j schema creation
│   │   ├── ingest.py               # Load context packages into Neo4j
│   │   ├── queries.py              # Pre-built Cypher query templates
│   │   └── visualize.py            # Graph visualization helpers
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── theme_extractor.py      # Claude API theme extraction
│   │   ├── parallel_detector.py    # Cross-company parallel detection
│   │   ├── sentiment_scorer.py     # Letter sentiment analysis
│   │   └── market_analyzer.py      # Market response calculations
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── baseline_rag.py         # ChromaDB baseline RAG
│   │   └── embeddings.py           # Embedding generation
│   │
│   ├── query_engine/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py    # NL query → intent + entities
│   │   ├── hybrid_retriever.py     # Graph + vector combined retrieval
│   │   └── synthesizer.py          # Claude API insight synthesis
│   │
│   └── demo/
│       ├── __init__.py
│       └── app.py                  # Streamlit demo application
│
├── scripts/
│   ├── 01_collect_data.py          # Run all data collection
│   ├── 02_process_letters.py       # Extract text, compute market data
│   ├── 03_build_context_packages.py # Assemble context JSON files
│   ├── 04_extract_themes.py        # Run Claude theme extraction
│   ├── 05_setup_neo4j.py           # Create schema and load data
│   ├── 06_build_baseline_rag.py    # Set up ChromaDB
│   ├── 07_run_comparisons.py       # Execute demo queries, capture results
│   └── 08_launch_demo.py           # Start Streamlit
│
└── presentation/
    ├── architecture_diagrams/      # Pre-built diagrams (already created)
    ├── demo_screenshots/           # Captured during comparison runs
    └── graph_visualizations/       # Neo4j browser screenshots
```

---

## 10. CONTEXT PACKAGE JSON TEMPLATE

Each letter gets a structured JSON context package. Claude Code should generate these.

```json
{
  "meta": {
    "company": "Berkshire Hathaway",
    "company_ticker": "BRK-B",
    "letter_year": 2022,
    "fiscal_year_covered": "CY2021",
    "publication_date": "2022-02-26",
    "author": "Warren Buffett",
    "letter_type": "annual_shareholder_letter",
    "geography": "US",
    "sector": "Diversified Conglomerate / Insurance / Investment"
  },

  "before": {
    "stock_price_30d_before": 302.45,
    "stock_price_on_publication": 318.72,
    "stock_30d_return_pct": 5.38,
    "benchmark_index": "S&P 500",
    "benchmark_30d_return_pct": 3.12,
    "relative_return_30d_pct": 2.26,
    "analyst_consensus_eps": null,
    "analyst_recommendations": {
      "buy": 5,
      "hold": 3,
      "sell": 0
    },
    "pre_letter_sentiment": "bullish",
    "key_analyst_concerns": "Focus on cash deployment strategy. Questions about succession planning. Interest in insurance float growth trajectory.",
    "macro_context": {
      "us_fed_rate": "0.00-0.25%",
      "us_inflation_rate": "7.5%",
      "key_headline": "Inflation surging to 40-year high. Fed signaling imminent rate hikes. Post-COVID economic boom with supply chain challenges.",
      "sector_context": "Insurance industry benefiting from hard market. Investment portfolio seeing strong equity returns."
    }
  },

  "during": {
    "letter_text": "FULL TEXT OF LETTER HERE",
    "word_count": 4200,
    "overall_sentiment_score": 0.65,
    "forward_looking_ratio": 0.35,
    "themes": [],
    "key_quotes": [
      "Quote 1 from letter",
      "Quote 2 from letter"
    ]
  },

  "after": {
    "stock_change_7d_pct": 1.2,
    "stock_change_30d_pct": -3.8,
    "benchmark_change_7d_pct": 0.5,
    "benchmark_change_30d_pct": -2.1,
    "relative_return_7d_pct": 0.7,
    "relative_return_30d_pct": -1.7,
    "post_letter_analyst_reaction": "Analysts praised capital allocation discipline. Concerns about energy exposure given Ukraine situation. Insurance results exceeded expectations.",
    "sentiment_shift": "unchanged"
  }
}
```

---

## 11. STREAMLIT DEMO APPLICATION

### 11.1 Layout

```
┌────────────────────────────────────────────────────────────┐
│  CONTEXT GRAPH: Executive Communication Intelligence       │
│  A Knowledge Graph Approach to Shareholder Letter Analysis │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [Text Input: Ask a question about executive communication]│
│  [🔍 Query]                                                │
│                                                            │
│  ┌─── Toggle: [Graph-Enhanced] [RAG-Only] [Side-by-Side]  │
│  │                                                         │
│  │  ┌─────────────────────┐  ┌────────────────────────┐   │
│  │  │  GRAPH RESPONSE     │  │  RAG RESPONSE          │   │
│  │  │                     │  │                        │   │
│  │  │  Rich contextual    │  │  Flat text-based       │   │
│  │  │  insight with       │  │  response from         │   │
│  │  │  market data,       │  │  letter text only.     │   │
│  │  │  cross-cultural     │  │  No context, no        │   │
│  │  │  patterns, and      │  │  market data, no       │   │
│  │  │  temporal analysis  │  │  cross-company links   │   │
│  │  │                     │  │                        │   │
│  │  └─────────────────────┘  └────────────────────────┘   │
│  │                                                         │
│  │  ┌─────────────────────────────────────────────────┐   │
│  │  │  GRAPH VISUALIZATION                             │   │
│  │  │  (Shows nodes and relationships queried)         │   │
│  │  └─────────────────────────────────────────────────┘   │
│  └─────────────────────────────────────────────────────────│
│                                                            │
│  ── Pre-built Demo Queries ──                              │
│  [Cross-Cultural] [Temporal] [Theme Parallel]              │
│  [Context-to-Outcome] [Pattern Extraction]                 │
│                                                            │
│  ── Data Overview ──                                       │
│  Companies: Berkshire Hathaway, Infosys                    │
│  Period: 2021-2023 (6 letters analyzed)                    │
│  Nodes: XX | Relationships: XX                             │
└────────────────────────────────────────────────────────────┘
```

### 11.2 Key UI Requirements
1. **Side-by-side comparison** is the most important view — make it the default for demo queries
2. **Pre-built query buttons** at the bottom — these trigger the 5 demo queries with a single click
3. **Graph visualization** panel — even a simple Mermaid diagram showing the relevant nodes is sufficient; does not need to be interactive Neo4j visualization
4. **Response time** should be under 10 seconds (Claude API is the bottleneck; pre-cache if needed)
5. **Professional appearance** — use Streamlit dark theme, clean typography, no visual clutter

### 11.3 Graph Visualization in Streamlit
**Simplest approach:** For each query result, generate a Mermaid diagram string showing the relevant nodes and relationships, and render it using `streamlit-mermaid` component or an embedded HTML iframe.

**Alternative:** Use `pyvis` library to create interactive network graphs inline.

---

## 12. VALIDATION CHECKPOINTS

### Checkpoint 1: After Data Collection (End of Week 1)
SG verifies:
- [ ] All 6 letter PDFs downloaded and text extracted correctly
- [ ] Market data CSV files have correct date ranges and prices
- [ ] At least 2 analyst data points per letter period captured
- [ ] Macro context summaries are accurate for each year
- [ ] Neo4j instance is running and accessible

### Checkpoint 2: After Graph Population (End of Week 2, Day 10)
SG verifies:
- [ ] All 6 context packages loaded as JSON files
- [ ] Neo4j Browser shows correct node counts (expected: ~6 letters, ~30-42 themes, 6 market contexts, 6 market responses, 6-9 macro conditions, 2 companies)
- [ ] Can run a basic Cypher query: `MATCH (l:Letter)-[:ADDRESSES_THEME]->(t:Theme) RETURN l.company_name, l.year, t.label`
- [ ] Graph visualization in Neo4j Browser looks correct

### Checkpoint 3: After Theme Extraction (End of Week 2, Day 14)
SG verifies:
- [ ] Theme labels are meaningful and distinct (not generic)
- [ ] Cross-company parallels feel genuine (not forced)
- [ ] Sentiment and temporal orientation classifications are reasonable
- [ ] EVOLVED_TO relationships make logical sense year-over-year
- [ ] ChromaDB baseline RAG returns results for test queries

### Checkpoint 4: After Query Engine Build (End of Week 3, Day 18)
SG verifies:
- [ ] All 5 demo queries return results from both systems
- [ ] Graph-enhanced responses are demonstrably richer than RAG-only
- [ ] Cross-cultural insights are genuine and interesting
- [ ] No crashes or timeouts during query execution
- [ ] Streamlit UI is clean and professional

### Checkpoint 5: Pre-Presentation (Week 4, Day 25)
SG verifies:
- [ ] Full demo runs end-to-end without intervention
- [ ] Backup video recorded of successful demo
- [ ] Presentation slides reference correct data and findings
- [ ] Can handle at least 2 "off-script" questions from the panel

---

## 13. PRESENTATION STRUCTURE (For SG's Reference)

### Recommended Flow (30 minutes total)

1. **The Problem** (3 min) — CEO communication impacts markets; current tools miss context
2. **The Thesis** (2 min) — Knowledge graphs > flat retrieval for relational intelligence
3. **Context Envelope Framework** (5 min) — Before-During-After model (use architecture diagram)
4. **Live Demo** (10 min) — Run 3-4 queries, show side-by-side comparison
5. **Cross-Cultural Findings** (5 min) — What differs between US and Indian executive communication
6. **Architecture & Technical Stack** (3 min) — Neo4j + LangChain + Claude hybrid
7. **Future Roadmap** (2 min) — 10+ companies, automated pipeline, predictive analysis

### Anticipated Panel Questions
1. "Why knowledge graphs instead of just better prompting with RAG?"
   → The relationships ARE the insight. You can't prompt your way to temporal theme evolution or cross-company market response correlation.

2. "How does this scale beyond 2 companies?"
   → Schema is designed for N companies. Adding a company means adding nodes and edges; the query patterns remain identical.

3. "What about the small sample size (6 letters)?"
   → This is a proof of architecture, not a statistical study. The framework demonstrates that graph-structured context produces richer insights. Scaling data validates findings; it doesn't change the architectural argument.

4. "How does this connect to your consulting practice?"
   → Direct advisory enhancement: "Here's how your peer at comparable scale addressed this challenge, in the specific market conditions you're facing."

5. "What's the cross-cultural insight?"
   → [This will come from actual data analysis — prepare this once themes are extracted]

---

## 14. EXECUTION INSTRUCTIONS FOR CLAUDE CODE

### How to Use This Spec
1. **Read this entire document** before starting any implementation
2. **Execute the numbered scripts in order** (01 through 08)
3. **Pause at each validation checkpoint** for SG to review
4. **When stuck:** Refer to the schema definitions, query templates, and prompt templates in this spec
5. **When making decisions:** Prefer simplicity. If two approaches could work, choose the one with fewer dependencies and less setup time.

### Key Principles
- **Depth over breadth:** 6 letters with rich context > 20 letters with thin context
- **Demo-driven:** Everything we build serves the live demo. If it doesn't appear in the demo, deprioritize it.
- **Comparison is king:** The side-by-side RAG vs. Graph comparison is the thesis proof. It must work flawlessly.
- **Cross-cultural is non-negotiable:** The advisor expects it. Every feature should surface US vs. India patterns.
- **Fail gracefully:** Pre-built query templates > dynamic query generation for reliability in a live demo.

### Fallback Strategies
| If This Fails... | Do This Instead... |
|---|---|
| Neo4j Aura Free Tier | Docker local instance |
| yfinance API issues | Hard-code market data from Yahoo Finance website |
| Claude API rate limits | Pre-compute all theme extractions and cache as JSON |
| LangChain GraphCypherQA unreliable | Pre-built parameterized Cypher queries |
| Streamlit graph visualization | Static Mermaid diagrams or screenshots |
| Live demo crashes | Pre-recorded backup video |

---

## 15. ACADEMIC REFERENCES (For Presentation)

SG should cite these in the presentation to establish credibility:

1. **CEO Communication Impact on Markets:**
   - Henry & Leone (2016): "Measuring Qualitative Information in Capital Markets Research"
   - Loughran & McDonald (2011): "When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks"
   - Price et al. (2012): "Earnings Conference Calls and Stock Returns"

2. **Knowledge Graphs in Business Intelligence:**
   - Hogan et al. (2021): "Knowledge Graphs" (ACM Computing Surveys)
   - Pan et al. (2024): "Unifying Large Language Models and Knowledge Graphs: A Roadmap"

3. **RAG Systems:**
   - Lewis et al. (2020): "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
   - Gao et al. (2024): "Retrieval-Augmented Generation for Large Language Models: A Survey"

---

*End of Project Specification*
*Version 1.0 — February 24, 2026*
*This document should be placed in the project root and referenced by Claude Code throughout implementation.*
