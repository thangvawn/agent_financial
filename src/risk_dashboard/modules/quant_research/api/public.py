"""Public REST API endpoints for quant_research."""
from __future__ import annotations

from collections import OrderedDict
import logging
import threading
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.quant_research.application.service import QuantResearchService
from risk_dashboard.modules.quant_research.infrastructure.engine_adapter import (
    QuantAdapterError,
)
from risk_dashboard.modules.quant_research.schemas.artifacts import QuantResearchArtifactV1
from risk_dashboard.modules.quant_research.schemas.requests import QuantResearchRequestV1
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

logger = logging.getLogger(__name__)

FEATURE_FLAG = "module.quant_research.enabled"
MAX_RUN_STORE_SIZE = 1000

_RUN_LOCK = threading.RLock()
_RUN_STORE: OrderedDict[str, dict[str, Any]] = OrderedDict()


def _save_run(entry: dict[str, Any]) -> None:
    with _RUN_LOCK:
        run_id = entry["run_id"]
        if run_id in _RUN_STORE:
            _RUN_STORE.move_to_end(run_id)
        _RUN_STORE[run_id] = entry
        while len(_RUN_STORE) > MAX_RUN_STORE_SIZE:
            _RUN_STORE.popitem(last=False)


def _get_run(run_id: str) -> dict[str, Any] | None:
    with _RUN_LOCK:
        entry = _RUN_STORE.get(run_id)
        if entry is not None:
            _RUN_STORE.move_to_end(run_id)
        return entry


def _check_feature_enabled() -> None:
    if not FeatureFlagService().is_enabled(FEATURE_FLAG, default=False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quant research module is disabled.",
        )


def _check_auth(principal: AuthPrincipal) -> None:
    if not principal.account_id or principal.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )


def _check_scope(principal: AuthPrincipal, required_scope: str) -> None:
    if required_scope not in principal.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: Missing required scope '{required_scope}'.",
        )


class QuantRunResponseV1(BaseModel):
    run_id: str
    status: str
    artifact: QuantResearchArtifactV1


router = APIRouter(
    prefix="/api/quant-research",
    tags=["Quant Research"],
    dependencies=[Depends(_check_feature_enabled)],
)

_service_instance: QuantResearchService | None = None


def get_service() -> QuantResearchService:
    global _service_instance
    if _service_instance is None:
        _service_instance = QuantResearchService()
    return _service_instance


def set_service_for_testing(service: QuantResearchService | None) -> None:
    global _service_instance
    _service_instance = service


def clear_run_store() -> None:
    with _RUN_LOCK:
        _RUN_STORE.clear()


@router.post("/runs", response_model=QuantRunResponseV1)
async def create_quant_run(
    request: QuantResearchRequestV1,
    principal: AuthPrincipal = Depends(resolve_principal),
    service: QuantResearchService = Depends(get_service),
) -> QuantRunResponseV1:
    """Create and execute a quant research query."""
    _check_auth(principal)

    scope_map = {
        "eod_analysis": "quant_research:analysis:read",
        "scenario_compare": "quant_research:scenario:read",
        "model_report": "quant_research:model_report:read",
    }
    required_scope = scope_map.get(request.operation, "quant_research:analysis:read")
    _check_scope(principal, required_scope)

    start_time = time.monotonic()
    try:
        artifact = await service.execute_research(request=request, principal=principal)
    except QuantAdapterError as exc:
        status_map = {
            "invalid_input": status.HTTP_400_BAD_REQUEST,
            "date_out_of_range": status.HTTP_400_BAD_REQUEST,
            "numeric_review_failed": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "deadline_exceeded": status.HTTP_504_GATEWAY_TIMEOUT,
            "panel_unavailable": status.HTTP_503_SERVICE_UNAVAILABLE,
            "model_unavailable": status.HTTP_503_SERVICE_UNAVAILABLE,
            "engine_failure": status.HTTP_503_SERVICE_UNAVAILABLE,
        }
        status_code = status_map.get(exc.error_type, status.HTTP_500_INTERNAL_SERVER_ERROR)
        err_detail: dict[str, Any] = {"error_type": exc.error_type, "message": exc.message}
        if exc.hint:
            err_detail["hint"] = exc.hint
        raise HTTPException(status_code=status_code, detail=err_detail) from exc
    except Exception as exc:
        logger.error("Unexpected error in create_quant_run: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "internal_error", "message": "An internal error occurred."},
        ) from exc

    latency_ms = int((time.monotonic() - start_time) * 1000)
    logger.info("quant_run: id=%s, acc=%s, op=%s, ms=%d", artifact.run_id, principal.account_id, request.operation, latency_ms)

    run_status = "completed" if artifact.review_status == "verified" else "blocked"
    _save_run({
        "account_id": principal.account_id,
        "run_id": artifact.run_id,
        "status": run_status,
        "artifact": artifact,
    })
    return QuantRunResponseV1(run_id=artifact.run_id, status=run_status, artifact=artifact)


@router.get("/runs/{run_id}", response_model=QuantRunResponseV1)
def get_quant_run(
    run_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> QuantRunResponseV1:
    """Retrieve an existing quant research run by ID with strict ownership validation."""
    _check_auth(principal)

    allowed_scopes = {
        "quant_research:analysis:read",
        "quant_research:scenario:read",
        "quant_research:model_report:read",
    }
    if not any(s in principal.scopes for s in allowed_scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Missing required quant_research read scope.",
        )

    entry = _get_run(run_id)
    if entry is None or entry.get("account_id") != principal.account_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

    return QuantRunResponseV1(
        run_id=entry["run_id"],
        status=entry["status"],
        artifact=entry["artifact"],
    )

