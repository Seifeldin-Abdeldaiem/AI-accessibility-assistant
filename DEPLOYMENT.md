# Publishing Unkerb

The whole app (the website and the scanner) ships as **one Docker image**
and one web service. Its site is a static Next.js export, and the FastAPI
process that runs the scans serves it too. There are no URLs to wire
between services and no CORS to configure.

## Deploy on Render (free)

1. Sign in at [dashboard.render.com](https://dashboard.render.com). Any
   existing Render account works; you don't need a new one per website.
2. **New → Blueprint**, choose the `AI-accessibility-assistant` repo
   (connect GitHub first if Render asks), then **Apply**.
3. Render reads `render.yaml`, builds the root `Dockerfile` and starts a
   service called `unkerb` on the free plan. When the first build is done
   (about 5–10 minutes), the site is live at the URL Render shows. It is
   usually `https://unkerb.onrender.com`, with a suffix if that name is
   taken.

That is everything. Leave `ANTHROPIC_API_KEY` blank when Render asks.
Visitors can paste their own key into the scan form (it is used for that
one scan and never stored), and without a key every report still comes
with the built-in plain-English guidance.

After that, every merge to `main` redeploys automatically.

### Your own address (unkerb.co.uk)

The domain can only be attached once the Render service exists, but you
can buy it at any time to hold the name. No code changes are needed: the
site calls its own API on whatever address it is served from.

1. **Buy `unkerb.co.uk`** at any UK registrar (Cloudflare, Namecheap,
   123-reg, …). It is usually under £10 a year.
2. **Deploy** as above, then open the `unkerb` service in Render →
   **Settings → Custom Domains** → add both `unkerb.co.uk` and
   `www.unkerb.co.uk`.
3. **Add the DNS records Render shows you** at your registrar. Copy them
   from Render's screen, since they are the source of truth. Typically:
   - `unkerb.co.uk`: an `A` record pointing to Render's IP address. Some
     registrars offer `ALIAS`/`ANAME` records instead; use one pointing to
     `unkerb.onrender.com` if so.
   - `www.unkerb.co.uk`: a `CNAME` pointing to `unkerb.onrender.com`
     (or whatever `.onrender.com` address your service got).
   - If your registrar has **CAA** records set, allow Let's Encrypt and
     Google Trust Services, or HTTPS certificates can't be issued.
4. **Wait for Render to verify** the domain (click *Verify* if it doesn't
   happen on its own). DNS changes can take minutes to a few hours. Render
   then issues the HTTPS certificate automatically, and the
   `.onrender.com` address keeps working too.

### What the free plan means

- **$0**, 512 MB memory. The image is tested at exactly that limit (see
  below). `MAX_CONCURRENT_SCANS=1` makes scans queue instead of running two
  browsers at once.
- The service **sleeps after about 15 minutes with no visitors**. The first
  visit after that takes about a minute while it wakes up.
  `.github/workflows/keep-awake.yml` pings `/api/health` every 5 minutes to
  keep it awake. Change `SITE_URL` there if the service's address changes.
- **Free hours are shared.** A Render workspace gets about 750 free instance
  hours a month across all its free services, and an always-awake service
  uses about 730 of them. If other free services in the same workspace also
  stay busy, the workspace can run out before the month ends and Render
  suspends its free services until the next month. Watch the usage under
  **Billing** in Render; to stop pinging, disable the workflow in the
  repository's **Actions** tab.
- For always-on without pinging (and much faster scans), change
  `plan: free` to `plan: starter` in `render.yaml`.

## How the image is tested

`.github/workflows/docker.yml` runs on every push and pull request. It:

1. builds the root `Dockerfile` (the same image Render deploys),
2. runs it with `--memory 512m`,
3. checks the website is served,
4. scans `https://example.com` for real,
5. downloads the Markdown and PDF reports,
6. confirms a cloud-metadata address (`169.254.169.254`) is refused.

## Never do this

Don't set `ALLOW_PRIVATE_NETWORKS` on a public deployment. It switches off
the protection that stops people using the scanner to reach internal
addresses, and exists only for scanning a local test page in development.

## Other hosts

Any host that runs a Docker image and gives it a `PORT` works (Fly.io,
Railway, Google Cloud Run, a VPS): build the root `Dockerfile`, expose the
port and point the health check at `/api/health`. `backend/Dockerfile`
still builds the API alone if you'd rather host the website separately
(set `NEXT_PUBLIC_API_BASE_URL` for the website and `CORS_ORIGINS` for
the API).

## Before real traffic

- **Rate limits and reports live in memory** in the single process
  (`backend/app/rate_limit.py`, default 10 scans per IP per hour). They
  reset on each deploy or restart. Keep one instance and one worker
  unless you move them to a shared store such as Redis.
- **There is no monitoring yet** beyond the logs Render keeps.
