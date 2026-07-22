from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.news_intelligence.application.enrichment import enrich_article
from risk_dashboard.modules.news_intelligence.application.highlights import resolve_period_window
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.platform.database import (
    clear_db_path_cache,
    clear_migration_cache,
    open_app_state_db,
    reset_app_state_tables,
)


@pytest.fixture(autouse=True)
def isolated_news_db(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(tmp_path / "news_intelligence.sqlite3"))
    clear_db_path_cache()
    clear_migration_cache()
    yield
    clear_db_path_cache()
    clear_migration_cache()


def _article(
    article_id: str,
    headline: str,
    *,
    source_id: str = "fed_press",
    source: str = "Federal Reserve",
    region: str = "US",
    category: str = "macro",
) -> NewsArticle:
    now = datetime.now(timezone.utc)
    return enrich_article(
        NewsArticle(
            article_id=article_id,
            headline=headline,
            summary="Inflation and rate policy remain in focus for global markets.",
            source=source,
            source_id=source_id,
            source_tier=1,
            source_flag="official",
            region=region,
            category=category,
            url=f"https://example.com/{article_id}",
            published_at=now.isoformat(),
            fetched_at=now.isoformat(),
            sort_ts=int(now.timestamp()),
        )
    )


class FakeProducer:
    def fetch(self):
        return (
            [
                _article("a1", "Fed signals rate patience as markets digest inflation risk"),
                _article("a2", "Fed officials discuss inflation risk and rate outlook", source_id="bbc_business", source="BBC Business"),
                _article("a3", "Bitcoin rally lifts crypto risk appetite", source_id="coindesk", source="CoinDesk", category="crypto"),
                _article("a4", "VN stocks rise as banking liquidity improves", source_id="cafef_stock", source="CafeF Chứng khoán", region="VN", category="markets"),
            ],
            {"source_count": 4, "successful_source_count": 4, "errors": []},
        )


class FilterProducer:
    def fetch(self):
        oil = _article(
            "filter-oil",
            "Oil prices fall as gold demand cools after rate relief",
            source_id="oilprice",
            source="OilPrice",
            region="global",
            category="commodities",
        )
        oil.sentiment = "negative"
        oil.impact = "medium"
        oil.importance_label = "medium"
        oil.importance_score = 60
        oil.affected_markets = ["Oil", "Gold"]
        oil.affected_sectors = ["Energy"]
        oil.related_entities = ["OPEC"]

        vn = _article(
            "filter-vn",
            "VN stocks rise as banking liquidity improves",
            source_id="cafef_stock",
            source="CafeF Chứng khoán",
            region="VN",
            category="markets",
        )
        fed = _article("filter-fed", "Fed officials discuss inflation risk and rates")
        return (
            [oil, vn, fed],
            {"source_count": 3, "successful_source_count": 3, "errors": []},
        )


def test_news_intelligence_feed_enriches_and_clusters():
    reset_app_state_tables()
    feed = NewsIntelligenceService(producer=FakeProducer()).get_feed(force=True)

    assert feed["freshness"] == "fresh"
    assert feed["articles"]
    assert feed["articles"][0]["source_flag"] == "official"
    assert feed["pulse"]["article_count"] == 4
    assert any(cluster["article_count"] >= 2 for cluster in feed["clusters"])


def test_news_intelligence_feed_supports_region_and_source_group_filters():
    reset_app_state_tables()
    service = NewsIntelligenceService(producer=FakeProducer())

    vn_feed = service.get_feed(force=True, region="VN")
    crypto_feed = service.get_feed(source_group="crypto")

    assert [article["region"] for article in vn_feed["articles"]] == ["VN"]
    assert [article["source_group"] for article in crypto_feed["articles"]] == ["crypto"]
    assert vn_feed["selected_filters"]["region"] == "VN"


def test_news_feed_search_and_advanced_filters_stack():
    reset_app_state_tables()
    service = NewsIntelligenceService(producer=FilterProducer())

    feed = service.get_feed(
        force=True,
        query="Gold",
        source_group="commodities_energy",
        sentiment="negative",
        impact_level="medium",
        importance="medium",
        time_range_hours=168,
    )

    assert [article["article_id"] for article in feed["articles"]] == ["filter-oil"]
    assert feed["articles"][0]["source_group"] == "commodities_energy"


def test_news_intelligence_public_feed_endpoint(monkeypatch):
    reset_app_state_tables()
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: FakeProducer().fetch(),
    )
    client = TestClient(app)

    response = client.get("/api/v1/public/news/feed?limit=2&force=true")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["articles"]) == 2
    assert payload["confidence_label"] in {"moderate", "limited"}


