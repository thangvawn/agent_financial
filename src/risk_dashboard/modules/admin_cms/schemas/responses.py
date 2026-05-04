from __future__ import annotations

from pydantic import BaseModel


class CmsContentVersionResponse(BaseModel):
    version_id: str
    version_number: int
    status: str
    origin: str
    change_summary: str | None = None
    created_by: str
    reviewed_by: str | None = None
    compliance_reviewed_by: str | None = None
    published_by: str | None = None
    created_at: str
    published_at: str | None = None
    payload: dict[str, object]


class CmsContentResponse(BaseModel):
    content_id: str
    content_type: str
    slug: str
    title: str
    locale: str
    owner_team: str
    risk_category: str
    workflow_state: str
    current_version: int
    published_version: int | None = None
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str
    latest_payload: dict[str, object]
    latest_origin: str


class CmsReviewTaskResponse(BaseModel):
    task_id: str
    content_id: str
    version_number: int
    review_type: str
    assignee_role: str
    status: str
    created_by: str
    reviewer_id: str | None = None
    comments: str | None = None
    created_at: str
    completed_at: str | None = None


class CmsAnalyticsResponse(BaseModel):
    content_id: str
    impression_count: int
    open_count: int
    completion_count: int
    clickthrough_count: int
    last_event_at: str | None = None


class CmsStatusResponse(BaseModel):
    enabled: bool
    actor_role: str
    permissions: list[str]
    supported_content_types: list[str]
    workflow_states: list[str]
    analytics_overview: dict[str, object]
