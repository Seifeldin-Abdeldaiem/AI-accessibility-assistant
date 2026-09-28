"use client";

import { FormEvent, useState } from "react";

interface Props {
  onSubmit: (url: string, anthropicApiKey?: string) => void;
  isLoading: boolean;
}

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
    <form className="scan-form-wrap" onSubmit={handleSubmit}>
      <div className="scan-form">
        <div className="field">
          <label htmlFor="scan-url">Page URL</label>
          <input
            id="scan-url"
            name="url"
            type="url"
            inputMode="url"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            disabled={isLoading}
            aria-describedby="scan-url-hint"
          />
          <span id="scan-url-hint" className="muted-note">
            We'll load this page in a headless browser and run an accessibility scan on it.
          </span>
        </div>
        <button className="primary" type="submit" disabled={isLoading}>
          {isLoading ? "Scanning…" : "Scan page"}
        </button>
      </div>

      <details className="byok-details">
        <summary>Use your own Anthropic API key (optional)</summary>
        <div className="field byok-field">
          <label htmlFor="scan-api-key">Anthropic API key</label>
          <input
            id="scan-api-key"
            name="anthropicApiKey"
            type="password"
            autoComplete="off"
            placeholder="sk-ant-…"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            disabled={isLoading}
            aria-describedby="scan-api-key-hint"
          />
          <span id="scan-api-key-hint" className="muted-note">
            Without a key you still get every automated finding — just not Claude's
            plain-English explanations and verified code fixes. Your key is sent with this
            scan only, never stored on our server, and cleared from this page on reload.
          </span>
        </div>
      </details>
    </form>
  );
}
