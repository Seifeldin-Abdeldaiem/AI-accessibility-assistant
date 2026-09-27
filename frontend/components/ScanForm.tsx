"use client";

import { FormEvent, useState } from "react";

interface Props {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export default function ScanForm({ onSubmit, isLoading }: Props) {
  const [url, setUrl] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    const withScheme = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
    onSubmit(withScheme);
  }

  return (
    <form className="scan-form" onSubmit={handleSubmit}>
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
    </form>
  );
}
