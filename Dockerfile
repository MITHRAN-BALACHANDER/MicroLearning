# ── Stage 1: dependency builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System libs needed to compile native wheels (psycopg2, Pillow, moviepy…)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY Agents/requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Runtime system deps only (ffmpeg for moviepy, libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed wheels from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY Agents/ .

# Writable dirs the app needs at runtime
RUN mkdir -p logs data/documents data/chroma_db data/videos \
    && chown -R appuser:appgroup /app

USER appuser

# 5000 = Flask admin dashboard, 8000 = WhatsApp webhook + /health
EXPOSE 5000 8000

# Health-check against the webhook server's /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "start_bot.py"]
