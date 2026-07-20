from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from risk_dashboard.modules.news_intelligence.application.finnhub_desk import get_finnhub_desk_snapshot
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService
from risk_dashboard.modules.news_intelligence.safety.news_policy import build_safety_block

router = APIRouter(prefix="/news", tags=["News Intelligence"])


class SaveNewsRequest(BaseModel):
    user_id: str = Field(default="anonymous", max_length=120)
    note: str = Field(default="", max_length=500)


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
    sentiment: str | None = Query(default=None),
    impact_level: str | None = Query(default=None),
    importance: str | None = Query(default=None),
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
        sentiment=sentiment,
        impact_level=impact_level,
        importance=importance,
    )


@router.get("/articles/{article_id}")
def get_article_detail(article_id: str) -> dict:
    detail = NewsIntelligenceService().get_article_detail(article_id)
    if not detail:
        return {
            "error": "Article not found",
            "article_id": article_id,
            "safety": build_safety_block(),
        }
    return detail


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
        "data_quality": feed["data_quality"],
        "safety": feed["safety"],
    }


@router.get("/pulse")
def get_news_pulse(
    category: str | None = Query(default=None),
    region: str | None = Query(default=None),
    source_group: str | None = Query(default=None),
    preset: str | None = Query(default=None),
    time_range_hours: int = Query(default=24, ge=1, le=168),
) -> dict:
    feed = NewsIntelligenceService().get_feed(
        category=category,
        limit=80,
        region=region,
        source_group=source_group,
        preset=preset,
        time_range_hours=time_range_hours,
    )
    return {
        "as_of": feed["as_of"],
        "freshness": feed["freshness"],
        "confidence_label": feed["confidence_label"],
        "pulse": feed["pulse"],
        "data_quality": feed["data_quality"],
        "safety": feed["safety"],
    }


# ── Saved News ──────────────────────────────────────────────────────────

@router.post("/articles/{article_id}/save")
def save_news(article_id: str, req: SaveNewsRequest) -> dict:
    svc = NewsIntelligenceService()
    svc.save_article(user_id=req.user_id, article_id=article_id, note=req.note)
    return {"saved": True, "article_id": article_id, "safety": build_safety_block()}


@router.delete("/articles/{article_id}/save")
def unsave_news(article_id: str, user_id: str = Query(default="anonymous")) -> dict:
    svc = NewsIntelligenceService()
    svc.unsave_article(user_id=user_id, article_id=article_id)
    return {"saved": False, "article_id": article_id, "safety": build_safety_block()}


@router.get("/saved")
def get_saved_news(
    user_id: str = Query(default="anonymous"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    svc = NewsIntelligenceService()
    items = svc.get_saved_articles(user_id=user_id, limit=limit)
    return {
        "saved_articles": items,
        "count": len(items),
        "safety": build_safety_block(),
    }


@router.get("/desk/finnhub")
def get_finnhub_macro_desk(
    force: bool = Query(default=False),
    calendar_days: int = Query(default=14, ge=1, le=30),
    include_quotes: bool = Query(
        default=False,
        description="If true, include SPY/QQQ/GLD/BTC/EUR quote strip (extra Finnhub calls). News UI uses calendar only.",
    ),
) -> dict:
    """Cached Finnhub economic calendar; optional quote strip when include_quotes=true."""
    payload = get_finnhub_desk_snapshot(
        force=force,
        calendar_days=calendar_days,
        include_quotes=include_quotes,
    )
    payload["safety"] = build_safety_block()
    return payload


@router.get("/source-health")
def get_source_health() -> dict:
    svc = NewsIntelligenceService()
    return {
        "sources": svc.get_source_health(),
        "safety": build_safety_block(),
    }
