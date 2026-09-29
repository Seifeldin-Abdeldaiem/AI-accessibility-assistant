"use client";

import { useEffect, useState } from "react";
import { CheckIcon } from "./icons";

// The scan is one request with no progress events, so steps advance on a
// timer and the last one stays active until the response lands. The step
// names are the real pipeline stages, in order; only their timing is
// approximate.
const STEP_MS = 2600;

export default function ScanProgress({ withAi }: { withAi: boolean }) {
  const steps = [
    "Opening the page in a real browser",
    "Running axe-core accessibility checks",
    "Grouping repeated problems",
    withAi ? "Writing fixes and re-checking each one" : "Checking alt text and link wording",
    "Building your report",
  ];

  const [active, setActive] = useState(0);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const stepTimer = setInterval(() => {
      setActive((a) => Math.min(a + 1, steps.length - 1));
    }, STEP_MS);
    const clock = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => {
      clearInterval(stepTimer);
      clearInterval(clock);
    };
  }, [steps.length]);

  return (
    <div className="progress">
      <div className="progress-head">
        <p className="progress-title" role="status" aria-live="polite">
          {steps[active]}…
        </p>
        <span className="progress-time" aria-hidden="true">
          {seconds}s
        </span>
      </div>
      <ol className="progress-steps" aria-label="Scan steps">
        {steps.map((label, i) => {
          const state = i < active ? "done" : i === active ? "active" : "pending";
          return (
            <li key={label} data-state={state}>
              <span className="step-dot" aria-hidden="true">
                {state === "done" && <CheckIcon size={13} />}
              </span>
              {label}
              <span className="visually-hidden">
                {state === "done" ? " (done)" : state === "active" ? " (in progress)" : ""}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
