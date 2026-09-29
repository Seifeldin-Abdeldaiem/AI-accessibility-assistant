import type { Metadata, Viewport } from "next";
import "@fontsource-variable/atkinson-hyperlegible-next";
import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";
import Logo from "@/components/Logo";
import { BRAND } from "@/lib/brand";

export const metadata: Metadata = {
  title: `${BRAND.name} — is your website disability friendly?`,
  description: `Paste a URL. In a minute or two ${BRAND.name} shows what stops blind, deaf, low-vision and keyboard-only people using your page, and the code change that fixes it.`,
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
              <a href="#hear">Hear the difference</a>
              <a href="#how">How it works</a>
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
                {BRAND.name} finds the small steps on your website that stop disabled people
                getting in — and shows how to level them. Honest about what automated checks
                can&apos;t catch.
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
