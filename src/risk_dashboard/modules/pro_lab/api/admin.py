from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, HTTPException

from risk_dashboard.modules.pro_lab.application.services import ListAuditLogs, ListProLabRuns
from risk_dashboard.modules.pro_lab.application.services import ReviewProLabExperiment
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    SqliteProLabAuditRepository,
    SqliteProLabExperimentRepository,
    SqliteProLabExperimentRunRepository,
)
from risk_dashboard.modules.pro_lab.schemas.requests import ProLabExperimentReviewRequest
from risk_dashboard.modules.pro_lab.schemas.responses import ProLabAccessTokenResponse
from risk_dashboard.platform.security.access_control import (
    AccessToken,
    assign_role,
    issue_token_for_actor,
    require_scope_from_token,
)

router = APIRouter(tags=["Trading Lab (Admin)"])


async def verify_trading_lab_admin(
    x_admin_trading_lab_key: str | None = Header(None, alias="X-Admin-Trading-Lab-Key"),
) -> bool:
    expected = os.getenv("ADMIN_TRADING_LAB_KEY", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Trading Lab chưa bật: đặt ADMIN_TRADING_LAB_KEY trong .env (và restart backend).",
        )
    if not x_admin_trading_lab_key or x_admin_trading_lab_key.strip() != expected:
        raise HTTPException(status_code=401, detail="Thiếu hoặc sai khóa X-Admin-Trading-Lab-Key.")
    return True


def require_pro_lab_admin(
    x_access_token: str | None = Header(default=None, alias="X-Access-Token"),
) -> AccessToken:
    return require_scope_from_token("admin:pro_lab:manage", x_access_token)


@router.get("/trading-lab/status", tags=["Trading Lab (Admin)"])
def trading_lab_status():
    key = os.getenv("ADMIN_TRADING_LAB_KEY", "").strip()
    return {
        "enabled": bool(key),
        "pro_enabled": bool(os.getenv("PRO_LAB_KEY", "").strip()),
        "chat_removed": True,
        "log_file": "data/trading_lab/paper_notes.jsonl",
        "workspace_positioning": "Pro Lab is separated from retail surfaces and used as premium/internal research workspace.",
    }


@router.post("/pro-lab/access/bootstrap", response_model=ProLabAccessTokenResponse, tags=["Trading Lab (Admin)"])
def pro_lab_access_bootstrap(_: bool = Depends(verify_trading_lab_admin)) -> ProLabAccessTokenResponse:
    assign_role(actor_id="internal-admin", role="internal_admin")
    token = issue_token_for_actor(actor_id="internal-admin", role="internal_admin", ttl_hours=24)
    return ProLabAccessTokenResponse(
        actor_id=token.actor_id,
        role=token.role,
        access_token=token.token_id,
        scopes=list(token.scopes),
        expires_at=token.expires_at,
    )


@router.get("/pro-lab/experiments", tags=["Trading Lab (Admin)"])
def pro_lab_experiments(_: AccessToken = Depends(require_pro_lab_admin)):
    repo = SqliteProLabExperimentRepository()
    items = repo.list_all()
    return {
        "count": len(items),
        "items": [
            {
                "experiment_id": item.experiment_id,
                "user_id": item.user_id,
                "blueprint_id": item.blueprint_id,
                "experiment_type": item.experiment_type,
                "status": item.status,
                "created_at": item.created_at,
                "review_status": item.review_status,
                "review_notes": item.review_notes,
                "reviewed_at": item.reviewed_at,
                "reviewer_id": item.reviewer_id,
            }
            for item in items
        ],
    }


@router.get("/pro-lab/runs", tags=["Trading Lab (Admin)"])
def pro_lab_runs(_: AccessToken = Depends(require_pro_lab_admin)):
    return {
        "items": [item.model_dump() for item in ListProLabRuns(runs=SqliteProLabExperimentRunRepository()).execute()],
    }


@router.post("/pro-lab/experiments/{experiment_id}/review", tags=["Trading Lab (Admin)"])
def pro_lab_review_experiment(
    experiment_id: str,
    req: ProLabExperimentReviewRequest,
    token: AccessToken = Depends(require_pro_lab_admin),
):
    try:
        reviewed = ReviewProLabExperiment(
            experiments=SqliteProLabExperimentRepository(),
            audit=SqliteProLabAuditRepository(),
        ).execute(
            experiment_id=experiment_id,
            review_status=req.review_status,
            review_notes=req.review_notes,
            reviewer_id=token.actor_id,
        )
        return reviewed.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/pro-lab/audit-logs", tags=["Trading Lab (Admin)"])
def pro_lab_audit_logs(_: AccessToken = Depends(require_pro_lab_admin)):
    return {
        "items": [item.model_dump() for item in ListAuditLogs(audit=SqliteProLabAuditRepository()).execute()],
    }
