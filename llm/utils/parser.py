import os
import re
from typing import Optional, Tuple
import email
from email import policy
from email.parser import BytesParser

# lazy imports for optional dependencies
try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore

try:
    import docx
except ImportError:
    docx = None  # type: ignore

try:
    import extract_msg
except ImportError:
    extract_msg = None  # type: ignore

# optional HTML-to-text helper
try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    BeautifulSoup = None  # type: ignore


# === Exceptions ===
class ExtractionError(Exception):
    """Base extraction error."""
    pass


class DependencyMissingError(ExtractionError):
    """Raised when a required third-party library is missing."""
    pass


class UnsupportedFileTypeError(ExtractionError):
    """Raised when the file extension is not supported."""
    pass


class FileNotFoundErrorCustom(ExtractionError):
    """Raised when the input file is absent."""
    pass


# Helping me
def _strip_html(html: str) -> str:
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n")
    # fallback naive stripping
    text = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    try:
        import html as _html_module

        text = _html_module.unescape(text)
    except ImportError:
        pass
    return text


# Extractorsss therla
def extract_pdf_text(file_path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
    if pdfplumber is None:
        raise DependencyMissingError("pdfplumber is required. polease   Install via `pip install pdfplumber`.")
    if not os.path.isfile(file_path):
        raise FileNotFoundErrorCustom(f"PDF not found: {file_path}")

    parts = []
    with pdfplumber.open(file_path) as pdf:
        num_pages = len(pdf.pages)
        start, end = 1, num_pages
        if page_range:
            start, end = page_range
            if start < 1 or end > num_pages or start > end:
                raise ExtractionError(f"Invalid page range {page_range} for PDF with {num_pages} pages.")
        for i in range(start - 1, end):
            page = pdf.pages[i]
            page_text = page.extract_text()
            if page_text:
                parts.append(page_text)
    return "\n\n".join(parts)


def extract_docx_text(file_path: str) -> str:
    if docx is None:
        raise DependencyMissingError("python-docx is required. polease Install via `pip install python-docx`.")
    if not os.path.isfile(file_path):
        raise FileNotFoundErrorCustom(f"DOCX not found: {file_path}")
    try:
        document = docx.Document(file_path)
    except Exception as e:
        raise ExtractionError(f"Failed to open DOCX: {e}") from e
    paragraphs = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs)


def extract_eml_text(file_path: str) -> str:
    if not os.path.isfile(file_path):
        raise FileNotFoundErrorCustom(f"EML not found: {file_path}")
    try:
        with open(file_path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)
    except Exception as e:
        raise ExtractionError(f"Failed to parse EML: {e}") from e

    headers = {
        "Subject": msg.get("subject", ""),
        "From": msg.get("from", ""),
        "To": msg.get("to", ""),
        "Date": msg.get("date", ""),
    }

    plain = None
    html_body = None
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            try:
                content = part.get_content()
            except Exception:
                continue
            if ctype == "text/plain" and plain is None:
                plain = content
            elif ctype == "text/html" and html_body is None:
                html_body = content
    else:
        ctype = msg.get_content_type()
        try:
            content = msg.get_content()
        except Exception:
            content = ""
        if ctype == "text/plain":
            plain = content
        elif ctype == "text/html":
            html_body = content

    body = plain if plain else (_strip_html(html_body) if html_body else "")

    parts = [
        f"Subject: {headers['Subject']}",
        f"From: {headers['From']}",
        f"To: {headers['To']}",
        f"Date: {headers['Date']}",
        "",
        "Body:",
        body.strip(),
    ]
    return "\n".join(parts)


def extract_msg_text(file_path: str) -> str:
    if extract_msg is None:
        raise DependencyMissingError("extract_msg is required for .msg files. poleaseee install via `pip install extract-msg`.")
    if not os.path.isfile(file_path):
        raise FileNotFoundErrorCustom(f"MSG not found: {file_path}")
    try:
        msg = extract_msg.Message(file_path)
        subject = msg.subject or ""
        sender = msg.sender or ""
        to = msg.to or ""
        date = msg.date or ""
        body = msg.body or ""
        if not body and hasattr(msg, "htmlBody") and msg.htmlBody:
            body = _strip_html(msg.htmlBody)
    except Exception as e:
        raise ExtractionError(f"Failed to read .msg file: {e}") from e

    parts = [
        f"Subject: {subject}",
        f"From: {sender}",
        f"To: {to}",
        f"Date: {date}",
        "",
        "Body:",
        body.strip(),
    ]
    return "\n".join(parts)


# Dispatching it ig
def extract_text(file_path: str, pdf_page_range: Optional[Tuple[int, int]] = None) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_pdf_text(file_path, page_range=pdf_page_range)
    elif ext == ".docx":
        return extract_docx_text(file_path)
    elif ext == ".eml":
        return extract_eml_text(file_path)
    elif ext == ".msg":
        return extract_msg_text(file_path)
    else:
        raise UnsupportedFileTypeError(f"Unsupported file extension: {ext}")
