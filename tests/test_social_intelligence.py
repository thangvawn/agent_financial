import time
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.modules.auth.api.public import router as auth_router
from risk_dashboard.modules.news_intelligence.api.social import router
from risk_dashboard.modules.news_intelligence.application.social_worker import run_once
from risk_dashboard.modules.news_intelligence.domain.social_content import (
    canonical_url,
    normalize_item,
)
from risk_dashboard.modules.news_intelligence.domain.social_topics import entities
from risk_dashboard.modules.news_intelligence.infrastructure.agent_reach_adapter import (
    AgentReachAdapter,
    ReachFailure,
)
from risk_dashboard.modules.news_intelligence.infrastructure.social_jobs import (
    claim_job,
    enqueue,
    finish_job,
)
from risk_dashboard.modules.news_intelligence.infrastructure.social_repository import save_posts
from risk_dashboard.platform.database import clear_db_path_cache, clear_migration_cache
from risk_dashboard.platform.database.connection import open_db

BASE = "/news/social"


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(tmp_path / "social.db"))
    monkeypatch.setenv("ENABLE_SOCIAL_WORKER", "0")
    clear_db_path_cache()
    clear_migration_cache()
    app = FastAPI()
    app.include_router(router)
    app.include_router(auth_router)
    client = TestClient(app)
    users = []
    for i in range(2):
        result = client.post(
            "/auth/register",
            json={
                "email": f"social{i}@example.test",
                "name": f"Reader {i}",
                "password": "Test-password-1234!",
            },
        )
        assert result.status_code == 200, result.text
        body = result.json()
        users.append(
            (body["profile"]["account_id"], {"Authorization": f"Bearer {body['session_id']}"})
        )
    yield client, users
    clear_db_path_cache()
    clear_migration_cache()


def payload(i=1, title=None, market="vietnam", published=True):
    return normalize_item(
        {
            "url": f"https://www.youtube.com/watch?v={i:011d}",
            "title": title or f"Bản tin chủ đề_{i} nhận định_{i} công ty_{i}",
            "author": f"Research {i}",
            "text": f"Nội dung riêng {i} có nguồn gốc và thông tin về thị trường.",
            "published_at": datetime.now(timezone.utc).isoformat() if published else None,
        },
        platform="youtube",
        market=market,
        backend="fixture",
        content_kind="description",
    )


def insert(owner, rows):
    with open_db() as conn:
        save_posts(conn, owner, rows)


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1/admin",
        "file:///etc/passwd",
        "https://youtube.com.evil.test/watch?v=12345678901",
        "https://user:pass@youtube.com/watch?v=12345678901",
        "https://youtube.com:443/watch?v=12345678901",
        "https://www.youtube.com/playlist?list=123",
        "https://www.reddit.com/user/user",
        "https://www.facebook.com/groups/123",
    ],
)
def test_import_url_boundaries(url):
    with pytest.raises(ValueError):
        canonical_url(url)


def test_youtube_aliases_share_identity():
    assert canonical_url("https://youtu.be/12345678901?t=20") == canonical_url(
        "https://www.youtube.com/watch?v=12345678901&list=123"
    )


def test_auth_and_account_isolation(ctx):
    client, ((owner, a), (_, b)) = ctx
    assert client.get(BASE + "/feed").status_code == 401
    insert(owner, [payload()])
    topic = client.get(BASE + "/feed", headers=a).json()["topics"][0]
    assert client.get(BASE + "/feed", headers=b).json()["total"] == 0
    assert client.get(BASE + f"/topics/{topic['id']}", headers=b).status_code == 404
    assert client.post(BASE + f"/posts/{topic['id']}/save", headers=b).status_code == 404
    assert client.post(BASE + f"/posts/{topic['id']}/save", headers=a).status_code == 200
    assert client.get(BASE + "/feed?scope=saved", headers=a).json()["total"] == 1
    assert client.get(BASE + "/feed", headers=a).headers["cache-control"] == "private, no-store"


def test_immutable_cursor_filters_and_scope(ctx):
    client, ((owner, a), (_, b)) = ctx
    insert(owner, [payload(i, market="global" if i % 2 else "vietnam") for i in range(1, 31)])
    first = client.get(BASE + "/feed?market=vietnam&limit=5", headers=a).json()
    assert first["total"] == 15
    cursor = first["next_cursor"]
    insert(owner, [payload(100)])
    second = client.get(
        BASE + "/feed", params={"market": "vietnam", "limit": 5, "cursor": cursor}, headers=a
    ).json()
    assert second["total"] == 15
    assert not {r["id"] for r in first["topics"]} & {r["id"] for r in second["topics"]}
    assert (
        client.get(
            BASE + "/feed", params={"market": "global", "cursor": cursor}, headers=a
        ).status_code
        == 400
    )
    assert (
        client.get(
            BASE + "/feed", params={"market": "vietnam", "cursor": cursor}, headers=b
        ).status_code
        == 410
    )


