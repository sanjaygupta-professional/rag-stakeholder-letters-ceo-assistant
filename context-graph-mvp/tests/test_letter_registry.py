from src.data_collection.letter_registry import LETTERS, get_letter, get_unique_tickers

def test_registry_has_six_letters():
    assert len(LETTERS) == 6

def test_berkshire_letters_have_correct_years():
    brk = [l for l in LETTERS if l["company"] == "Berkshire Hathaway"]
    years = sorted([l["year"] for l in brk])
    assert years == [2021, 2022, 2023]

def test_infosys_letters_have_correct_years():
    infy = [l for l in LETTERS if l["company"] == "Infosys"]
    years = sorted([l["year"] for l in infy])
    assert years == [2021, 2022, 2023]

def test_all_letters_have_required_fields():
    required = {"company", "ticker", "year", "fiscal_year_covered",
                "publication_date", "author", "pdf_url", "output_filename",
                "benchmark_ticker", "geography", "sector"}
    for letter in LETTERS:
        missing = required - set(letter.keys())
        assert not missing, f"{letter['company']} {letter['year']} missing: {missing}"

def test_get_letter_by_company_and_year():
    l = get_letter("Berkshire Hathaway", 2022)
    assert l["author"] == "Warren Buffett"
    assert l["publication_date"] == "2023-02-25"

def test_get_letter_returns_none_for_unknown():
    assert get_letter("Apple", 2022) is None

def test_get_unique_tickers():
    tickers = get_unique_tickers()
    assert "BRK-B" in tickers
    assert "INFY" in tickers
    assert "^GSPC" in tickers
    assert "^CNXIT" in tickers
