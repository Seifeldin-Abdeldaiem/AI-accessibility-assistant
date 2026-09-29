import { BRAND } from "@/lib/brand";

function RampArt() {
  // A kerb in profile with a curb cut, yellow tactile paving and a wheel on
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
              The curb-cut effect
            </p>
            <h2 id="why-heading" className="visually-hidden">
              Why {BRAND.name}
            </h2>
            <p className="why-quote">
              Curb cuts were won by disabled activists. Now everyone with a pushchair, a suitcase
              or a delivery trolley uses them. <mark>Accessible websites work the same way.</mark>
            </p>
            <p className="why-body">
              Clear labels, readable contrast and working keyboard controls help blind users and
              people on a cracked phone screen alike. {BRAND.name} is named after that idea: fix
              it for the people locked out, and it gets better for everyone.
            </p>
          </div>
          <RampArt />
        </div>

        <div className="stats">
          <div className="stat">
            <p className="stat-num">95.9%</p>
            <p>of the top million home pages fail automated WCAG checks.</p>
          </div>
          <div className="stat">
            <p className="stat-num">56</p>
            <p>detectable errors on the average home page.</p>
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
          Sources: WebAIM Million (2026); UK Government Digital Service accessibility tool audit
          (2017).
        </p>
      </div>
    </section>
  );
}
