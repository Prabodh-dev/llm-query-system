import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import app.pdf as pdf_module
from app.config import Settings
from app.errors import DocumentFetchError, DocumentTooLargeError, UnsafeURLError
from app.security import validate_public_url as real_validate


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/ok":
            body = b"%PDF-1.4 hello"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/big":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"x" * 5000)
        elif self.path == "/missing":
            self.send_response(404)
            self.end_headers()
        elif self.path == "/to-metadata":
            self.send_response(302)
            self.send_header("Location", "http://169.254.169.254/latest")
            self.end_headers()
        elif self.path == "/loop":
            self.send_response(302)
            self.send_header("Location", "/loop")
            self.end_headers()


@pytest.fixture
def server(monkeypatch):
    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"

    # Allow only the local test server; everything else goes through the real check.
    def validate(url):
        if not url.startswith(base):
            real_validate(url)

    monkeypatch.setattr(pdf_module, "validate_public_url", validate)
    yield base
    httpd.shutdown()


def test_downloads(server):
    assert pdf_module.download_pdf(server + "/ok", Settings()).startswith(b"%PDF")


def test_size_limit_enforced_while_streaming(server):
    with pytest.raises(DocumentTooLargeError):
        pdf_module.download_pdf(server + "/big", Settings(max_pdf_bytes=1000))


def test_non_200(server):
    with pytest.raises(DocumentFetchError):
        pdf_module.download_pdf(server + "/missing", Settings())


def test_redirect_to_private_address_blocked(server):
    with pytest.raises(UnsafeURLError):
        pdf_module.download_pdf(server + "/to-metadata", Settings())


def test_redirect_loop_stops(server):
    with pytest.raises(DocumentFetchError):
        pdf_module.download_pdf(server + "/loop", Settings())
