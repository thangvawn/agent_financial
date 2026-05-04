from __future__ import annotations

import logging
import os
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_ops_event
from risk_dashboard.platform.security.access_control import get_token_scopes, scope_allows

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


def _pro_lab_local_test_open() -> bool:
    explicit = os.getenv("PRO_LAB_LOCAL_TEST_OPEN", "").strip().lower()
    mode = os.getenv("MODE", "").strip().lower()
    return explicit in {"1", "true", "yes", "on"} or mode in {"development", "dev", "local", "test"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Optional API key gate. Disabled when API_SECRET_KEY env var is empty."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        secret = os.getenv("API_SECRET_KEY", "")
        if not secret:
            return await call_next(request)

        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        path = request.url.path
        # Trạng thái lab (không lộ khóa) — cho phép gọi không cần API key.
        if request.method == "GET" and path == "/admin/trading-lab/status":
            return await call_next(request)

        # Cho phép Trading Lab chỉ với khóa admin (tránh phải nhúng API_SECRET_KEY vào frontend).
        if path.startswith("/admin/trading-lab"):
            access_token = get_token_scopes(request.headers.get("X-Access-Token", "").strip())
            if access_token and scope_allows(access_token.scopes, "admin:pro_lab:manage"):
                return await call_next(request)
            lab = os.getenv("ADMIN_TRADING_LAB_KEY", "").strip()
            if lab and request.headers.get("X-Admin-Trading-Lab-Key", "").strip() == lab:
                return await call_next(request)

        if path.startswith("/api/v1/pro/pro-lab"):
            if _pro_lab_local_test_open():
                return await call_next(request)
            access_token = get_token_scopes(request.headers.get("X-Access-Token", "").strip())
            if access_token and scope_allows(access_token.scopes, "pro:pro_lab:use"):
                return await call_next(request)

        if path.startswith("/admin/pro-lab"):
            access_token = get_token_scopes(request.headers.get("X-Access-Token", "").strip())
            if access_token and scope_allows(access_token.scopes, "admin:pro_lab:manage"):
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
        path = request.url.path
        logger.info(
            "%s %s → %d (%.0fms)",
            request.method,
            path,
            response.status_code,
            duration_ms,
        )
        if _should_skip_analytics_logging(path):
            return response
        emit_ops_event(
            event_name="ops_api_request_logged",
            module="api",
            surface=_surface_for_path(path),
            properties={
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "success": response.status_code < 500,
                "latency_ms": round(duration_ms, 2),
                "endpoint_group": _endpoint_group_for_path(path),
            },
        )
        return response


def _should_skip_analytics_logging(path: str) -> bool:
    return path.startswith("/admin/analytics") or path.startswith("/api/v1/public/analytics/")


def _endpoint_group_for_path(path: str) -> str:
    if path.startswith("/admin/"):
        return "admin"
    if path.startswith("/api/v1/pro/"):
        return "pro"
    if path.startswith("/api/v1/public/"):
        return "public"
    return "system"


def _surface_for_path(path: str) -> str:
    if path.startswith("/admin/analytics"):
        return "analytics_monitoring"
    if path.startswith("/admin/trust-safety"):
        return "trust_safety"
    if path.startswith("/admin/pro-lab"):
        return "pro_lab_admin"
    if path.startswith("/api/v1/pro/pro-lab"):
        return "pro_lab"
    if path.startswith("/api/v1/public/"):
        trimmed = path.removeprefix("/api/v1/public/").split("/", 1)[0]
        return trimmed or "public_api"
    if path.startswith("/admin/"):
        return path.removeprefix("/admin/").split("/", 1)[0] or "admin_api"
    return "system"
