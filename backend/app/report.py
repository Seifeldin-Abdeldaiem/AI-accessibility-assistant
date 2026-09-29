from __future__ import annotations

import base64
import io
from datetime import datetime, timezone

from jinja2 import Environment, select_autoescape
from PIL import Image, ImageDraw, ImageFont

from .config import Settings
from .models import ScanReport, ScanSummary, ViolationGroup
from .rule_guides import AFFECTED_GROUPS

BRAND_NAME = "Curbcut"

TOOL_COVERAGE_NOTE = (
    "This report only lists what automated checks (axe-core) can detect. "
    "Independent testing has found automated tools catch a minority of "
    "real accessibility failures on their own — this tool does not claim "
    "the page is compliant, only that these specific issues were found. "
    "Keyboard navigation, screen reader use, and zoom/reflow still need a "
    "person to test."
)

# Same values as the frontend's severity tokens, so a printed report and
# the web report read as the same product.
IMPACT_COLORS = {
    "critical": "#b91c1c",
    "serious": "#c2410c",
    "moderate": "#b45309",
    "minor": "#475569",
}
SIGNAL_YELLOW = "#ffc91f"
INK = "#16150f"


def format_wcag(tag: str) -> str:
    """"wcag1410" -> "1.4.10". axe encodes success criteria as digits with
    the first two being principle and guideline, the rest the criterion."""
    digits = tag[4:]
    if len(digits) < 3 or not digits.isdigit():
        return tag
    return f"{digits[0]}.{digits[1]}.{digits[2:]}"


def build_summary(groups: list[ViolationGroup]) -> ScanSummary:
    summary = ScanSummary()
    for g in groups:
        if g.impact == "critical":
            summary.critical += 1
        elif g.impact == "serious":
            summary.serious += 1
        elif g.impact == "moderate":
            summary.moderate += 1
        else:
            summary.minor += 1
    return summary


def annotate_screenshot(png_bytes: bytes, groups: list[ViolationGroup]) -> bytes:
    """Outline the first occurrence of each issue in its severity colour and
    pin a numbered yellow tag to it — the same tag the web report uses on
    each issue card, so "#3 on the page" and "#3 in the list" visibly match."""
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default(size=15)
    except TypeError:
        font = ImageFont.load_default()

    radius = 13
    placed: list[tuple[float, float]] = []
    for idx, group in enumerate(groups, start=1):
        box = next((n.bounding_box for n in group.nodes if n.bounding_box), None)
        if not box:
            continue
        color = IMPACT_COLORS.get(group.impact, IMPACT_COLORS["minor"])
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)

        cx = min(max(x, radius + 2), image.width - radius - 2)
        cy = min(max(y, radius + 2), image.height - radius - 2)
        # Page-level rules (html, body, landmarks) often share a corner;
        # slide a colliding tag sideways so every number stays readable.
        while any(abs(cx - px) < radius * 2 and abs(cy - py) < radius * 2 for px, py in placed):
            cx += radius * 2 + 2
        placed.append((cx, cy))
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=SIGNAL_YELLOW,
            outline=INK,
            width=2,
        )
        label = str(idx)
        text_w = draw.textlength(label, font=font)
        draw.text((cx - text_w / 2, cy - 9), label, fill=INK, font=font)

    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def build_report(
    *,
    scan_id: str,
    url: str,
    page_title: str,
    groups: list[ViolationGroup],
    manual_review_items,
    screenshot_png: bytes | None,
    ai_status: str = "off",
    ai_note: str | None = None,
    claude_calls_made: int = 0,
    claude_calls_skipped_budget: int = 0,
) -> ScanReport:
    annotated = annotate_screenshot(screenshot_png, groups) if screenshot_png else None
    return ScanReport(
        id=scan_id,
        url=url,
        scanned_at=datetime.now(timezone.utc).isoformat(),
        page_title=page_title,
        summary=build_summary(groups),
        groups=groups,
        manual_review_items=manual_review_items,
        screenshot_png_base64=base64.b64encode(annotated).decode() if annotated else None,
        tool_coverage_note=TOOL_COVERAGE_NOTE,
        ai_status=ai_status,
        ai_note=ai_note,
        claude_calls_made=claude_calls_made,
        claude_calls_skipped_budget=claude_calls_skipped_budget,
    )


