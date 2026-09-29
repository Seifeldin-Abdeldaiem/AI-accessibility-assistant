import { CheckIcon } from "./icons";

/** Decorative illustration of the product: a page with numbered issue pins
 * and one finished finding. Hidden from assistive tech — the hero copy next
 * to it already says what it shows. */
export default function HeroMock() {
  return (
    <div className="mock" aria-hidden="true">
      <div className="mock-window">
        <div className="mock-bar">
          <i />
          <i />
          <i />
          <span className="mock-url">yourshop.com/product</span>
        </div>
        <div className="mock-page">
          <div className="mock-nav">
            <b />
            <span />
            <span />
            <span />
          </div>
          <div className="mock-field">
            <span className="flag" />
            <span className="pin p3">3</span>
          </div>
          <div className="mock-main">
            <div className="mock-lines">
              <span className="h" />
              <span />
              <span className="faint" />
              <span />
              <div className="mock-btn">
                <span className="flag critical" />
                <span className="pin p2">2</span>
              </div>
            </div>
            <div className="mock-img">
              <span className="flag critical" />
              <span className="pin">1</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mock-card">
        <div className="mock-card-head">
          <span className="pin">2</span>
          <span className="sev sev-critical">Critical</span>
          Button has no name
        </div>
        <div className="mock-code">
          <span className="del">- &lt;button&gt;&lt;svg/&gt;&lt;/button&gt;</span>
          <span className="add">+ &lt;button&gt;&lt;svg/&gt;Add to cart&lt;/button&gt;</span>
        </div>
        <span className="stamp">
          <span className="stamp-check">
            <CheckIcon size={14} />
          </span>
          Verified in a real browser
        </span>
      </div>
    </div>
  );
}
