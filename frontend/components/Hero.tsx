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
            Can <mark>disabled people</mark> use{" "}
            <span className="nowrap">your website?</span>
          </h1>
          <p className="hero-lede">
            <strong>1 in 6 people</strong> lives with a disability. Paste your web address and in
            about 30 seconds {BRAND.name} shows what&apos;s stopping blind, deaf, low-vision and
            keyboard-only visitors — and exactly how to fix it.
          </p>

          {children}

          <ul className="hero-points">
            <li>
              <CheckIcon size={16} /> Free, no sign-up
            </li>
            <li>
              <CheckIcon size={16} /> Results in about 30 seconds
            </li>
            <li>
              <CheckIcon size={16} /> Fixes in plain English
            </li>
          </ul>
        </div>
        <HeroMock />
      </div>
    </section>
  );
}
