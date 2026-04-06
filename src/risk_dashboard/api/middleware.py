from __future__ import annotations

import logging
import os
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Optional API key gate. Disabled when API_SECRET_KEY env var is empty."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        secret = os.getenv("API_SECRET_KEY", "")
        if not secret:
            return await call_next(request)

        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        provided = request.headers.get("X-API-Key", "")
        if provided != secret:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
