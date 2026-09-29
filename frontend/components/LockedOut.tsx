import { PersonIcon } from "./icons";

const GROUPS = [
  {
    key: "screen-reader",
    who: "Blind people using screen readers",
    what: "Buttons and images with no text are read out as just “button” or “image”.",
  },
  {
    key: "keyboard",
    who: "People who can’t use a mouse",
    what: "Menus that only open on hover, and controls they can’t reach or can’t see focused.",
  },
  {
    key: "low-vision",
    who: "People with low vision",
    what: "Faint grey text fades into the background, and some pages won’t let them zoom in.",
  },
  {
    key: "colour-blind",
    who: "Colour-blind people",
    what: "Links, errors and charts that rely on colour alone simply don’t show up.",
  },
  {
    key: "deaf",
    who: "Deaf and hard-of-hearing people",
    what: "A video without captions says nothing at all.",
  },
  {
    key: "cognitive",
    who: "People with cognitive disabilities",
    what: "Vague links, missing labels and placeholder text that vanishes turn forms into guesswork.",
  },
];

export default function LockedOut() {
  return (
    <section className="section section-alt" id="who" aria-labelledby="who-heading">
      <div className="container">
        <div className="section-head">
          <h2 id="who-heading">Who gets locked out — and what stops them</h2>
          <p>
            Most barriers are a few lines of code. You won&apos;t notice them until you rely on a
            screen reader, a keyboard or zoom. These are the people they shut out.
          </p>
        </div>
        <ul className="locked-grid">
          {GROUPS.map(({ key, who, what }) => (
            <li className="locked-card" key={key}>
              <span className="locked-icon">
                <PersonIcon group={key} size={22} />
              </span>
              <h3>{who}</h3>
              <p>{what}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
