"use client";

import { useEffect, useRef, useState } from "react";
import { BRAND } from "@/lib/brand";

type Mode = "before" | "after";

// What a screen reader typically announces for each element. Exact wording
// varies between VoiceOver, NVDA and JAWS; these are representative.
const LINES = [
  {
    pin: 1,
    before: "IMG_4021.jpg, image",
    after: "Two-person tent pitched by a lake, image",
    problem: "The file name, not what it shows",
    fix: "Image given a description",
  },
  {
    pin: 2,
    before: "Button",
    after: "Add to cart, button",
    problem: "Button for what?",
    fix: "Button given a name",
  },
  {
    pin: 3,
    before: "Edit text",
    after: "Email address, edit text",
    problem: "Type what, where?",
    fix: "Field given a label",
  },
  {
    pin: 4,
    before: "Link, click here",
    after: "Link, read our returns policy",
    problem: "Click here for what?",
    fix: "Link says where it goes",
  },
];

function CartGlyph() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 4h2l2.4 11h10.2L20 8H6.2" />
      <circle cx="9" cy="19.5" r="1.3" />
      <circle cx="17" cy="19.5" r="1.3" />
    </svg>
  );
}

function ShopMock({ mode }: { mode: Mode }) {
  const after = mode === "after";
  return (
    <div className="shop" aria-hidden="true">
      <div className="shop-product">
        <div className="shop-img">
          <span className="pin">1</span>
        </div>
        <div className="shop-info">
          <p className="shop-title">Two-person tent</p>
          <p className="shop-price">£129</p>
          <span className={`shop-buy${after ? " has-text" : ""}`}>
            <CartGlyph />
            {after && "Add to cart"}
            <span className="pin">2</span>
          </span>
        </div>
      </div>
      <div className="shop-signup">
        {after && <span className="shop-label">Email address</span>}
        <span className="shop-input">
          {after ? "you@example.com" : "Email address"}
          <span className="pin">3</span>
        </span>
      </div>
      <p className="shop-link">
        Changed your mind?{" "}
        <span className="shop-a">
          {after ? "Read our returns policy" : "click here"}
          <span className="pin">4</span>
        </span>
      </p>
    </div>
  );
}

export default function HearTheDifference() {
  const [mode, setMode] = useState<Mode>("before");
  const [speaking, setSpeaking] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [canSpeak, setCanSpeak] = useState(false);
  const [speechFailed, setSpeechFailed] = useState(false);
  // Guards against late onstart events from a cancelled run.
  const runId = useRef(0);

  useEffect(() => {
    setCanSpeak(typeof window !== "undefined" && "speechSynthesis" in window);
    return () => {
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    };
  }, []);

  function stop() {
    runId.current += 1;
    window.speechSynthesis.cancel();
    setSpeaking(null);
    setIsPlaying(false);
  }

  function play() {
    stop();
    const run = runId.current;
    setIsPlaying(true);
    setSpeechFailed(false);
    const finish = () => {
      if (runId.current !== run) return;
      setSpeaking(null);
      setIsPlaying(false);
    };
    // No installed voice (some Linux browsers) fails straight away; say so
    // rather than leaving the button looking broken.
    const fail = (e: SpeechSynthesisErrorEvent) => {
      if (runId.current !== run) return;
      if (e.error !== "canceled" && e.error !== "interrupted") setSpeechFailed(true);
      finish();
    };
    LINES.forEach((line, i) => {
      const u = new SpeechSynthesisUtterance(line[mode]);
      u.rate = 1.15;
      u.onstart = () => runId.current === run && setSpeaking(i);
      u.onerror = fail;
      if (i === LINES.length - 1) u.onend = finish;
      window.speechSynthesis.speak(u);
    });
  }

  function switchTo(next: Mode) {
    if (canSpeak) stop();
    setMode(next);
  }

  return (
    <section className="section hear" id="hear" aria-labelledby="hear-heading">
      <div className="container">
        <div className="section-head">
          <p className="eyebrow">
            <span className="eyebrow-dot" aria-hidden="true" />
            The 30-second version
          </p>
          <h2 id="hear-heading">Hear a website the way a blind visitor does</h2>
          <p>
            Blind people browse with a screen reader, which reads the page out loud. Here is a
            typical shop page — before and after fixing four common problems.
          </p>
        </div>

        <div className="hear-controls">
          <div className="seg" role="group" aria-label="Which version of the page">
            <button type="button" aria-pressed={mode === "before"} onClick={() => switchTo("before")}>
              Before fixes
            </button>
            <button type="button" aria-pressed={mode === "after"} onClick={() => switchTo("after")}>
              After fixes
            </button>
          </div>
          {canSpeak && (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={isPlaying ? stop : play}
            >
              <span aria-hidden="true">{isPlaying ? "■" : "▶"}</span>
              {isPlaying ? "Stop" : "Play it out loud"}
            </button>
          )}
          <p className="hear-fallback" role="status">
            {speechFailed &&
              "Your browser has no text-to-speech voice installed, so read the transcript below instead."}
          </p>
        </div>

        <div className="hear-grid" data-mode={mode}>
          <div className="hear-panel">
            <p className="hear-panel-title">What you see</p>
            <ShopMock mode={mode} />
          </div>
          <div className="hear-panel hear-panel-dark">
            <p className="hear-panel-title">What a screen reader says</p>
            <ol className="transcript" aria-live="polite">
              {LINES.map((line, i) => (
                <li key={line.pin} data-speaking={speaking === i || undefined}>
                  <span className="pin-static" aria-hidden="true">
                    {line.pin}
                  </span>
                  <span className="transcript-text">
                    <span className="transcript-said">&ldquo;{line[mode]}&rdquo;</span>
                    {mode === "after" ? (
                      <span className="transcript-fix">✓ {line.fix}</span>
                    ) : (
                      <span className="transcript-problem">{line.problem}</span>
                    )}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        </div>

        <p className="hear-caption">
          <strong>Same page, four small code changes</strong> — most of them invisible to sighted
          visitors. {BRAND.name} finds changes like these on your page and shows you each one.
          <span className="hear-note">
            {" "}
            Exact wording varies between screen readers; this is representative.
          </span>
        </p>
      </div>
    </section>
  );
}