def test_job_deduplication_fencing_and_import_saved(ctx):
    client, ((owner, a), (_, b)) = ctx
    url = "https://www.youtube.com/watch?v=00000000001"
    one = client.post(BASE + "/imports", json={"url": url, "market": "vietnam"}, headers=a).json()
    two = client.post(BASE + "/imports", json={"url": url, "market": "vietnam"}, headers=a).json()
    assert one["id"] == two["id"]
    assert client.get(BASE + f"/jobs/{one['id']}", headers=b).status_code == 404
    job = claim_job()
    assert claim_job() is None
    assert not finish_job({**job, "lease_token": "wrong"}, [payload()])
    old = payload()
    old["published_at"], old["published_ts"] = "2020-01-01", 1577836800
    assert finish_job(job, [old])
    assert client.get(BASE + "/feed", headers=a).json()["total"] == 0
    assert client.get(BASE + "/feed?scope=saved", headers=a).json()["total"] == 1


def test_replay_preserves_transcript_and_revisions(ctx):
    client, ((owner, a), _) = ctx
    full = payload()
    full.update(transcript="Bản phụ đề đã đọc từ nguồn", transcript_status="available")
    insert(owner, [full, full])
    shallow = {**full, "transcript": "", "transcript_status": "not_requested"}
    insert(owner, [shallow])
    result = client.get(BASE + "/feed", headers=a).json()
    assert result["total"] == 1
    detail = client.get(BASE + f"/topics/{result['topics'][0]['id']}", headers=a).json()
    assert detail["posts"][0]["revision"] == 1
    assert detail["posts"][0]["transcript"] == full["transcript"]
    assert detail["evidence"][0]["content_kind"] == "transcript"
    insert(owner, [{**full, "text": "Nội dung đã sửa"}])
    assert (
        client.get(BASE + f"/topics/{result['topics'][0]['id']}", headers=a).json()["posts"][0][
            "revision"
        ]
        == 2
    )


def test_disabled_source_cancels_queued_and_inflight(ctx):
    client, ((_, a), _) = ctx
    created = client.post(BASE + "/refresh", headers=a).json()["jobs"]
    job = claim_job()
    client.patch(BASE + f"/subscriptions/{job['source_id']}", json={"enabled": False}, headers=a)
    assert finish_job(job, [payload()])
    assert client.get(BASE + "/feed", headers=a).json()["total"] == 0
    assert len(created) == 4


def test_failure_keeps_cached_data_and_real_error(ctx):
    client, ((owner, a), _) = ctx
    insert(owner, [payload()])
    client.post(BASE + "/refresh", headers=a)

    class Blocked:
        def collect(self, job):
            raise ReachFailure("PLATFORM_BLOCKED")

    result = run_once(Blocked())
    assert result["error_code"] == "PLATFORM_BLOCKED"
    assert client.get(BASE + "/feed", headers=a).json()["total"] == 1
    status = client.get(BASE + "/sources", headers=a).json()
    failed = next(s for s in status["sources"] if s["last_error"])
    assert failed["last_success_at"] is None
    assert status["attention"]["available"] is False


def test_html_comments_and_unknown_dates():
    item = {
        "url": "https://www.reddit.com/r/stocks/comments/abc123/",
        "title": "FPT",
        "author": "original",
        "text": "<script>alert(1)</script> Original post\n"
        "## Top comments (1)\n@other: sell everything",
    }
    result = normalize_item(item, platform="reddit", market="global", backend="public-web")
    assert "other" not in result["text"] and "alert" not in result["text"]
    assert result["published_at"] is None and result["published_ts"] is None


def test_entity_disambiguation():
    assert entities("Natural GAS prices rising in Europe") == []
    result = entities("Cổ phiếu HOSE:GAS và $FPT, Bitcoin")
    assert {x["symbol"] for x in result} == {"GAS", "FPT", "BTC"}
    assert entities("Thị trường chứng khoán hôm nay. VTV Index, nhóm VIP. Đổi USD sang VND.") == []


def test_watchlist_uses_authenticated_owner(ctx):
    client, ((owner, a), (_, b)) = ctx
    insert(owner, [payload(title="Cổ phiếu FPT công bố lợi nhuận")])
    with open_db() as conn:
        conn.execute(
            "INSERT INTO mp_watchlist_items(item_id,user_id,symbol,label,created_at) "
            "VALUES ('wl',?,'FPT','FPT',?)",
            (owner, datetime.now(timezone.utc).isoformat()),
        )
    assert client.get(BASE + "/feed?scope=watchlist", headers=a).json()["total"] == 1
    assert client.get(BASE + "/feed?scope=watchlist", headers=b).json()["total"] == 0


