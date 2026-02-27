"""Thin LLM abstraction — call Gemini (default) or Anthropic if key is available."""

import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_PROVIDER = None  # "anthropic" | "gemini"


def _get_secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets (cloud) first, then fall back to env vars."""
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def _get_provider() -> str:
    global _PROVIDER
    if _PROVIDER:
        return _PROVIDER

    if _get_secret("ANTHROPIC_API_KEY"):
        _PROVIDER = "anthropic"
        logger.info("LLM provider: Anthropic (Claude)")
    elif _get_secret("GEMINI_API_KEY"):
        _PROVIDER = "gemini"
        logger.info("LLM provider: Google Gemini")
    else:
        raise RuntimeError("No LLM API key found. Set GEMINI_API_KEY or ANTHROPIC_API_KEY in .env")
    return _PROVIDER


def call_llm(prompt: str, system: str = "", temperature: float = 0.3,
             max_tokens: int = 4096) -> str:
    """Send a prompt to the configured LLM and return the text response."""
    provider = _get_provider()

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful analyst.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    # Gemini
    from google import genai
    client = genai.Client(api_key=_get_secret("GEMINI_API_KEY"))
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt,
        config=genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


def call_llm_json(prompt: str, system: str = "", temperature: float = 0.1,
                  max_tokens: int = 4096) -> dict | list:
    """Call LLM and parse the response as JSON. Retries once on parse failure."""
    for attempt in range(2):
        raw = call_llm(prompt, system=system, temperature=temperature,
                       max_tokens=max_tokens)
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt == 0:
                logger.warning("JSON parse failed (attempt 1), retrying with stricter prompt")
                prompt = prompt + "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanation."
            else:
                logger.error("JSON parse failed after 2 attempts. Raw response:\n%s", raw[:500])
                raise
