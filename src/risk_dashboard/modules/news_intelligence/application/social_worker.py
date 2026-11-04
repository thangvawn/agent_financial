"""Background collection; HTTP handlers only enqueue work and read cached posts."""

from __future__ import annotations

import logging
import os
import threading
import time

from risk_dashboard.modules.news_intelligence.infrastructure.agent_reach_adapter import (
    AgentReachAdapter,
    ReachFailure,
)
from risk_dashboard.modules.news_intelligence.infrastructure.social_jobs import (
    QueueLimit,
    claim_job,
    enqueue,
    finish_job,
)
from risk_dashboard.platform.database.connection import open_db

_lock = threading.Lock()
_thread: threading.Thread | None = None
_stop = threading.Event()
logger = logging.getLogger(__name__)


def run_once(adapter: AgentReachAdapter | None = None) -> dict | None:
    job = claim_job()
    if not job:
        return None
    try:
        posts, partial = (adapter or AgentReachAdapter()).collect(job)
        committed = finish_job(job, posts, partial=partial)
        return {
            "id": job["id"],
            "status": "succeeded" if committed else "lease_expired",
            "count": len(posts),
        }
    except ReachFailure as exc:
        finish_job(job, [], error=exc.code)
        return {"id": job["id"], "status": "failed", "error_code": exc.code}
    except Exception:
        logger.exception("Social collection failed for job %s", job["id"])
        finish_job(job, [], error="UPSTREAM_BROKEN")
        return {"id": job["id"], "status": "failed", "error_code": "UPSTREAM_BROKEN"}


def schedule_due() -> None:
    with open_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        # Only previously requested sources repeat; opening the page does not trigger collection.
        rows = conn.execute(
            """SELECT * FROM social_sources WHERE enabled=1 AND last_attempt_at IS NOT NULL
            AND next_run_at<=? ORDER BY next_run_at LIMIT 8""",
            (time.time(),),
        ).fetchall()
        for row in rows:
            if row["last_error"] in {"NEED_LOGIN", "NEED_SETUP", "PLATFORM_BLOCKED", "BAD_INPUT"}:
                continue
            try:
                enqueue(
                    conn,
                    row["account_id"],
                    row["platform"],
                    "search",
                    row["query"],
                    row["market"],
                    row["id"],
                )
            except QueueLimit:
                continue
            conn.execute(
                "UPDATE social_sources SET next_run_at=? WHERE account_id=? AND id=?",
                (time.time() + 3600, row["account_id"], row["id"]),
            )


def _loop() -> None:
    while not _stop.is_set():
        try:
            schedule_due()
            if run_once():
                continue
        except Exception:
            logger.exception("Social worker iteration failed")
        _stop.wait(5)


def start_social_worker() -> None:
    global _thread
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("ENABLE_SOCIAL_WORKER", "1").lower() in {
        "0",
        "false",
        "off",
    }:
        return
    if not AgentReachAdapter().available():
        return
    with _lock:
        if _thread and _thread.is_alive():
            return
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="social-collector", daemon=True)
        _thread.start()


def stop_social_worker() -> None:
    _stop.set()