def test_no_provider_calls_on_read(ctx, monkeypatch):
    client, ((_, a), _) = ctx

    def forbidden(*args, **kwargs):
        raise AssertionError("Provider called from HTTP GET")

    monkeypatch.setattr(AgentReachAdapter, "call", forbidden)
    assert client.get(BASE + "/feed", headers=a).status_code == 200
    assert client.get(BASE + "/sources", headers=a).status_code == 200


def test_expired_job_is_reclaimed_without_old_worker_commit(ctx):
    client, ((_, a), _) = ctx
    client.post(BASE + "/imports", json={"url": "https://youtu.be/00000000001"}, headers=a)
    first = claim_job()
    with open_db() as conn:
        conn.execute(
            "UPDATE social_jobs SET lease_until=? WHERE id=?", (time.time() - 1, first["id"])
        )
    second = claim_job()
    assert second["id"] == first["id"] and second["lease_token"] != first["lease_token"]
    assert not finish_job(first, [payload()])
    assert finish_job(second, [payload()])


def test_source_and_market_are_part_of_job_identity(ctx):
    _, ((owner, _), _) = ctx
    with open_db() as conn:
        first = enqueue(conn, owner, "youtube", "search", "same query", "global", "one")
        second = enqueue(conn, owner, "youtube", "search", "same query", "global", "two")
        third = enqueue(conn, owner, "youtube", "search", "same query", "vietnam", "one")
        assert len({first["id"], second["id"], third["id"]}) == 3


def test_removed_source_hidden_but_saved_survives(ctx):
    client, ((owner, a), _) = ctx
    source = client.post(
        BASE + "/subscriptions",
        headers=a,
        json={
            "platform": "youtube",
            "market": "global",
            "query": "bitcoin economy",
            "label": "Bitcoin",
        },
    ).json()["id"]
    with open_db() as conn:
        save_posts(conn, owner, [payload(title="Bitcoin market update", market="global")], source)
        conn.execute(
            "INSERT INTO mp_watchlist_items(item_id,user_id,symbol,label,created_at) "
            "VALUES ('wl-btc',?,'BTC-USD','Bitcoin',?)",
            (owner, datetime.now(timezone.utc).isoformat()),
        )
    feed = client.get(BASE + "/feed?scope=watchlist", headers=a).json()
    assert feed["total"] == 1
    client.post(BASE + f"/posts/{feed['topics'][0]['id']}/save", headers=a)
    assert client.delete(BASE + f"/subscriptions/{source}", headers=a).status_code == 200
    assert client.get(BASE + "/feed", headers=a).json()["total"] == 0
    assert client.get(BASE + "/feed?scope=saved", headers=a).json()["total"] == 1


def test_blocked_detail_propagates_original_error(monkeypatch):
    adapter = AgentReachAdapter()

    def call(platform, action, params):
        if action == "search":
            return {"items": [{"url": "https://youtu.be/00000000001"}]}
        raise ReachFailure("PLATFORM_BLOCKED")

    monkeypatch.setattr(adapter, "call", call)
    with pytest.raises(ReachFailure, match=".") as caught:
        adapter.collect(
            {"platform": "youtube", "action": "search", "target": "finance", "market": "global"}
        )
    assert caught.value.code == "PLATFORM_BLOCKED"


def test_reddit_http200_access_gate_is_not_stored_as_content(ctx, monkeypatch):
    client, ((owner, a), _) = ctx
    url = "https://www.reddit.com/r/stocks/comments/abc123/"
    cached = normalize_item(
        {"url": url, "title": "Original market discussion", "text": "Original excerpt"},
        platform="reddit",
        market="global",
        backend="public-web",
        content_kind="search_excerpt",
    )
    insert(owner, [cached])
    client.post(BASE + "/imports", json={"url": url}, headers=a)
    adapter = AgentReachAdapter()
    monkeypatch.setattr(
        adapter,
        "call",
        lambda *args: {
            "items": [
                {
                    "url": url,
                    "title": "URL Source",
                    "text": "You've been blocked by network security. "
                    "Log in to your Reddit account or use your developer token.",
                }
            ]
        },
    )
    assert run_once(adapter)["error_code"] == "PLATFORM_BLOCKED"
    feed = client.get(BASE + "/feed", headers=a).json()
    assert feed["topics"][0]["title"] == "Original market discussion"
    assert client.get(BASE + "/feed?scope=saved", headers=a).json()["total"] == 0
