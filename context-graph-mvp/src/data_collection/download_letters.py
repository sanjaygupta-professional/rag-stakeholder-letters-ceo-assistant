"""Download shareholder letter PDFs to data/raw/letters/."""

import os
import logging
import requests
from src.data_collection.letter_registry import LETTERS

logger = logging.getLogger(__name__)


def download_pdf(url: str, output_path: str, timeout: int = 60) -> bool:
    """Download a single PDF. Skips if file already exists and is > 1KB."""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        logger.info("SKIP (exists): %s", os.path.basename(output_path))
        return True

    try:
        logger.info("Downloading: %s", url)
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)

        size_kb = len(resp.content) / 1024
        logger.info("Saved: %s (%.0f KB)", os.path.basename(output_path), size_kb)
        return True

    except Exception as e:
        logger.error("FAILED: %s — %s", os.path.basename(output_path), e)
        return False


def download_all_letters(output_dir: str = "data/raw/letters") -> dict[str, bool]:
    """Download all letter PDFs from registry. Returns {filename: success}."""
    results = {}
    for letter in LETTERS:
        filename = letter["output_filename"]
        output_path = os.path.join(output_dir, filename)
        results[filename] = download_pdf(letter["pdf_url"], output_path)

    succeeded = sum(1 for v in results.values() if v)
    logger.info("PDFs: %d/%d downloaded successfully", succeeded, len(results))
    return results
