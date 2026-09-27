import type { ManualReviewItem } from "@/lib/types";

const KIND_LABELS: Record<string, string> = {
  alt_text: "Alt text",
  link_text: "Link text",
};

export default function ManualReviewSection({ items }: { items: ManualReviewItem[] }) {
  if (items.length === 0) return null;

  return (
    <section className="manual-review" aria-labelledby="manual-review-heading">
      <h2 id="manual-review-heading">Needs a human look</h2>
      <p className="muted-note">
        Automated rules can only tell you whether alt text or link text exists, not
        whether it's actually useful. These were flagged by heuristics — Claude
        suggested wording, but check it before using it.
      </p>
      <ul className="issue-list">
        {items.map((item, i) => (
          <li className="manual-item" key={`${item.selector}-${i}`}>
            <p>
              <strong>{KIND_LABELS[item.kind] ?? item.kind}</strong>{" "}
              <code>{item.selector}</code>
            </p>
            <p>{item.reason}</p>
            {item.suggestion && (
              <p>
                Suggested: &ldquo;{item.suggestion}&rdquo;{" "}
                <span className="caveat">({item.suggestion_caveat})</span>
              </p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
