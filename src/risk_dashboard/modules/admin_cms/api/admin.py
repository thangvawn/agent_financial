from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from risk_dashboard.modules.admin_cms.application.services import (
    ApproveContent,
    ArchiveContent,
    GenerateAiDraft,
    GetAnalyticsOverview,
    GetCmsStatus,
    GetContentAnalytics,
    GetContentDetail,
    ListContent,
    ListContentVersions,
    ListReviewQueue,
    PublishContent,
    RecordContentAnalytics,
    RollbackContent,
    SubmitContentForReview,
    UpsertContentDraft,
)
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import SqliteAdminCmsRepository
from risk_dashboard.modules.admin_cms.schemas.requests import (
    CmsAiDraftRequest,
    CmsAnalyticsRecordRequest,
    CmsUpsertContentRequest,
    CmsWorkflowActionRequest,
)
from risk_dashboard.modules.admin_cms.schemas.responses import (
    CmsAnalyticsResponse,
    CmsContentResponse,
    CmsContentVersionResponse,
    CmsReviewTaskResponse,
    CmsStatusResponse,
)

router = APIRouter(prefix="/cms", tags=["Content Ops (Admin)"])

ADMIN_HEADER = "X-Admin-Content-Ops-Key"
ROLE_HEADER = "X-Content-Ops-Role"
ADMIN_ENV = "ADMIN_CONTENT_OPS_KEY"


async def verify_content_ops_admin(
    x_admin_content_ops_key: str | None = Header(default=None, alias=ADMIN_HEADER),
) -> bool:
    expected = os.getenv(ADMIN_ENV, "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Content Ops CMS chua bat: dat ADMIN_CONTENT_OPS_KEY va restart backend.")
    if not x_admin_content_ops_key or x_admin_content_ops_key.strip() != expected:
        raise HTTPException(status_code=401, detail=f"Thieu hoac sai khoa {ADMIN_HEADER}.")
    return True


def _repo() -> SqliteAdminCmsRepository:
    return SqliteAdminCmsRepository()


def _role(x_content_ops_role: str | None = Header(default="admin", alias=ROLE_HEADER)) -> str:
    return (x_content_ops_role or "admin").strip().lower()


def _actor(role: str) -> str:
    return f"content-ops:{role}"


@router.get("/status", response_model=CmsStatusResponse)
def cms_status(
    _: bool = Depends(verify_content_ops_admin),
    role: str = Depends(_role),
) -> CmsStatusResponse:
    return GetCmsStatus(repo=_repo()).execute(
        actor_role=role,
        enabled=bool(os.getenv(ADMIN_ENV, "").strip()),
    )


@router.get("/content", response_model=list[CmsContentResponse])
def list_cms_content(
    content_type: str | None = Query(default=None),
    _: bool = Depends(verify_content_ops_admin),
) -> list[CmsContentResponse]:
    return ListContent(repo=_repo()).execute(content_type=content_type)


