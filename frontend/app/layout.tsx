import type { Metadata, Viewport } from "next";
import "@fontsource-variable/atkinson-hyperlegible-next";
import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";
import Logo from "@/components/Logo";
import { BRAND } from "@/lib/brand";

export const metadata: Metadata = {
  title: `${BRAND.name} — accessibility checks with fixes that work`,
  description:
    "Paste a URL. Curbcut finds what stops disabled people using your page, explains it in plain English, and shows the code change that fixes it.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fbf8f1" },
    { media: "(prefers-color-scheme: dark)", color: "#121210" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        <header className="site-header">
          <div className="container site-header-inner">
            <a href="/" className="brand-link" aria-label={`${BRAND.name} home`}>
              <Logo />
            </a>
            <nav aria-label="Primary" className="site-nav">
              <a href="#how">How it works</a>
              <a href="#why">Why {BRAND.name}</a>
              <a href="#scan" className="nav-cta">
                Scan a page
              </a>
            </nav>
          </div>
        </header>

        <main id="main-content">{children}</main>

        <footer className="site-footer">
          <div className="container footer-inner">
            <div className="footer-brand">
              <Logo size={26} />
              <p>
                Accessibility fixes help everyone — like the curb cut. {BRAND.name} finds what
                automated checks can catch and is honest about what they can&apos;t.
              </p>
            </div>
            <div className="footer-cols">
              <div>
                <h2 className="footer-heading">Product</h2>
                <ul>
                  <li>
                    <a href="#how">How it works</a>
                  </li>
                  <li>
                    <a href="#scan">Scan a page</a>
                  </li>
                </ul>
              </div>
              <div>
                <h2 className="footer-heading">Built on</h2>
                <ul>
                  <li>
                    <a href="https://github.com/dequelabs/axe-core" rel="noreferrer">
                      axe-core by Deque
                    </a>
                  </li>
                  <li>
                    <a href={BRAND.repoUrl} rel="noreferrer">
                      Source on GitHub
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          <div className="container footer-legal">
            <p>
              Automated checks catch only part of the picture. {BRAND.name} never certifies a page
              as compliant — test with a keyboard and a screen reader too.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
