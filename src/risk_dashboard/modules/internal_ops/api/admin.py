from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.internal_ops.application.investigation_service import InvestigationService
from risk_dashboard.modules.internal_ops.application.policy import (
    OpsRole,
    PolicyDeniedError,
    PolicyEngine,
    parse_iso,
    utc_now,
)
from risk_dashboard.modules.internal_ops.domain.contracts import (
    InvestigationRequest,
    OpsActionRecommendation,
    OpsInvestigationReport,
)
from risk_dashboard.modules.internal_ops.infrastructure.adapters.admin_cms import AdminCmsAdapter
from risk_dashboard.modules.internal_ops.infrastructure.adapters.agentic_core import AgenticCoreAdapter
from risk_dashboard.modules.internal_ops.infrastructure.adapters.analytics import AnalyticsAdapter
from risk_dashboard.modules.internal_ops.infrastructure.adapters.trust_safety import TrustSafetyAdapter
from risk_dashboard.modules.internal_ops.infrastructure.sqlite import SqliteInternalOpsRepository
from risk_dashboard.modules.internal_ops.schemas.api import EvidenceListApiResponse
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

router = APIRouter(prefix="/internal-ops", tags=["Internal Ops (Admin)"])

FLAG_NAME = "module.internal_ops.enabled"


def _check_feature_flag() -> None:
    flags = FeatureFlagService()
    if not flags.is_enabled(FLAG_NAME):
        raise HTTPException(status_code=404, detail="Internal Ops module is disabled.")


def _repo() -> SqliteInternalOpsRepository:
    return SqliteInternalOpsRepository()


def _service(repo: SqliteInternalOpsRepository = Depends(_repo)) -> InvestigationService:
    adapters = {
        "analytics": AnalyticsAdapter(),
        "trust_safety": TrustSafetyAdapter(),
        "admin_cms": AdminCmsAdapter(),
        "agentic_core": AgenticCoreAdapter(),
    }
    return InvestigationService(adapters=adapters, repository=repo)


@router.post("/investigations", response_model=OpsInvestigationReport)
def create_investigation(
    req: InvestigationRequest,
    principal: AuthPrincipal = Depends(resolve_principal),
    service: InvestigationService = Depends(_service),
    _: None = Depends(_check_feature_flag),
) -> OpsInvestigationReport:
    try:
        PolicyEngine.resolve_role(principal)
    except PolicyDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return service.run_investigation(principal, req)


@router.get("/investigations/{investigation_id}", response_model=OpsInvestigationReport)
def get_investigation(
    investigation_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
    repo: SqliteInternalOpsRepository = Depends(_repo),
    _: None = Depends(_check_feature_flag),
) -> OpsInvestigationReport:
    try:
        role = PolicyEngine.resolve_role(principal)
    except PolicyDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    result = repo.get_investigation(investigation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    owner_account_id, report = result
    if owner_account_id != principal.account_id and role != OpsRole.SECURITY_ADMIN:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    if parse_iso(report.access_expires_at) <= utc_now():
        raise HTTPException(status_code=403, detail="Access to investigation report has expired.")

    repo.record_audit(principal.account_id, "view_report", report.purpose, investigation_id)
    return report


@router.get("/investigations/{investigation_id}/evidence", response_model=EvidenceListApiResponse)
def get_investigation_evidence(
    investigation_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    principal: AuthPrincipal = Depends(resolve_principal),
    repo: SqliteInternalOpsRepository = Depends(_repo),
    _: None = Depends(_check_feature_flag),
) -> EvidenceListApiResponse:
    try:
        role = PolicyEngine.resolve_role(principal)
    except PolicyDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    result = repo.get_investigation(investigation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    owner_account_id, report = result
    if owner_account_id != principal.account_id and role != OpsRole.SECURITY_ADMIN:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    if parse_iso(report.access_expires_at) <= utc_now():
        raise HTTPException(status_code=403, detail="Access to investigation report has expired.")

    capped_limit = min(limit, 500)
    items, total = repo.get_evidence(investigation_id, limit=capped_limit, offset=offset)
    repo.record_audit(principal.account_id, "view_evidence", report.purpose, investigation_id)

    return EvidenceListApiResponse(
        investigation_id=investigation_id,
        items=items,
        total=total,
        limit=capped_limit,
        offset=offset,
    )


@router.post(
    "/investigations/{investigation_id}/recommendations",
    response_model=list[OpsActionRecommendation],
)
def get_investigation_recommendations(
    investigation_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
    repo: SqliteInternalOpsRepository = Depends(_repo),
    _: None = Depends(_check_feature_flag),
) -> list[OpsActionRecommendation]:
    try:
        role = PolicyEngine.resolve_role(principal)
    except PolicyDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    result = repo.get_investigation(investigation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    owner_account_id, report = result
    if owner_account_id != principal.account_id and role != OpsRole.SECURITY_ADMIN:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    if parse_iso(report.access_expires_at) <= utc_now():
        raise HTTPException(status_code=403, detail="Access to investigation report has expired.")

    repo.record_audit(principal.account_id, "view_recommendations", report.purpose, investigation_id)
    return list(report.recommendations)

