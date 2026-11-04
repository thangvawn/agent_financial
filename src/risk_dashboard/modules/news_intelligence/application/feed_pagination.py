"""Short-lived, persisted public-news pages; a refresh cannot reorder a cursor."""

from __future__ import annotations

import hashlib
import json
import re
import time
from uuid import uuid4


class NewsCursorError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def filter_key(filters: dict) -> str:
    return hashlib.sha256(json.dumps(filters, sort_keys=True).encode()).hexdigest()


def page_from_snapshot(payload: dict, snapshot_id: str, offset: int, limit: int) -> dict:
    articles = payload["articles"]
    end = min(offset + limit, len(articles))
    return {
        **payload,
        "articles": articles[offset:end],
        "total": len(articles),
        "has_more": end < len(articles),
        "snapshot_id": snapshot_id,
        "next_cursor": f"{snapshot_id}:{end}" if end < len(articles) else None,
    }


def save_page(conn, payload: dict, key: str, limit: int) -> dict:
    snapshot_id = uuid4().hex
    now = time.time()
    conn.execute("DELETE FROM news_feed_snapshots WHERE expires_at <= ?", (now,))
    # A bounded cache, including searches from public clients.
    conn.execute("""DELETE FROM news_feed_snapshots WHERE snapshot_id IN (
        SELECT snapshot_id FROM news_feed_snapshots ORDER BY expires_at DESC LIMIT -1 OFFSET 255
    )""")
    if len(payload["articles"]) > limit:
        conn.execute(
            "INSERT INTO news_feed_snapshots VALUES (?, ?, ?, ?)",
            (snapshot_id, key, json.dumps(payload, ensure_ascii=False), now + 900),
        )
    return page_from_snapshot(payload, snapshot_id, 0, limit)


def load_page(conn, cursor: str, key: str, limit: int) -> dict:
    if not re.fullmatch(r"[0-9a-f]{32}:[1-9][0-9]{0,8}", cursor):
        raise NewsCursorError("Con trỏ trang không hợp lệ.")
    snapshot_id, offset = cursor.split(":")
    row = conn.execute(
        "SELECT * FROM news_feed_snapshots WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchone()
    if not row or row["expires_at"] <= time.time():
        raise NewsCursorError("Danh sách đã hết hạn. Vui lòng cập nhật tin.", 410)
    if row["filter_key"] != key:
        raise NewsCursorError("Con trỏ trang không khớp bộ lọc.")
    payload = json.loads(row["payload_json"])
    if int(offset) >= len(payload["articles"]):
        raise NewsCursorError("Trang nằm ngoài danh sách tin.")
    return page_from_snapshot(payload, snapshot_id, int(offset), limit)
