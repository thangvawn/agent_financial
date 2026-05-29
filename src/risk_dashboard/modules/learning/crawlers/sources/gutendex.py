"""Project Gutenberg crawler via the public Gutendex API.

Gutendex (https://gutendex.com) is a free JSON wrapper over Gutenberg's
catalog. We pull books matching finance/economics keywords. Items are
public-domain — safe to link directly.
"""
from __future__ import annotations

import sqlite3
from urllib.parse import urlencode

from ..common import (
    ResourceRow,
    http_get_json,
    stable_id,
    upsert_resource,
)
from ..runner import CrawlResult

KIND = "book"
SOURCE = "gutenberg"

# Search terms → topics. Gutendex full-text search uses the ?search= param.
SEARCH_QUERIES: list[tuple[str, list[str]]] = [
    ("economics", ["macroeconomics"]),
    ("political economy", ["macroeconomics"]),
    ("finance", ["valuation"]),
    ("banking", ["banking_products", "macroeconomics"]),
    ("investment", ["portfolio_theory", "valuation"]),
    ("money", ["macroeconomics", "banking_products"]),
    ("capital", ["macroeconomics", "valuation"]),
    ("speculation", ["behavioral_finance"]),
    ("stocks", ["stocks"]),
    ("wealth of nations", ["macroeconomics"]),
]


def crawl(conn: sqlite3.Connection, *, limit: int, run_id: str) -> CrawlResult:  # noqa: ARG001
    result = CrawlResult(source=SOURCE, kind=KIND)
    per_query = max(5, limit // len(SEARCH_QUERIES))

    for query, topics in SEARCH_QUERIES:
        url = "https://gutendex.com/books/?" + urlencode(
            {"search": query, "languages": "en", "mime_type": "application/pdf"}
        )
        try:
            payload = http_get_json(url, timeout=60)
        except Exception as err:  # noqa: BLE001 — log per-query and move on
            result.skipped += 1
            continue

        for book in (payload.get("results") or [])[:per_query]:
            external_id = str(book.get("id") or "")
            if not external_id:
                result.skipped += 1
                continue
            title = book.get("title") or "Untitled"
            authors = book.get("authors") or []
            author_name = authors[0]["name"] if authors else None
            birth_year = authors[0].get("birth_year") if authors else None

            formats = book.get("formats") or {}
            pdf_url = (
                formats.get("application/pdf")
                or formats.get("application/epub+zip")
                or formats.get("text/html")
            )
            html_url = formats.get("text/html") or f"https://www.gutenberg.org/ebooks/{external_id}"
            cover = formats.get("image/jpeg")

            resource_id = stable_id("book", SOURCE, external_id)
            row = ResourceRow(
                kind=KIND,
                resource_id=resource_id,
                source=SOURCE,
                external_id=external_id,
                title=title,
                url=html_url,
                language=(book.get("languages") or ["en"])[0],
                topics=topics,
                fields={
                    "author": author_name,
                    "description": _shorten(book.get("subjects") or [], 800),
                    "download_url": pdf_url,
                    "cover_url": cover,
                    "publication_year": birth_year,  # best-effort proxy
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


def _shorten(subjects: list[str], max_len: int) -> str:
    joined = "; ".join(subjects)
    return joined[:max_len]
