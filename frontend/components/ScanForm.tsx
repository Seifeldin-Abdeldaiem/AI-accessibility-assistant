"use client";

import { FormEvent, useState } from "react";
import { ArrowRightIcon, ChevronIcon, GlobeIcon, SparkleIcon } from "./icons";

interface Props {
  onSubmit: (url: string, anthropicApiKey?: string) => void;
  isLoading: boolean;
}

export const BYOK_DETAILS_ID = "byok";
export const API_KEY_INPUT_ID = "scan-api-key";
export const URL_INPUT_ID = "scan-url";

export default function ScanForm({ onSubmit, isLoading }: Props) {
  const [url, setUrl] = useState("");
  const [apiKey, setApiKey] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    const withScheme = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
    onSubmit(withScheme, apiKey);
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor={URL_INPUT_ID} className="scan-label">
        Website address
      </label>
      <div className="command-bar">
        <span className="command-icon">
          <GlobeIcon size={20} />
        </span>
        <input
          id={URL_INPUT_ID}
          name="url"
          type="url"
          inputMode="url"
          autoComplete="url"
          placeholder="https://yourwebsite.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          disabled={isLoading}
          aria-describedby="scan-hint"
        />
        <button className="btn btn-primary" type="submit" disabled={isLoading}>
          {isLoading ? "Scanning…" : "Scan page"}
          {!isLoading && <ArrowRightIcon size={18} />}
        </button>
      </div>
      <p id="scan-hint" className="scan-hint">
        Free, no sign-up. We open the page in a real browser and check it the way a visitor
        meets it.
      </p>

      <details className="byok" id={BYOK_DETAILS_ID}>
        <summary>
          <SparkleIcon size={17} />
          <span>
            Get fixes written for your exact code{" "}
            <span className="byok-optional">(optional)</span>
          </span>
          <ChevronIcon size={16} className="chev" />
        </summary>
        <div className="byok-body">
          <label htmlFor={API_KEY_INPUT_ID}>Your Anthropic API key</label>
          <input
            id={API_KEY_INPUT_ID}
            name="anthropicApiKey"
            type="password"
            autoComplete="off"
            spellCheck={false}
            placeholder="sk-ant-…"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            disabled={isLoading}
            aria-describedby="scan-api-key-hint"
          />
          <p id="scan-api-key-hint">
            Claude rewrites each problem element for your page, then we apply the change in a
            real browser and re-check it. Used for this scan only — never stored, and cleared when
            you leave the page.
          </p>
        </div>
      </details>
    </form>
  );
}
