import pytest

from app.errors import UnsafeURLError
from app.security import validate_public_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/a.pdf",
        "http://localhost/a.pdf",
        "http://10.0.0.5/a.pdf",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/a.pdf",
        "http://[::ffff:127.0.0.1]/a.pdf",
        "file:///etc/passwd",
        "ftp://example.com/a.pdf",
        "http:///nohost",
    ],
)
def test_blocked(url):
    with pytest.raises(UnsafeURLError):
        validate_public_url(url)


def test_public_ip_allowed():
    validate_public_url("https://93.184.216.34/a.pdf")
