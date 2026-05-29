"""arXiv crawler for the q-fin (quantitative finance) category.

Uses the public arXiv Atom API: https://export.arxiv.org/api/query
No API key required. We map arXiv subcategories to our internal topics.
"""
from __future__ import annotations

import sqlite3
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

from ..common import (
    ResourceRow,
    http_get_text,
    stable_id,
    upsert_resource,
)
from ..runner import CrawlResult

KIND = "paper"
SOURCE = "arxiv"

# arXiv search categories → our topic ids. One paper can be tagged with multiple.
CATEGORY_TOPICS: dict[str, list[str]] = {
    "q-fin.PM": ["portfolio_theory", "risk_management"],          # Portfolio Management
    "q-fin.RM": ["risk_management"],                              # Risk Management
    "q-fin.PR": ["derivatives", "valuation"],                     # Pricing of Securities
    "q-fin.MF": ["quantitative_finance", "valuation"],            # Mathematical Finance
    "q-fin.ST": ["quantitative_finance"],                         # Statistical Finance
    "q-fin.GN": ["quantitative_finance"],                         # General Finance
    "q-fin.TR": ["technical_analysis"],                           # Trading & Microstructure
    "q-fin.CP": ["quantitative_finance"],                         # Computational Finance
    "q-fin.EC": ["macroeconomics"],                               # Economics
}


ATOM_NS = {
    "a": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def crawl(conn: sqlite3.Connection, *, limit: int, run_id: str) -> CrawlResult:  # noqa: ARG001
    """Fetch ``limit`` papers spread across the q-fin subcategories."""
    result = CrawlResult(source=SOURCE, kind=KIND)
    per_category = max(5, limit // len(CATEGORY_TOPICS))

    for category, topics in CATEGORY_TOPICS.items():
        params = urlencode(
            {
                "search_query": f"cat:{category}",
                "start": 0,
                "max_results": per_category,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        url = f"https://export.arxiv.org/api/query?{params}"
        try:
            text = http_get_text(url, timeout=30)
        except RuntimeError as err:
            result.error = f"{category}: {err}"
            continue

        try:
            root = ET.fromstring(text)
        except ET.ParseError as err:
            result.error = f"{category} parse: {err}"
            continue

        for entry in root.findall("a:entry", ATOM_NS):
            arxiv_id_raw = entry.findtext("a:id", default="", namespaces=ATOM_NS)
            external_id = arxiv_id_raw.rsplit("/", 1)[-1].split("v")[0].strip()
            if not external_id:
                result.skipped += 1
                continue

            title = " ".join((entry.findtext("a:title", default="", namespaces=ATOM_NS) or "").split())
            abstract = " ".join((entry.findtext("a:summary", default="", namespaces=ATOM_NS) or "").split())
            published = entry.findtext("a:published", default=None, namespaces=ATOM_NS)
            authors = [
                (a.findtext("a:name", default="", namespaces=ATOM_NS) or "").strip()
                for a in entry.findall("a:author", ATOM_NS)
            ]
            authors = [a for a in authors if a][:8]

            pdf_url = None
            html_url = None
            for link in entry.findall("a:link", ATOM_NS):
                rel = link.attrib.get("rel")
                title_attr = link.attrib.get("title")
                href = link.attrib.get("href")
                if title_attr == "pdf" and href:
                    pdf_url = href
                elif rel == "alternate" and href:
                    html_url = href

            url_canonical = html_url or f"https://arxiv.org/abs/{external_id}"
            resource_id = stable_id("paper", SOURCE, external_id)

            row = ResourceRow(
                kind=KIND,
                resource_id=resource_id,
                source=SOURCE,
                external_id=external_id,
                title=title or "Untitled paper",
                url=url_canonical,
                language="en",
                topics=topics,
                fields={
                    "authors_json": _json_dumps(authors),
                    "abstract": abstract[:4000],
                    "pdf_url": pdf_url,
                    "category": category,
                    "published_at": published,
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


def _json_dumps(value) -> str:
    import json
    return json.dumps(value, ensure_ascii=False)
