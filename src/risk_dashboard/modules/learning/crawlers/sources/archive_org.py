"""Internet Archive crawler via the open Advanced Search JSON API.

We mine `texts` collections (books / textbooks) for finance-aligned topics.
Items returned have a canonical URL like https://archive.org/details/<id> and
optional PDF/EPUB at https://archive.org/download/<id>/<id>.pdf.
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
SOURCE = "archive_org"

SEARCH_QUERIES: list[tuple[str, list[str]]] = [
    ("subject:(finance) AND mediatype:texts AND format:pdf", ["valuation", "portfolio_theory"]),
    ("subject:(investing) AND mediatype:texts AND format:pdf", ["portfolio_theory", "stocks"]),
    ("subject:(stock market) AND mediatype:texts AND format:pdf", ["stocks", "valuation"]),
    ("subject:(behavioral finance) AND mediatype:texts", ["behavioral_finance"]),
    ("subject:(econometrics) AND mediatype:texts", ["quantitative_finance"]),
    ("subject:(macroeconomics) AND mediatype:texts AND format:pdf", ["macroeconomics"]),
    ("subject:(technical analysis) AND mediatype:texts", ["technical_analysis"]),
    ("title:(value investing) AND mediatype:texts", ["valuation", "stocks"]),
    ("title:(options pricing) AND mediatype:texts", ["derivatives"]),
    ("title:(intelligent investor) AND mediatype:texts", ["stocks", "valuation"]),
    ("title:(security analysis) AND mediatype:texts", ["valuation", "stocks"]),
    ("subject:(corporate finance) AND mediatype:texts AND format:pdf", ["valuation", "financial_statements"]),
    ("subject:(risk management) AND mediatype:texts AND format:pdf", ["risk_management"]),
    ("subject:(fixed income) AND mediatype:texts AND format:pdf", ["bonds", "valuation"]),
    ("subject:(financial accounting) AND mediatype:texts AND format:pdf", ["financial_statements"]),
    ("subject:(quantitative finance) AND mediatype:texts", ["quantitative_finance"]),
    ("subject:(algorithmic trading) AND mediatype:texts", ["quantitative_finance", "stocks"]),
    ("title:(principles of economics) AND mediatype:texts", ["macroeconomics"]),
    ("subject:(portfolio management) AND mediatype:texts AND format:pdf", ["portfolio_theory", "asset_classes"]),
    ("subject:(derivatives) AND mediatype:texts AND format:pdf", ["derivatives"]),
    ("subject:(money banking) AND mediatype:texts AND format:pdf", ["banking_products", "macroeconomics"]),
    ("title:(reminiscences of a stock operator) AND mediatype:texts", ["behavioral_finance", "stocks"]),
    ("title:(market wizards) AND mediatype:texts", ["technical_analysis", "behavioral_finance"]),
    ("subject:(personal finance) AND mediatype:texts AND format:pdf", ["budgeting", "saving"]),
    ("subject:(wealth of nations) AND mediatype:texts", ["macroeconomics"]),
    ("title:(theory of investment value) AND mediatype:texts", ["valuation", "stocks"]),
    ("subject:(financial modeling) AND mediatype:texts", ["valuation", "financial_statements"]),
    ("subject:(behavioral economics) AND mediatype:texts", ["behavioral_finance"]),
]

FIELDS = ["identifier", "title", "creator", "year", "language", "description"]


def crawl(conn: sqlite3.Connection, *, limit: int, run_id: str) -> CrawlResult:  # noqa: ARG001
    result = CrawlResult(source=SOURCE, kind=KIND)
    per_query = max(6, limit // len(SEARCH_QUERIES))

    for query, topics in SEARCH_QUERIES:
        params = [("q", query), ("rows", str(per_query)), ("output", "json"), ("sort[]", "downloads desc")]
        params.extend(("fl[]", field) for field in FIELDS)
        url = "https://archive.org/advancedsearch.php?" + urlencode(params)
        try:
            payload = http_get_json(url, timeout=30)
        except Exception as err:  # noqa: BLE001
            result.error = f"{query}: {err}"
            continue

        docs = payload.get("response", {}).get("docs", [])
        for doc in docs:
            external_id = doc.get("identifier")
            if not external_id:
                result.skipped += 1
                continue

            title = doc.get("title")
            if isinstance(title, list):
                title = title[0] if title else ""
            creator = doc.get("creator")
            if isinstance(creator, list):
                creator = ", ".join(creator[:3])

            language = (doc.get("language") or "en")
            if isinstance(language, list):
                language = (language[0] or "en").lower()[:5]

            year = doc.get("year")
            try:
                year_int = int(year) if year else None
            except (TypeError, ValueError):
                year_int = None

            description = doc.get("description") or ""
            if isinstance(description, list):
                description = " ".join(description)
            description = description.strip()[:1200]

            resource_id = stable_id("book", SOURCE, external_id)
            row = ResourceRow(
                kind=KIND,
                resource_id=resource_id,
                source=SOURCE,
                external_id=external_id,
                title=title or external_id,
                url=f"https://archive.org/details/{external_id}",
                language=language[:5] if language else "en",
                topics=topics,
                fields={
                    "author": creator,
                    "description": description,
                    "download_url": f"https://archive.org/download/{external_id}/{external_id}.pdf",
                    "cover_url": f"https://archive.org/services/img/{external_id}",
                    "publication_year": year_int,
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