@router.get("/content/{content_id}", response_model=CmsContentResponse)
def get_cms_content(
    content_id: str,
    _: bool = Depends(verify_content_ops_admin),
) -> CmsContentResponse:
    try:
        return GetContentDetail(repo=_repo()).execute(content_id=content_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/content/{content_type}/{content_id}", response_model=CmsContentResponse)
def upsert_cms_content(
    content_type: str,
    content_id: str,
    req: CmsUpsertContentRequest,
    _: bool = Depends(verify_content_ops_admin),
    role: str = Depends(_role),
) -> CmsContentResponse:
    try:
        actual_id = None if content_id == "new" else content_id
        return UpsertContentDraft(repo=_repo()).execute(
            content_type=content_type,
            content_id=actual_id,
            slug=req.slug,
            title=req.title,
            locale=req.locale,
            owner_team=req.owner_team,
            risk_category=req.risk_category,
            payload=req.payload,
            change_summary=req.change_summary,
            actor_role=role,
            actor_id=_actor(role),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/content/{content_id}/submit-review", response_model=CmsContentResponse)
def submit_cms_review(
    content_id: str,
    req: CmsWorkflowActionRequest,
    _: bool = Depends(verify_content_ops_admin),
    role: str = Depends(_role),
) -> CmsContentResponse:
    try:
        return SubmitContentForReview(repo=_repo()).execute(
            content_id=content_id,
            actor_role=role,
            actor_id=_actor(role),
            comments=req.comments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/content/{content_id}/approve", response_model=CmsContentResponse)
def approve_cms_content(
    content_id: str,
    req: CmsWorkflowActionRequest,
    _: bool = Depends(verify_content_ops_admin),
    role: str = Depends(_role),
) -> CmsContentResponse:
    try:
        return ApproveContent(repo=_repo()).execute(
            content_id=content_id,
            actor_role=role,
            actor_id=_actor(role),
            comments=req.comments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/content/{content_id}/publish", response_model=CmsContentResponse)
def publish_cms_content(
    content_id: str,
    req: CmsWorkflowActionRequest,
    _: bool = Depends(verify_content_ops_admin),
    role: str = Depends(_role),
) -> CmsContentResponse:
    try:
        return PublishContent(repo=_repo()).execute(
            content_id=content_id,
            actor_role=role,
            actor_id=_actor(role),
            comments=req.comments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/content/{content_id}/archive", response_model=CmsContentResponse)
def archive_cms_content(
    content_id: str,
    req: CmsWorkflowActionRequest,
    _: bool = Depends(verify_content_ops_admin),
    role: str = Depends(_role),
) -> CmsContentResponse:
    try:
        return ArchiveContent(repo=_repo()).execute(
            content_id=content_id,
            actor_role=role,
            actor_id=_actor(role),
            comments=req.comments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/content/{content_id}/rollback", response_model=CmsContentResponse)
def rollback_cms_content(
    content_id: str,
    req: CmsWorkflowActionRequest,
    _: bool = Depends(verify_content_ops_admin),
    role: str = Depends(_role),
) -> CmsContentResponse:
    try:
        if req.version_number is None:
            raise ValueError("version_number la bat buoc khi rollback.")
        return RollbackContent(repo=_repo()).execute(
            content_id=content_id,
            version_number=req.version_number,
            actor_role=role,
            actor_id=_actor(role),
            comments=req.comments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/content/{content_id}/versions", response_model=list[CmsContentVersionResponse])
def cms_versions(
    content_id: str,
    _: bool = Depends(verify_content_ops_admin),
) -> list[CmsContentVersionResponse]:
    return ListContentVersions(repo=_repo()).execute(content_id=content_id)


@router.get("/review-queue", response_model=list[CmsReviewTaskResponse])
def cms_review_queue(
    _: bool = Depends(verify_content_ops_admin),
) -> list[CmsReviewTaskResponse]:
    return ListReviewQueue(repo=_repo()).execute()


@router.get("/analytics/overview")
def cms_analytics_overview(_: bool = Depends(verify_content_ops_admin)) -> dict[str, object]:
    return GetAnalyticsOverview(repo=_repo()).execute()


@router.get("/analytics/content/{content_id}", response_model=CmsAnalyticsResponse)
def cms_content_analytics(
    content_id: str,
    _: bool = Depends(verify_content_ops_admin),
) -> CmsAnalyticsResponse:
    return GetContentAnalytics(repo=_repo()).execute(content_id=content_id)


@router.post("/analytics/content/{content_id}/record", response_model=CmsAnalyticsResponse)
def cms_record_analytics(
    content_id: str,
    req: CmsAnalyticsRecordRequest,
    _: bool = Depends(verify_content_ops_admin),
) -> CmsAnalyticsResponse:
    try:
        return RecordContentAnalytics(repo=_repo()).execute(content_id=content_id, event_type=req.event_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ai/generate-draft", response_model=CmsContentResponse)
def cms_generate_ai_draft(
    req: CmsAiDraftRequest,
    _: bool = Depends(verify_content_ops_admin),
    role: str = Depends(_role),
) -> CmsContentResponse:
    try:
        return GenerateAiDraft(repo=_repo()).execute(
            content_type=req.content_type,
            title=req.title,
            prompt=req.prompt,
            locale=req.locale,
            owner_team=req.owner_team,
            risk_category=req.risk_category,
            actor_role=role,
            actor_id=_actor(role),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
