from __future__ import annotations

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    url: str


class ViolationNode(BaseModel):
    target: str  # CSS selector axe used to identify the element
    html: str  # outerHTML at scan time
    failure_summary: str
    bounding_box: dict | None = None  # {x, y, width, height} in page coords, if captured


class Fix(BaseModel):
    old_html: str
    new_html: str
    note: str | None = None


class ViolationGroup(BaseModel):
    rule_id: str
    impact: str  # minor | moderate | serious | critical
    description: str
    help_text: str
    help_url: str
    wcag_tags: list[str]
    nodes: list[ViolationNode]
    total_node_count: int  # may exceed len(nodes) if truncated

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
    claude_calls_made: int = 0
    claude_calls_skipped_budget: int = 0
