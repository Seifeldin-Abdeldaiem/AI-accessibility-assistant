import { BrowserIcon, ChecklistIcon, SpeechIcon, StampIcon } from "./icons";

const STEPS = [
  {
    icon: BrowserIcon,
    title: "Open it for real",
    body: "We load your page in a real browser — JavaScript and all — so you get what visitors actually see, not the raw HTML.",
  },
  {
    icon: ChecklistIcon,
    title: "Check every element",
    body: "axe-core, the open-source engine behind Lighthouse's accessibility score, runs dozens of WCAG checks. Repeats are grouped: 40 unlabelled images is one fix, not 40 problems.",
  },
  {
    icon: SpeechIcon,
    title: "Explain it like a person",
    body: "Each problem says who it blocks — screen reader users, keyboard users, people with low vision — and exactly what to change.",
  },
  {
    icon: StampIcon,
    title: "Prove the fix works",
    body: "Bring an Anthropic key and every fix is written for your exact code, applied in the browser and re-checked. Only fixes that pass get the stamp.",
    tag: "With your own key",
  },
];

export default function HowItWorks() {
  return (
    <section className="section section-alt" id="how" aria-labelledby="how-heading">
      <div className="container">
        <div className="section-head">
          <h2 id="how-heading">How it works</h2>
          <p>Four steps, usually under a minute. Nothing to install on your site.</p>
        </div>
        <ol className="steps">
          {STEPS.map(({ icon: Icon, title, body, tag }, i) => (
            <li className="step" key={title}>
              <div className="step-top">
                <span className="step-icon">
                  <Icon size={22} />
                </span>
                <span className="step-num" aria-hidden="true">
                  0{i + 1}
                </span>
              </div>
              <h3>{title}</h3>
              <p>{body}</p>
              {tag && <span className="step-tag">{tag}</span>}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
