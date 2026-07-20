from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.news_intelligence.application.enrichment import enrich_article
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.platform.database import reset_app_state_tables


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
