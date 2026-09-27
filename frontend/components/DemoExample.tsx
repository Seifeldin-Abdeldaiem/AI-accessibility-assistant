import { CheckCircleIcon } from "./icons";

export default function DemoExample() {
  return (
    <div className="demo-section">
      <h2>
        <span>What a finding looks like</span>
      </h2>
      <ul className="issue-list">
        <li className="issue-card" data-impact="serious">
          <span className="demo-badge">Example — not a live result</span>
          <div className="issue-heading">
            <span className="badge" style={{ background: "var(--serious)" }}>
              Serious
            </span>
            <p className="issue-title">Form field has no label</p>
          </div>
          <p className="issue-meta">WCAG 4.1.2 · 3 places on this page</p>

          <p className="explanation">
            Screen readers just say &ldquo;edit text,&rdquo; so blind visitors
            don&apos;t know what to type. The placeholder also vanishes once
            someone starts typing, which trips up people with memory
            difficulties.
          </p>

          <pre className="code-block" tabIndex={0} aria-label="Suggested fix, as a diff">
            <span className="diff-old">
              - &lt;input type=&quot;email&quot; placeholder=&quot;Email address&quot;&gt;
            </span>
            <span className="diff-new">
              + &lt;label for=&quot;signup-email&quot;&gt;Email address&lt;/label&gt;
              <br />
              + &lt;input type=&quot;email&quot; id=&quot;signup-email&quot; autocomplete=&quot;email&quot;&gt;
            </span>
          </pre>

          <p className="verify-line verify-yes">
            <CheckCircleIcon />
            Fix checked: issue gone, nothing new introduced.
          </p>
        </li>
      </ul>
    </div>
  );
}
