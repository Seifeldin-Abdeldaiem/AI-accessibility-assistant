"""SSRF protection for the URL a user submits to be scanned.

Any tool that fetches a URL supplied by a stranger can be turned into a
proxy onto the host's internal network (cloud metadata endpoints, internal
admin panels, etc). We defend in two layers:

1. Before navigation: resolve the hostname and reject anything that isn't a
   public, routable IP address.
2. During navigation: every request the browser makes (including redirects
   and subresources) is re-checked the same way via Playwright's request
   routing, which also closes the DNS-rebinding gap (a hostname that
   resolves to a public IP at check time but a private one at connect
   time).
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

ALLOWED_SCHEMES = {"http", "https"}

# Hostnames that resolve to "here" no matter what DNS says.
BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
}


class UnsafeUrlError(ValueError):
    """Raised when a submitted URL is not safe to fetch server-side."""


@dataclass(frozen=True)
class SafeUrl:
    url: str
    hostname: str
    resolved_ips: tuple[str, ...]


def _is_public_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        return False
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return _is_public_ip(str(ip.ipv4_mapped))
    return True


def resolve_hostname(hostname: str) -> tuple[str, ...]:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Could not resolve host '{hostname}': {exc}") from None
    ips = sorted({info[4][0] for info in infos})
    if not ips:
        raise UnsafeUrlError(f"Host '{hostname}' did not resolve to any address")
    return tuple(ips)


def validate_url(url: str, *, allow_private_networks: bool = False) -> SafeUrl:
    """Validate a user-submitted URL. Raises UnsafeUrlError if it isn't safe.

    Set allow_private_networks only for local development against a
    localhost test fixture — never in a deployment reachable by others.
    """
    parts = urlsplit(url.strip())

    if parts.scheme not in ALLOWED_SCHEMES:
        raise UnsafeUrlError("URL must start with http:// or https://")
    if not parts.hostname:
        raise UnsafeUrlError("URL is missing a host")
    if parts.username or parts.password:
        raise UnsafeUrlError("URLs with embedded credentials are not allowed")

    hostname = parts.hostname.lower()

    if allow_private_networks:
        ips = resolve_hostname(hostname)
        return SafeUrl(url=url, hostname=hostname, resolved_ips=ips)

    if hostname in BLOCKED_HOSTNAMES:
        raise UnsafeUrlError(f"Host '{hostname}' is not allowed")

    ips = resolve_hostname(hostname)
    unsafe_ips = [ip for ip in ips if not _is_public_ip(ip)]
    if unsafe_ips:
        raise UnsafeUrlError(
            f"Host '{hostname}' resolves to a non-public address ({unsafe_ips[0]}) "
            "and cannot be scanned"
        )
    return SafeUrl(url=url, hostname=hostname, resolved_ips=ips)


def is_request_url_safe(url: str, *, allow_private_networks: bool = False) -> bool:
    """Cheaper re-check used on every in-page request/redirect while scanning."""
    try:
        validate_url(url, allow_private_networks=allow_private_networks)
        return True
    except UnsafeUrlError:
        return False
    except Exception:
        # Data URLs, about:blank, blob: etc. have no hostname to resolve;
        # urlsplit won't raise, resolve_hostname would. Treat anything that
        # isn't http(s) with a resolvable host as unsafe to route to the
        # network, but harmless local schemes (data:, blob:, about:) are
        # handled separately by the caller before this is invoked.
        return False
