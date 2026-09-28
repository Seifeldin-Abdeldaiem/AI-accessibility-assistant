FROM python:3.11-slim

WORKDIR /app

# System deps for headless Chromium come from `playwright install --with-deps`
# below; this just keeps pip installs reproducible and small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installs Chromium itself plus the OS-level libraries it needs (fonts,
# libnss3, etc.) — this is the single most common reason a from-scratch
# Playwright deployment fails, so let Playwright's own installer handle it
# rather than hand-listing system packages.
RUN playwright install --with-deps chromium

COPY app ./app

# Most PaaS providers (Render, Fly, Railway, ...) inject PORT at runtime;
# 8000 is just the local default if it isn't set.
ENV PORT=8000
EXPOSE 8000

# Docker-native orchestrators (Fly.io, plain `docker run` + a scheduler)
# read this directly; Render/most PaaS use their own external check
# against healthCheckPath instead (see render.yaml) but this doesn't hurt
# there either.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# --workers 1 because each worker holds its own headless-browser pool —
# scale by raising this only alongside available memory (a Chromium
# instance is not cheap). Concurrency within one worker is already capped
# by MAX_CONCURRENT_SCANS (see app/config.py).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