def _md_text(value: str) -> str:
    """Escape a string for use in Markdown *prose* (never inside a fenced
    code block). Findings quote text straight off the scanned page — its
    alt text, its link text, its <title> — so a malicious page could plant
    raw HTML (e.g. alt="<img src=x onerror=...>") hoping it survives into
    an exported report that someone later opens in a Markdown renderer
    with HTML passthrough enabled. Escaping <, >, and & here treats that
    text as data, never as markup, the same guarantee Jinja2's autoescape
    already gives the HTML/PDF report."""
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _affects_labels(g: ViolationGroup) -> list[str]:
    if not g.guidance:
        return []
    return [AFFECTED_GROUPS.get(k, k) for k in g.guidance.affects]


def render_markdown(report: ScanReport) -> str:
    lines: list[str] = []
    lines.append(f"# {BRAND_NAME} accessibility report: {_md_text(report.page_title or report.url)}")
    lines.append("")
    lines.append(f"- **URL:** {_md_text(report.url)}")
    lines.append(f"- **Scanned:** {report.scanned_at}")
    lines.append(
        f"- **Summary:** {report.summary.critical} critical, {report.summary.serious} serious, "
        f"{report.summary.moderate} moderate, {report.summary.minor} minor"
    )
    if report.ai_status == "on":
        lines.append("- **Fixes:** written by Claude for this page, each re-checked in a real browser")
    lines.append("")
    lines.append(f"> {_md_text(report.tool_coverage_note)}")
    lines.append("")
    if report.ai_note:
        lines.append(f"_{_md_text(report.ai_note)}_")
        lines.append("")

    if report.screenshot_png_base64:
        lines.append("## Page screenshot (numbered to match issues below)")
        lines.append("")
        lines.append(f"![Annotated screenshot](data:image/png;base64,{report.screenshot_png_base64})")
        lines.append("")

    lines.append("## Issues found")
    lines.append("")
    for idx, g in enumerate(report.groups, start=1):
        wcag = ", ".join(format_wcag(t) for t in g.wcag_tags) if g.wcag_tags else "best practice"
        lines.append(
            f"### {idx}. {g.impact.capitalize()} · {_md_text(g.help_text)} · WCAG {wcag} · "
            f"{g.total_node_count} place(s)"
        )
        lines.append("")
        affects = _affects_labels(g)
        if affects:
            lines.append(f"**Affects:** {_md_text(', '.join(affects))}")
            lines.append("")
        summary = g.explanation or (g.guidance.summary if g.guidance else g.description)
        lines.append(_md_text(summary))
        lines.append("")
        if g.nodes:
            lines.append("**Found on the page:**")
            lines.append("")
            lines.append("```html")
            lines.append(g.nodes[0].html)
            lines.append("```")
            lines.append("")
        lines.append("**How to fix:**")
        lines.append("")
        if g.fix:
            lines.append("```diff")
            lines.append(f"- {g.fix.old_html}")
            lines.append(f"+ {g.fix.new_html}")
            lines.append("```")
            if g.fix.note:
                lines.append("")
                lines.append(f"_{_md_text(g.fix.note)}_")
            lines.append("")
            if g.fix_verified is True:
                lines.append(f"✓ **Verified in a real browser:** {_md_text(g.fix_verification_note or '')}")
            elif g.fix_verified is False:
                lines.append(f"✗ **Not verified:** {_md_text(g.fix_verification_note or '')}")
            elif g.fix_verification_note:
                lines.append(f"_{_md_text(g.fix_verification_note)}_")
            lines.append("")
        elif g.guidance:
            for step in g.guidance.steps:
                lines.append(f"- {_md_text(step)}")
            lines.append("")
            if g.guidance.example_before and g.guidance.example_after:
                lines.append("```diff")
                for line in g.guidance.example_before.splitlines():
                    lines.append(f"- {line}")
                for line in g.guidance.example_after.splitlines():
                    lines.append(f"+ {line}")
                lines.append("```")
                lines.append("")
        lines.append(f"[Rule reference]({g.help_url})")
        lines.append("")

    if report.manual_review_items:
        lines.append("## Needs a human look")
        lines.append("")
        lines.append(
            "Automated rules can only tell whether alt text or link text exists, "
            "not whether it's useful. Check these by hand."
        )
        lines.append("")
        for item in report.manual_review_items:
            lines.append(
                f"- **{item.kind.replace('_', ' ')}** (`{item.selector}`): {_md_text(item.reason)}"
            )
            if item.suggestion:
                lines.append(
                    f'  - Suggested: "{_md_text(item.suggestion)}" _{_md_text(item.suggestion_caveat)}_'
                )
        lines.append("")

    lines.append("---")
    lines.append(f"Generated by {BRAND_NAME} · automated checks by axe-core")
    return "\n".join(lines)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{{ brand }} report: {{ report.page_title or report.url }}</title>
