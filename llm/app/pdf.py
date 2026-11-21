"""Safe PDF download and text extraction."""

from __future__ import annotations

import io
import logging
from typing import Callable
from urllib.parse import urljoin

import requests
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from .config import Settings
from .errors import (
    DocumentFetchError,
    DocumentTooLargeError,
    InvalidDocumentError,
)
from .security import validate_public_url

log = logging.getLogger("llm.pdf")

Fetcher = Callable[[str, Settings], bytes]


def download_pdf(url: str, settings: Settings) -> bytes:
    """Download a PDF with timeouts, a size cap and per-hop SSRF validation."""
    current = url
    with requests.Session() as session:
        for _ in range(settings.max_redirects + 1):
            validate_public_url(current)
            try:
                response = session.get(
                    current,
                    stream=True,
                    allow_redirects=False,
                    timeout=(5, settings.download_timeout_s),
                )
            except requests.RequestException as exc:
                raise DocumentFetchError("Unable to download the document") from exc

            with response:
                if response.is_redirect or response.is_permanent_redirect:
                    location = response.headers.get("Location")
                    if not location:
                        raise DocumentFetchError("Redirect without a location")
                    current = urljoin(current, location)
                    continue
                if response.status_code != 200:
                    raise DocumentFetchError(
                        f"Document server returned HTTP {response.status_code}"
                    )
                return _read_limited(response, settings.max_pdf_bytes)

    raise DocumentFetchError("Too many redirects while downloading the document")


def _read_limited(response: requests.Response, limit: int) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared and declared.isdigit() and int(declared) > limit:
        raise DocumentTooLargeError(f"Document exceeds the {limit} byte limit")

    buffer = bytearray()
    try:
        for part in response.iter_content(chunk_size=64 * 1024):
            buffer.extend(part)
            if len(buffer) > limit:
                raise DocumentTooLargeError(f"Document exceeds the {limit} byte limit")
    except requests.RequestException as exc:
        raise DocumentFetchError("Download was interrupted") from exc
    return bytes(buffer)


def extract_pages(data: bytes, settings: Settings) -> list[str]:
    """Return the text of each page. Raises InvalidDocumentError for unusable input."""
    if not data.lstrip()[:5] == b"%PDF-":
        raise InvalidDocumentError("The document is not a PDF")

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise InvalidDocumentError("The PDF is password protected")
        if len(reader.pages) > settings.max_pdf_pages:
            raise InvalidDocumentError(
                f"The PDF has more than {settings.max_pdf_pages} pages"
            )
        pages = [(page.extract_text() or "") for page in reader.pages]
    except InvalidDocumentError:
        raise
    except (PyPdfError, ValueError, KeyError, OSError) as exc:
        raise InvalidDocumentError("The PDF could not be parsed") from exc

    if not any(p.strip() for p in pages):
        raise InvalidDocumentError(
            "No extractable text found (scanned PDFs are not supported)"
        )
    log.info("pdf parsed", extra={"pages": len(pages)})
    return pages
