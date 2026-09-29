"use client";

import type { ScanReport } from "@/lib/types";
import { markdownExportUrl, pdfExportUrl } from "@/lib/api";
import { PEOPLE, peopleAffected } from "@/lib/people";
import {
  AlertIcon,
  CheckCircleIcon,
  CheckIcon,
  DownloadIcon,
  InfoIcon,
  PersonIcon,
  RefreshIcon,
  SparkleIcon,
} from "./icons";
import IssueCard from "./IssueCard";
import ManualReviewSection from "./ManualReviewSection";

const SEVERITIES = [
  { key: "critical", label: "Critical", color: "var(--critical)" },
  { key: "serious", label: "Serious", color: "var(--serious)" },
  { key: "moderate", label: "Moderate", color: "var(--moderate)" },
  { key: "minor", label: "Minor", color: "var(--minor)" },
] as const;

interface Props {
  report: ScanReport;
  headingRef: React.Ref<HTMLHeadingElement>;
  onRequestKey: () => void;
  onNewScan: () => void;
}

function openIssue(index: number) {
  const details = document.getElementById(`issue-${index}-details`) as HTMLDetailsElement | null;
  if (details) details.open = true;
}

export default function ScanReportView({ report, headingRef, onRequestKey, onNewScan }: Props) {
  const { summary, groups } = report;
  const total = groups.length;
  const places = groups.reduce((sum, g) => sum + g.total_node_count, 0);
  const people = peopleAffected(groups).slice(0, 6);
  const scannedAt = new Date(report.scanned_at).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <section className="report" aria-labelledby="report-heading">
      <div className="container">
        <div className="report-head">
          <div>
            <p className="eyebrow">
              <span className="eyebrow-dot" aria-hidden="true" />
              Your report
            </p>
            <h2 id="report-heading" ref={headingRef} tabIndex={-1}>
              {report.page_title || report.url}
            </h2>
            <p className="report-url">
              <a href={report.url} target="_blank" rel="noreferrer">
                {report.url}
                <span className="visually-hidden"> (opens in a new tab)</span>
              </a>{" "}
              · scanned {scannedAt}
            </p>
          </div>
          <div className="report-actions">
            <a className="btn btn-ghost btn-sm" href={pdfExportUrl(report.id)} download>
              <DownloadIcon size={16} /> PDF
            </a>
            <a className="btn btn-ghost btn-sm" href={markdownExportUrl(report.id)} download>
              <DownloadIcon size={16} /> Markdown
            </a>
            <button type="button" className="btn btn-ghost btn-sm" onClick={onNewScan}>
              <RefreshIcon size={16} /> New scan
            </button>
          </div>
        </div>

        {report.ai_status === "on" && (
          <p className="ai-line">
            <span className="stamp">
              <span className="stamp-check">
                <CheckIcon size={14} />
              </span>
              Fixes written by Claude, re-checked in a real browser
            </span>
            {report.ai_note && <span>{report.ai_note}</span>}
          </p>
        )}
        {report.ai_status === "error" && report.ai_note && (
          <p className="ai-line error">
            <AlertIcon size={18} />
            {report.ai_note}
          </p>
        )}

        <div className="overview">
          <div className="panel">
            <h3>What we found</h3>
            <div className="total">
              <span className="total-num">{total}</span>
              <span className="total-label">
                {total === 1 ? "type of problem" : "types of problem"}
              </span>
            </div>
            {total > 0 && (
              <div className="sev-bar" aria-hidden="true">
                {SEVERITIES.map(({ key, color }) =>
                  summary[key] > 0 ? (
                    <span
                      key={key}
                      style={{ width: `${(summary[key] / total) * 100}%`, background: color }}
                    />
                  ) : null
                )}
              </div>
            )}
            <ul className="sev-legend">
              {SEVERITIES.map(({ key, label, color }) => (
                <li key={key}>
                  <b>{summary[key]}</b>
                  <span>
                    <i style={{ background: color }} aria-hidden="true" />
                    {label}
                  </span>
                </li>
              ))}
            </ul>
            {total > 0 && (
              <p className="places-total">
                Across <strong>{places}</strong> {places === 1 ? "place" : "places"} on the page.
                Fix the top ones first — they&apos;re sorted by severity below.
              </p>
            )}
          </div>

          <div className="panel">
            <h3>Who&apos;s blocked</h3>
            {people.length > 0 ? (
              <ul className="people-list">
                {people.map(({ key, count }) => (
                  <li key={key}>
                    <span className="people-icon">
                      <PersonIcon group={key} size={18} />
                    </span>
                    <span>{PEOPLE[key]?.label ?? key}</span>
                    <span className="people-count">
                      {count} {count === 1 ? "issue" : "issues"}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="issue-meta">No automated barriers detected for any group.</p>
            )}
          </div>
        </div>

        <p className="coverage">
          <InfoIcon size={18} />
          <span>{report.tool_coverage_note}</span>
        </p>

        {total === 0 ? (
          <div className="empty-report">
            <CheckCircleIcon size={26} />
            <div>
              <h3>No automated issues found</h3>
              <p>
                A great start. Automated checks catch only part of the picture, so try the page
                with a keyboard and a screen reader too.
              </p>
            </div>
          </div>
        ) : (
          <div className="report-body">
            <div className="report-side">
              {report.screenshot_png_base64 && (
                <figure className="shot">
                  <div
                    className="shot-frame"
                    tabIndex={0}
                    role="region"
                    aria-label="Annotated page screenshot"
                  >
                    <img
                      src={`data:image/png;base64,${report.screenshot_png_base64}`}
                      alt={`Screenshot of ${report.page_title || report.url} with a numbered marker on each issue`}
                    />
                  </div>
                  <figcaption>Numbers on the screenshot match the issues.</figcaption>
                </figure>
              )}
              <nav className="panel" aria-labelledby="index-heading">
                <h3 id="index-heading">Jump to an issue</h3>
                <ol className="index-list">
                  {groups.map((g, i) => (
                    <li key={g.rule_id}>
                      <a href={`#issue-${i + 1}`} onClick={() => openIssue(i + 1)}>
                        <span className="num-pin" aria-hidden="true">
                          {i + 1}
                        </span>
                        <span>{g.help_text}</span>
                      </a>
                    </li>
                  ))}
                </ol>
              </nav>
            </div>

            <div className="report-main">
              <h3>Issues, most serious first</h3>
              <ul className="issue-list">
                {groups.map((g, i) => (
                  <IssueCard key={g.rule_id} group={g} index={i + 1} defaultOpen={i < 2} />
                ))}
              </ul>

              <ManualReviewSection items={report.manual_review_items} />

              {report.ai_status === "off" && (
                <p className="ai-line ai-tip">
                  <SparkleIcon size={18} />
                  <span>
                    Want each fix rewritten for this exact page and re-checked in a browser?{" "}
                    <button type="button" className="link-button" onClick={onRequestKey}>
                      Add your Anthropic key
                    </button>{" "}
                    and scan again.
                  </span>
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
