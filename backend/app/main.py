from __future__ import annotations

import asyncio
import logging
import uuid
from collections import OrderedDict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from .claude_client import ClaudeClient
from .config import get_settings
from .grouping import build_violation_groups
from .manual_review import find_manual_review_items
from .models import ScanReport, ScanRequest
from .rate_limit import check_and_record, client_ip
from .report import build_report, render_html, render_markdown, render_pdf
from .scanner import ScanBlockedError, scan_session
from .security import UnsafeUrlError, validate_url
from .verifier import verify_fix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="AI Accessibility Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_methods=["*"],
    allow_headers=["*"],
)

_scan_semaphore = asyncio.Semaphore(settings.max_concurrent_scans)
_reports: "OrderedDict[str, ScanReport]" = OrderedDict()


def _store_report(report: ScanReport) -> None:
    _reports[report.id] = report
    while len(_reports) > settings.max_stored_reports:
        _reports.popitem(last=False)


def _get_report_or_404(scan_id: str) -> ScanReport:
    report = _reports.get(scan_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Scan not found (reports are kept in memory only)")
    return report


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "claude_configured": bool(settings.anthropic_api_key)}


@app.post("/api/scan", response_model=ScanReport)
async def create_scan(req: ScanRequest, request: Request) -> ScanReport:
    ip = client_ip(request)
    if not check_and_record(ip, limit_per_hour=settings.max_scans_per_ip_per_hour):
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit reached: this IP has run {settings.max_scans_per_ip_per_hour} "
                "scans in the last hour. Please try again later."
            ),
        )

    try:
        safe_url = validate_url(req.url, allow_private_networks=settings.allow_private_networks)
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    scan_id = uuid.uuid4().hex[:12]
    claude = ClaudeClient(settings, api_key_override=req.anthropic_api_key)

    async with _scan_semaphore:
        try:
            async with scan_session(safe_url, settings) as session:
                groups = build_violation_groups(session.violations)

                # Issues past the cap keep their built-in guidance.
                explain_tasks = [
                    claude.explain_and_fix(group)
                    for group in groups[: settings.max_groups_explained_by_claude]
                ]
                if explain_tasks:
                    await asyncio.gather(*explain_tasks)

                for group in groups:
                    if group.fix:
                        await verify_fix(session.page, group)

                manual_items = await find_manual_review_items(session.page, claude)
                screenshot = await session.screenshot()
                ai_status, ai_note = claude.status()

                report = build_report(
                    scan_id=scan_id,
                    url=session.final_url,
                    page_title=session.page_title,
                    groups=groups,
                    manual_review_items=manual_items,
                    screenshot_png=screenshot,
                    ai_status=ai_status,
                    ai_note=ai_note,
                    claude_calls_made=claude.calls_made,
                    claude_calls_skipped_budget=claude.calls_skipped_budget,
                )
        except ScanBlockedError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from None
        except Exception:
            logger.exception("Scan failed for %s", req.url)
            raise HTTPException(status_code=500, detail="The scan failed unexpectedly. Please try again.") from None

    _store_report(report)
    return report


@app.get("/api/scan/{scan_id}", response_model=ScanReport)
async def get_scan(scan_id: str) -> ScanReport:
    return _get_report_or_404(scan_id)


@app.get("/api/scan/{scan_id}/report.md")
async def get_scan_markdown(scan_id: str) -> PlainTextResponse:
    report = _get_report_or_404(scan_id)
    return PlainTextResponse(render_markdown(report), media_type="text/markdown")


@app.get("/api/scan/{scan_id}/report.pdf")
async def get_scan_pdf(scan_id: str) -> Response:
    report = _get_report_or_404(scan_id)
    html = render_html(report)
    pdf_bytes = await render_pdf(html, settings)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="accessibility-report-{scan_id}.pdf"'},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):  # noqa: ARG001
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Mounted last so every /api route above takes precedence over the site.
if settings.frontend_dir:
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="site")
