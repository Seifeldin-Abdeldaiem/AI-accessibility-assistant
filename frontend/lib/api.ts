import type { ScanReport } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {}

export async function runScan(url: string): Promise<ScanReport> {
  const res = await fetch(`${API_BASE_URL}/api/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiRequestError(body?.detail ?? `Scan failed (HTTP ${res.status})`);
  }
  return res.json();
}

export function markdownExportUrl(scanId: string): string {
  return `${API_BASE_URL}/api/scan/${scanId}/report.md`;
}

export function pdfExportUrl(scanId: string): string {
  return `${API_BASE_URL}/api/scan/${scanId}/report.pdf`;
}
