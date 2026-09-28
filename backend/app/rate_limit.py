"""A minimal in-memory per-IP rate limiter for the public scan endpoint.

This is deliberately simple rather than pulling in a dependency: a scan is
expensive (a full headless-browser navigation, possibly a Claude call), and
this is a no-signin public tool, so without *some* cap a single visitor
could queue unlimited scans and either run up someone else's Claude bill
(if the server has its own key configured) or just peg the server's CPU
and memory with concurrent Chromium instances.

Being in-memory, this resets on restart and doesn't coordinate across
multiple server processes — fine for a single-instance deployment, a real
limitation the moment this needs to scale horizontally (at that point, a
shared store like Redis is the right fix, not a bigger in-memory dict).
"""

from __future__ import annotations

import time
from collections import OrderedDict

from fastapi import Request

_RATE_LIMIT_WINDOW_SECONDS = 3600.0
# Bounds memory from an unbounded number of distinct IPs over a long
# server lifetime; least-recently-active IP is evicted first.
_MAX_TRACKED_IPS = 5000

_hits: "OrderedDict[str, list[float]]" = OrderedDict()


def client_ip(request: Request) -> str:
    """Best-effort client IP. Most PaaS deployments (Render, Fly, etc.) sit
    behind an edge proxy that sets X-Forwarded-For; without honoring it,
    every visitor would appear to share the proxy's IP and rate limiting
    would be meaningless in production. This trusts the first hop in that
    header, which is fine for a single reverse-proxy deployment — a
    multi-hop setup would need to pick a more specific trusted hop."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_and_record(ip: str, *, limit_per_hour: int) -> bool:
    """Returns True if this request is allowed (and records it), False if
    the caller has hit the per-hour limit."""
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW_SECONDS

    timestamps = _hits.get(ip)
    if timestamps is None:
        timestamps = []
    else:
        _hits.move_to_end(ip)

    while timestamps and timestamps[0] < window_start:
        timestamps.pop(0)

    allowed = len(timestamps) < limit_per_hour
    if allowed:
        timestamps.append(now)
    _hits[ip] = timestamps

    while len(_hits) > _MAX_TRACKED_IPS:
        _hits.popitem(last=False)

    return allowed
