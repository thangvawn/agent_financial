"""Persisted day/week/month highlight snapshots for News Intelligence."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

NEWS_TIMEZONE = "Asia/Ho_Chi_Minh"
PERIODS = ("day", "week", "month")
_LOCAL_TZ = ZoneInfo(NEWS_TIMEZONE)


@dataclass(frozen=True)
class PeriodWindow:
    kind: str
    key: str
    start: datetime
    end: datetime


def resolve_period_window(period: str, *, now: datetime | None = None) -> PeriodWindow:
    if period not in PERIODS:
        raise ValueError(f"Unsupported highlight period: {period}")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    local = current.astimezone(_LOCAL_TZ)
    day_start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "day":
        start, end, key = day_start, day_start + timedelta(days=1), local.strftime("%Y-%m-%d")
    elif period == "week":
        start = day_start - timedelta(days=local.weekday())
        end = start + timedelta(days=7)
        iso = local.isocalendar()
        key = f"{iso.year}-W{iso.week:02d}"
    else:
        start = day_start.replace(day=1)
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
        key = local.strftime("%Y-%m")
    return PeriodWindow(period, key, start.astimezone(timezone.utc), end.astimezone(timezone.utc))


def rebuild_current_snapshots(
    conn: sqlite3.Connection,
    *,
    now: datetime | None = None,
    source_run_id: str | None = None,
) -> None:
    current = now or datetime.now(timezone.utc)
    for period in PERIODS:
        upsert_snapshot(
            conn,
            resolve_period_window(period, now=current),
            now=current,
            source_run_id=source_run_id,
        )


def get_or_build_snapshot(
    conn: sqlite3.Connection,
    period: str,
    *,
    now: datetime | None = None,
) -> dict:
    current = now or datetime.now(timezone.utc)
    window = resolve_period_window(period, now=current)
    row = conn.execute(
        "SELECT * FROM news_highlight_snapshots WHERE period_kind = ? AND period_key = ?",
        (period, window.key),
    ).fetchone()
    if row is None:
        upsert_snapshot(conn, window, now=current)
        row = conn.execute(
            "SELECT * FROM news_highlight_snapshots WHERE period_kind = ? AND period_key = ?",
            (period, window.key),
        ).fetchone()
    return _snapshot_from_row(row)


def upsert_snapshot(
    conn: sqlite3.Connection,
    window: PeriodWindow,
    *,
    now: datetime,
    source_run_id: str | None = None,
) -> None:
    items = _select_items(conn, window, limit=10)
    generated_at = now.astimezone(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO news_highlight_snapshots (
          snapshot_id, period_kind, period_key, timezone, window_start, window_end,
          items_json, item_count, generated_at, source_run_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(period_kind, period_key) DO UPDATE SET
          window_start=excluded.window_start, window_end=excluded.window_end,
          items_json=excluded.items_json, item_count=excluded.item_count,
          generated_at=excluded.generated_at, source_run_id=excluded.source_run_id
        """,
        (
            f"news-highlight:{window.kind}:{window.key}", window.kind, window.key,
            NEWS_TIMEZONE, window.start.isoformat(), window.end.isoformat(),
            json.dumps(items, ensure_ascii=False), len(items), generated_at, source_run_id,
        ),
    )


def _select_items(conn: sqlite3.Connection, window: PeriodWindow, *, limit: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM news_articles
        WHERE sort_ts >= ? AND sort_ts < ?
          AND headline NOT LIKE 'Distinct financial event number %'
        ORDER BY importance_score DESC, sort_ts DESC, fetched_at DESC, article_id ASC
        """,
        (int(window.start.timestamp()), int(window.end.timestamp())),
    ).fetchall()
    unique: list[sqlite3.Row] = []
    seen_hashes: set[str] = set()
    seen_headlines: set[str] = set()
    for row in rows:
        content_hash = str(row["content_hash"] or "").strip()
        headline_key = _headline_key(str(row["headline"]))
        if (content_hash and content_hash in seen_hashes) or headline_key in seen_headlines:
            continue
        if content_hash:
            seen_hashes.add(content_hash)
        seen_headlines.add(headline_key)
        unique.append(row)

    selected: list[sqlite3.Row] = []
    deferred: list[sqlite3.Row] = []
    category_counts: dict[str, int] = {}
    for row in unique:
        category = str(row["category"])
        if category_counts.get(category, 0) >= 2:
            deferred.append(row)
            continue
        selected.append(row)
        category_counts[category] = category_counts.get(category, 0) + 1
        if len(selected) == limit:
            break
    if len(selected) < limit:
        selected.extend(deferred[: limit - len(selected)])
    return [_item_payload(row) for row in selected]


def _headline_key(headline: str) -> str:
    normalized = "".join(char if char.isalnum() else " " for char in headline.casefold())
    return " ".join(normalized.split())


def _item_payload(row: sqlite3.Row) -> dict:
    markets = json.loads(row["affected_markets_json"] or "[]")
    importance = str(row["importance_label"])
    category = str(row["category"])
    sentiment = str(row["sentiment"])
    why = f"Phân loại: {category} · {sentiment}."
    if importance in {"critical", "high"}:
        why = f"Tin {importance} impact."
    if markets:
        why = f"{why[:-1]} — ảnh hưởng {', '.join(markets[:2])}."
    return {
        "article_id": row["article_id"], "headline": row["headline"],
        "summary": row["summary"], "source": row["source"],
        "url": row["url"],
        "source_flag": row["source_flag"], "published_at": row["published_at"],
        "category": category, "region": row["region"],
        "importance_score": int(row["importance_score"] or 0),
        "importance_label": importance, "sentiment": sentiment,
        "impact": row["impact"], "why_it_matters": why,
        "affected_markets": markets[:3],
    }


def _snapshot_from_row(row: sqlite3.Row) -> dict:
    payload = dict(row)
    payload["items"] = json.loads(payload.pop("items_json") or "[]")
    return payload
