"""Unit tests for learning crawlers: open_courses and curated_books."""
from __future__ import annotations

import sqlite3

from risk_dashboard.modules.learning.crawlers.common import (
    LEARNING_CATALOG_SCHEMA,
    ensure_topics_seeded,
)
from risk_dashboard.modules.learning.crawlers.runner import SOURCE_MODULES, run_source
from risk_dashboard.modules.learning.crawlers.sources import curated_books, open_courses


def _create_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(LEARNING_CATALOG_SCHEMA)
    ensure_topics_seeded(conn)
    conn.commit()
    return conn


def test_sources_registered() -> None:
    assert "open_courses" in SOURCE_MODULES
    assert "curated_books" in SOURCE_MODULES
    assert "mit_ocw" in SOURCE_MODULES
    assert "archive_org" in SOURCE_MODULES


def test_open_courses_crawl() -> None:
    conn = _create_test_db()
    res = open_courses.crawl(conn, limit=5, run_id="test_open_courses")
    assert res.inserted == 5
    assert res.error is None

    cursor = conn.execute("SELECT count(*) FROM learning_courses")
    assert cursor.fetchone()[0] == 5

    row = conn.execute(
        "SELECT * FROM learning_courses WHERE source = 'open_courses' LIMIT 1"
    ).fetchone()
    assert row["course_id"].startswith("course_")
    assert row["provider"] is not None
    conn.close()


def test_curated_books_crawl() -> None:
    conn = _create_test_db()
    res = curated_books.crawl(conn, limit=5, run_id="test_curated_books")
    assert res.inserted == 5
    assert res.error is None

    cursor = conn.execute("SELECT count(*) FROM learning_books")
    assert cursor.fetchone()[0] == 5

    row = conn.execute(
        "SELECT * FROM learning_books WHERE source = 'curated_books' LIMIT 1"
    ).fetchone()
    assert row["book_id"].startswith("book_")
    assert row["author"] is not None
    conn.close()


def test_runner_run_source() -> None:
    conn = _create_test_db()
    res = run_source(conn, "curated_books", limit=3)
    assert res.source == "curated_books"
    assert res.inserted == 3
    assert res.error is None
    conn.close()
