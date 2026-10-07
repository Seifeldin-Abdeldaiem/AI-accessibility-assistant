"""Wake other free-plan sites when a real visitor opens Unkerb.

Unkerb is kept awake; the owner's other Render services sleep when idle.
When someone opens Unkerb in a browser, the page calls POST /api/wake and
the server pings each configured URL so those sites start booting.

Safety and cost:
- The URLs come only from server config (WAKE_URLS), never from the request,
  so this can't be used to make the server fetch arbitrary addresses.
- At most one round of pings per WAKE_INTERVAL_SECONDS, however many people
  call the endpoint. A woken service stays up for roughly 15 minutes, so
  pinging more often would only spend free hours twice.
"""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)

# A sleeping free Render service can take about a minute to answer.
PING_TIMEOUT_SECONDS = 90.0


class Waker:
    def __init__(self, urls: list[str], interval_seconds: int) -> None:
        self.urls = urls
        self.interval_seconds = interval_seconds
        self._last_started: float | None = None
        # Keeps running ping tasks referenced so they aren't garbage-collected.
        self._tasks: set[asyncio.Task] = set()

    def trigger(self) -> bool:
        """Start a round of pings in the background unless one started recently.
        Returns whether pings were started."""
        if not self.urls:
            return False
        now = time.monotonic()
        if self._last_started is not None and now - self._last_started < self.interval_seconds:
            return False
        self._last_started = now
        task = asyncio.create_task(self._ping_all())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return True

    async def _ping_all(self) -> None:
        async with httpx.AsyncClient(timeout=PING_TIMEOUT_SECONDS, follow_redirects=True) as client:
            await asyncio.gather(*(self._ping(client, url) for url in self.urls))

    async def _ping(self, client: httpx.AsyncClient, url: str) -> None:
        started = time.monotonic()
        try:
            response = await client.get(url)
            logger.info("Woke %s: HTTP %s in %.0fs", url, response.status_code, time.monotonic() - started)
        except Exception as exc:  # a failed wake must never affect Unkerb itself
            logger.info("Wake ping to %s failed after %.0fs: %s", url, time.monotonic() - started, exc)
