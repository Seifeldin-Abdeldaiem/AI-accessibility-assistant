// Small hand-rolled icon set (no icon library dependency). Every icon is
// decorative next to visible text, so each carries aria-hidden — the
// adjacent text is what assistive tech reads.

type IconProps = { size?: number };

export function LogoMark({ size = 18 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M8 12.5l2.5 2.5L16 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ScanIcon({ size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M3 8V5a2 2 0 0 1 2-2h3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M21 16v3a2 2 0 0 1-2 2h-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="4" y1="12" x2="20" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function SparkleIcon({ size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

export function CheckShieldIcon({ size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function FileOutIcon({ size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M14 3v5h5" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

export function CheckCircleIcon({ size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M8 12.5l2.5 2.5L16 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function XCircleIcon({ size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M9.5 9.5l5 5m0-5l-5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function AlertIcon({ size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 4l9 16H3L12 4z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <line x1="12" y1="10" x2="12" y2="14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="17" r="0.9" fill="currentColor" />
    </svg>
  );
}

export function EyeIcon({ size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}
