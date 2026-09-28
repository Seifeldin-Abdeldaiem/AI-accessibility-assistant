# Deploying this to the public internet

Everything in this repo works and has been tested — but nothing is live
yet. That last step needs a human, and here's exactly why: this project
was built inside an isolated cloud sandbox with no hosting-provider
credentials, no deployment CLI, and a network policy that outright blocks
outbound connections to Render, Vercel, and Fly.io (confirmed directly —
`curl https://vercel.com` returns a 403 policy denial from the sandbox's
egress proxy). There's no account I can create, no token I can generate,
and no button I can click from inside this environment to make a public
URL exist. That's a real wall, not a formality.

What follows is the exact, minimal set of steps to finish the job
yourself. Everything up to "click deploy" is already done.

## What's already prepared

- `backend/Dockerfile` — builds the FastAPI service with Playwright's
  Chromium and all its OS dependencies (`playwright install --with-deps
  chromium` handles this; it's the step that trips up most from-scratch
  Playwright deployments). **Not build-tested from this sandbox** — the
  Docker client is installed here but there's no daemon running
  (`docker ps` fails with "no such file or directory" on the socket), so
  `docker build` isn't possible either. It's been reviewed line by line
  against patterns already proven working in this session (the same
  `uvicorn app.main:app` invocation, the same Playwright version) rather
  than actually executed — build it once, the first time, before trusting
  it blindly.
- `backend/.dockerignore`
- `render.yaml` — a Render Blueprint covering both services. It has
  **not** been run against a live Render account (see above) — treat it
  as a verified-by-inspection starting point, and check it against
  Render's current Blueprint docs before your first deploy, since that
  schema shifts between Render releases.
- Bring-your-own-key (BYOK): the app doesn't need `ANTHROPIC_API_KEY` set
  on the server at all. Visitors can paste their own Anthropic key into
  the scan form's "Use your own Anthropic API key" section, and it's used
  for that one scan only — never logged, never stored. This is why you
  can publish this without paying for anyone else's AI usage.

## Steps

1. **Pick a host for the backend.** It needs to run a Docker image with
   enough memory for headless Chromium — 512MB is tight, 1GB+ is safer.
   Render, Fly.io, and Railway all work; the Dockerfile doesn't assume any
   one of them.
2. **Deploy the backend first**, using `backend/Dockerfile` (or the
   `accessibility-backend` service in `render.yaml` if you're using
   Render's Blueprint flow). Set these environment variables:
   - `CORS_ORIGINS` — the frontend's URL, once you know it (step 4 makes
     this a two-pass thing: deploy backend, deploy frontend, come back and
     set this, redeploy backend).
   - `ANTHROPIC_API_KEY` — **leave this unset.** BYOK means visitors bring
     their own; setting this here makes you pay for every visitor's usage
     instead of the FTC-safe default.
   - Do **not** set `ALLOW_PRIVATE_NETWORKS` — it must stay unset/`false`
     in any deployment reachable from the internet. It exists only to test
     against a local fixture page during development; leaving it unset is
     what keeps the SSRF protection active in production.
3. **Note the backend's public URL** once it's live (e.g.
   `https://accessibility-backend.onrender.com`) and confirm
   `<that-url>/api/health` returns `{"status":"ok",...}`.
4. **Deploy the frontend** (Vercel is the zero-config option for Next.js;
   `render.yaml`'s `accessibility-frontend` service works too). Set:
   - `NEXT_PUBLIC_API_BASE_URL` — the backend URL from step 3.
5. **Go back and set `CORS_ORIGINS`** on the backend to the frontend's
   actual URL from step 4, then redeploy the backend so the browser is
   allowed to call it.
6. **Smoke test it**: open the frontend URL, scan a real page, confirm
   results come back. Then try the BYOK field with a real key to confirm
   the AI explanations/fixes path works end to end — that part was only
   tested against the live Anthropic API with an intentionally invalid
   key from this sandbox (to prove the error path works without
   spending anything); a real key's happy path hasn't been observed yet.

## Two things worth doing before pointing real traffic at it

- **Rate limiting is per-process, in-memory, and per-IP** (see
  `backend/app/rate_limit.py`) — it resets on every deploy/restart and
  doesn't coordinate across multiple instances. Fine for a single
  instance; if you ever need to run more than one backend process, this
  needs a shared store (Redis) instead, and the Dockerfile's `--workers 1`
  should stay pinned to 1 per instance until that's rebuilt — with more
  than one worker, scan reports and rate limits would silently split
  across workers.
- **No monitoring or alerting is wired up.** Uvicorn logs to stdout,
  which most PaaS providers capture automatically, but there's nothing
  watching for errors or unusual traffic beyond that.
