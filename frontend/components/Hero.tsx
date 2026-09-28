import { ScanIcon, SparkleIcon, CheckShieldIcon, FileOutIcon } from "./icons";

const FEATURES = [
  {
    icon: ScanIcon,
    title: "Scans the real page",
    body: "Loads your URL in a real browser and runs axe-core, so JavaScript-rendered content is checked the way a visitor sees it.",
  },
  {
    icon: SparkleIcon,
    title: "Plain-English fixes",
    body: "Claude explains who's affected and proposes a drop-in code fix, preferring native HTML over ARIA.",
  },
  {
    icon: CheckShieldIcon,
    title: "Verified, not guessed",
    body: "Every fix is applied to the live DOM and re-checked. Only fixes proven to work get a ✓.",
  },
  {
    icon: FileOutIcon,
    title: "Export the report",
    body: "Take findings with you as Markdown or PDF, screenshot included.",
  },
];

export default function Hero() {
  return (
    <div className="hero">
      <h1>Find what's blocking people from using your site</h1>
      <p className="tagline">
        Paste a URL. Get plain-English accessibility findings and code fixes,
        each one checked in a real browser before you see it.
      </p>

      <h2 className="visually-hidden">How it works</h2>
      <div className="feature-strip">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <div className="feature-card" key={title}>
            <div className="feature-icon">
              <Icon size={18} />
            </div>
            <h3>{title}</h3>
            <p>{body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
