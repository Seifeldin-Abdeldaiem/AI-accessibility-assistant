import type { ManualReviewItem } from "@/lib/types";
import { EyeIcon, SpeechIcon } from "./icons";

const KINDS: Record<string, { label: string; Icon: typeof EyeIcon }> = {
  alt_text: { label: "Image description", Icon: EyeIcon },
  link_text: { label: "Link wording", Icon: SpeechIcon },
};

export default function ManualReviewSection({ items }: { items: ManualReviewItem[] }) {
  if (items.length === 0) return null;

  return (
    <section className="manual" aria-labelledby="manual-heading">
      <h3 id="manual-heading">Worth a human look</h3>
      <p className="manual-intro">
        Automated rules can tell that alt text or link text exists, not whether it&apos;s any
        good. These look suspicious — check them yourself.
      </p>
      <ul className="issue-list">
        {items.map((item, i) => {
          const kind = KINDS[item.kind] ?? { label: item.kind, Icon: EyeIcon };
          return (
            <li className="manual-item" key={`${item.selector}-${i}`}>
              <span className="manual-kind">
                <kind.Icon size={18} />
                {kind.label}
              </span>
              <p>{item.reason}</p>
              <code>{item.selector}</code>
              {item.suggestion && (
                <p className="suggestion">
                  Try: &ldquo;{item.suggestion}&rdquo;
                  <small>{item.suggestion_caveat}</small>
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
