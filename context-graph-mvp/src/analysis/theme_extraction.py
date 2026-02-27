"""Theme extraction, parallel detection, and temporal evolution via LLM."""

import json
import logging
import os

from src.llm import call_llm_json

logger = logging.getLogger(__name__)


def extract_themes(letter_meta: dict, letter_text: str, macro_context: str) -> list[dict]:
    """Extract 5-7 themes from a single letter using the LLM.

    Prompt follows PROJECT_SPEC Section 8.1.
    """
    prompt = f"""You are analyzing a CEO shareholder letter for a knowledge graph about executive communication patterns.

LETTER CONTEXT:
- Company: {letter_meta['company']}
- Author: {letter_meta['author']}
- Year: {letter_meta['letter_year']}
- Fiscal Year Covered: {letter_meta['fiscal_year_covered']}
- Key Macro Conditions: {macro_context}

LETTER TEXT:
{letter_text[:12000]}

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

Return as JSON array."""

    system = "You are an expert analyst of executive communication. Return only valid JSON."
    return call_llm_json(prompt, system=system, temperature=0.2)


def detect_parallels(brk_themes: list[dict], infy_themes: list[dict],
                     year: int, macro_context: str) -> list[dict]:
    """Detect cross-company thematic parallels for a given year.

    Prompt follows PROJECT_SPEC Section 8.2.
    """
    prompt = f"""You are identifying thematic parallels between CEO letters from different companies and cultures.

BERKSHIRE HATHAWAY THEMES ({year}):
{json.dumps(brk_themes, indent=2)}

INFOSYS THEMES ({year}):
{json.dumps(infy_themes, indent=2)}

SHARED MACRO CONTEXT:
{macro_context}

For each meaningful thematic parallel between the two companies:

1. **berkshire_theme_label**: The Berkshire theme label
2. **infosys_theme_label**: The Infosys theme label
3. **similarity_score**: 0.0 to 1.0 (how similar the themes are)
4. **parallel_description**: One sentence describing the parallel
5. **cultural_difference**: How the same theme is framed differently due to cultural/market context
6. **shared_driver**: What external factor drove both companies to address this theme

Return as JSON array. Only include parallels with similarity_score >= 0.5."""

    system = "You are an expert in cross-cultural executive communication analysis. Return only valid JSON."
    return call_llm_json(prompt, system=system, temperature=0.2)


def detect_temporal_evolution(themes_by_year: dict[int, list[dict]],
                              company: str) -> list[dict]:
    """Detect how themes evolved year-over-year within a single company."""
    years = sorted(themes_by_year.keys())
    if len(years) < 2:
        return []

    themes_summary = {}
    for y in years:
        themes_summary[str(y)] = themes_by_year[y]

    prompt = f"""You are analyzing how executive communication themes evolved over time for {company}.

THEMES BY YEAR:
{json.dumps(themes_summary, indent=2)}

For each meaningful theme evolution (a theme in one year that evolved into a related theme in a later year):

1. **from_year**: The earlier year
2. **from_theme_label**: The theme label in the earlier year
3. **to_year**: The later year
4. **to_theme_label**: The theme label in the later year
5. **evolution_description**: One sentence describing how the theme evolved
6. **driver**: What caused this evolution (macro change, company event, etc.)
7. **years_gap**: Number of years between the two themes

Return as JSON array. Only include genuine evolutions, not coincidental similarities."""

    system = "You are an expert in longitudinal executive communication analysis. Return only valid JSON."
    return call_llm_json(prompt, system=system, temperature=0.2)


def extract_and_cache(letter_meta: dict, letter_text: str, macro_context: str,
                      cache_dir: str = "data/themes") -> list[dict]:
    """Extract themes and cache to disk. Skip if cache exists."""
    os.makedirs(cache_dir, exist_ok=True)

    base = f"{letter_meta['company'].lower().replace(' ', '_')}_{letter_meta['letter_year']}"
    if letter_meta.get("geography") == "India":
        base = f"infosys_fy{letter_meta['letter_year']}"
    cache_path = os.path.join(cache_dir, f"{base}_themes.json")

    if os.path.exists(cache_path):
        logger.info("SKIP (cached): %s", cache_path)
        with open(cache_path) as f:
            return json.load(f)

    logger.info("Extracting themes for %s %d...", letter_meta["company"], letter_meta["letter_year"])
    themes = extract_themes(letter_meta, letter_text, macro_context)

    with open(cache_path, "w") as f:
        json.dump(themes, f, indent=2)
    logger.info("Cached %d themes to %s", len(themes), cache_path)
    return themes
