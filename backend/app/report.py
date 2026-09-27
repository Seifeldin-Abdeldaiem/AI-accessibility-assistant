from __future__ import annotations

import base64
import io
from datetime import datetime, timezone

from jinja2 import Environment, select_autoescape
from PIL import Image, ImageDraw, ImageFont

from .config import Settings
from .models import ScanReport, ScanSummary, ViolationGroup

TOOL_COVERAGE_NOTE = (
    "This report only lists what automated checks (axe-core) can detect. "
    "Independent testing has found automated tools catch a minority of "
    "real accessibility failures on their own — this tool does not claim "
    "the page is compliant, only that these specific issues were found. "
    "Keyboard navigation, screen reader use, and zoom/reflow still need a "
    "person to test."
)

IMPACT_COLORS = {
    "critical": "#b91c1c",
    "serious": "#c2410c",
    "moderate": "#a16207",
    "minor": "#4b5563",
}


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
    """Draw a numbered box over the first occurrence of each violation group
    that has a captured bounding box, so the report reads like "here's what
    #4 on the list looks like on the page" rather than a bare list."""
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default(size=16)
    except TypeError:
        font = ImageFont.load_default()

    for idx, group in enumerate(groups, start=1):
        box = next((n.bounding_box for n in group.nodes if n.bounding_box), None)
        if not box:
            continue
        color = IMPACT_COLORS.get(group.impact, "#4b5563")
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
        label = str(idx)
        label_w = draw.textlength(label, font=font) + 8
        draw.rectangle([x, max(0, y - 20), x + label_w, y], fill=color)
        draw.text((x + 4, max(0, y - 19)), label, fill="white", font=font)

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
    claude_calls_made: int,
    claude_calls_skipped_budget: int,
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


