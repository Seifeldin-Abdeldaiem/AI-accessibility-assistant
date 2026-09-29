import type { ViolationGroup } from "@/lib/types";
import { PEOPLE } from "@/lib/people";
import { wcagLabel } from "@/lib/wcag";
import { CheckIcon, ChevronIcon, PersonIcon, SparkleIcon, XCircleIcon } from "./icons";

const IMPACT_LABELS: Record<string, string> = {
  critical: "Critical",
  serious: "Serious",
  moderate: "Moderate",
  minor: "Minor",
};

interface Props {
  group: ViolationGroup;
  index: number;
  /** 3 on the landing page (under an h2), 4 inside the report (under an h3). */
  headingLevel?: 3 | 4;
  defaultOpen?: boolean;
  /** Sample cards don't get ids, so they can't collide with a real report. */
  sample?: boolean;
}

function DiffLines({ before, after }: { before: string; after: string }) {
  return (
    <>
      {before.split("\n").map((line, i) => (
        <span className="del" key={`d${i}`}>
          - {line}
        </span>
      ))}
      {after.split("\n").map((line, i) => (
        <span className="add" key={`a${i}`}>
          + {line}
        </span>
      ))}
    </>
  );
}

export default function IssueCard({
  group,
  index,
  headingLevel = 4,
  defaultOpen = false,
  sample = false,
}: Props) {
  const H = `h${headingLevel}` as "h3" | "h4";
  const representative = group.nodes[0];
  const guidance = group.guidance;
  const explanation = group.explanation ?? guidance?.summary ?? group.description;
  const places = group.total_node_count;

  return (
    <li
      className="issue"
      data-impact={group.impact}
      id={sample ? undefined : `issue-${index}`}
    >
      <details open={defaultOpen} id={sample ? undefined : `issue-${index}-details`}>
        <summary>
          <span className="num-pin" aria-hidden="true">
            {index}
          </span>
          <span className="issue-heading">
            <span className="issue-title-row">
              <span className="visually-hidden">Issue {index}: </span>
              <span className={`sev sev-${group.impact}`}>
                {IMPACT_LABELS[group.impact] ?? group.impact}
              </span>
              <span className="issue-title">{group.help_text}</span>
            </span>
            <span className="issue-meta">
              {wcagLabel(group.wcag_tags)} · {places} {places === 1 ? "place" : "places"} on
              this page
            </span>
          </span>
          <ChevronIcon size={20} className="issue-chev" />
        </summary>

        <div className="issue-body">
          {guidance && guidance.affects.length > 0 && (
            <div className="affects">
              <span className="affects-label">Blocks</span>
              {guidance.affects.map((key) => (
                <span className="person-chip" key={key}>
                  <PersonIcon group={key} size={15} />
                  {PEOPLE[key]?.label ?? key}
                </span>
              ))}
            </div>
          )}

          <p className="issue-explain">{explanation}</p>

          <div className="issue-cols">
            <div>
              <H className="issue-col-title">Found on your page</H>
              {representative ? (
                <>
                  <pre className="code" tabIndex={0} aria-label="Flagged HTML">
                    <code>{representative.html}</code>
                  </pre>
                  {places > 1 && (
                    <p className="code-caption">
                      The first of {places} matching elements — the same fix applies to all of
                      them.
                    </p>
                  )}
                </>
              ) : (
                <p className="code-caption">This rule applies to the whole page.</p>
              )}
            </div>

            <div>
              <H className="issue-col-title">
                How to fix
                {group.fix && (
                  <span className="fix-source">
                    <SparkleIcon size={13} />
                    Written for this page
                  </span>
                )}
              </H>

              {group.fix ? (
                <>
                  <pre className="code" tabIndex={0} aria-label="Suggested fix, as a diff">
                    <DiffLines before={group.fix.old_html} after={group.fix.new_html} />
                  </pre>
                  {group.fix.note && <p className="fix-note">{group.fix.note}</p>}
                  {group.fix_verified === true && (
                    <p className="stamp-row">
                      <span className="stamp">
                        <span className="stamp-check">
                          <CheckIcon size={14} />
                        </span>
                        Verified in a real browser
                      </span>
                    </p>
                  )}
                  {group.fix_verified === false && (
                    <p className="verify-fail">
                      <XCircleIcon size={18} />
                      <span>Not verified: {group.fix_verification_note}</span>
                    </p>
                  )}
                  {group.fix_verified === null && group.fix_verification_note && (
                    <p className="fix-note">{group.fix_verification_note}</p>
                  )}
                </>
              ) : guidance ? (
                <>
                  <ol className="fix-steps">
                    {guidance.steps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                  {guidance.example_before && guidance.example_after && (
                    <>
                      <pre className="code" tabIndex={0} aria-label="Example fix, as a diff">
                        <DiffLines
                          before={guidance.example_before}
                          after={guidance.example_after}
                        />
                      </pre>
                      <p className="code-caption">Example — adapt it to your own markup.</p>
                    </>
                  )}
                </>
              ) : (
                <p>{group.description}</p>
              )}
            </div>
          </div>

          <a className="rule-link" href={group.help_url} target="_blank" rel="noreferrer">
            Rule reference: {group.rule_id}
            <span className="visually-hidden"> (opens in a new tab)</span>
          </a>
        </div>
      </details>
    </li>
  );
}
