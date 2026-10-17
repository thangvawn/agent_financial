"""Curated classic finance and investment books seeder.

Injects foundational, must-read finance books with verified author,
cover images, topics, and public reading/download links.
"""
from __future__ import annotations

import sqlite3

from ..common import ResourceRow, stable_id, upsert_resource
from ..runner import CrawlResult
from .curated_books_data import CURATED_BOOKS

KIND = "book"
SOURCE = "curated_books"


def crawl(conn: sqlite3.Connection, *, limit: int, run_id: str) -> CrawlResult:  # noqa: ARG001
    result = CrawlResult(source=SOURCE, kind=KIND)

    for item in CURATED_BOOKS[:limit]:
        external_id = item["id"]
        resource_id = stable_id("book", SOURCE, external_id)
        row = ResourceRow(
            kind=KIND,
            resource_id=resource_id,
            source=SOURCE,
            external_id=external_id,
            title=item["title"],
            url=item["url"],
            language=item.get("language", "vi"),
            topics=item["topics"],
            fields={
                "author": item.get("author"),
                "description": item.get("description", ""),
                "download_url": item.get("download_url"),
                "cover_url": item.get("cover_url"),
                "publication_year": item.get("year"),
            },
        )
        status = upsert_resource(conn, row)
        if status == "inserted":
            result.inserted += 1
        elif status == "updated":
            result.updated += 1
        else:
            result.skipped += 1

    conn.commit()
    return result
