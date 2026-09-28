"use client";

import { useRef, useState } from "react";
import Hero from "@/components/Hero";
import ScanForm from "@/components/ScanForm";
import DemoExample from "@/components/DemoExample";
import ScanReportView from "@/components/ScanReportView";
import { AlertIcon } from "@/components/icons";
import { ApiRequestError, runScan } from "@/lib/api";
import type { ScanReport } from "@/lib/types";

export default function HomePage() {
  const [report, setReport] = useState<ScanReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);

  async function handleScan(url: string, anthropicApiKey?: string) {
    setIsLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await runScan(url, anthropicApiKey);
      setReport(result);
      // Move focus to the results so keyboard/screen reader users land
      // where the new content actually is, instead of staying on the form.
      requestAnimationFrame(() => reportRef.current?.focus());
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : "Something went wrong while scanning that page. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <>
      <Hero />

      <div className="scan-panel">
        <ScanForm onSubmit={handleScan} isLoading={isLoading} />

        <div className="status-region" role="status" aria-live="polite">
          {isLoading && (
            <>
              <span className="spinner" aria-hidden="true" />
              Scanning the page — this loads it in a real browser, so it can
              take a moment…
            </>
          )}
        </div>

        {error && (
          <div className="error-banner" role="alert">
            <AlertIcon />
            <span>{error}</span>
          </div>
        )}
      </div>

      {!report && !isLoading && <DemoExample />}

      {report && (
        <div ref={reportRef} tabIndex={-1}>
          <ScanReportView report={report} />
        </div>
      )}
    </>
  );
}
