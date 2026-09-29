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

// A calm, conversational pace for people hearing a screen reader for the
// first time. (Many everyday screen reader users listen far faster.)
const SPEECH_RATE = 0.88;
// Breathing room between announcements, like moving from one element to
// the next with the keyboard.
const PAUSE_BETWEEN_LINES_MS = 750;

// Most browsers ship a robotic default voice and better ones alongside it;
// prefer the natural-sounding English voices when they're installed.
const PREFERRED_VOICES = [
  /natural/i,
  /neural/i,
  /premium/i,
  /enhanced/i,
  /google uk english female/i,
  /google uk english male/i,
  /google us english/i,
  /\b(serena|daniel|kate|samantha|karen|moira|tessa|libby|sonia|ryan)\b/i,
];

function pickVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const english = voices.filter((v) => /^en([-_]|$)/i.test(v.lang));
  const pool = english.length ? english : voices;
  for (const pattern of PREFERRED_VOICES) {
    const match = pool.find((v) => pattern.test(v.name));
    if (match) return match;
  }
  return (
    pool.find((v) => /^en[-_]GB/i.test(v.lang)) ?? pool.find((v) => v.default) ?? pool[0] ?? null
  );
}

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
            {after && <span className="soft-in">Add to cart</span>}
            <span className="pin">2</span>
          </span>
        </div>
      </div>
      <div className="shop-signup">
        {after && <span className="shop-label soft-in">Email address</span>}
        <span className="shop-input">
          <span className="soft-in" key={mode}>
            {after ? "you@example.com" : "Email address"}
          </span>
          <span className="pin">3</span>
        </span>
      </div>
      <p className="shop-link">
        Changed your mind?{" "}
        <span className="shop-a">
          <span className="soft-in" key={mode}>
            {after ? "Read our returns policy" : "click here"}
          </span>
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
  // Guards against late events from a cancelled run.
  const runId = useRef(0);
  const voice = useRef<SpeechSynthesisVoice | null>(null);
  const pauseTimer = useRef<number | undefined>(undefined);
  // Chrome can drop events for an utterance that's been garbage-collected
  // mid-sentence; holding a reference keeps onend firing.
  const current = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    setCanSpeak(true);
    const synth = window.speechSynthesis;
    // Voices often load asynchronously, after the first render.
    const loadVoices = () => {
      voice.current = pickVoice(synth.getVoices());
    };
    loadVoices();
    synth.addEventListener("voiceschanged", loadVoices);
    return () => {
      synth.removeEventListener("voiceschanged", loadVoices);
      window.clearTimeout(pauseTimer.current);
      synth.cancel();
    };
  }, []);

  function stop() {
    runId.current += 1;
    window.clearTimeout(pauseTimer.current);
    window.speechSynthesis.cancel();
    current.current = null;
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
    // One line at a time, with a pause between, rather than queueing all
    // four back to back.
    const speakLine = (i: number) => {
      if (runId.current !== run) return;
      if (i >= LINES.length) {
        finish();
        return;
      }
      const u = new SpeechSynthesisUtterance(LINES[i][mode]);
      u.rate = SPEECH_RATE;
      u.pitch = 1;
      if (voice.current) {
        u.voice = voice.current;
        u.lang = voice.current.lang;
      }
      u.onstart = () => runId.current === run && setSpeaking(i);
      u.onend = () => {
        if (runId.current !== run) return;
        pauseTimer.current = window.setTimeout(() => speakLine(i + 1), PAUSE_BETWEEN_LINES_MS);
      };
      u.onerror = fail;
      current.current = u;
      window.speechSynthesis.speak(u);
    };
    speakLine(0);
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
          <div className="seg" role="group" aria-label="Which version of the page" data-active={mode}>
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
                    <span className="transcript-said soft-in" key={`said-${mode}`}>
                      &ldquo;{line[mode]}&rdquo;
                    </span>
                    {mode === "after" ? (
                      <span className="transcript-fix soft-in" key="fix">
                        ✓ {line.fix}
                      </span>
                    ) : (
                      <span className="transcript-problem soft-in" key="problem">
                        {line.problem}
                      </span>
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
