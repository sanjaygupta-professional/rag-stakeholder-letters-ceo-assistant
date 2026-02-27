import os
import tempfile
from unittest.mock import patch, MagicMock
from src.data_collection.download_letters import download_pdf

def test_download_pdf_saves_file():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.content = b"%PDF-1.4 fake pdf content here"
    fake_response.raise_for_status = MagicMock()

    with tempfile.TemporaryDirectory() as tmpdir:
        outpath = os.path.join(tmpdir, "test.pdf")
        with patch("src.data_collection.download_letters.requests.get", return_value=fake_response):
            result = download_pdf("https://example.com/test.pdf", outpath)
        assert result is True
        assert os.path.exists(outpath)

def test_download_pdf_returns_false_on_failure():
    with patch("src.data_collection.download_letters.requests.get", side_effect=Exception("Network error")):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_pdf("https://example.com/bad.pdf",
                                  os.path.join(tmpdir, "bad.pdf"))
            assert result is False

def test_download_pdf_skips_existing(tmp_path):
    outpath = tmp_path / "exists.pdf"
    outpath.write_bytes(b"%PDF-1.4 already here" + b"x" * 2000)
    with patch("src.data_collection.download_letters.requests.get") as mock_get:
        result = download_pdf("https://example.com/x.pdf", str(outpath))
        assert result is True
        mock_get.assert_not_called()
