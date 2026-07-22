from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, tzinfo
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterator
from zoneinfo import ZoneInfo

from risk_dashboard.platform.database.connection import connect_db

_NEWS_TIME_NORMALIZE_KEY = "news_articles_time_normalize_v1"


def _default_tz_for_news_region(region: str) -> tzinfo:
    """Match rss_producer naive-date handling: VN wall clock vs UTC."""
    if (region or "").upper() == "VN":
        return ZoneInfo("Asia/Ho_Chi_Minh")
    return timezone.utc


def _parse_news_datetime(raw: str, *, region: str) -> datetime | None:
    """Parse published_at / fetched_at into aware UTC, or None."""
    s = (raw or "").strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = parsedate_to_datetime(s)
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_default_tz_for_news_region(region))
    return dt.astimezone(timezone.utc)


def _coerce_news_published_sort_ts(
    published_at: str,
    fetched_at: str,
    sort_ts: int,
    region: str,
) -> tuple[str, int] | None:
    """Canonical ISO UTC for published_at + matching sort_ts epoch seconds."""
    dt = _parse_news_datetime(published_at, region=region)
    if dt is None:
        dt = _parse_news_datetime(fetched_at, region=region)
    if dt is None and sort_ts > 0:
        try:
            dt = datetime.fromtimestamp(int(sort_ts), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if dt is None:
        return None
    dt = dt.astimezone(timezone.utc)
    return dt.isoformat(), int(dt.timestamp())


def _normalize_news_articles_timestamps(conn: sqlite3.Connection) -> None:
    """One-time backfill: align published_at (ISO UTC) with sort_ts for legacy rows."""
    conn.execute("CREATE TABLE IF NOT EXISTS app_kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    done = conn.execute(
        "SELECT 1 FROM app_kv WHERE key = ? AND value = ?",
        (_NEWS_TIME_NORMALIZE_KEY, "1"),
    ).fetchone()
    if done:
        return

    rows = conn.execute(
        "SELECT article_id, published_at, fetched_at, sort_ts, region FROM news_articles",
    ).fetchall()
    for r in rows:
        coerced = _coerce_news_published_sort_ts(
            str(r["published_at"]),
            str(r["fetched_at"]),
            int(r["sort_ts"]),
            str(r["region"]),
        )
        if coerced is None:
            continue
        pub_iso, st = coerced
        if pub_iso == str(r["published_at"]) and st == int(r["sort_ts"]):
            continue
        conn.execute(
            "UPDATE news_articles SET published_at = ?, sort_ts = ? WHERE article_id = ?",
            (pub_iso, st, r["article_id"]),
        )

    conn.execute(
        """
        INSERT INTO app_kv(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (_NEWS_TIME_NORMALIZE_KEY, "1"),
    )


def _connect_app_state_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Connect via shared database module (migrations + path resolution)."""
    conn = connect_db(db_path)
    _ensure_schema_compatibility(conn)
    conn.commit()
    return conn


@contextmanager
def open_app_state_db(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open the shared Northstar SQLite DB (compat name).

    Commits on success and always closes the connection.
    """
    conn = _connect_app_state_db(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_schema_compatibility(conn: sqlite3.Connection) -> None:
    comment_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(community_comments)").fetchall()
    }
    if comment_cols and "updated_at" not in comment_cols:
        conn.execute("ALTER TABLE community_comments ADD COLUMN updated_at TEXT")
        conn.execute("UPDATE community_comments SET updated_at = created_at WHERE updated_at IS NULL")
    if comment_cols and "parent_comment_id" not in comment_cols:
        conn.execute("ALTER TABLE community_comments ADD COLUMN parent_comment_id TEXT")
    if comment_cols and "thread_depth" not in comment_cols:
        conn.execute("ALTER TABLE community_comments ADD COLUMN thread_depth INTEGER NOT NULL DEFAULT 0")
        conn.execute("UPDATE community_comments SET thread_depth = 0 WHERE thread_depth IS NULL")
    pro_lab_experiment_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(pro_lab_experiments)").fetchall()
    }
    if pro_lab_experiment_cols and "review_status" not in pro_lab_experiment_cols:
        conn.execute("ALTER TABLE pro_lab_experiments ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending_review'")
    if pro_lab_experiment_cols and "review_notes" not in pro_lab_experiment_cols:
        conn.execute("ALTER TABLE pro_lab_experiments ADD COLUMN review_notes TEXT")
    if pro_lab_experiment_cols and "reviewed_at" not in pro_lab_experiment_cols:
        conn.execute("ALTER TABLE pro_lab_experiments ADD COLUMN reviewed_at TEXT")
    if pro_lab_experiment_cols and "reviewer_id" not in pro_lab_experiment_cols:
        conn.execute("ALTER TABLE pro_lab_experiments ADD COLUMN reviewer_id TEXT")
    trust_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(trust_safety_audit_logs)").fetchall()
    }
    if trust_cols and "topic" not in trust_cols:
        conn.execute("ALTER TABLE trust_safety_audit_logs ADD COLUMN topic TEXT")
    incident_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(trust_safety_incidents)").fetchall()
    }
    if incident_cols and "topic" not in incident_cols:
        conn.execute("ALTER TABLE trust_safety_incidents ADD COLUMN topic TEXT")
    # ── News articles new columns (Sprint 1) ──
    news_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(news_articles)").fetchall()
    }
    _news_migrations = [
        ("importance_score", "ALTER TABLE news_articles ADD COLUMN importance_score INTEGER NOT NULL DEFAULT 0"),
        ("importance_label", "ALTER TABLE news_articles ADD COLUMN importance_label TEXT NOT NULL DEFAULT 'noise'"),
        ("importance_breakdown_json", "ALTER TABLE news_articles ADD COLUMN importance_breakdown_json TEXT NOT NULL DEFAULT '{}'"),
        ("source_mix", "ALTER TABLE news_articles ADD COLUMN source_mix TEXT NOT NULL DEFAULT ''"),
        ("content_hash", "ALTER TABLE news_articles ADD COLUMN content_hash TEXT NOT NULL DEFAULT ''"),
        ("affected_markets_json", "ALTER TABLE news_articles ADD COLUMN affected_markets_json TEXT NOT NULL DEFAULT '[]'"),
        ("affected_sectors_json", "ALTER TABLE news_articles ADD COLUMN affected_sectors_json TEXT NOT NULL DEFAULT '[]'"),
        ("what_to_monitor_json", "ALTER TABLE news_articles ADD COLUMN what_to_monitor_json TEXT NOT NULL DEFAULT '[]'"),
        ("learn_links_json", "ALTER TABLE news_articles ADD COLUMN learn_links_json TEXT NOT NULL DEFAULT '[]'"),
        ("related_entities_json", "ALTER TABLE news_articles ADD COLUMN related_entities_json TEXT NOT NULL DEFAULT '[]'"),
    ]
    for col_name, sql in _news_migrations:
        if news_cols and col_name not in news_cols:
            conn.execute(sql)

    if news_cols:
        _normalize_news_articles_timestamps(conn)


def reset_app_state_tables() -> None:
    with open_app_state_db() as conn:
        conn.executescript(
            """
            DELETE FROM onboarding_sessions;
            DELETE FROM onboarding_profiles;
            DELETE FROM home_states;
            DELETE FROM financial_health_inputs;
            DELETE FROM financial_health_snapshots;
            DELETE FROM learning_home_states;
            DELETE FROM learning_lesson_progress;
            DELETE FROM learning_cms_documents;
            DELETE FROM news_highlight_snapshots;
            DELETE FROM news_articles;
            DELETE FROM app_kv WHERE key = 'news_articles_time_normalize_v1';
            DELETE FROM news_fetch_runs;
            DELETE FROM saved_news;
            DELETE FROM source_health;
            DELETE FROM goals;
            DELETE FROM goal_snapshots;
            DELETE FROM goal_checkins;
            DELETE FROM goal_reminder_states;
            DELETE FROM guided_watchlist_items;
            DELETE FROM guided_journal_entries;
            DELETE FROM guided_saved_portfolios;
            DELETE FROM guided_portfolio_review_history;
            DELETE FROM mp_watchlist_items;
            DELETE FROM mp_paper_accounts;
            DELETE FROM mp_orders;
            DELETE FROM mp_holdings;
            DELETE FROM ingest_runs;
            DELETE FROM community_memberships;
            DELETE FROM community_posts;
            DELETE FROM community_comments;
            DELETE FROM community_moderation_events;
            DELETE FROM community_challenge_progress;
            DELETE FROM community_notification_states;
            DELETE FROM pro_lab_blueprints;
            DELETE FROM pro_lab_experiments;
            DELETE FROM pro_lab_experiment_runs;
            DELETE FROM pro_lab_workspaces;
            DELETE FROM pro_lab_audit_logs;
            DELETE FROM access_role_assignments;
            DELETE FROM access_tokens;
            DELETE FROM ai_conversation_sessions;
            DELETE FROM ai_messages;
            DELETE FROM ai_feedback;
            DELETE FROM ai_event_logs;
            DELETE FROM cms_content_items;
            DELETE FROM cms_content_versions;
            DELETE FROM cms_review_tasks;
            DELETE FROM cms_publish_events;
            DELETE FROM cms_ai_generation_logs;
            DELETE FROM cms_analytics_snapshots;
            DELETE FROM trust_safety_audit_logs;
            DELETE FROM trust_safety_incidents;
            DELETE FROM analytics_events;
            DELETE FROM analytics_kpi_snapshots;
            DELETE FROM ops_metric_snapshots;
            DELETE FROM ops_alert_events;
            """
        )
        conn.commit()