def test_news_chat_endpoint_removed(monkeypatch):
    reset_app_state_tables()
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: FakeProducer().fetch(),
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/public/news/chat",
        json={"message": "Fed giảm lãi suất?", "time_range_hours": 168},
    )
    assert response.status_code == 404


def test_news_feed_has_today_brief():
    reset_app_state_tables()
    feed = NewsIntelligenceService(producer=FakeProducer()).get_feed(force=True)

    assert "today_brief" in feed
    assert len(feed["today_brief"]) > 0
    brief_item = feed["today_brief"][0]
    assert "headline" in brief_item
    assert "importance_label" in brief_item
    assert "why_it_matters" in brief_item
    assert "affected_markets" in brief_item


def test_news_feed_has_enhanced_pulse():
    reset_app_state_tables()
    feed = NewsIntelligenceService(producer=FakeProducer()).get_feed(force=True)

    pulse = feed["pulse"]
    assert "top_drivers" in pulse
    assert "top_affected_markets" in pulse
    assert "source_health" in pulse
    assert "freshness_status" in pulse
    assert "cluster_summary" in pulse
    assert pulse["source_health"]["status"] in ("healthy", "partial", "degraded")


def test_news_feed_has_safety_and_data_quality():
    reset_app_state_tables()
    feed = NewsIntelligenceService(producer=FakeProducer()).get_feed(force=True)

    assert "safety" in feed
    assert feed["safety"]["no_buy_sell_recommendation"] is True
    assert "data_quality" in feed
    assert "freshness" in feed["data_quality"]
    assert "confidence_label" in feed["data_quality"]


def test_article_detail_has_full_sections(monkeypatch):
    reset_app_state_tables()
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: FakeProducer().fetch(),
    )
    client = TestClient(app)
    client.get("/api/v1/public/news/feed?limit=2&force=true")

    response = client.get("/api/v1/public/news/articles/a1")

    assert response.status_code == 200
    detail = response.json()
    assert "badges" in detail
    assert "info_grid" in detail
    assert "why_this_matters" in detail
    assert "affected_markets" in detail
    assert "what_to_monitor" in detail
    assert "learn_links" in detail
    assert "related_articles" in detail
    assert "original_source" in detail
    assert "safety" in detail
    assert "data_quality" in detail


def test_importance_scoring():
    article = _article("score_test", "Fed signals emergency rate cut amid inflation crisis")
    assert article.importance_score > 0
    assert article.importance_label in ("critical", "high", "medium", "low", "noise")
    assert article.importance_breakdown


def test_impact_mapping():
    article = _article("impact_test", "Oil prices surge as Fed cuts rates and gold rallies")
    assert article.affected_markets
    assert article.what_to_monitor
    assert article.learn_links


def test_saved_news_endpoints(monkeypatch):
    reset_app_state_tables()
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: FakeProducer().fetch(),
    )
    client = TestClient(app)
    client.get("/api/v1/public/news/feed?limit=2&force=true")

    save_response = client.post(
        "/api/v1/public/news/articles/a1/save",
        json={"user_id": "test_user", "note": "important"},
    )
    assert save_response.status_code == 200
    assert save_response.json()["saved"] is True

    list_response = client.get("/api/v1/public/news/saved?user_id=test_user")
    assert list_response.status_code == 200
    saved = list_response.json()
    assert saved["count"] >= 1

    unsave_response = client.delete("/api/v1/public/news/articles/a1/save?user_id=test_user")
    assert unsave_response.status_code == 200
    assert unsave_response.json()["saved"] is False


def test_news_feed_sentiment_filter():
    reset_app_state_tables()
    service = NewsIntelligenceService(producer=FakeProducer())
    feed = service.get_feed(force=True, sentiment="negative")
    for article in feed["articles"]:
        assert article["sentiment"] == "negative"


def test_news_feed_importance_filter():
    reset_app_state_tables()
    service = NewsIntelligenceService(producer=FakeProducer())
    feed = service.get_feed(force=True)
    assert feed["articles"]
    first_score = feed["articles"][0].get("importance_score", 0)
    for article in feed["articles"][1:]:
        assert article.get("importance_score", 0) <= first_score
        first_score = article.get("importance_score", 0)


