import type { ViolationGroup } from "@/lib/types";

const IMPACT_LABELS: Record<string, string> = {
  critical: "Critical",
  serious: "Serious",
  moderate: "Moderate",
  minor: "Minor",
};

interface Props {
  group: ViolationGroup;
  index: number;
}

export default function IssueCard({ group, index }: Props) {
  const representative = group.nodes[0];

  return (
    <li className="issue-card" data-impact={group.impact}>
      <div className="issue-heading">
        <span className={`badge`} style={{ background: `var(--color-${group.impact})` }}>
          {IMPACT_LABELS[group.impact] ?? group.impact}
        </span>
        <p className="issue-title">
          {index}. {group.help_text}
        </p>
      </div>
      <p className="issue-meta">
        WCAG {group.wcag_tags.length > 0 ? group.wcag_tags.join(", ") : "n/a"} ·{" "}
        {group.total_node_count} place{group.total_node_count === 1 ? "" : "s"} on this page
      </p>

      {group.explanation && <p className="explanation">{group.explanation}</p>}
      {!group.explanation && group.explanation_error && (
        <p className="muted-note">{group.explanation_error}</p>
      )}

      {representative && (
        <pre className="code-block">
          <code>{representative.html}</code>
        </pre>
      )}

      {group.fix && (
        <>
          <pre className="code-block">
            <span className="diff-old">- {group.fix.old_html}</span>
            <span className="diff-new">+ {group.fix.new_html}</span>
          </pre>
          {group.fix.note && <p className="muted-note">{group.fix.note}</p>}
          {group.fix_verified === true && (
            <p className="verify-line verify-yes">✓ Fix checked: {group.fix_verification_note}</p>
          )}
          {group.fix_verified === false && (
            <p className="verify-line verify-no">✗ Fix not verified: {group.fix_verification_note}</p>
          )}
          {group.fix_verified === null && group.fix_verification_note && (
            <p className="muted-note">{group.fix_verification_note}</p>
          )}
        </>
      )}

      <p>
        <a href={group.help_url} target="_blank" rel="noreferrer">
          Learn more about this rule
        </a>
      </p>
    </li>
  );
}
