"""Social read model and immutable, account-bound pagination."""

from __future__ import annotations

import hashlib
import json
import re
import time
from uuid import uuid4

from risk_dashboard.modules.news_intelligence.domain.social_content import ERRORS
from risk_dashboard.modules.news_intelligence.domain.social_topics import (
    build_topics,
    normalize_symbol,
    same_discussion,
)
from risk_dashboard.modules.news_intelligence.infrastructure.agent_reach_adapter import (
    AgentReachAdapter,
)
from risk_dashboard.modules.news_intelligence.infrastructure.social_jobs import recent_jobs
from risk_dashboard.modules.news_intelligence.infrastructure.social_repository import (
    get_post,
    list_posts,
    sources,
)
from risk_dashboard.platform.database.connection import open_db


class SocialCursorError(ValueError):
    def __init__(self, message: str, status: int = 400):
        self.status = status
        super().__init__(message)


def status(owner: str) -> dict:
    rows = sources(owner)
    jobs = recent_jobs(owner)
    latest = {}
    for job in jobs:
        latest.setdefault(job["source_id"], job)
    with open_db() as conn:
        heartbeat = conn.execute(
            "SELECT heartbeat_at FROM social_worker_state WHERE id='collector'"
        ).fetchone()
        running = conn.execute(
            "SELECT 1 FROM social_jobs WHERE status='running' AND lease_until>?", (time.time(),)
        ).fetchone()
    worker_active = bool(running or heartbeat and heartbeat[0] > time.time() - 30)
    return {
        "sources": [
            {
                **{k: v for k, v in r.items() if k != "account_id"},
                "error_message": ERRORS.get(r["last_error"]),
                "partial_count": latest.get(r["id"], {}).get("partial_count", 0),
            }
            for r in rows
        ],
        "collector_configured": AgentReachAdapter().available() or worker_active,
        "worker_active": worker_active,
        "data_updated_at": max(
            [r["last_success_at"] or 0 for r in rows]
            + [j["updated_at"] for j in jobs if j["status"] == "succeeded"],
            default=0,
        )
        or None,
        "jobs": [public_job(r) for r in jobs],
        "sampling_mode": "search_sample",
        "completeness_verified": False,
        "attention": {
            "available": False,
            "reason": "Mẫu tìm kiếm chưa đủ độ phủ để tính mức tăng chú ý.",
        },
    }


def public_job(row: dict) -> dict:
    return {
        **{
            k: row[k]
            for k in (
                "id",
                "source_id",
                "platform",
                "status",
                "created_at",
                "updated_at",
                "result_count",
                "partial_count",
                "error_code",
            )
        },
        "message": ERRORS.get(row["error_code"]),
    }


def _summary(topic: dict) -> dict:
    lead = topic["posts"][0]
    return {k: v for k, v in topic.items() if k not in {"posts", "evidence"}} | {
        "market": lead["market"],
        "platforms": sorted({p["platform"] for p in topic["posts"]}),
        "preview": (lead.get("transcript") or lead["text"])[:240],
        "lead": {
            k: lead[k]
            for k in (
                "id",
                "title",
                "url",
                "author",
                "platform",
                "saved",
                "published_at",
                "time_precision",
                "first_seen_at",
                "content_kind",
            )
        },
    }


