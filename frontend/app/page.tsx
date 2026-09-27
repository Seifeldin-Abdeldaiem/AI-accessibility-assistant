"use client";

import { useState } from "react";
import ScanForm from "@/components/ScanForm";
import ScanReportView from "@/components/ScanReportView";
import { ApiRequestError, runScan } from "@/lib/api";
import type { ScanReport } from "@/lib/types";

export default function HomePage() {
  const [report, setReport] = useState<ScanReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleScan(url: string) {
    setIsLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await runScan(url);
      setReport(result);
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
      <ScanForm onSubmit={handleScan} isLoading={isLoading} />

      <div className="status-region" role="status" aria-live="polite">
        {isLoading && "Scanning the page — this loads it in a real browser, so it can take a moment…"}
      </div>

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      {report && <ScanReportView report={report} />}
    </>
  );
}
