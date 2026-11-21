"""Guards against server-side request forgery (SSRF) on user-supplied URLs."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from .errors import UnsafeURLError

_DEFAULT_PORTS = {"http": 80, "https": 443}


def validate_public_url(url: str) -> None:
    """Raise UnsafeURLError unless `url` is http(s) and resolves only to public IPs."""
    parsed = urlparse(url)
    if parsed.scheme not in _DEFAULT_PORTS:
        raise UnsafeURLError("Only http and https document URLs are allowed")
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("Document URL has no host")

    try:
        port = parsed.port or _DEFAULT_PORTS[parsed.scheme]
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, ValueError, UnicodeError) as exc:
        raise UnsafeURLError("Document host could not be resolved") from exc

    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if getattr(address, "ipv4_mapped", None):
            address = address.ipv4_mapped
        if not address.is_global:
            raise UnsafeURLError("Document URL points to a non-public address")
