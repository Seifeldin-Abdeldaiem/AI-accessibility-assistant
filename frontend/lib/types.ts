export type Impact = "critical" | "serious" | "moderate" | "minor";

export interface ViolationNode {
  target: string;
  html: string;
  failure_summary: string;
  bounding_box: { x: number; y: number; width: number; height: number } | null;
}

export interface Fix {
  old_html: string;
  new_html: string;
  note: string | null;
}

export interface ViolationGroup {
  rule_id: string;
  impact: Impact;
  description: string;
  help_text: string;
  help_url: string;
  wcag_tags: string[];
  nodes: ViolationNode[];
  total_node_count: number;
  explanation: string | null;
  fix: Fix | null;
  fix_verified: boolean | null;
  fix_verification_note: string | null;
  explanation_error: string | null;
}

export interface ManualReviewItem {
  kind: "alt_text" | "link_text";
  selector: string;
  html: string;
  reason: string;
  suggestion: string | null;
  suggestion_caveat: string;
}

export interface ScanSummary {
  critical: number;
  serious: number;
  moderate: number;
  minor: number;
}

export interface ScanReport {
  id: string;
  url: string;
  scanned_at: string;
  page_title: string;
  summary: ScanSummary;
  groups: ViolationGroup[];
  manual_review_items: ManualReviewItem[];
  screenshot_png_base64: string | null;
  tool_coverage_note: string;
  automated_checks_only: boolean;
  claude_calls_made: number;
  claude_calls_skipped_budget: number;
}

export interface ApiError {
  detail: string;
}
