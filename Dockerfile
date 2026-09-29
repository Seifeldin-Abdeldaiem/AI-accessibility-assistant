# One image for the whole app: the website (a static Next.js export) and the
# scanning API are served by the same FastAPI process on one port. This is
# what render.yaml deploys. backend/Dockerfile still builds the API alone.

# --- 1. Build the website as static files ---------------------------------
FROM node:20-slim AS site
WORKDIR /site
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# Empty base URL = call the API on the same origin that served the page.
ENV STATIC_EXPORT=1 \
    NEXT_PUBLIC_API_BASE_URL="" \
    NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# --- 2. API + Chromium, serving the site ----------------------------------
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium plus the OS libraries it needs (fonts, libnss3, ...).
RUN playwright install --with-deps chromium

COPY backend/app ./app
COPY --from=site /site/out ./site

ENV PORT=8000 \
    FRONTEND_DIR=/app/site
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# One worker: each holds its own headless browser. Concurrency inside it is
# capped by MAX_CONCURRENT_SCANS (app/config.py).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