def feed(owner: str, filters: dict, limit: int = 20, cursor: str | None = None) -> dict:
    key = hashlib.sha256(json.dumps(filters, sort_keys=True).encode()).hexdigest()
    now = time.time()
    if cursor:
        if not re.fullmatch(r"[a-f0-9]{32}:[0-9]{1,7}", cursor):
            raise SocialCursorError("Trang tiếp theo không hợp lệ.")
        sid, offset = cursor.split(":")
        offset = int(offset)
        with open_db() as conn:
            row = conn.execute(
                "SELECT * FROM social_feed_snapshots WHERE id=? AND account_id=?", (sid, owner)
            ).fetchone()
        if not row or row["expires_at"] < now:
            raise SocialCursorError("Danh sách đã hết hạn. Vui lòng tải lại.", 410)
        if row["filter_key"] != key:
            raise SocialCursorError("Trang tiếp theo không khớp bộ lọc.")
        payload = json.loads(row["payload_json"])
        if offset >= len(payload["topics"]):
            raise SocialCursorError("Trang nằm ngoài danh sách.")
    else:
        posts = list_posts(owner, hours=filters["hours"], saved=filters["scope"] == "saved")
        wanted = set()
        with open_db() as conn:
            enabled = {
                r[0]
                for r in conn.execute(
                    "SELECT id FROM social_sources WHERE account_id=? AND enabled=1", (owner,)
                )
            }
            membership = {}
            for r in conn.execute(
                "SELECT post_id,source_id FROM social_post_sources WHERE account_id=?", (owner,)
            ):
                membership.setdefault(r[0], set()).add(r[1])
            if filters["scope"] == "watchlist":
                wanted = {
                    normalize_symbol(r[0])
                    for r in conn.execute(
                        "SELECT symbol FROM mp_watchlist_items WHERE user_id=?", (owner,)
                    )
                }

        def matches(p: dict) -> bool:
            if (
                filters["scope"] != "saved"
                and membership.get(p["id"])
                and not membership[p["id"]].intersection(enabled)
            ):
                return False
            if filters["market"] != "all" and p["market"] != filters["market"]:
                return False
            if filters["platform"] != "all" and p["platform"] != filters["platform"]:
                return False
            if (
                filters["q"]
                and filters["q"].casefold() not in (p["title"] + " " + p["text"]).casefold()
            ):
                return False
            if filters["scope"] == "watchlist" and not any(
                x["symbol"] in wanted for x in p.get("entities", [])
            ):
                return False
            return True

        topics = [_summary(t) for t in build_topics([p for p in posts if matches(p)])]
        payload = {
            "topics": topics,
            "total": len(topics),
            "post_count": sum(t["post_count"] for t in topics),
            "as_of": now,
        }
        sid, offset = uuid4().hex, 0
        if len(topics) > limit:
            with open_db() as conn:
                conn.execute("DELETE FROM social_feed_snapshots WHERE expires_at<?", (now,))
                conn.execute(
                    """DELETE FROM social_feed_snapshots WHERE id IN
                    (SELECT id FROM social_feed_snapshots WHERE account_id=?
                     ORDER BY expires_at DESC LIMIT -1 OFFSET 9)""",
                    (owner,),
                )
                conn.execute(
                    "INSERT INTO social_feed_snapshots VALUES (?,?,?,?,?)",
                    (sid, owner, key, json.dumps(payload), now + 900),
                )
    end = offset + limit
    page = payload["topics"][offset:end]
    with open_db() as conn:
        saved_ids = {
            r[0]
            for r in conn.execute(
                "SELECT post_id FROM social_saved_posts WHERE account_id=?", (owner,)
            )
        }
    for topic in page:
        topic["lead"]["saved"] = topic["lead"]["id"] in saved_ids
    return {
        **payload,
        "topics": page,
        "has_more": end < payload["total"],
        "next_cursor": f"{sid}:{end}" if end < payload["total"] else None,
        "sampling_mode": "search_sample",
    }


def topic_detail(owner: str, post_id: str) -> dict | None:
    anchor = get_post(owner, post_id)
    if not anchor:
        return None
    candidates = list_posts(owner, hours=168)
    others = [
        p
        for p in candidates
        if p["id"] != anchor["id"]
        and same_discussion(anchor, p)
        and abs(
            (p.get("published_ts") or p["first_seen_at"])
            - (anchor.get("published_ts") or anchor["first_seen_at"])
        )
        <= 172800
    ]
    topics = build_topics([anchor, *others])
    topic = next(t for t in topics if any(p["id"] == post_id for p in t["posts"]))
    symbols = {x["symbol"] for x in topic["entities"]}
    with open_db() as conn:
        rows = conn.execute(
            "SELECT article_id,headline,url,source,tickers_json FROM news_articles "
            "WHERE sort_ts>? ORDER BY sort_ts DESC LIMIT 500",
            (time.time() - 7 * 86400,),
        ).fetchall()
    topic["related_news"] = [
        {k: r[k] for k in ("article_id", "headline", "url", "source")}
        for r in rows
        if symbols.intersection(json.loads(r["tickers_json"] or "[]"))
    ][:5]
    return topic
