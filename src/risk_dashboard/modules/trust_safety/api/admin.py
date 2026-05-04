from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from risk_dashboard.modules.trust_safety.application.services import (
    GetTrustSafetyStatus,
    ListTrustSafetyAudit,
    ListTrustIncidents,
    OpenTrustIncident,
    UpdateTrustIncident,
)
from risk_dashboard.modules.trust_safety.infrastructure.repositories.sqlite import SqliteTrustSafetyRepository
from risk_dashboard.modules.trust_safety.schemas.requests import (
    TrustIncidentActionRequest,
    TrustIncidentOpenRequest,
)
from risk_dashboard.modules.trust_safety.schemas.responses import (
    TrustIncidentResponse,
    TrustSafetyAuditResponse,
    TrustSafetyStatusResponse,
)

router = APIRouter(prefix="/trust-safety", tags=["Trust Safety (Admin)"])

ADMIN_HEADER = "X-Admin-Trust-Safety-Key"
ADMIN_ENV = "ADMIN_TRUST_SAFETY_KEY"


async def verify_trust_safety_admin(
    x_admin_trust_safety_key: str | None = Header(default=None, alias=ADMIN_HEADER),
) -> bool:
    expected = os.getenv(ADMIN_ENV, "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Trust Safety admin chua bat: dat ADMIN_TRUST_SAFETY_KEY va restart backend.")
    if not x_admin_trust_safety_key or x_admin_trust_safety_key.strip() != expected:
        raise HTTPException(status_code=401, detail=f"Thieu hoac sai khoa {ADMIN_HEADER}.")
    return True


def _repo() -> SqliteTrustSafetyRepository:
    return SqliteTrustSafetyRepository()


@router.get("/status", response_model=TrustSafetyStatusResponse)
def trust_safety_status(_: bool = Depends(verify_trust_safety_admin)) -> TrustSafetyStatusResponse:
    return GetTrustSafetyStatus(repo=_repo()).execute(enabled=bool(os.getenv(ADMIN_ENV, "").strip()))


@router.get("/audit", response_model=list[TrustSafetyAuditResponse])
def trust_safety_audit(
    surface: str | None = Query(default=None),
    risk_class: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    _: bool = Depends(verify_trust_safety_admin),
) -> list[TrustSafetyAuditResponse]:
    return ListTrustSafetyAudit(repo=_repo()).execute(
        surface=surface,
        risk_class=risk_class,
        severity=severity,
        search=search,
        limit=limit,
    )


@router.get("/incidents", response_model=list[TrustIncidentResponse])
def trust_safety_incidents(
    status: str | None = Query(default=None),
    surface: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    _: bool = Depends(verify_trust_safety_admin),
) -> list[TrustIncidentResponse]:
    return ListTrustIncidents(repo=_repo()).execute(
        status=status,
        surface=surface,
        severity=severity,
        search=search,
        limit=limit,
    )


@router.post("/incidents/open", response_model=TrustIncidentResponse)
def trust_safety_open_incident(
    req: TrustIncidentOpenRequest,
    _: bool = Depends(verify_trust_safety_admin),
) -> TrustIncidentResponse:
    return OpenTrustIncident(repo=_repo()).execute(actor_id="trust-admin", req=req)


@router.post("/incidents/{incident_id}/action", response_model=TrustIncidentResponse)
def trust_safety_incident_action(
    incident_id: str,
    req: TrustIncidentActionRequest,
    _: bool = Depends(verify_trust_safety_admin),
) -> TrustIncidentResponse:
    try:
        return UpdateTrustIncident(repo=_repo()).execute(incident_id=incident_id, actor_id="trust-admin", req=req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
