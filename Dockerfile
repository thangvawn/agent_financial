# (Không dùng # syntax=docker/dockerfile:1 — tránh BuildKit phải pull image từ Docker Hub khi Hub lỗi.)

# ── Stage 1: Frontend ────────────────────────────────────
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python deps (cached independently of src) ──
FROM python:3.12-slim AS deps
ARG PIP_VERSION=26.2.2
ARG PIP_TIMEOUT=120
ARG PIP_RETRIES=10
ARG PIP_RESUME_RETRIES=10
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=${PIP_TIMEOUT} \
    PIP_RETRIES=${PIP_RETRIES} \
    PIP_RESUME_RETRIES=${PIP_RESUME_RETRIES} \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-vie && \
    rm -rf /var/lib/apt/lists/*

# pip >=25.2 resumes interrupted downloads; connection retries alone do not
# recover a read timeout partway through a large wheel with the base image's pip.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade "pip==${PIP_VERSION}"

# Copy only what setuptools needs to resolve dependencies.
# A stub __init__.py lets "pip install .[auto]" read pyproject.toml
# without shipping the real source code into this layer.
COPY pyproject.toml README.md ./
RUN mkdir -p src/risk_dashboard && \
    echo '__version__ = "0.1.0"' > src/risk_dashboard/__init__.py
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install ".[auto]"

# ── Stage 3: Final runtime ──────────────────────────────
FROM deps AS runtime
LABEL maintainer="thangvawn"
ENV PYTHONUNBUFFERED=1

# Overlay real source — only this layer invalidates on code changes
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --no-deps -e .

COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN groupadd -r app && useradd -r -g app -d /app app && \
    mkdir -p data/models data/cache data/financials/cache .cache/py-yfinance && \
    chown -R app:app /app

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "risk_dashboard.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
