from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import Browser, Page, Playwright, Route, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .config import Settings
from .security import SafeUrl, is_request_url_safe

logger = logging.getLogger(__name__)

AXE_JS_PATH = Path(__file__).parent / "static" / "axe.min.js"

# Schemes a page legitimately uses internally that never touch the network
# and therefore can't be used for SSRF; these skip the per-request check.
_NON_NETWORK_SCHEMES = {"data", "blob", "about", "chrome-error", "chrome-extension"}

# Video and audio never change what axe checks (it reads the DOM, not the
# stream), but they cost a lot of memory and bandwidth on a small server.
_SKIPPED_RESOURCE_TYPES = {"media"}

# Very long pages (news homepages) make enormous full-page screenshots that
# can exhaust a 512 MB server. Issues further down are still reported; they
# just aren't pinned on the image.
MAX_SCREENSHOT_HEIGHT = 6000

# After the HTML has loaded, how long to let the rest of the page settle.
# Busy sites (ads, analytics, live tickers) may never go fully quiet, so
# these are best-effort waits, not requirements.
_SETTLE_WAITS_MS = (("load", 15_000), ("networkidle", 5_000))


@dataclass
class RawViolationNode:
    target: str
    html: str
    failure_summary: str
    bounding_box: dict | None = None


@dataclass
class RawViolation:
    rule_id: str
    impact: str
    description: str
    help_text: str
    help_url: str
    tags: list[str]
    nodes: list[RawViolationNode] = field(default_factory=list)
    total_node_count: int = 0


class ScanBlockedError(RuntimeError):
    """Raised when navigation was blocked or failed outright."""


def _load_error_message(exc: Exception, timeout_seconds: int) -> str:
    """Turn a Playwright navigation error into something a visitor can act on."""
    text = str(exc)
    if isinstance(exc, PlaywrightTimeoutError) or "Timeout" in text:
        return (
            f"That page took longer than {timeout_seconds} seconds to start loading. "
            "It may be slow or blocking automated visitors. Please try again."
        )
    if "ERR_NAME_NOT_RESOLVED" in text:
        return "We couldn't find that website. Check the address and try again."
    if "ERR_CONNECTION_REFUSED" in text or "ERR_CONNECTION_RESET" in text:
        return "That website refused the connection. Please try again later."
    if "ERR_CERT" in text or "SSL" in text:
        return "That website's security certificate isn't valid, so we didn't load it."
    if "ERR_ABORTED" in text or "ERR_BLOCKED" in text:
        return "That page couldn't be loaded safely, so it wasn't scanned."
    return "We couldn't load that page. Check the address and try again."


async def _guard_route(route: Route, allow_private_networks: bool) -> None:
    request = route.request
    parsed = urlsplit(request.url)
    if parsed.scheme in _NON_NETWORK_SCHEMES:
        await route.continue_()
        return
    if parsed.scheme not in ("http", "https"):
        await route.abort()
        return
    if request.resource_type in _SKIPPED_RESOURCE_TYPES:
        await route.abort()
        return
    # The check resolves DNS, which blocks; keep it off the event loop so a
    # page with hundreds of requests doesn't stall everything else.
    if await asyncio.to_thread(
        is_request_url_safe, request.url, allow_private_networks=allow_private_networks
    ):
        await route.continue_()
    else:
        await route.abort()


async def _run_axe(page: Page, settings: Settings) -> list[RawViolation]:
    await page.add_script_tag(path=str(AXE_JS_PATH))
    axe_results = await page.evaluate(
        """async () => {
            const results = await axe.run(document, { resultTypes: ['violations'] });
            return results.violations;
        }"""
    )

    violations: list[RawViolation] = []
    for v in axe_results:
        nodes: list[RawViolationNode] = []
        for n in v["nodes"][: settings.max_violation_nodes_per_rule]:
            target_selector = n["target"][0] if n.get("target") else None
            bbox = None
            if target_selector:
                try:
                    locator = page.locator(target_selector).first
                    box = await locator.bounding_box(timeout=2000)
                    if box:
                        bbox = box
                except Exception:
                    bbox = None
            nodes.append(
                RawViolationNode(
                    target=target_selector or "",
                    html=n.get("html", ""),
                    failure_summary=n.get("failureSummary", ""),
                    bounding_box=bbox,
                )
            )
        violations.append(
            RawViolation(
                rule_id=v["id"],
                impact=v.get("impact") or "moderate",
                description=v.get("description", ""),
                help_text=v.get("help", ""),
                help_url=v.get("helpUrl", ""),
                tags=v.get("tags", []),
                nodes=nodes,
                total_node_count=len(v["nodes"]),
            )
        )
    return violations


@dataclass
class ScanSession:
    """Holds the live page open for the rest of the pipeline (fix
    verification, manual-review screenshots) after the initial axe run, so
    those steps see the same DOM the scan saw instead of re-fetching the
    page and risking a different result (A/B tests, ads, live data)."""

    page: Page
    page_title: str
    final_url: str
    violations: list[RawViolation]

    async def screenshot(self) -> bytes:
        height = await self.page.evaluate(
            "Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)"
        )
        width = self.page.viewport_size["width"] if self.page.viewport_size else 1366
        if height > MAX_SCREENSHOT_HEIGHT:
            return await self.page.screenshot(
                full_page=True,
                type="png",
                clip={"x": 0, "y": 0, "width": width, "height": MAX_SCREENSHOT_HEIGHT},
            )
        return await self.page.screenshot(full_page=True, type="png")


@asynccontextmanager
async def scan_session(safe_url: SafeUrl, settings: Settings):
    if settings.playwright_browsers_path:
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", settings.playwright_browsers_path)

    async with async_playwright() as pw:
        pw: Playwright
        browser: Browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            context = await browser.new_context(
                viewport={"width": 1366, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (compatible; AccessibilityAssistant/0.1; "
                    "+https://github.com/) AccessibilityAudit"
                ),
            )
            page: Page = await context.new_page()

            await page.route(
                "**/*",
                lambda route: _guard_route(route, settings.allow_private_networks),
            )

            try:
                response = await page.goto(
                    safe_url.url,
                    wait_until="domcontentloaded",
                    timeout=settings.scan_timeout_seconds * 1000,
                )
            except Exception as exc:
                logger.info("Navigation failed for %s: %s", safe_url.url, exc)
                raise ScanBlockedError(
                    _load_error_message(exc, settings.scan_timeout_seconds)
                ) from None
            if response is None:
                raise ScanBlockedError("The page did not respond. Please try again.")

            for state, wait_ms in _SETTLE_WAITS_MS:
                try:
                    await page.wait_for_load_state(state, timeout=wait_ms)
                except PlaywrightTimeoutError:
                    pass

            violations = await _run_axe(page, settings)
            title = await page.title()

            yield ScanSession(
                page=page,
                page_title=title,
                final_url=page.url,
                violations=violations,
            )
        finally:
            await browser.close()
