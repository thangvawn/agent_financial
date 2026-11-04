from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.modules.news_intelligence.api.public import router
from risk_dashboard.modules.news_intelligence.application.enrichment import enrich_article
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.platform.database import (
    clear_db_path_cache,
    clear_migration_cache,
    open_app_state_db,
)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(tmp_path / "news.db"))
    clear_db_path_cache()
    clear_migration_cache()
    yield
    clear_db_path_cache()
    clear_migration_cache()


def article(index, headline=None):
    now = datetime.now(timezone.utc)
    return NewsArticle(
        article_id=str(index),
        headline=headline or f"alpha{index} beta{index} gamma{index}",
        summary="",
        source="Test",
        source_id="test",
        source_tier=3,
        source_flag="local_media",
        region="VN",
        category="markets",
        url=f"https://example.test/{index}",
        published_at=now.isoformat(),
        fetched_at=now.isoformat(),
        sort_ts=int(now.timestamp()),
        importance_score=90 if index < 90 else 40,
        importance_label="critical" if index < 90 else "low",
    )


@pytest.mark.parametrize(
    ("headline", "sentiment"),
    [
        ("Cổ phiếu tăng trưởng mạnh, lợi nhuận doanh nghiệp tăng kỷ lục", "positive"),
        ("Cổ phiếu giảm mạnh, doanh nghiệp thua lỗ và phá sản", "negative"),
        ("Doanh nghiệp không còn thua lỗ", "unknown"),
        ("Lợi nhuận chưa tăng trưởng", "unknown"),
        ("Giá giữ ổn định, lãi suất không đổi", "neutral"),
        ("Thông báo lịch họp cổ đông", "unknown"),
        ("Lạm phát tăng mạnh", "unknown"),
        ("Chi phí giảm mạnh", "unknown"),
        ("Thị trường chưa ổn định", "unknown"),
    ],
)
def test_vietnamese_sentiment_and_negation(headline, sentiment):
    assert enrich_article(article(1, headline)).sentiment == sentiment


def test_classification_preserves_vietnamese_diacritics():
    investment = enrich_article(
        article(1, "Hải Phòng dự kiến chi hơn 38.760 tỉ đồng đầu tư công năm 2027")
    )
    oil = enrich_article(article(2, "Giá dầu tăng sau thông báo của OPEC"))
    assert investment.category != "commodities"
    assert "Oil" not in investment.affected_markets
    assert oil.category == "commodities" and "Oil" in oil.affected_markets


@pytest.fixture
def client(monkeypatch):
    rows = [article(index) for index in range(160)]
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: (rows, {"source_count": 1, "successful_source_count": 1}),
    )
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/public")
    return TestClient(app)


def test_importance_filter_before_limit_and_stable_scores(client):
    base = "/api/v1/public/news/feed"
    filtered = client.get(base, params={"importance": "low", "limit": 20}).json()
    assert filtered["total"] == 70
    assert len(filtered["articles"]) == 20 and filtered["has_more"]
    item = filtered["articles"][0]
    searched = client.get(base, params={"q": item["headline"]}).json()["articles"][0]
    detail = client.get(f"/api/v1/public/news/articles/{item['article_id']}").json()["article"]
    assert item["importance_score"] == searched["importance_score"] == detail["importance_score"]
    assert item["importance_label"] == searched["importance_label"] == detail["importance_label"]


def test_cursor_keeps_full_snapshot_through_refresh(client):
    base = "/api/v1/public/news/feed"
    first = client.get(base, params={"limit": 30}).json()
    ids = [a["article_id"] for a in first["articles"]]
    # Simulate a new ranking while the reader is paging through the old snapshot.
    with open_app_state_db() as conn:
        conn.execute("UPDATE news_articles SET importance_score = 100 - importance_score")
    cursor = first["next_cursor"]
    while cursor:
        response = client.get(base, params={"limit": 30, "cursor": cursor})
        assert response.status_code == 200
        page = response.json()
        ids.extend(a["article_id"] for a in page["articles"])
        assert all(a["importance_score"] in {90, 40} for a in page["articles"])
        cursor = page["next_cursor"]
    assert len(ids) == len(set(ids)) == 160
    assert set(ids) == {str(i) for i in range(160)}
    assert (
        client.get(base, params={"cursor": first["next_cursor"], "q": "other"}).status_code == 400
    )
    assert client.get(base, params={"cursor": "bad"}).status_code == 400
    with open_app_state_db() as conn:
        conn.execute("UPDATE news_feed_snapshots SET expires_at=0")
    assert client.get(base, params={"cursor": first["next_cursor"]}).status_code == 410


def test_legacy_cache_is_reclassified_once_without_changing_originals(monkeypatch):
    old = article(1, "Hải Phòng dự kiến chi đầu tư công")
    old.source_id = "vietnamplus_economy"
    old.category = "commodities"
    old.affected_markets = ["Oil"]
    svc = NewsIntelligenceService()
    with open_app_state_db() as conn:
        svc._upsert_article(conn, old)
    monkeypatch.setattr(svc, "_needs_refresh", lambda conn: False)
    fixed = svc.get_feed(region="VN", time_range_hours=168)["articles"][0]
    assert fixed["headline"] == old.headline and fixed["published_at"] == old.published_at
    assert fixed["category"] == "macro" and "Oil" not in fixed["affected_markets"]
    with open_app_state_db() as conn:
        conn.execute("UPDATE news_articles SET importance_score=12")
    assert svc.get_feed(region="VN", time_range_hours=168)["articles"][0]["importance_score"] == 12


def test_failed_sources_do_not_advance_data_update_time(client, monkeypatch):
    endpoint = "/api/v1/public/news/feed"
    first = client.get(endpoint).json()
    assert first["data_updated_at"]
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: ([], {"source_count": 1, "successful_source_count": 0}),
    )
    failed = client.get(endpoint, params={"force": True}).json()
    assert failed["data_updated_at"] == first["data_updated_at"]
    assert failed["successful_source_count"] == 0
    assert failed["freshness"] != "fresh"
    assert failed["total"] == first["total"]
