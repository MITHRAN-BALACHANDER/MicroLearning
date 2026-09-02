# ── Stage 1: dependency builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System libs needed to compile native wheels (psycopg2, Pillow…)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# A venv keeps the whole dependency tree in one directory that stage 2 copies
# wholesale, and lets torch be pinned to a CPU build before anything else asks
# for it.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# sentence-transformers pulls torch, and the default PyPI wheel drags ~2 GB of
# CUDA libraries that a free CPU host can neither use nor store. Installing the
# CPU build first means the requirements install below sees torch as satisfied.
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch

COPY Agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image. Free hosts have an ephemeral disk, so
# without this every restart re-downloads ~90 MB before RAG can answer anything.
ENV HF_HOME=/opt/hf-cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# UID 1000 is what container platforms (Hugging Face Spaces among them) expect
# the process to run as, so the app can write to the dirs it owns.
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --create-home appuser

WORKDIR /app

# Runtime system deps only (ffmpeg for moviepy, libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/hf-cache /opt/hf-cache

ENV PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/opt/hf-cache \
    PYTHONUNBUFFERED=1 \
    ANONYMIZED_TELEMETRY=False

# Application source
COPY Agents/ .

# Defaults that make the image work unchanged on a single-port PaaS. Every one
# of them is overridable, and docker-compose overrides the port back to 8000.
ENV WEBHOOK_HOST=0.0.0.0 \
    WEBHOOK_PORT=7860 \
    WHATSAPP_WEBHOOK_PATH=/webhook/whatsapp \
    VIDEOS_DIR=/app/data/videos \
    CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db \
    LOG_FILE=/app/logs/bot.log

# Writable dirs the app needs at runtime
RUN mkdir -p logs data/documents data/chroma_db data/videos \
    && chown -R appuser:appgroup /app /opt/hf-cache

USER appuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('WEBHOOK_PORT','7860') + '/health')" || exit 1

# main.py, not start_bot.py: the pre-flight checks in start_bot.py exit(1) when
# the database has no deliverable videos yet, which on a fresh cloud deploy
# would kill the container and take the webhook down with it.
CMD ["python", "main.py"]
