"""Arena-inspired CSS injection for the Streamlit demo.

Provides an earthy, prestigious aesthetic: Playfair Display headings,
Inter body text, teal/copper palette, pill buttons, no shadows.
"""

import streamlit as st

# ── Palette constants ────────────────────────────────────────────────
ARENA = {
    "cream": "#F7F6F5",
    "white": "#FFFFFF",
    "teal": "#487265",
    "teal_light": "#DDEFEF",
    "copper": "#BC976A",
    "sand": "#CB9F69",
    "olive": "#AAB788",
    "dark_copper": "#8B6B4A",
    "warm_gray": "#898584",
    "cream_dark": "#F3F1EF",
    "border": "#D9D9D9",
    "text_primary": "#292C33",
    "text_secondary": "#5A5A5A",
}

COMPANY_COLORS = {
    "Berkshire Hathaway": ARENA["teal"],
    "Infosys": ARENA["copper"],
}

SENTIMENT_COLORS = {
    "positive": ARENA["olive"],
    "negative": ARENA["dark_copper"],
    "neutral": ARENA["warm_gray"],
}

EDGE_COLORS = {
    "PARALLELS": ARENA["sand"],
}

PYVIS_BG = ARENA["cream"]
PYVIS_FONT_COLOR = ARENA["text_primary"]


# ── CSS injection ────────────────────────────────────────────────────
_ARENA_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── Global reset ──────────────────────────────────────────────── */
* {{
    box-shadow: none !important;
}}

/* ── Backgrounds ───────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {{
    background-color: {ARENA["cream"]} !important;
}}

[data-testid="stSidebar"] {{
    background-color: {ARENA["white"]} !important;
    border-right: 1px solid {ARENA["border"]} !important;
}}

[data-testid="stHeader"] {{
    background-color: {ARENA["cream"]} !important;
    border-bottom: 1px solid {ARENA["border"]} !important;
}}

/* ── Typography ────────────────────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    color: {ARENA["text_primary"]} !important;
}}

h1, h2, h3 {{
    font-family: 'Playfair Display', serif !important;
    color: {ARENA["text_primary"]} !important;
}}

h1 {{
    font-weight: 700 !important;
}}

h2, h3 {{
    font-weight: 600 !important;
}}

/* ── Buttons (pill) ────────────────────────────────────────────── */
.stButton > button {{
    border-radius: 999px !important;
    border: 1px solid {ARENA["teal"]} !important;
    background-color: {ARENA["white"]} !important;
    color: {ARENA["teal"]} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: background-color 0.2s, color 0.2s !important;
}}

.stButton > button:hover {{
    background-color: {ARENA["teal"]} !important;
    color: {ARENA["white"]} !important;
}}

.stButton > button:active,
.stButton > button:focus {{
    background-color: {ARENA["teal"]} !important;
    color: {ARENA["white"]} !important;
    border-color: {ARENA["teal"]} !important;
}}

/* ── Text input ────────────────────────────────────────────────── */
[data-testid="stTextInput"] input {{
    border: 1px solid {ARENA["border"]} !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}}

[data-testid="stTextInput"] input:focus {{
    border-color: {ARENA["teal"]} !important;
}}

/* ── Expanders ─────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    border: 1px solid {ARENA["border"]} !important;
    border-radius: 8px !important;
    background-color: {ARENA["white"]} !important;
}}

/* ── Metrics ───────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
    border: 1px solid {ARENA["border"]} !important;
    border-radius: 8px !important;
    padding: 12px !important;
    background-color: {ARENA["white"]} !important;
}}

[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {ARENA["teal"]} !important;
    font-family: 'Playfair Display', serif !important;
}}

/* ── Alerts (st.info) ──────────────────────────────────────────── */
.stAlert {{
    background-color: {ARENA["teal_light"]} !important;
    border-left: 4px solid {ARENA["teal"]} !important;
    border-radius: 4px !important;
}}

/* ── Code blocks ───────────────────────────────────────────────── */
div.stCodeBlock {{
    border: 1px solid {ARENA["border"]} !important;
    border-radius: 8px !important;
}}

/* ── Dividers ──────────────────────────────────────────────────── */
hr {{
    border: none !important;
    border-top: 1px solid {ARENA["border"]} !important;
}}

/* ── Links ─────────────────────────────────────────────────────── */
a {{
    color: {ARENA["teal"]} !important;
}}

a:hover {{
    color: {ARENA["dark_copper"]} !important;
}}
</style>
"""


def inject_arena_css():
    """Call once after st.set_page_config() to apply Arena styling."""
    st.markdown(_ARENA_CSS, unsafe_allow_html=True)
