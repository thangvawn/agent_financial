"""Working-papers crawler for central banks / multilaterals.

We pull RSS / Atom feeds that are publicly published. No API key needed.
Items go into ``learning_papers`` with source set to the originating
institution so the UI can label them.
"""
from __future__ import annotations

import re
import sqlite3
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from ..common import (
    ResourceRow,
    http_get_text,
    stable_id,
    upsert_resource,
)
from ..runner import CrawlResult

KIND = "paper"
SOURCE = "policy_papers"

# Each feed: (source-label, feed URL, topics, language).
# Only well-formed RSS feeds verified to return XML in 2026-05 are listed here.
FEEDS: list[tuple[str, str, list[str], str]] = [
    ("fed_feds", "https://www.federalreserve.gov/feeds/feds.xml",
     ["macroeconomics", "quantitative_finance"], "en"),
    ("fed_ifdp", "https://www.federalreserve.gov/feeds/ifdp.xml",
     ["macroeconomics"], "en"),
    ("nber", "https://data.nber.org/rss/new.xml",
     ["macroeconomics", "valuation"], "en"),
]


def crawl(conn: sqlite3.Connection, *, limit: int, run_id: str) -> CrawlResult:  # noqa: ARG001
    result = CrawlResult(source=SOURCE, kind=KIND)
    per_feed = max(5, limit // len(FEEDS))

    for label, feed_url, topics, language in FEEDS:
        try:
            text = http_get_text(feed_url, timeout=30)
        except RuntimeError as err:
            result.error = f"{label}: {err}"
            continue

        try:
            root = ET.fromstring(text)
        except ET.ParseError as err:
            result.error = f"{label} parse: {err}"
            continue

        items = _iter_items(root)[:per_feed]
        for item in items:
            link = (item.get("link") or "").strip()
            title = _clean(item.get("title") or "")
            description = _clean(item.get("description") or "")
            published = item.get("pubdate") or item.get("published")
            published_iso = _to_iso(published) if published else None
            if not link or not title:
                result.skipped += 1
                continue

            external_id = _extract_external_id(link, label)
            resource_id = stable_id("paper", label, external_id)
            row = ResourceRow(
                kind=KIND,
                resource_id=resource_id,
                source=label,
                external_id=external_id,
                title=title,
                url=link,
                language=language,
                topics=topics,
                fields={
                    "abstract": description[:4000],
                    "pdf_url": link if link.lower().endswith(".pdf") else None,
                    "category": f"{label}_working_paper",
                    "authors_json": "[]",
                    "published_at": published_iso,
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


def _iter_items(root: ET.Element) -> list[dict[str, str]]:
    """Normalize RSS 2.0 and Atom feed entries."""
    items: list[dict[str, str]] = []
    # RSS 2.0
    for it in root.findall(".//item"):
        items.append({
            "title": (it.findtext("title") or ""),
            "link": (it.findtext("link") or ""),
            "description": (it.findtext("description") or ""),
            "pubdate": (it.findtext("pubDate") or ""),
        })
    # Atom
    atom_ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//a:entry", atom_ns):
        link_el = entry.find("a:link", atom_ns)
        link = link_el.attrib.get("href", "") if link_el is not None else ""
        items.append({
            "title": entry.findtext("a:title", default="", namespaces=atom_ns) or "",
            "link": link,
            "description": entry.findtext("a:summary", default="", namespaces=atom_ns) or "",
            "published": entry.findtext("a:published", default="", namespaces=atom_ns) or "",
        })
    return items


def _clean(value: str) -> str:
    # Strip HTML tags + collapse whitespace
    no_tags = re.sub(r"<[^>]+>", " ", value)
    return " ".join(no_tags.split()).strip()


def _to_iso(value: str) -> str | None:
    try:
        dt = parsedate_to_datetime(value)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return value[:32] if value else None


def _extract_external_id(link: str, label: str) -> str:
    """Use the final URL path segment as the stable external id."""
    cleaned = link.rstrip("/").split("?", 1)[0]
    segment = cleaned.rsplit("/", 1)[-1] or label
    return segment[:96]
