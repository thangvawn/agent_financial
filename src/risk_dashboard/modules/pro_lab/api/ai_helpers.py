"""Helper utilities, auth dependencies, and dependency providers for Pro Lab AI endpoints."""
from __future__ import annotations

import json
from typing import Any

from fastapi import Header, HTTPException

from risk_dashboard.modules.pro_lab.application.services import is_pro_lab_local_test_open
from risk_dashboard.platform.ai_runtime.contracts import ModelError
from risk_dashboard.platform.ai_runtime.factory import get_default_provider
from risk_dashboard.platform.ai_runtime.provider import LLMProvider
from risk_dashboard.platform.security.access_control import AccessToken, require_scope_from_token


def require_pro_scope(
    x_access_token: str | None = Header(default=None, alias="X-Access-Token"),
) -> AccessToken:
    """Validate token has required pro:pro_lab:use scope (or local test bypass)."""
    if is_pro_lab_local_test_open():
        return AccessToken(
            token_id=x_access_token or "local_pro_lab_bypass",
            actor_id="local_pro_lab_user",
            role="internal_admin",
            scopes=("public:*", "pro:*", "admin:pro_lab:manage"),
        )
    return require_scope_from_token("pro:pro_lab:use", x_access_token)


def get_ai_provider() -> LLMProvider:
    """Dependency provider resolving the configured default LLMProvider."""
    try:
        return get_default_provider()
    except ModelError as exc:
        if exc.code == "configuration_error":
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        raise HTTPException(status_code=500, detail=f"AI Provider error: {exc}") from exc


def get_ai_provider_or_none() -> LLMProvider | None:
    """Non-throwing dependency for health/status probing."""
    try:
        return get_default_provider()
    except Exception:
        return None


def handle_model_error(exc: Exception) -> None:
    """Translate ModelError into typed HTTPException."""
    if isinstance(exc, ModelError):
        if exc.code == "configuration_error":
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if exc.code == "deadline_exceeded":
            raise HTTPException(status_code=504, detail="AI request exceeded deadline timeout.") from exc
        if exc.code == "rate_limited":
            raise HTTPException(status_code=429, detail="AI rate limit exceeded.") from exc
        if exc.code == "cancelled":
            raise HTTPException(status_code=499, detail="AI request was cancelled.") from exc
        raise HTTPException(status_code=502, detail=f"AI provider error ({exc.code}): {exc}") from exc
    raise HTTPException(status_code=500, detail="Internal server error executing AI task.") from exc


def parse_json_payload(raw_text: str, parsed: dict[str, Any] | None) -> dict[str, Any]:
    """Safely decode JSON response from model text or parsed dictionary."""
    if parsed is not None:
        return parsed
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="AI returned invalid JSON output.",
        ) from exc
