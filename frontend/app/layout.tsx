import type { Metadata, Viewport } from "next";
import "./globals.css";
import { LogoMark } from "@/components/icons";

export const metadata: Metadata = {
  title: "AI Accessibility Assistant",
  description:
    "Paste a URL and get plain-English accessibility findings with code fixes that are checked in a real browser before they're shown to you.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0b1120" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        <header className="site-header">
          <div className="site-header-inner">
            <span className="brand-mark">
              <LogoMark />
            </span>
            <span className="brand-name">AI Accessibility Assistant</span>
          </div>
        </header>
        <main id="main-content">
          <div className="wrap">{children}</div>
        </main>
        <footer className="app-footer">
          Automated checks only find a fraction of real accessibility issues.
          This tool does not certify a page as compliant — treat it as a
          starting point, and test with a keyboard and a screen reader too.
        </footer>
      </body>
    </html>
  );
}
