import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Accessibility Assistant",
  description:
    "Paste a URL and get plain-English accessibility findings with code fixes that are checked in a real browser before they're shown to you.",
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
          <h1>AI Accessibility Assistant</h1>
          <p className="tagline">
            Paste a URL. Get plain-English accessibility findings and code fixes,
            each checked in a real browser before you see it.
          </p>
        </header>
        <main id="main-content">{children}</main>
        <footer className="app-footer">
          Automated checks only find a fraction of real accessibility issues.
          This tool does not certify a page as compliant — treat it as a
          starting point, and test with a keyboard and a screen reader too.
        </footer>
      </body>
    </html>
  );
}
