import pytest

from app.config import Settings
from app.errors import InvalidDocumentError
from app.pdf import extract_pages
from tests.conftest import make_pdf

S = Settings()


def test_extracts_text_per_page():
    pages = extract_pages(make_pdf(["First page text", "Second page text"]), S)
    assert "First page" in pages[0] and "Second page" in pages[1]


def test_rejects_non_pdf():
    with pytest.raises(InvalidDocumentError):
        extract_pages(b"hello", S)


def test_rejects_pdf_without_text():
    with pytest.raises(InvalidDocumentError):
        extract_pages(make_pdf([""]), S)


def test_rejects_too_many_pages():
    with pytest.raises(InvalidDocumentError):
        extract_pages(make_pdf(["a", "b", "c"]), Settings(max_pdf_pages=2))


def test_rejects_corrupt_pdf():
    with pytest.raises(InvalidDocumentError):
        extract_pages(b"%PDF-1.4\ngarbage", S)
