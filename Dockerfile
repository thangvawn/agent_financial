# ── Stage 1: Build React frontend ────────────────────────
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python application ─────────────────────────
FROM python:3.12-slim AS runtime
LABEL maintainer="thangvawn"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir -e ".[auto]"

COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p data/models data/cache data/financials/cache && \
    chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "risk_dashboard.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
