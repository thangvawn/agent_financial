"""Authenticated Social API; source I/O is never performed in an HTTP handler."""

from __future__ import annotations

import time
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.news_intelligence.application import social_service as service
from risk_dashboard.modules.news_intelligence.domain.social_content import canonical_url
from risk_dashboard.modules.news_intelligence.infrastructure.social_jobs import (
    QueueLimit,
    enqueue,
    enqueue_refresh,
)
from risk_dashboard.modules.news_intelligence.infrastructure.social_repository import (
    save_bookmark,
    seed_sources,
)
from risk_dashboard.platform.database.connection import open_db

router = APIRouter(prefix="/news/social", tags=["Social Intelligence"])


def principal(
    response: Response, identity: AuthPrincipal = Depends(resolve_principal)
) -> AuthPrincipal:
    response.headers["Cache-Control"] = "private, no-store"
    return identity


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ImportInput(StrictInput):
    url: str = Field(min_length=10, max_length=2048)
    market: Literal["vietnam", "global"] = "global"

    @field_validator("url")
    @classmethod
    def valid_url(cls, value: str) -> str:
        return canonical_url(value)[2]


class SourceInput(StrictInput):
    platform: Literal["youtube", "reddit"]
    market: Literal["vietnam", "global"]
    query: str = Field(min_length=3, max_length=120)
    label: str = Field(min_length=3, max_length=80)

    @field_validator("query", "label")
    @classmethod
    def text_input(cls, value: str) -> str:
        if any(ord(c) < 32 for c in value) or value.startswith("-"):
            raise ValueError("Nội dung tìm kiếm không hợp lệ.")
        return value


class EnabledInput(StrictInput):
    enabled: bool


@router.get("/feed")
def get_feed(
    market: Literal["all", "vietnam", "global"] = "all",
    platform: Literal["all", "youtube", "reddit"] = "all",
    scope: Literal["all", "watchlist", "saved"] = "all",
    q: str = Query("", max_length=120),
    hours: int = Query(168, ge=1, le=168),
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None, max_length=64),
    user: AuthPrincipal = Depends(principal),
) -> dict:
    try:
        return service.feed(
            user.account_id,
            dict(market=market, platform=platform, scope=scope, q=q.strip(), hours=hours),
            limit,
            cursor,
        )
    except service.SocialCursorError as exc:
        raise HTTPException(exc.status, str(exc)) from exc


@router.get("/sources")
def get_sources(user: AuthPrincipal = Depends(principal)) -> dict:
    return service.status(user.account_id)


@router.get("/topics/{post_id}")
def get_topic(post_id: str, user: AuthPrincipal = Depends(principal)) -> dict:
    result = service.topic_detail(user.account_id, post_id)
    if not result:
        raise HTTPException(404, "Không tìm thấy thảo luận.")
    return result


@router.post("/refresh", status_code=202)
def refresh(user: AuthPrincipal = Depends(principal)) -> dict:
    try:
        return {"jobs": [service.public_job(r) for r in enqueue_refresh(user.account_id)]}
    except QueueLimit as exc:
        raise HTTPException(429, str(exc)) from exc


@router.post("/imports", status_code=202)
def import_post(req: ImportInput, user: AuthPrincipal = Depends(principal)) -> dict:
    platform, _, url = canonical_url(req.url)
    try:
        with open_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            return service.public_job(
                enqueue(conn, user.account_id, platform, "read", url, req.market)
            )
    except QueueLimit as exc:
        raise HTTPException(429, str(exc)) from exc


@router.get("/jobs/{job_id}")
def job_status(job_id: str, user: AuthPrincipal = Depends(principal)) -> dict:
    with open_db() as conn:
        row = conn.execute(
            "SELECT * FROM social_jobs WHERE id=? AND account_id=?", (job_id, user.account_id)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Không tìm thấy lượt thu thập.")
    return service.public_job(dict(row))


@router.post("/subscriptions", status_code=201)
def add_source(req: SourceInput, user: AuthPrincipal = Depends(principal)) -> dict:
    with open_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        seed_sources(conn, user.account_id)
        if (
            conn.execute(
                "SELECT COUNT(*) FROM social_sources WHERE account_id=?", (user.account_id,)
            ).fetchone()[0]
            >= 12
        ):
            raise HTTPException(409, "Tối đa 12 nguồn theo dõi. Hãy bỏ một nguồn trước khi thêm.")
        existing = conn.execute(
            "SELECT id FROM social_sources WHERE account_id=? "
            "AND platform=? AND query=? AND market=?",
            (user.account_id, req.platform, req.query, req.market),
        ).fetchone()
        if existing:
            return {"id": existing[0]}
        source_id = uuid4().hex
        conn.execute(
            """INSERT INTO social_sources(id,account_id,platform,label,query,market,created_at)
            VALUES (?,?,?,?,?,?,?)""",
            (
                source_id,
                user.account_id,
                req.platform,
                req.label,
                req.query,
                req.market,
                time.time(),
            ),
        )
        return {"id": source_id}


@router.patch("/subscriptions/{source_id}")
def update_source(
    source_id: str, req: EnabledInput, user: AuthPrincipal = Depends(principal)
) -> dict:
    with open_db() as conn:
        changed = conn.execute(
            "UPDATE social_sources SET enabled=? WHERE account_id=? AND id=?",
            (int(req.enabled), user.account_id, source_id),
        ).rowcount
        if not changed:
            raise HTTPException(404, "Không tìm thấy nguồn.")
        if not req.enabled:
            conn.execute(
                "DELETE FROM social_jobs WHERE account_id=? AND source_id=? AND status='queued'",
                (user.account_id, source_id),
            )
    return {"id": source_id, "enabled": req.enabled}


@router.delete("/subscriptions/{source_id}")
def delete_source(source_id: str, user: AuthPrincipal = Depends(principal)) -> dict:
    if source_id.startswith(("youtube-", "reddit-")):
        raise HTTPException(409, "Nguồn gợi ý có thể tắt bằng công tắc theo dõi.")
    with open_db() as conn:
        changed = conn.execute(
            "DELETE FROM social_sources WHERE account_id=? AND id=?", (user.account_id, source_id)
        ).rowcount
        if not changed:
            raise HTTPException(404, "Không tìm thấy nguồn.")
        conn.execute(
            "DELETE FROM social_jobs WHERE account_id=? AND source_id=? AND status='queued'",
            (user.account_id, source_id),
        )
    return {"deleted": True}


@router.post("/posts/{post_id}/save")
def save(post_id: str, user: AuthPrincipal = Depends(principal)) -> dict:
    if not save_bookmark(user.account_id, post_id, True):
        raise HTTPException(404, "Không tìm thấy bài viết.")
    return {"saved": True}


@router.delete("/posts/{post_id}/save")
def unsave(post_id: str, user: AuthPrincipal = Depends(principal)) -> dict:
    if not save_bookmark(user.account_id, post_id, False):
        raise HTTPException(404, "Không tìm thấy bài viết.")
    return {"saved": False}
