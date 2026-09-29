from __future__ import annotations

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    url: str
    # Bring-your-own-key: used only for this one scan's Claude calls, never
    # logged, never written to the stored ScanReport, never echoed back in
    # any response. Falls back to the server's own key (if any) when unset.
    anthropic_api_key: str | None = Field(default=None, repr=False)


class ViolationNode(BaseModel):
    target: str  # CSS selector axe used to identify the element
    html: str  # outerHTML at scan time
    failure_summary: str
    bounding_box: dict | None = None  # {x, y, width, height} in page coords, if captured


class Fix(BaseModel):
    old_html: str
    new_html: str
    note: str | None = None


class Guidance(BaseModel):
    """Built-in, non-AI guidance, always present, so a scan without an
    Anthropic key still reads as a complete report rather than a list of
    findings with "unavailable" notes on each."""

    # Keys from rule_guides.AFFECTED_GROUPS, e.g. "screen-reader".
    affects: list[str]
    summary: str
    steps: list[str]
    example_before: str | None = None
    example_after: str | None = None
    # False when this is the generic fallback built from axe's own text
    # rather than a hand-written guide for this rule.
    curated: bool = True


class ViolationGroup(BaseModel):
    rule_id: str
    impact: str  # minor | moderate | serious | critical
    description: str
    help_text: str
    help_url: str
    wcag_tags: list[str]
    nodes: list[ViolationNode]
    total_node_count: int  # may exceed len(nodes) if truncated

    guidance: Guidance | None = None
    explanation: str | None = None
    fix: Fix | None = None
    fix_verified: bool | None = None
    fix_verification_note: str | None = None
    explanation_error: str | None = None


class ManualReviewItem(BaseModel):
    kind: str  # "alt_text" | "link_text"
    selector: str
    html: str
    reason: str
    suggestion: str | None = None
    suggestion_caveat: str = "AI-suggested — check before using"


class ScanSummary(BaseModel):
    critical: int = 0
    serious: int = 0
    moderate: int = 0
    minor: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.serious + self.moderate + self.minor


class ScanReport(BaseModel):
    id: str
    url: str
    scanned_at: str
    page_title: str
    summary: ScanSummary
    groups: list[ViolationGroup]
    manual_review_items: list[ManualReviewItem]
    screenshot_png_base64: str | None = None
    tool_coverage_note: str
    automated_checks_only: bool = True
    # "off": no key supplied, report uses built-in guidance only.
    # "on": Claude wrote explanations/fixes for at least the top issues.
    # "error": a key was supplied but Anthropic rejected it or failed.
    ai_status: str = "off"
    ai_note: str | None = None
    claude_calls_made: int = 0
    claude_calls_skipped_budget: int = 0