def render_markdown(report: ScanReport) -> str:
    lines: list[str] = []
    lines.append(f"# Accessibility report: {_md_text(report.page_title or report.url)}")
    lines.append("")
    lines.append(f"- **URL:** {_md_text(report.url)}")
    lines.append(f"- **Scanned:** {report.scanned_at}")
    lines.append(
        f"- **Summary:** {report.summary.critical} critical, {report.summary.serious} serious, "
        f"{report.summary.moderate} moderate, {report.summary.minor} minor"
    )
    lines.append("")
    lines.append(f"> {_md_text(report.tool_coverage_note)}")
    lines.append("")

    if report.screenshot_png_base64:
        lines.append("## Page screenshot (numbered to match issues below)")
        lines.append("")
        lines.append(f"![Annotated screenshot](data:image/png;base64,{report.screenshot_png_base64})")
        lines.append("")

    lines.append("## Issues found")
    lines.append("")
    for idx, g in enumerate(report.groups, start=1):
        wcag = ", ".join(g.wcag_tags) if g.wcag_tags else "n/a"
        lines.append(
            f"### {idx}. {g.impact.capitalize()} · {_md_text(g.help_text)} · WCAG {wcag} · "
            f"{g.total_node_count} place(s)"
        )
        lines.append("")
        if g.explanation:
            lines.append(_md_text(g.explanation))
        elif g.explanation_error:
            lines.append(f"_{_md_text(g.explanation_error)}_")
        lines.append("")
        if g.nodes:
            lines.append("```html")
            lines.append(g.nodes[0].html)
            lines.append("```")
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
                lines.append(f"✓ **Fix checked:** {_md_text(g.fix_verification_note or '')}")
            elif g.fix_verified is False:
                lines.append(f"✗ **Fix not verified:** {_md_text(g.fix_verification_note or '')}")
            elif g.fix_verification_note:
                lines.append(f"_{_md_text(g.fix_verification_note)}_")
            lines.append("")
        lines.append(f"[Learn more about this rule]({g.help_url})")
        lines.append("")

    if report.manual_review_items:
        lines.append("## Needs a human look")
        lines.append("")
        lines.append(
            "Automated rules can't judge these — Claude suggested wording based on "
            "the image or surrounding text, but check it before using it."
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
    lines.append(
        f"AI review budget: {report.claude_calls_made} call(s) made"
        + (
            f", {report.claude_calls_skipped_budget} issue(s) skipped after the spend cap was reached."
            if report.claude_calls_skipped_budget
            else "."
        )
    )
    return "\n".join(lines)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Accessibility report: {{ report.page_title or report.url }}</title>
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; color: #111827; max-width: 860px; margin: 2rem auto; padding: 0 1rem; }
  h1 { font-size: 1.5rem; }
  .meta { color: #4b5563; font-size: 0.9rem; }
  .coverage-note { background: #f3f4f6; border-left: 4px solid #6b7280; padding: 0.75rem 1rem; margin: 1rem 0; font-size: 0.9rem; }
  img.screenshot { max-width: 100%; border: 1px solid #e5e7eb; border-radius: 4px; }
  .issue { border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin: 1rem 0; page-break-inside: avoid; }
  .badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 4px; color: white; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
  pre { background: #0b1021; color: #e5e7eb; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; }
  .diff-old { color: #fca5a5; }
  .diff-new { color: #86efac; }
  .verified-yes { color: #15803d; font-weight: 600; }
  .verified-no { color: #b91c1c; font-weight: 600; }
  .manual-item { border-top: 1px solid #e5e7eb; padding: 0.75rem 0; }
</style>
</head>
<body>
  <h1>Accessibility report: {{ report.page_title or report.url }}</h1>
  <div class="meta">
    {{ report.url }} · scanned {{ report.scanned_at }}<br>
    {{ report.summary.critical }} critical, {{ report.summary.serious }} serious,
    {{ report.summary.moderate }} moderate, {{ report.summary.minor }} minor
  </div>
  <div class="coverage-note">{{ report.tool_coverage_note }}</div>

  {% if report.screenshot_png_base64 %}
  <h2>Page screenshot</h2>
  <img class="screenshot" src="data:image/png;base64,{{ report.screenshot_png_base64 }}">
  {% endif %}

  <h2>Issues found</h2>
  {% for g in report.groups %}
  <div class="issue">
    <span class="badge" style="background:{{ colors.get(g.impact, '#4b5563') }}">{{ g.impact }}</span>
    <strong>{{ loop.index }}. {{ g.help_text }}</strong>
    · WCAG {{ g.wcag_tags | join(', ') if g.wcag_tags else 'n/a' }}
    · {{ g.total_node_count }} place(s)
    <p>{% if g.explanation %}{{ g.explanation }}{% elif g.explanation_error %}<em>{{ g.explanation_error }}</em>{% endif %}</p>
    {% if g.nodes %}<pre>{{ g.nodes[0].html }}</pre>{% endif %}
    {% if g.fix %}
      <pre><span class="diff-old">- {{ g.fix.old_html }}</span>
<span class="diff-new">+ {{ g.fix.new_html }}</span></pre>
      {% if g.fix.note %}<p><em>{{ g.fix.note }}</em></p>{% endif %}
      {% if g.fix_verified == true %}<p class="verified-yes">✓ Fix checked: {{ g.fix_verification_note }}</p>
      {% elif g.fix_verified == false %}<p class="verified-no">✗ Fix not verified: {{ g.fix_verification_note }}</p>
      {% elif g.fix_verification_note %}<p><em>{{ g.fix_verification_note }}</em></p>{% endif %}
    {% endif %}
    <p><a href="{{ g.help_url }}">Learn more about this rule</a></p>
  </div>
  {% endfor %}

  {% if report.manual_review_items %}
  <h2>Needs a human look</h2>
  <p>Automated rules can't judge these — Claude suggested wording based on the image or surrounding text, but check it before using it.</p>
  {% for item in report.manual_review_items %}
  <div class="manual-item">
    <strong>{{ item.kind.replace('_', ' ') }}</strong> (<code>{{ item.selector }}</code>): {{ item.reason }}
    {% if item.suggestion %}<br>Suggested: &ldquo;{{ item.suggestion }}&rdquo; <em>{{ item.suggestion_caveat }}</em>{% endif %}
  </div>
  {% endfor %}
  {% endif %}

  <hr>
  <p class="meta">AI review budget: {{ report.claude_calls_made }} call(s) made
  {% if report.claude_calls_skipped_budget %}, {{ report.claude_calls_skipped_budget }} issue(s) skipped after the spend cap was reached.{% else %}.{% endif %}</p>
</body>
</html>
"""

_env = Environment(autoescape=select_autoescape(["html"]))
_template = _env.from_string(_HTML_TEMPLATE)


def render_html(report: ScanReport) -> str:
    return _template.render(report=report, colors=IMPACT_COLORS)


async def render_pdf(html: str, settings: Settings) -> bytes:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")
            return await page.pdf(format="A4", margin={"top": "16mm", "bottom": "16mm", "left": "12mm", "right": "12mm"})
        finally:
            await browser.close()
