import HeroMock from "./HeroMock";
import { CheckIcon } from "./icons";
import { BRAND } from "@/lib/brand";

export default function Hero({ children }: { children: React.ReactNode }) {
  return (
    <section className="hero" aria-labelledby="hero-heading">
      <div className="container hero-grid">
        <div>
          <p className="eyebrow">
            <span className="eyebrow-dot" aria-hidden="true" />
            Free website accessibility checker
          </p>
          <h1 id="hero-heading">
            Find what&apos;s <mark>blocking people</mark> from using{" "}
            <span className="nowrap">your site.</span>
          </h1>
          <p className="hero-lede">
            Paste a URL. {BRAND.name} shows every barrier it can detect, who it shuts out, and the
            code change that fixes it — in plain English.
          </p>

          {children}

          <ul className="hero-points">
            <li>
              <CheckIcon size={16} /> Real-browser scan
            </li>
            <li>
              <CheckIcon size={16} /> WCAG checks by axe-core
            </li>
            <li>
              <CheckIcon size={16} /> Markdown &amp; PDF export
            </li>
          </ul>
        </div>
        <HeroMock />
      </div>
    </section>
  );
}
