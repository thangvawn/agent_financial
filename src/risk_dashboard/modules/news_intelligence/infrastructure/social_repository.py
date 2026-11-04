"""Scoped persistence for Social. No network calls while holding a DB connection."""

from __future__ import annotations

import hashlib
import json
import time

from risk_dashboard.modules.news_intelligence.domain.social_content import content_digest
from risk_dashboard.modules.news_intelligence.domain.social_topics import enrich
from risk_dashboard.platform.database.connection import open_db

DEFAULT_SOURCES = (
    ("youtube-vn", "youtube", "Chứng khoán Việt Nam", "chứng khoán Việt Nam VNIndex", "vietnam"),
    (
        "youtube-macro",
        "youtube",
        "Vĩ mô quốc tế",
        "global economy inflation interest rates",
        "global",
    ),
    (
        "reddit-markets",
        "reddit",
        "Thảo luận thị trường",
        "stock market investing economy",
        "global",
    ),
    ("reddit-vn", "reddit", "Góc nhìn về Việt Nam", "Vietnam economy stock market", "vietnam"),
)


def seed_sources(conn, owner: str) -> None:
    conn.executemany(
        """INSERT OR IGNORE INTO social_sources
        (id,account_id,platform,label,query,market,created_at) VALUES (?,?,?,?,?,?,?)""",
        [
            (sid, owner, platform, label, query, market, time.time())
            for sid, platform, label, query, market in DEFAULT_SOURCES
        ],
    )


def sources(owner: str) -> list[dict]:
    with open_db() as conn:
        seed_sources(conn, owner)
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM social_sources WHERE account_id=? ORDER BY created_at,id", (owner,)
            )
        ]


def save_posts(conn, owner: str, payloads: list[dict], source_id: str | None = None) -> int:
    now = time.time()
    for original in payloads:
        payload = enrich(original)
        post_id = hashlib.sha256(
            f"{owner}|{payload['platform']}|{payload['native_id']}".encode()
        ).hexdigest()[:32]
        old = conn.execute(
            "SELECT * FROM social_posts WHERE id=? AND account_id=?", (post_id, owner)
        ).fetchone()
        if old:
            previous = json.loads(old["payload_json"])
            if previous.get("transcript") and not payload.get("transcript"):
                payload["transcript"] = previous["transcript"]
                payload["transcript_status"] = previous["transcript_status"]
            if not payload.get("published_at") and previous.get("published_at"):
                for field in ("published_at", "published_ts", "time_precision"):
                    payload[field] = previous[field]
            if (
                payload.get("content_kind") == "search_excerpt"
                and previous.get("content_kind") == "public_page"
            ):
                payload["text"] = previous["text"]
                payload["content_kind"] = previous["content_kind"]
            payload = enrich(payload)
        digest = content_digest(payload)
        revision = (old["revision"] + int(old["content_hash"] != digest)) if old else 1
        encoded = json.dumps(payload, ensure_ascii=False)
        conn.execute(
            """INSERT INTO social_posts
            (id,account_id,platform,native_id,url,content_hash,published_ts,first_seen_at,fetched_at,revision,payload_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
            content_hash=excluded.content_hash,published_ts=excluded.published_ts,fetched_at=excluded.fetched_at,
            revision=excluded.revision,payload_json=excluded.payload_json""",
            (
                post_id,
                owner,
                payload["platform"],
                payload["native_id"],
                payload["url"],
                digest,
                payload["published_ts"],
                old["first_seen_at"] if old else now,
                now,
                revision,
                encoded,
            ),
        )
        conn.execute(
            "INSERT OR IGNORE INTO social_post_revisions VALUES (?,?,?,?)",
            (post_id, revision, now, encoded),
        )
        if source_id:
            conn.execute(
                "INSERT OR IGNORE INTO social_post_sources VALUES (?,?,?)",
                (post_id, owner, source_id),
            )
    return len(payloads)


def row_post(row) -> dict:
    payload = json.loads(row["payload_json"])
    return {
        **payload,
        **{k: row[k] for k in ("id", "content_hash", "revision", "first_seen_at", "fetched_at")},
        "saved": bool(row["saved"]) if "saved" in row.keys() else False,
    }


def list_posts(owner: str, *, hours: int = 168, saved: bool = False) -> list[dict]:
    with open_db() as conn:
        rows = conn.execute(
            """SELECT p.*,s.saved_at AS saved FROM social_posts p
            LEFT JOIN social_saved_posts s ON s.post_id=p.id AND s.account_id=p.account_id
            WHERE p.account_id=? AND (?=1 AND s.post_id IS NOT NULL OR ?=0 AND
              (p.published_ts>=? OR p.published_ts IS NULL AND p.first_seen_at>=?))
            ORDER BY COALESCE(p.published_ts,p.first_seen_at) DESC,p.id""",
            (owner, int(saved), int(saved), time.time() - hours * 3600, time.time() - hours * 3600),
        ).fetchall()
        return [row_post(r) for r in rows]


def get_post(owner: str, post_id: str) -> dict | None:
    with open_db() as conn:
        row = conn.execute(
            """SELECT p.*,s.saved_at AS saved FROM social_posts p
            LEFT JOIN social_saved_posts s ON s.post_id=p.id AND s.account_id=p.account_id
            WHERE p.account_id=? AND p.id=?""",
            (owner, post_id),
        ).fetchone()
        return row_post(row) if row else None


def save_bookmark(owner: str, post_id: str, enabled: bool) -> bool:
    with open_db() as conn:
        if not conn.execute(
            "SELECT 1 FROM social_posts WHERE account_id=? AND id=?", (owner, post_id)
        ).fetchone():
            return False
        if enabled:
            conn.execute(
                "INSERT OR IGNORE INTO social_saved_posts VALUES (?,?,?)",
                (owner, post_id, time.time()),
            )
        else:
            conn.execute(
                "DELETE FROM social_saved_posts WHERE account_id=? AND post_id=?", (owner, post_id)
            )
        return True
