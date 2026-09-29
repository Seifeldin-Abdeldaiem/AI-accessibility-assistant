# Unkerb — is your website disability friendly?

Paste a URL. In about 30 seconds, get plain-English findings on what stops
blind, deaf, low-vision and keyboard-only people using your page, and the
code change that fixes each one.

A kerb is a small step: nothing to most people, a wall to a wheelchair
user. Websites are full of small steps like that, and Unkerb finds them.
The brand name lives in `frontend/lib/brand.ts` and `BRAND_NAME` in
`backend/app/report.py` if you want to change it.

This is a v1: one URL at a time, no sign-in. It reports what an automated
scanner can find — it does not, and will not, claim a page is "compliant."

## How it works

1. **Load** — the page is opened in a real headless browser (Playwright),
   so JavaScript-rendered pages are checked the way a visitor sees them.
2. **Scan** — [axe-core](https://github.com/dequelabs/axe-core) (the engine
   behind Lighthouse's accessibility score) runs against the rendered DOM.
   Every failure comes with its WCAG success criterion and the exact element.
3. **Group** — repeats collapse into one finding. 40 product images with no
   alt text count as one problem in 40 places, not 40 problems to read.
4. **Explain & fix** — every group gets built-in, hand-written guidance
   (`backend/app/rule_guides.py`): who it blocks, the steps to fix it, and a
   before/after example — no API key needed. With a key (bring your own, or
   one set on the server), Claude also rewrites the flagged element for
   that exact page, preferring native HTML semantics over ARIA.
5. **Verify** — each fix is applied to a copy of the live DOM in the
   browser and axe is re-run on it. Only fixes that actually clear the
   issue (and don't introduce a new one) are marked "checked."
6. **Manual review** — heuristics flag things axe can't judge, like alt
   text that's really a filename ("IMG_4021.jpg") or a link that just says
   "click here." Claude suggests better wording, marked "check before using."
7. **Report** — a screenshot with each issue numbered, exportable as
   Markdown or PDF.

## Why this exists, and what it doesn't claim

- 95.9% of the top million home pages fail automated WCAG checks (WebAIM
  Million 2026) — but automated tools alone only catch a fraction of real
  failures. In a 2017 UK Government Digital Service test of 10 tools
  against a page with 143 known failures, the best single tool found 41%;
  all ten together found 71%.
- Because of that gap, this report never says a page is "compliant." It
  says what was checked, what failed, and what still needs a person to
  test — keyboard navigation, a screen reader, zoom/reflow.
- Fixes go into your own page's code. There is no "add one script tag and
  you're done" widget.

## Project structure

```
backend/    FastAPI service: Playwright + axe-core scanning, SSRF-safe URL
            fetching, Claude-generated explanations/fixes with in-browser
            verification, Markdown/PDF report export.
frontend/   Next.js app: URL form, results view, screenshot, export links.
```

## Running it locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # skip if you're pointing PLAYWRIGHT_BROWSERS_PATH
                               # at an already-installed Chromium
cp .env.example .env          # ANTHROPIC_API_KEY is optional — see below
uvicorn app.main:app --reload --port 8000
```

**You don't need to set `ANTHROPIC_API_KEY` at all.** The app supports
bring-your-own-key (BYOK): each visitor can optionally paste their own
Anthropic key into the scan form, used only for that one scan and never
stored server-side. Without any key — server-side or BYOK — the server
still runs and reports every automated finding; it just can't explain or
fix them, and says so in the report instead of failing. Setting
`ANTHROPIC_API_KEY` on the server is only for a self-hosted deployment
where you're deliberately paying for every visitor's AI usage yourself.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000, paste a URL, and scan it.

### Try it against a known fixture

`backend/tests/fixtures/test_page.html` has a handful of deliberate,
labelled issues (missing alt text, an unlabelled input, an unnamed button,
low color contrast, a generic "click here" link) — useful for a smoke test
without depending on a live third-party site:

```bash
cd backend/tests/fixtures && python3 -m http.server 8099
# in another shell, with the backend running:
# set ALLOW_PRIVATE_NETWORKS=true first (see below) and scan
# http://127.0.0.1:8099/test_page.html
```

## Security: fetching a stranger's URL

Accepting any URL from a form and fetching it server-side is a classic
SSRF vector — someone could point it at `169.254.169.254` (cloud metadata),
an internal admin panel, or `localhost`. This is handled in
`backend/app/security.py` and enforced twice:

1. Before navigation, the hostname is resolved and rejected unless every
   resolved IP is public and routable.
2. During navigation, **every** request the browser makes — redirects,
   subresources, everything — is re-checked the same way via Playwright's
   request routing. This also closes the DNS-rebinding gap (a hostname
   that resolves to a public IP at check time but a private one a moment
   later).

`ALLOW_PRIVATE_NETWORKS=true` disables both checks so you can scan a
localhost fixture during development. **Never set it to true in a
deployment reachable by anyone else.**

## Known limitations (v1)

- One URL at a time; no accounts, history, or whole-site crawling yet.
- No automated keyboard-navigation test (tab order, focus traps) yet —
  axe-core checks static/semantic issues, not interaction.
- The in-scan spend guard (`MAX_SCAN_SPEND_USD`) estimates cost from token
  usage; set a real cap in your Anthropic console too.
- Manual-review suggestions (alt text, link text) are capped per scan to
  bound latency and cost — see `MAX_ALT_SUGGESTIONS` / `MAX_LINK_SUGGESTIONS`
  in `backend/app/manual_review.py`.
- Fix verification mutates and reverts a copy of the live DOM in the
  browser tab used for scanning; it doesn't touch your actual site.
- Rate limiting (`backend/app/rate_limit.py`) and the in-memory report
  store are per-process — fine for one instance, not for multiple; see
  `DEPLOYMENT.md` for what that means before scaling out.

## Deploying this publicly

The root `Dockerfile` builds the whole app (website and scanner) as one
image, and `render.yaml` deploys it to Render's free plan: **New →
Blueprint → this repo → Apply**. See `DEPLOYMENT.md` for the details.

## Roadmap

Whole-site scans, an automated keyboard-navigation test, accounts and scan
history, re-checks to track progress over time, a draft accessibility
statement, and checks on GitHub pull requests.
