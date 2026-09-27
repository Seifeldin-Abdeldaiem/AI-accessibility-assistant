import type { ScanReport } from "@/lib/types";
import { markdownExportUrl, pdfExportUrl } from "@/lib/api";
import IssueCard from "./IssueCard";
import ManualReviewSection from "./ManualReviewSection";

export default function ScanReportView({ report }: { report: ScanReport }) {
  const { summary } = report;

  return (
    <section aria-labelledby="report-heading">
      <h2 id="report-heading">
        Results for {report.page_title || report.url}
      </h2>
      <p className="issue-meta">
        <a href={report.url} target="_blank" rel="noreferrer">
          {report.url}
        </a>{" "}
        · scanned {new Date(report.scanned_at).toLocaleString()}
      </p>

      <div className="coverage-note">{report.tool_coverage_note}</div>

      <div className="summary-row" aria-label="Issue counts by severity">
        <span className="summary-pill" style={{ background: "var(--color-critical)" }}>
          {summary.critical} critical
        </span>
        <span className="summary-pill" style={{ background: "var(--color-serious)" }}>
          {summary.serious} serious
        </span>
        <span className="summary-pill" style={{ background: "var(--color-moderate)" }}>
          {summary.moderate} moderate
        </span>
        <span className="summary-pill" style={{ background: "var(--color-minor)" }}>
          {summary.minor} minor
        </span>
      </div>

      {report.screenshot_png_base64 && (
        <div className="screenshot-wrap">
          <img
            src={`data:image/png;base64,${report.screenshot_png_base64}`}
            alt={`Screenshot of ${report.page_title || report.url}, with each issue below numbered and boxed on the page`}
          />
        </div>
      )}

      <div className="export-row">
        <a className="secondary" href={markdownExportUrl(report.id)} download>
          Export as Markdown
        </a>
        <a className="secondary" href={pdfExportUrl(report.id)} download>
          Export as PDF
        </a>
      </div>

      {report.groups.length === 0 ? (
        <p>No automated issues found. Remember: this only covers what a scanner can check.</p>
      ) : (
        <ul className="issue-list">
          {report.groups.map((group, i) => (
            <IssueCard key={group.rule_id} group={group} index={i + 1} />
          ))}
        </ul>
      )}

      <ManualReviewSection items={report.manual_review_items} />

      <p className="muted-note" style={{ marginTop: "1.5rem" }}>
        AI review budget: {report.claude_calls_made} call(s) made
        {report.claude_calls_skipped_budget > 0
          ? `, ${report.claude_calls_skipped_budget} issue(s) skipped after the spend cap was reached.`
          : "."}
      </p>
    </section>
  );
}
