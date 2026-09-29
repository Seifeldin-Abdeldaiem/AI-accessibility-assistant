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

### What the free plan means

- **$0**, 512 MB memory. The image is tested at exactly that limit (see
  below). `MAX_CONCURRENT_SCANS=1` makes scans queue instead of running two
  browsers at once.
- The service **sleeps after about 15 minutes with no visitors**. The first
  visit after that takes about a minute while it wakes up. For always-on,
  change `plan: free` to `plan: starter` in `render.yaml`.

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
