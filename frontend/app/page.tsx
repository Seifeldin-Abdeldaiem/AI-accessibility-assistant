"use client";

import { useEffect, useRef, useState } from "react";
import Hero from "@/components/Hero";
import ScanForm, { API_KEY_INPUT_ID, BYOK_DETAILS_ID, URL_INPUT_ID } from "@/components/ScanForm";
import ScanProgress from "@/components/ScanProgress";
import ScanReportView from "@/components/ScanReportView";
import DemoExample from "@/components/DemoExample";
import HowItWorks from "@/components/HowItWorks";
import WhySection from "@/components/WhySection";
import { AlertIcon } from "@/components/icons";
import { ApiRequestError, runScan } from "@/lib/api";
import type { ScanReport } from "@/lib/types";

export default function HomePage() {
  const [report, setReport] = useState<ScanReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [withAi, setWithAi] = useState(false);
  const reportHeadingRef = useRef<HTMLHeadingElement>(null);

  // Once a report renders, move focus to its heading so keyboard and screen
  // reader users land on the results instead of staying on the form.
  useEffect(() => {
    if (report) reportHeadingRef.current?.focus();
  }, [report]);

  async function handleScan(url: string, anthropicApiKey?: string) {
    setIsLoading(true);
    setWithAi(Boolean(anthropicApiKey?.trim()));
    setError(null);
    setReport(null);
    try {
      setReport(await runScan(url, anthropicApiKey));
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

  function requestKey() {
    const details = document.getElementById(BYOK_DETAILS_ID) as HTMLDetailsElement | null;
    if (details) details.open = true;
    document.getElementById(API_KEY_INPUT_ID)?.focus();
  }

  function newScan() {
    const input = document.getElementById(URL_INPUT_ID) as HTMLInputElement | null;
    input?.focus();
    input?.select();
  }

  return (
    <>
      <Hero>
        <div className="scan-card" id="scan">
          <ScanForm onSubmit={handleScan} isLoading={isLoading} />
          {isLoading && <ScanProgress withAi={withAi} />}
          {error && (
            <div className="error-banner" role="alert">
              <AlertIcon size={18} />
              <span>{error}</span>
            </div>
          )}
        </div>
      </Hero>

      {report && (
        <ScanReportView
          report={report}
          headingRef={reportHeadingRef}
          onRequestKey={requestKey}
          onNewScan={newScan}
        />
      )}

      {!report && !isLoading && <DemoExample />}
      <HowItWorks />
      <WhySection />
    </>
  );
}