def test_highlight_period_windows_use_vietnam_calendar_boundaries():
    now = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)

    day = resolve_period_window("day", now=now)
    week = resolve_period_window("week", now=now)
    month = resolve_period_window("month", now=now)

    assert (day.key, day.start.isoformat(), day.end.isoformat()) == (
        "2026-07-22", "2026-07-21T17:00:00+00:00", "2026-07-22T17:00:00+00:00",
    )
    assert (week.key, week.start.isoformat(), week.end.isoformat()) == (
        "2026-W30", "2026-07-19T17:00:00+00:00", "2026-07-26T17:00:00+00:00",
    )
    assert (month.key, month.start.isoformat(), month.end.isoformat()) == (
        "2026-07", "2026-06-30T17:00:00+00:00", "2026-07-31T17:00:00+00:00",
    )


class HighlightProducer:
    def fetch(self):
        now = datetime.now(timezone.utc)
        categories = ("macro", "markets", "commodities", "crypto", "technology")
        articles = []
        for index in range(15):
            headline_index = 0 if index == 1 else index
            article = _article(
                f"highlight-{index}", f"Macro market highlight scenario {headline_index}"
            )
            article.category = categories[index % len(categories)]
            article.importance_score = 100 - index
            article.importance_label = "high"
            article.content_hash = f"unique-{index}"
            article.published_at = (now - timedelta(minutes=index)).isoformat()
            article.sort_ts = int((now - timedelta(minutes=index)).timestamp())
            articles.append(article)
        return articles, {"source_count": 5, "successful_source_count": 5, "errors": []}


def test_highlights_are_ranked_diverse_and_persisted_across_services():
    reset_app_state_tables()
    first = NewsIntelligenceService(producer=HighlightProducer()).get_highlights(
        period="day", limit=10, force=True,
    )

    class FailingProducer:
        def fetch(self):
            raise AssertionError("persisted fresh snapshot should not fetch")

    second = NewsIntelligenceService(producer=FailingProducer()).get_highlights(
        period="day", limit=10,
    )

    assert first["items"] == second["items"]
    assert first["count"] == 10
    assert len({item["article_id"] for item in first["items"]}) == 10
    assert "highlight-1" not in {item["article_id"] for item in first["items"]}
    counts = {}
    for item in first["items"]:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    assert max(counts.values()) == 2

    with open_app_state_db() as conn:
        snapshots = conn.execute(
            "SELECT period_kind, source_run_id FROM news_highlight_snapshots ORDER BY period_kind"
        ).fetchall()
    assert {row["period_kind"] for row in snapshots} == {"day", "week", "month"}
    assert all(row["source_run_id"] for row in snapshots)


def test_missing_current_highlight_snapshot_is_built_on_demand():
    reset_app_state_tables()
    service = NewsIntelligenceService(producer=HighlightProducer())
    service.get_highlights(period="day", force=True)
    with open_app_state_db() as conn:
        conn.execute("DELETE FROM news_highlight_snapshots WHERE period_kind = ?", ("month",))

    payload = service.get_highlights(period="month", limit=5)

    assert payload["period"] == "month"
    assert payload["count"] == 5
    with open_app_state_db() as conn:
        assert conn.execute(
            "SELECT 1 FROM news_highlight_snapshots WHERE period_kind = ? AND period_key = ?",
            ("month", payload["period_key"]),
        ).fetchone()


def test_highlights_serve_persisted_snapshot_when_forced_refresh_fails():
    reset_app_state_tables()
    persisted = NewsIntelligenceService(producer=HighlightProducer()).get_highlights(
        period="week", limit=8, force=True,
    )

    class FailingProducer:
        def fetch(self):
            raise RuntimeError("source unavailable")

    fallback = NewsIntelligenceService(producer=FailingProducer()).get_highlights(
        period="week", limit=8, force=True,
    )

    assert fallback["items"] == persisted["items"]
    assert fallback["data_quality"]["stale_reason"] == (
        "news_refresh_failed_using_persisted_snapshot"
    )


def test_highlights_public_endpoint_and_validation(monkeypatch):
    reset_app_state_tables()
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: HighlightProducer().fetch(),
    )
    client = TestClient(app)

    response = client.get("/api/v1/public/news/highlights?period=month&limit=8&force=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"] == "month"
    assert payload["requested_limit"] == 8
    assert payload["count"] == 8
    assert payload["timezone"] == "Asia/Ho_Chi_Minh"
    assert client.get("/api/v1/public/news/highlights?period=quarter").status_code == 422
    assert client.get("/api/v1/public/news/highlights?limit=4").status_code == 422
    assert client.get("/api/v1/public/news/highlights?limit=11").status_code == 422
