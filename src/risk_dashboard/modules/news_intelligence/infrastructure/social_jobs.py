"""Durable queue with bounded retries and leases; completion uses a fencing token."""

from __future__ import annotations

import time
from uuid import uuid4

from risk_dashboard.modules.news_intelligence.infrastructure.social_repository import (
    save_posts,
    seed_sources,
)
from risk_dashboard.platform.database.connection import open_db


class QueueLimit(ValueError):
    pass


def enqueue(
    conn,
    owner: str,
    platform: str,
    action: str,
    target: str,
    market: str,
    source_id: str | None = None,
) -> dict:
    now = time.time()
    existing = conn.execute(
        """SELECT * FROM social_jobs WHERE account_id=? AND platform=? AND action=?
        AND target=? AND market=? AND source_id IS ?
        AND (status IN ('queued','running') OR created_at>?)
        ORDER BY created_at DESC LIMIT 1""",
        (owner, platform, action, target, market, source_id, now - 120),
    ).fetchone()
    if existing:
        return dict(existing)
    pending = conn.execute(
        "SELECT COUNT(*) FROM social_jobs WHERE account_id=? AND status IN ('queued','running')",
        (owner,),
    ).fetchone()[0]
    daily = conn.execute(
        "SELECT COUNT(*) FROM social_jobs WHERE account_id=? AND created_at>?", (owner, now - 86400)
    ).fetchone()[0]
    if pending >= 20 or daily >= 200:
        raise QueueLimit("Đã đạt giới hạn thu thập. Vui lòng chờ các lượt hiện tại hoàn tất.")
    job_id = uuid4().hex
    conn.execute(
        """INSERT INTO social_jobs
        (id,account_id,source_id,platform,action,target,market,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (job_id, owner, source_id, platform, action, target, market, now, now),
    )
    return dict(conn.execute("SELECT * FROM social_jobs WHERE id=?", (job_id,)).fetchone())


def enqueue_refresh(owner: str) -> list[dict]:
    with open_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        seed_sources(conn, owner)
        selected = conn.execute(
            "SELECT * FROM social_sources WHERE account_id=? AND enabled=1", (owner,)
        ).fetchall()
        return [
            enqueue(conn, owner, r["platform"], "search", r["query"], r["market"], r["id"])
            for r in selected
        ]


def claim_job() -> dict | None:
    with open_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        now = time.time()
        conn.execute("INSERT OR REPLACE INTO social_worker_state VALUES ('collector',?)", (now,))
        conn.execute(
            """UPDATE social_jobs SET status=CASE WHEN attempts<3 THEN 'queued' ELSE 'failed' END,
            error_code='TIMEOUT',lease_token=NULL,updated_at=?
            WHERE status='running' AND lease_until<?""",
            (now, now),
        )
        # One process at a time, including multiple API workers or external CLI workers.
        if conn.execute(
            "SELECT 1 FROM social_jobs WHERE status='running' AND lease_until>?", (now,)
        ).fetchone():
            return None
        row = conn.execute(
            "SELECT * FROM social_jobs WHERE status='queued' AND next_run_at<=? "
            "ORDER BY created_at,id LIMIT 1",
            (now,),
        ).fetchone()
        if not row:
            return None
        token = uuid4().hex
        conn.execute(
            """UPDATE social_jobs SET status='running',attempts=attempts+1,lease_token=?,
            lease_until=?,updated_at=? WHERE id=?""",
            (token, now + 600, now, row["id"]),
        )
        return dict(conn.execute("SELECT * FROM social_jobs WHERE id=?", (row["id"],)).fetchone())


def finish_job(job: dict, posts: list[dict], error: str | None = None, partial: int = 0) -> bool:
    with open_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM social_jobs WHERE id=? AND lease_token=? "
            "AND status='running' AND lease_until>?",
            (job["id"], job["lease_token"], time.time()),
        ).fetchone()
        if not row:
            return False
        now = time.time()
        if (
            job["source_id"]
            and not conn.execute(
                "SELECT 1 FROM social_sources WHERE account_id=? AND id=? AND enabled=1",
                (job["account_id"], job["source_id"]),
            ).fetchone()
        ):
            conn.execute(
                "UPDATE social_jobs SET status='cancelled',lease_token=NULL,"
                "lease_until=0,updated_at=? WHERE id=?",
                (now, job["id"]),
            )
            return True
        count = save_posts(conn, job["account_id"], posts, job["source_id"]) if not error else 0
        if not error and job["action"] == "read":
            for post in posts:
                conn.execute(
                    """INSERT OR IGNORE INTO social_saved_posts
                    SELECT account_id,id,? FROM social_posts
                    WHERE account_id=? AND platform=? AND native_id=?""",
                    (now, job["account_id"], post["platform"], post["native_id"]),
                )
        retry = error in {"TIMEOUT", "UPSTREAM_BROKEN"} and job["attempts"] < 3
        status = "queued" if retry else "failed" if error else "succeeded"
        delay = min(3600, 120 * 2 ** job["attempts"]) if retry else 0
        conn.execute(
            """UPDATE social_jobs SET status=?,updated_at=?,lease_token=NULL,lease_until=0,
            error_code=?,result_count=?,partial_count=?,next_run_at=? WHERE id=?""",
            (status, now, error, count, partial, now + delay, job["id"]),
        )
        if job["source_id"]:
            conn.execute(
                """UPDATE social_sources SET last_attempt_at=?,last_error=?,
                last_success_at=CASE WHEN ? IS NULL THEN ? ELSE last_success_at END,next_run_at=?
                WHERE account_id=? AND id=?""",
                (
                    now,
                    error,
                    error,
                    now,
                    now + (7200 if error else 3600),
                    job["account_id"],
                    job["source_id"],
                ),
            )
        return True


def recent_jobs(owner: str) -> list[dict]:
    with open_db() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM social_jobs WHERE account_id=? ORDER BY created_at DESC LIMIT 20",
                (owner,),
            )
        ]
