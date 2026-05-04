from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from risk_dashboard.modules.news_intelligence.application.news_agent import NewsAnalystAgent, NewsChatContext
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService

router = APIRouter(prefix="/news", tags=["News Intelligence"])


class NewsChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1400)
    conversation_id: str | None = Field(default=None, max_length=80)
    category: str | None = Field(default=None, max_length=40)
    region: str | None = Field(default=None, max_length=20)
    source_group: str | None = Field(default=None, max_length=60)
    preset: str | None = Field(default=None, max_length=60)
    time_range_hours: int = Field(default=168, ge=1, le=168)
    active_article_id: str | None = Field(default=None, max_length=120)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=10)


@router.get("/feed")
def get_news_feed(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=40, ge=1, le=100),
    time_range_hours: int = Query(default=24, ge=1, le=168),
    region: str | None = Query(default=None),
    source_group: str | None = Query(default=None),
    preset: str | None = Query(default=None),
    force: bool = Query(default=False),
) -> dict:
    return NewsIntelligenceService().get_feed(
        category=category,
        query=q,
        limit=limit,
        time_range_hours=time_range_hours,
        region=region,
        source_group=source_group,
        preset=preset,
        force=force,
    )


@router.get("/clusters")
def get_news_clusters(
    category: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    time_range_hours: int = Query(default=24, ge=1, le=168),
    region: str | None = Query(default=None),
    source_group: str | None = Query(default=None),
    preset: str | None = Query(default=None),
) -> dict:
    feed = NewsIntelligenceService().get_feed(
        category=category,
        limit=max(limit * 4, 40),
        time_range_hours=time_range_hours,
        region=region,
        source_group=source_group,
        preset=preset,
    )
    return {
        "as_of": feed["as_of"],
        "freshness": feed["freshness"],
        "confidence_label": feed["confidence_label"],
        "clusters": feed["clusters"][:limit],
    }


@router.get("/pulse")
def get_news_pulse(
    region: str | None = Query(default=None),
    source_group: str | None = Query(default=None),
    preset: str | None = Query(default=None),
) -> dict:
    feed = NewsIntelligenceService().get_feed(limit=80, region=region, source_group=source_group, preset=preset)
    return {
        "as_of": feed["as_of"],
        "freshness": feed["freshness"],
        "confidence_label": feed["confidence_label"],
        "pulse": feed["pulse"],
    }


@router.post("/chat")
def news_chat(req: NewsChatRequest) -> dict:
    context = NewsChatContext(
        category=req.category,
        region=req.region,
        source_group=req.source_group,
        preset=req.preset,
        time_range_hours=req.time_range_hours,
        active_article_id=req.active_article_id,
        history=tuple(req.history[-8:]),
    )
    return NewsAnalystAgent().respond(message=req.message, context=context, conversation_id=req.conversation_id)
