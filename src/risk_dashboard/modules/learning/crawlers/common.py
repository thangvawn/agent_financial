"""Common helpers shared by all crawlers: upsert builders, slug helpers,
HTTP fetch with polite headers, and topic-link recording.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

from .topics import TOPIC_BY_ID, normalize_topics, tier_for_topic

USER_AGENT = "NorthstarLearningCrawler/0.1 (+https://github.com/anthropics; educational use)"


LEARNING_CATALOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS learning_topics (
  topic_id TEXT PRIMARY KEY,
  label_vi TEXT NOT NULL,
  label_en TEXT NOT NULL,
  tier TEXT NOT NULL,
  description TEXT,
  sort_order INTEGER NOT NULL DEFAULT 100
);

CREATE TABLE IF NOT EXISTS learning_courses (
  course_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  external_id TEXT,
  title TEXT NOT NULL,
  provider TEXT,
  instructor TEXT,
  description TEXT,
  url TEXT NOT NULL,
  thumbnail_url TEXT,
  language TEXT NOT NULL DEFAULT 'en',
  level TEXT,
  duration_minutes INTEGER,
  topics_json TEXT NOT NULL DEFAULT '[]',
  tier TEXT,
  published_at TEXT,
  fetched_at TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_courses_source_ext ON learning_courses(source, external_id);
CREATE INDEX IF NOT EXISTS idx_learning_courses_tier ON learning_courses(tier);
CREATE INDEX IF NOT EXISTS idx_learning_courses_lang ON learning_courses(language);

CREATE TABLE IF NOT EXISTS learning_videos (
  video_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  channel TEXT,
  channel_id TEXT,
  description TEXT,
  url TEXT NOT NULL,
  thumbnail_url TEXT,
  language TEXT NOT NULL DEFAULT 'en',
  duration_seconds INTEGER,
  view_count INTEGER,
  topics_json TEXT NOT NULL DEFAULT '[]',
  tier TEXT,
  published_at TEXT,
  fetched_at TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_videos_source_ext ON learning_videos(source, external_id);
CREATE INDEX IF NOT EXISTS idx_learning_videos_tier ON learning_videos(tier);
CREATE INDEX IF NOT EXISTS idx_learning_videos_lang ON learning_videos(language);

CREATE TABLE IF NOT EXISTS learning_books (
  book_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  external_id TEXT,
  title TEXT NOT NULL,
  author TEXT,
  description TEXT,
  url TEXT NOT NULL,
  download_url TEXT,
  cover_url TEXT,
  language TEXT NOT NULL DEFAULT 'en',
  publication_year INTEGER,
  topics_json TEXT NOT NULL DEFAULT '[]',
  tier TEXT,
  fetched_at TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_books_source_ext ON learning_books(source, external_id);
CREATE INDEX IF NOT EXISTS idx_learning_books_tier ON learning_books(tier);
CREATE INDEX IF NOT EXISTS idx_learning_books_lang ON learning_books(language);

CREATE TABLE IF NOT EXISTS learning_papers (
  paper_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  authors_json TEXT NOT NULL DEFAULT '[]',
  abstract TEXT,
  url TEXT NOT NULL,
  pdf_url TEXT,
  category TEXT,
  language TEXT NOT NULL DEFAULT 'en',
  topics_json TEXT NOT NULL DEFAULT '[]',
  tier TEXT,
  published_at TEXT,
  fetched_at TEXT NOT NULL,
  citation_count INTEGER,
  is_active INTEGER NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_papers_source_ext ON learning_papers(source, external_id);
CREATE INDEX IF NOT EXISTS idx_learning_papers_tier ON learning_papers(tier);
CREATE INDEX IF NOT EXISTS idx_learning_papers_published ON learning_papers(published_at DESC);

CREATE TABLE IF NOT EXISTS learning_resource_topics (
  resource_kind TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  topic_id TEXT NOT NULL,
  PRIMARY KEY (resource_kind, resource_id, topic_id)
);
CREATE INDEX IF NOT EXISTS idx_learning_resource_topics_topic ON learning_resource_topics(topic_id);

CREATE TABLE IF NOT EXISTS learning_crawl_runs (
  run_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  kind TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  rows_inserted INTEGER NOT NULL DEFAULT 0,
  rows_updated INTEGER NOT NULL DEFAULT 0,
  rows_skipped INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  error TEXT
);
CREATE INDEX IF NOT EXISTS idx_learning_crawl_runs_started ON learning_crawl_runs(started_at DESC);
"""


def default_db_path() -> Path:
    """Repo-relative default. Matches risk_dashboard.app.config.settings."""
    return Path(__file__).resolve().parents[5] / "data" / "app_state.db"


