from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class CmsContentItem:
    content_id: str
    content_type: str
    slug: str
    title: str
    locale: str
    owner_team: str
    risk_category: str
    workflow_state: str
    current_version: int
    published_version: int | None
    created_by: str
    updated_by: str
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class CmsContentVersion:
    version_id: str
    content_id: str
    version_number: int
    payload: dict[str, object]
    status: str
    origin: str
    change_summary: str | None
    created_by: str
    reviewed_by: str | None = None
    compliance_reviewed_by: str | None = None
    published_by: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    published_at: str | None = None


@dataclass(frozen=True)
class CmsReviewTask:
    task_id: str
    content_id: str
    version_number: int
    review_type: str
    assignee_role: str
    status: str
    created_by: str
    reviewer_id: str | None = None
    comments: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None


@dataclass(frozen=True)
class CmsPublishEvent:
    event_id: str
    content_id: str
    version_number: int
    action: str
    actor_role: str
    actor_id: str
    notes: str | None = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class CmsAiGenerationLog:
    generation_id: str
    content_type: str
    content_id: str
    prompt_version: str
    model_name: str
    input_summary: str
    output_summary: str
    created_by: str
    created_at: str = field(default_factory=utc_now_iso)
