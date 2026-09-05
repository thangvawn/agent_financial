"""Public REST API endpoints for Legacy Reactivation Gates Framework."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.legacy_gate.application.service import LegacyGateService
from risk_dashboard.modules.legacy_gate.domain.errors import LegacyGateError
from risk_dashboard.modules.legacy_gate.schemas.gates import (
    BaselineReportResponse,
    DecisionRecordResponse,
    ModuleGateListResponse,
    ModuleGateStatusResponse,
    ReactivationDecisionRequest,
)
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

logger = logging.getLogger(__name__)

FEATURE_FLAG = "module.legacy_gate.enabled"
REQUIRED_SCOPE = "public:legacy_gate:read"

_service_instance: LegacyGateService | None = None


def get_service() -> LegacyGateService:
    global _service_instance
    if _service_instance is None:
        _service_instance = LegacyGateService()
    return _service_instance


def set_service_for_testing(service: LegacyGateService | None) -> None:
    global _service_instance
    _service_instance = service


def _check_feature_enabled() -> None:
    if not FeatureFlagService().is_enabled(FEATURE_FLAG, default=True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legacy gate module is disabled.",
        )


def _check_auth(principal: AuthPrincipal) -> None:
    if not principal.account_id or principal.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )


def _check_scope(principal: AuthPrincipal, required_scope: str = REQUIRED_SCOPE) -> None:
    if required_scope not in principal.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: Missing required scope '{required_scope}'.",
        )


def _handle_gate_error(exc: LegacyGateError) -> None:
    if exc.error_type == "module_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    elif exc.error_type in {"gate_not_ready", "gates_not_passed", "missing_baseline", "decision_required"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    elif exc.error_type in {"approval_required", "already_reactivated"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.message)


router = APIRouter(
    dependencies=[Depends(_check_feature_enabled)],
)

# Core router: /api/legacy-gates
api_router = APIRouter(
    prefix="/api/legacy-gates",
    tags=["Legacy Reactivation Gates"],
)


@api_router.get("/modules", response_model=ModuleGateListResponse)
def list_legacy_modules(
    principal: AuthPrincipal = Depends(resolve_principal),
    service: LegacyGateService = Depends(get_service),
) -> ModuleGateListResponse:
    _check_auth(principal)
    _check_scope(principal)
    try:
        statuses = service.list_modules()
        return ModuleGateListResponse(
            modules=[ModuleGateStatusResponse.model_validate(s.model_dump()) for s in statuses],
            total=len(statuses),
        )
    except LegacyGateError as exc:
        _handle_gate_error(exc)


@api_router.get("/modules/{slug}", response_model=ModuleGateStatusResponse)
def get_module_gate_status(
    slug: str,
    principal: AuthPrincipal = Depends(resolve_principal),
    service: LegacyGateService = Depends(get_service),
) -> ModuleGateStatusResponse:
    _check_auth(principal)
    _check_scope(principal)
    try:
        status_obj = service.get_module_status(slug)
        return ModuleGateStatusResponse.model_validate(status_obj.model_dump())
    except LegacyGateError as exc:
        _handle_gate_error(exc)


@api_router.post("/modules/{slug}/evaluate", response_model=ModuleGateStatusResponse)
def evaluate_module_gates(
    slug: str,
    principal: AuthPrincipal = Depends(resolve_principal),
    service: LegacyGateService = Depends(get_service),
) -> ModuleGateStatusResponse:
    _check_auth(principal)
    _check_scope(principal)
    try:
        status_obj = service.evaluate_module(slug)
        return ModuleGateStatusResponse.model_validate(status_obj.model_dump())
    except LegacyGateError as exc:
        _handle_gate_error(exc)


@api_router.post("/modules/{slug}/decisions", response_model=DecisionRecordResponse)
def record_reactivation_decision(
    slug: str,
    req: ReactivationDecisionRequest,
    principal: AuthPrincipal = Depends(resolve_principal),
    service: LegacyGateService = Depends(get_service),
) -> DecisionRecordResponse:
    _check_auth(principal)
    _check_scope(principal)
    try:
        record = service.record_decision(slug, req)
        return DecisionRecordResponse.model_validate(record.model_dump())
    except LegacyGateError as exc:
        _handle_gate_error(exc)


@api_router.get("/modules/{slug}/baseline", response_model=BaselineReportResponse)
def get_module_baseline(
    slug: str,
    principal: AuthPrincipal = Depends(resolve_principal),
    service: LegacyGateService = Depends(get_service),
) -> BaselineReportResponse:
    _check_auth(principal)
    _check_scope(principal)
    try:
        report = service.get_baseline_report(slug)
        return BaselineReportResponse.model_validate(report.model_dump())
    except LegacyGateError as exc:
        _handle_gate_error(exc)


# Compatibility router: /api/v1/public/legacy-gates
v1_public_router = APIRouter(
    prefix="/api/v1/public/legacy-gates",
    tags=["Legacy Reactivation Gates (v1)"],
)
v1_public_router.add_api_route("/modules", list_legacy_modules, methods=["GET"], response_model=ModuleGateListResponse)
v1_public_router.add_api_route("/modules/{slug}", get_module_gate_status, methods=["GET"], response_model=ModuleGateStatusResponse)
v1_public_router.add_api_route("/modules/{slug}/evaluate", evaluate_module_gates, methods=["POST"], response_model=ModuleGateStatusResponse)
v1_public_router.add_api_route("/modules/{slug}/decisions", record_reactivation_decision, methods=["POST"], response_model=DecisionRecordResponse)
v1_public_router.add_api_route("/modules/{slug}/baseline", get_module_baseline, methods=["GET"], response_model=BaselineReportResponse)

router.include_router(api_router)
router.include_router(v1_public_router)


