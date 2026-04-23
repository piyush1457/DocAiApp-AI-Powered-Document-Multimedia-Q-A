import pytest
from unittest.mock import MagicMock, patch
from app.utils.file_parser import parse_pdf
from app.core.exceptions import IngestionError
from app.api.v1.routes.upload import ALLOWED_EXTENSIONS, MAX_FILE_SIZE

def test_parse_pdf_extraction_page_numbers():
    """Test that PDF extraction returns correct text and page numbers."""
    mock_pdf = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 content"
    mock_pdf.pages = [mock_page1, mock_page2]
    mock_pdf.__enter__.return_value = mock_pdf
    
    with patch("pdfplumber.open", return_value=mock_pdf):
        results = parse_pdf("dummy.pdf")
        assert len(results) == 2
        assert results[0]["page_number"] == 1
        assert results[1]["page_number"] == 2
        assert "Page 1 content" in results[0]["text"]

def test_parse_pdf_fallback_to_pymupdf():
    """Test fallback to PyMuPDF when pdfplumber returns empty text."""
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "" # Empty
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__.return_value = mock_pdf
    
    mock_doc = MagicMock()
    mock_fitz_page = MagicMock()
    mock_fitz_page.get_text.return_value = "PyMuPDF text content"
    mock_doc.__iter__.return_value = [mock_fitz_page]
    
    with patch("pdfplumber.open", return_value=mock_pdf), \
         patch("fitz.open", return_value=mock_doc):
        results = parse_pdf("dummy.pdf")
        assert len(results) == 1
        assert results[0]["text"] == "PyMuPDF text content"

def test_mime_type_validation_rejects_invalid():
    """Test that invalid MIME types/extensions are rejected."""
    invalid_ext = "exe"
    assert invalid_ext not in ALLOWED_EXTENSIONS

def test_mime_type_validation_accepts_valid():
    """Test that valid MIME types are accepted."""
    assert "pdf" in ALLOWED_EXTENSIONS
    assert "mp3" in ALLOWED_EXTENSIONS

def test_file_size_limit_enforcement():
    """Test that file size limit is set correctly (500MB)."""
    assert MAX_FILE_SIZE == 500 * 1024 * 1024

def test_parse_pdf_no_text_raises_error():
    """Test that an error is raised when no text can be extracted by any parser."""
    mock_pdf = MagicMock()
    mock_pdf.pages = []
    mock_pdf.__enter__.return_value = mock_pdf
    
    with patch("pdfplumber.open", return_value=mock_pdf), \
         patch("fitz.open", return_value=MagicMock()):
        with pytest.raises(IngestionError):
            parse_pdf("dummy.pdf")
