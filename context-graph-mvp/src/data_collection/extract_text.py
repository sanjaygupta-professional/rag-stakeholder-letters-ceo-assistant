"""Extract text from shareholder letter PDFs using pdfplumber."""

import logging
import os

import pdfplumber

logger = logging.getLogger(__name__)

# Infosys CEO letter page ranges (0-indexed).
# These may need adjustment after inspecting the actual PDFs.
# Berkshire letters are extracted in full (entire PDF is the letter).
PAGE_RANGES = {
    "infosys_fy2021_ar.pdf": (6, 13),   # CEO & MD's letter section
    "infosys_fy2022_ar.pdf": (6, 13),
    "infosys_fy2023_ar.pdf": (6, 13),
}


def extract_full_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF. Used for Berkshire letters."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    full_text = "\n\n".join(text_parts)
    logger.info("%s: %d pages, %d words", os.path.basename(pdf_path),
                len(text_parts), len(full_text.split()))
    return full_text


def extract_page_range(pdf_path: str, start: int, end: int) -> str:
    """Extract text from pages [start, end) (0-indexed). Used for Infosys CEO sections."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(start, min(end, len(pdf.pages))):
            page_text = pdf.pages[i].extract_text()
            if page_text:
                text_parts.append(page_text)
    full_text = "\n\n".join(text_parts)
    logger.info("%s: pages %d-%d, %d words", os.path.basename(pdf_path),
                start, end - 1, len(full_text.split()))
    return full_text


def extract_letter_text(pdf_path: str) -> str:
    """Extract letter text from a PDF, auto-detecting whether to use full or range extraction."""
    filename = os.path.basename(pdf_path)
    if filename in PAGE_RANGES:
        start, end = PAGE_RANGES[filename]
        return extract_page_range(pdf_path, start, end)
    return extract_full_pdf(pdf_path)


def extract_all_letters(raw_dir: str = "data/raw/letters",
                        output_dir: str = "data/processed/letters") -> dict[str, int]:
    """Extract text from all PDFs and save as .txt files.

    Returns {output_filename: word_count}.
    """
    from src.data_collection.letter_registry import LETTERS

    os.makedirs(output_dir, exist_ok=True)
    results = {}

    for letter in LETTERS:
        pdf_path = os.path.join(raw_dir, letter["output_filename"])
        if not os.path.exists(pdf_path):
            logger.warning("PDF not found: %s", pdf_path)
            continue

        # Determine output filename
        base = os.path.splitext(letter["output_filename"])[0]
        if letter["company"] == "Infosys":
            out_name = f"{base.replace('_ar', '')}_ceo.txt"
        else:
            out_name = f"{base}.txt"

        out_path = os.path.join(output_dir, out_name)

        # Skip if already extracted
        if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
            word_count = len(open(out_path).read().split())
            logger.info("SKIP (exists): %s (%d words)", out_name, word_count)
            results[out_name] = word_count
            continue

        text = extract_letter_text(pdf_path)
        if text.strip():
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            word_count = len(text.split())
            results[out_name] = word_count
            logger.info("Saved: %s (%d words)", out_name, word_count)
        else:
            logger.error("No text extracted from %s", pdf_path)
            results[out_name] = 0

    return results