def open_catalog_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open SQLite + ensure the learning-catalog tables exist (idempotent).

    Standalone of ``risk_dashboard.app.config.settings`` to avoid pulling in
    the full FastAPI bootstrap chain when running the CLI.
    """
    resolved = Path(db_path) if db_path else default_db_path()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(resolved), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(LEARNING_CATALOG_SCHEMA)
    conn.commit()
    return conn


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(value: str, max_len: int = 80) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned[:max_len] or "untitled"


def stable_id(prefix: str, *parts: str) -> str:
    joined = "|".join(p for p in parts if p)
    digest = hashlib.sha1(joined.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def http_get(url: str, *, timeout: int = 30, headers: dict[str, str] | None = None) -> bytes:
    """Polite GET with retries. Returns raw bytes."""
    final_headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        final_headers.update(headers)
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            req = Request(url, headers=final_headers)
            with urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except URLError as err:  # network / 4xx / 5xx
            last_err = err
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed for {url}: {last_err}")


def http_get_text(url: str, **kwargs) -> str:
    return http_get(url, **kwargs).decode("utf-8", errors="replace")


def http_get_json(url: str, **kwargs):
    return json.loads(http_get_text(url, headers={"Accept": "application/json"}, **kwargs))


@dataclass
class ResourceRow:
    """Generic upsert payload — converted to per-kind SQL by helpers below."""

    kind: str  # 'course' | 'video' | 'book' | 'paper'
    resource_id: str
    source: str
    external_id: str
    title: str
    url: str
    language: str = "en"
    topics: list[str] = field(default_factory=list)
    tier: str | None = None
    fields: dict[str, object] = field(default_factory=dict)

    def normalized_topics(self) -> list[str]:
        return normalize_topics(self.topics)

    def resolved_tier(self) -> str | None:
        if self.tier:
            return self.tier
        topics = self.normalized_topics()
        if not topics:
            return None
        return tier_for_topic(topics[0])


_COURSE_COLUMNS = (
    "course_id", "source", "external_id", "title", "provider", "instructor",
    "description", "url", "thumbnail_url", "language", "level",
    "duration_minutes", "topics_json", "tier", "published_at", "fetched_at", "is_active",
)
_VIDEO_COLUMNS = (
    "video_id", "source", "external_id", "title", "channel", "channel_id",
    "description", "url", "thumbnail_url", "language", "duration_seconds",
    "view_count", "topics_json", "tier", "published_at", "fetched_at", "is_active",
)
_BOOK_COLUMNS = (
    "book_id", "source", "external_id", "title", "author", "description",
    "url", "download_url", "cover_url", "language", "publication_year",
    "topics_json", "tier", "fetched_at", "is_active",
)
_PAPER_COLUMNS = (
    "paper_id", "source", "external_id", "title", "authors_json", "abstract",
    "url", "pdf_url", "category", "language", "topics_json", "tier",
    "published_at", "fetched_at", "citation_count", "is_active",
)


_TABLE_BY_KIND = {
    "course": ("learning_courses", _COURSE_COLUMNS, "course_id"),
    "video": ("learning_videos", _VIDEO_COLUMNS, "video_id"),
    "book": ("learning_books", _BOOK_COLUMNS, "book_id"),
    "paper": ("learning_papers", _PAPER_COLUMNS, "paper_id"),
}


def upsert_resource(conn: sqlite3.Connection, row: ResourceRow) -> str:
    """Insert or update a resource. Returns 'inserted' | 'updated' | 'skipped'.

    Uses (source, external_id) as the dedup key — guaranteed unique via index.
    """
    if row.kind not in _TABLE_BY_KIND:
        raise ValueError(f"unknown resource kind: {row.kind}")
    table, columns, pk = _TABLE_BY_KIND[row.kind]

    existing = conn.execute(
        f"SELECT {pk} FROM {table} WHERE source = ? AND external_id = ?",
        (row.source, row.external_id),
    ).fetchone()

    topics = row.normalized_topics()
    payload: dict[str, object] = {
        pk: row.resource_id,
        "source": row.source,
        "external_id": row.external_id,
        "title": row.title.strip()[:512] or "Untitled",
        "url": row.url,
        "language": row.language or "en",
        "topics_json": json.dumps(topics, ensure_ascii=False),
        "tier": row.resolved_tier(),
        "fetched_at": utc_now_iso(),
        "is_active": 1,
    }
    payload.update({k: v for k, v in row.fields.items() if k in columns})

    if existing:
        # update
        cols_to_update = [c for c in columns if c not in (pk, "source", "external_id")]
        sets = ", ".join(f"{c} = ?" for c in cols_to_update)
        values = [payload.get(c) for c in cols_to_update]
        conn.execute(
            f"UPDATE {table} SET {sets} WHERE {pk} = ?",
            (*values, existing[pk]),
        )
        resource_id = existing[pk]
        status = "updated"
    else:
        placeholders = ", ".join("?" for _ in columns)
        values = [payload.get(c) for c in columns]
        conn.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
        resource_id = row.resource_id
        status = "inserted"

    record_topics(conn, row.kind, resource_id, topics)
    return status


def record_topics(conn: sqlite3.Connection, kind: str, resource_id: str, topics: Iterable[str]) -> None:
    """Refresh the resource-topic links table for this resource."""
    conn.execute(
        "DELETE FROM learning_resource_topics WHERE resource_kind = ? AND resource_id = ?",
        (kind, resource_id),
    )
    for topic_id in topics:
        if topic_id not in TOPIC_BY_ID:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO learning_resource_topics(resource_kind, resource_id, topic_id) VALUES (?, ?, ?)",
            (kind, resource_id, topic_id),
        )


def ensure_topics_seeded(conn: sqlite3.Connection) -> int:
    """Seed the learning_topics table from the taxonomy. Idempotent."""
    from .topics import TOPICS  # local import to avoid cycle on module load

    inserted = 0
    for topic in TOPICS:
        cursor = conn.execute(
            """
            INSERT OR REPLACE INTO learning_topics(
                topic_id, label_vi, label_en, tier, description, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                topic.topic_id, topic.label_vi, topic.label_en,
                topic.tier, topic.description, topic.sort_order,
            ),
        )
        inserted += cursor.rowcount
    return inserted
