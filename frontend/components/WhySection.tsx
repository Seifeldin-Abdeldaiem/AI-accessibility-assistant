import { BRAND } from "@/lib/brand";

function RampArt() {
  // A kerb in profile with a dropped kerb, yellow tactile paving and a wheel on
  // its way up. Decorative.
  return (
    <svg className="ramp-art" viewBox="0 0 400 270" aria-hidden="true" focusable="false">
      <rect x="0" y="190" width="400" height="80" rx="4" style={{ fill: "#2b2a22" }} />
      <path d="M12 232h376" style={{ stroke: "#ffc91f", strokeWidth: 5, strokeDasharray: "28 18" }} />
      <path d="M0 108h168l102 82H0z" style={{ fill: "var(--ink)" }} />
      <path d="M270 190h130" style={{ stroke: "var(--ink)", strokeWidth: 4 }} />
      <path
        d="M222 151l40 32"
        style={{ stroke: "#ffc91f", strokeWidth: 16, strokeLinecap: "round" }}
      />
      {[0, 1, 2, 3].map((i) => (
        <circle
          key={i}
          cx={226 + i * 11}
          cy={154 + i * 8.8}
          r="2.6"
          style={{ fill: "#16150f" }}
        />
      ))}
      {/* Centre sits one radius off the ramp surface, perpendicular to it. */}
      <g transform="translate(219 118)">
        <circle r="24" style={{ fill: "#ffc91f", stroke: "#16150f", strokeWidth: 4 }} />
        <circle r="5" style={{ fill: "#16150f" }} />
        <path
          d="M0-20V20M-20 0H20M-14-14l28 28M14-14l-28 28"
          style={{ stroke: "#16150f", strokeWidth: 2.5 }}
        />
      </g>
    </svg>
  );
}

export default function WhySection() {
  return (
    <section className="section" id="why" aria-labelledby="why-heading">
      <div className="container">
        <div className="why-grid">
          <div>
            <p className="eyebrow">
              <span className="eyebrow-dot" aria-hidden="true" />
              Why &ldquo;{BRAND.name}&rdquo;
            </p>
            <h2 id="why-heading" className="visually-hidden">
              Why {BRAND.name}
            </h2>
            <p className="why-quote">
              A kerb is a small step. For most people it&apos;s nothing — for a wheelchair user
              it&apos;s a wall. Websites are full of small steps like that.{" "}
              <mark>{BRAND.name} finds them and shows you how to level them.</mark>
            </p>
            <p className="why-body">
              Dropped kerbs were won by disabled campaigners, and now everyone with a pushchair or
              a suitcase uses them. Accessible websites work the same way: clear labels and
              readable text help someone on a cracked phone screen as much as a blind visitor.
            </p>
          </div>
          <RampArt />
        </div>

        <div className="stats">
          <div className="stat">
            <p className="stat-num">1 in 6</p>
            <p>people worldwide live with a significant disability — about 1.3 billion people.</p>
          </div>
          <div className="stat">
            <p className="stat-num">95.9%</p>
            <p>of the top million home pages fail automated accessibility checks.</p>
          </div>
          <div className="stat">
            <p className="stat-num">41%</p>
            <p>
              of known barriers found by the best single automated tool in a UK government test —
              so we tell you what still needs a person.
            </p>
          </div>
        </div>
        <p className="source">
          Sources: World Health Organization (2023); WebAIM Million (2026); UK Government
          Digital Service accessibility tool audit (2017).
        </p>
      </div>
    </section>
  );
}
