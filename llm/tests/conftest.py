import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_pdf(pages: list[str]) -> bytes:
    """Build a minimal valid PDF whose pages contain the given text."""
    objects: list[bytes] = []
    n = len(pages)
    kids = " ".join(f"{3 + i * 2} 0 R" for i in range(n))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    font_id = 3 + n * 2
    for i, text in enumerate(pages):
        content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {4 + i * 2} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return bytes(out)


class FakeGenerator:
    def __init__(self):
        self.calls = []

    def answer(self, questions, contexts):
        self.calls.append((questions, contexts))
        return [f"answer to: {q}" for q in questions]


@pytest.fixture
def settings():
    return Settings(google_api_key="test-key", log_level="WARNING")


@pytest.fixture
def generator():
    return FakeGenerator()


@pytest.fixture
def client(settings, generator):
    pdf = make_pdf(["The grace period for premium payment is thirty days."])
    app = create_app(settings, generator=generator, fetcher=lambda url, s: pdf)
    # Public host name that resolves publicly is not available offline, so
    # bypass DNS for the endpoint tests; SSRF logic is tested separately.
    import app.main as main_module

    original = main_module.validate_public_url
    main_module.validate_public_url = lambda url: None
    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        main_module.validate_public_url = original
