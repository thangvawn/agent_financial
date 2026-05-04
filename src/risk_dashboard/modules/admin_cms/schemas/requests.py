from __future__ import annotations

from pydantic import BaseModel, Field


class CmsUpsertContentRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=120)
    title: str = Field(..., min_length=2, max_length=200)
    locale: str = Field(default="vi-VN", min_length=2, max_length=20)
    owner_team: str = Field(default="education", min_length=2, max_length=60)
    risk_category: str = Field(default="education", min_length=2, max_length=60)
    payload: dict[str, object] = Field(default_factory=dict)
    change_summary: str | None = Field(default=None, max_length=500)


class CmsWorkflowActionRequest(BaseModel):
    comments: str | None = Field(default=None, max_length=2000)
    version_number: int | None = Field(default=None, ge=1)


class CmsAnalyticsRecordRequest(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=40)


class CmsAiDraftRequest(BaseModel):
    content_type: str = Field(..., min_length=2, max_length=60)
    title: str = Field(..., min_length=2, max_length=200)
    prompt: str = Field(..., min_length=5, max_length=1000)
    locale: str = Field(default="vi-VN", min_length=2, max_length=20)
    owner_team: str = Field(default="education", min_length=2, max_length=60)
    risk_category: str = Field(default="education", min_length=2, max_length=60)
