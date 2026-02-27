"""Central registry of shareholder/stakeholder letters used across the pipeline."""

LETTERS = [
    # --- Berkshire Hathaway ---
    {
        "company": "Berkshire Hathaway",
        "ticker": "BRK-B",
        "year": 2021,
        "fiscal_year_covered": "CY2021",
        "publication_date": "2022-02-26",
        "author": "Warren Buffett",
        "pdf_url": "https://www.berkshirehathaway.com/letters/2021ltr.pdf",
        "output_filename": "berkshire_2021.pdf",
        "benchmark_ticker": "^GSPC",
        "geography": "US",
        "sector": "Diversified Conglomerate",
    },
    {
        "company": "Berkshire Hathaway",
        "ticker": "BRK-B",
        "year": 2022,
        "fiscal_year_covered": "CY2022",
        "publication_date": "2023-02-25",
        "author": "Warren Buffett",
        "pdf_url": "https://www.berkshirehathaway.com/letters/2022ltr.pdf",
        "output_filename": "berkshire_2022.pdf",
        "benchmark_ticker": "^GSPC",
        "geography": "US",
        "sector": "Diversified Conglomerate",
    },
    {
        "company": "Berkshire Hathaway",
        "ticker": "BRK-B",
        "year": 2023,
        "fiscal_year_covered": "CY2023",
        "publication_date": "2024-02-24",
        "author": "Warren Buffett",
        "pdf_url": "https://www.berkshirehathaway.com/letters/2023ltr.pdf",
        "output_filename": "berkshire_2023.pdf",
        "benchmark_ticker": "^GSPC",
        "geography": "US",
        "sector": "Diversified Conglomerate",
    },
    # --- Infosys ---
    {
        "company": "Infosys",
        "ticker": "INFY",
        "year": 2021,
        "fiscal_year_covered": "FY2021 (Apr 2020 – Mar 2021)",
        "publication_date": "2021-07-01",
        "author": "Salil Parekh",
        "pdf_url": "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-21.pdf",
        "output_filename": "infosys_fy2021_ar.pdf",
        "benchmark_ticker": "^CNXIT",
        "geography": "India",
        "sector": "IT Services",
    },
    {
        "company": "Infosys",
        "ticker": "INFY",
        "year": 2022,
        "fiscal_year_covered": "FY2022 (Apr 2021 – Mar 2022)",
        "publication_date": "2022-07-01",
        "author": "Salil Parekh",
        "pdf_url": "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-22.pdf",
        "output_filename": "infosys_fy2022_ar.pdf",
        "benchmark_ticker": "^CNXIT",
        "geography": "India",
        "sector": "IT Services",
    },
    {
        "company": "Infosys",
        "ticker": "INFY",
        "year": 2023,
        "fiscal_year_covered": "FY2023 (Apr 2022 – Mar 2023)",
        "publication_date": "2023-07-01",
        "author": "Salil Parekh",
        "pdf_url": "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-23.pdf",
        "output_filename": "infosys_fy2023_ar.pdf",
        "benchmark_ticker": "^CNXIT",
        "geography": "India",
        "sector": "IT Services",
    },
]


def get_letter(company: str, year: int) -> dict | None:
    """Return the letter metadata for a given company and year, or None."""
    for letter in LETTERS:
        if letter["company"] == company and letter["year"] == year:
            return letter
    return None


def get_unique_tickers() -> set[str]:
    """Return all unique stock and benchmark tickers across the registry."""
    tickers: set[str] = set()
    for letter in LETTERS:
        tickers.add(letter["ticker"])
        tickers.add(letter["benchmark_ticker"])
    return tickers