<style>
  :root { --ink: #16150f; --paper: #fbf8f1; --line: #e4ddcb; --muted: #5c584b; --signal: #ffc91f; }
  * { box-sizing: border-box; }
  body { font-family: "Atkinson Hyperlegible", -apple-system, "Segoe UI", Roboto, sans-serif; color: var(--ink); background: #fff; max-width: 820px; margin: 0 auto; padding: 0 0.5rem; line-height: 1.5; font-size: 13px; }
  .brandbar { display: flex; align-items: center; gap: 10px; padding: 14px 0; border-bottom: 3px solid var(--ink); margin-bottom: 18px; }
  .mark { width: 26px; height: 26px; border-radius: 7px; background: var(--signal); border: 2px solid var(--ink); position: relative; }
  .mark::after { content: ""; position: absolute; left: 4px; right: 4px; bottom: 5px; height: 9px; background: var(--ink); clip-path: polygon(0 100%, 100% 100%, 100% 0, 45% 0); }
  .brand { font-weight: 800; font-size: 17px; letter-spacing: -0.02em; }
  .brand-sub { margin-left: auto; color: var(--muted); font-size: 11px; }
  h1 { font-size: 22px; margin: 0 0 4px; letter-spacing: -0.02em; }
  h2 { font-size: 16px; margin: 26px 0 10px; }
  .meta { color: var(--muted); }
  .counts { display: flex; gap: 8px; margin: 14px 0; }
  .count { flex: 1; border-radius: 8px; color: #fff; padding: 8px 10px; }
  .count b { display: block; font-size: 20px; line-height: 1; }
  .count span { font-size: 10px; text-transform: uppercase; letter-spacing: .04em; font-weight: 700; }
  .note { background: var(--paper); border: 1px solid var(--line); border-left: 4px solid var(--ink); padding: 10px 12px; border-radius: 0 6px 6px 0; color: var(--muted); }
  img.screenshot { max-width: 100%; border: 1px solid var(--line); border-radius: 6px; }
  .issue { border: 1px solid var(--line); border-left-width: 5px; border-radius: 8px; padding: 12px 14px; margin: 12px 0; page-break-inside: avoid; }
  .head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .num { width: 24px; height: 24px; border-radius: 50%; background: var(--signal); border: 2px solid var(--ink); font-weight: 800; display: inline-flex; align-items: center; justify-content: center; font-size: 12px; }
  .sev { color: #fff; border-radius: 4px; padding: 1px 7px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
  .title { font-weight: 700; font-size: 14px; }
  .sub { color: var(--muted); font-size: 11px; margin: 4px 0 0; }
  .affects { font-size: 11px; margin: 8px 0 0; }
  .affects span { display: inline-block; border: 1px solid var(--line); background: var(--paper); border-radius: 999px; padding: 1px 8px; margin: 2px 4px 0 0; }
  h3 { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); margin: 12px 0 4px; }
  pre { background: #16150f; color: #efe9da; padding: 8px 10px; border-radius: 6px; white-space: pre-wrap; word-break: break-all; font-size: 10.5px; margin: 0; }
  .del { color: #ffaaa0; } .add { color: #9fe6b0; }
  ul { margin: 0; padding-left: 18px; }
  .stamp { display: inline-block; margin-top: 8px; background: var(--ink); color: #fbf8f1; border-radius: 999px; padding: 3px 10px; font-weight: 700; font-size: 11px; }
  .stamp b { color: var(--signal); }
  .unverified { color: #b91c1c; font-weight: 700; margin-top: 8px; }
  .manual { border-top: 1px solid var(--line); padding: 8px 0; }
  a { color: var(--ink); }
  footer { margin: 28px 0 10px; padding-top: 10px; border-top: 1px solid var(--line); color: var(--muted); font-size: 11px; }
</style>
</head>
<body>
  <div class="brandbar"><span class="mark"></span><span class="brand">{{ brand }}</span><span class="brand-sub">Accessibility report</span></div>
  <h1>{{ report.page_title or report.url }}</h1>
  <div class="meta">{{ report.url }} · scanned {{ report.scanned_at[:16].replace('T', ' ') }} UTC</div>

  <div class="counts">
    <div class="count" style="background:{{ colors.critical }}"><b>{{ report.summary.critical }}</b><span>Critical</span></div>
    <div class="count" style="background:{{ colors.serious }}"><b>{{ report.summary.serious }}</b><span>Serious</span></div>
    <div class="count" style="background:{{ colors.moderate }}"><b>{{ report.summary.moderate }}</b><span>Moderate</span></div>
    <div class="count" style="background:{{ colors.minor }}"><b>{{ report.summary.minor }}</b><span>Minor</span></div>
  </div>
  <div class="note">{{ report.tool_coverage_note }}</div>
  {% if report.ai_note %}<p class="meta">{{ report.ai_note }}</p>{% endif %}

  {% if report.screenshot_png_base64 %}
  <h2>Where the issues are</h2>
  <img class="screenshot" alt="Screenshot of the page with each issue numbered" src="data:image/png;base64,{{ report.screenshot_png_base64 }}">
  {% endif %}

  <h2>Issues found</h2>
  {% for g in report.groups %}
  <div class="issue" style="border-left-color:{{ colors.get(g.impact, colors.minor) }}">
    <div class="head">
      <span class="num">{{ loop.index }}</span>
      <span class="sev" style="background:{{ colors.get(g.impact, colors.minor) }}">{{ g.impact }}</span>
      <span class="title">{{ g.help_text }}</span>
    </div>
    <p class="sub">WCAG {% if g.wcag_tags %}{{ g.wcag_tags | map('wcag') | join(', ') }}{% else %}best practice{% endif %} · {{ g.total_node_count }} place{{ '' if g.total_node_count == 1 else 's' }} on this page</p>
    {% if g.guidance and g.guidance.affects %}
    <p class="affects">Affects {% for a in g.guidance.affects %}<span>{{ groups_labels.get(a, a) }}</span>{% endfor %}</p>
    {% endif %}
    <p>{{ g.explanation or (g.guidance.summary if g.guidance else g.description) }}</p>
    {% if g.nodes %}<h3>Found on the page</h3><pre>{{ g.nodes[0].html }}</pre>{% endif %}
    <h3>How to fix</h3>
    {% if g.fix %}
      <pre><span class="del">- {{ g.fix.old_html }}</span>
<span class="add">+ {{ g.fix.new_html }}</span></pre>
      {% if g.fix.note %}<p><em>{{ g.fix.note }}</em></p>{% endif %}
      {% if g.fix_verified == true %}<div class="stamp"><b>✓</b> Verified in a real browser</div>
      {% elif g.fix_verified == false %}<p class="unverified">✗ Not verified: {{ g.fix_verification_note }}</p>{% endif %}
    {% elif g.guidance %}
      <ul>{% for s in g.guidance.steps %}<li>{{ s }}</li>{% endfor %}</ul>
      {% if g.guidance.example_before and g.guidance.example_after %}
      <pre style="margin-top:8px"><span class="del">{% for l in g.guidance.example_before.splitlines() %}- {{ l }}
{% endfor %}</span><span class="add">{% for l in g.guidance.example_after.splitlines() %}+ {{ l }}
{% endfor %}</span></pre>
      {% endif %}
    {% endif %}
  </div>
  {% endfor %}

  {% if report.manual_review_items %}
  <h2>Needs a human look</h2>
  <p class="meta">Automated rules can only tell whether alt text or link text exists, not whether it's useful.</p>
  {% for item in report.manual_review_items %}
  <div class="manual">
    <strong>{{ item.kind.replace('_', ' ') }}</strong> (<code>{{ item.selector }}</code>): {{ item.reason }}
    {% if item.suggestion %}<br>Suggested: &ldquo;{{ item.suggestion }}&rdquo; <em>{{ item.suggestion_caveat }}</em>{% endif %}
  </div>
  {% endfor %}
  {% endif %}

  <footer>Generated by {{ brand }} · automated checks by axe-core · not a compliance certificate</footer>
</body>
</html>
"""

_env = Environment(autoescape=select_autoescape(["html"], default_for_string=True))
_env.filters["wcag"] = format_wcag
_template = _env.from_string(_HTML_TEMPLATE)


def render_html(report: ScanReport) -> str:
    return _template.render(
        report=report, colors=IMPACT_COLORS, brand=BRAND_NAME, groups_labels=AFFECTED_GROUPS
    )


async def render_pdf(html: str, settings: Settings) -> bytes:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")
            return await page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "14mm", "bottom": "14mm", "left": "12mm", "right": "12mm"},
            )
        finally:
            await browser.close()
