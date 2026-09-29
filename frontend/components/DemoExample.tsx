import IssueCard from "./IssueCard";
import type { ViolationGroup } from "@/lib/types";

const SAMPLE: ViolationGroup = {
  rule_id: "label",
  impact: "serious",
  description: "Ensure every form element has a label",
  help_text: "Form field has no label",
  help_url: "https://dequeuniversity.com/rules/axe/4.10/label",
  wcag_tags: ["wcag412", "wcag131"],
  nodes: [
    {
      target: "#signup input",
      html: '<input type="email" placeholder="Email address">',
      failure_summary: "",
      bounding_box: null,
    },
  ],
  total_node_count: 3,
  guidance: {
    affects: ["screen-reader", "voice", "cognitive"],
    summary: "",
    steps: [],
    example_before: null,
    example_after: null,
    curated: true,
  },
  explanation:
    "Screen readers just say “edit text”, so blind visitors don’t know what to type. The placeholder also vanishes once someone starts typing, which trips up people with memory difficulties.",
  fix: {
    old_html: '<input type="email" placeholder="Email address">',
    new_html:
      '<label for="signup-email">Email address</label>\n<input type="email" id="signup-email" autocomplete="email">',
    note: null,
  },
  fix_verified: true,
  fix_verification_note: "Applied in a real browser and re-checked: issue gone, nothing new introduced.",
  explanation_error: null,
};

export default function DemoExample() {
  return (
    <section className="section" aria-labelledby="demo-heading">
      <div className="container">
        <div className="section-head">
          <h2 id="demo-heading">What you get for every problem</h2>
          <p>
            Who it blocks, what we found, and the change that fixes it — numbered to match a
            marked-up screenshot of your page.
          </p>
        </div>
        <div className="demo-wrap">
          <p className="demo-ribbon">Sample finding</p>
          <ul className="issue-list">
            <IssueCard group={SAMPLE} index={1} headingLevel={3} defaultOpen sample />
          </ul>
        </div>
      </div>
    </section>
  );
}
