from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import Browser, Page, Playwright, Route, async_playwright

from .config import Settings
from .security import SafeUrl, is_request_url_safe

AXE_JS_PATH = Path(__file__).parent / "static" / "axe.min.js"

# Schemes a page legitimately uses internally that never touch the network
# and therefore can't be used for SSRF; these skip the per-request check.
_NON_NETWORK_SCHEMES = {"data", "blob", "about", "chrome-error", "chrome-extension"}


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


async def _guard_route(route: Route, allow_private_networks: bool) -> None:
    request = route.request
    parsed = urlsplit(request.url)
    if parsed.scheme in _NON_NETWORK_SCHEMES:
        await route.continue_()
        return
    if parsed.scheme not in ("http", "https"):
        await route.abort()
        return
    if is_request_url_safe(request.url, allow_private_networks=allow_private_networks):
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
                    wait_until="networkidle",
                    timeout=settings.scan_timeout_seconds * 1000,
                )
            except Exception as exc:
                raise ScanBlockedError(f"Could not load the page: {exc}") from None
            if response is None:
                raise ScanBlockedError("The page did not respond")

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
