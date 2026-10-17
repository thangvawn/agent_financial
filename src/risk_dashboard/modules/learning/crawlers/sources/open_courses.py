"""Open university courses crawler and seeder.

Collects public lecture series and syllabi from world-leading universities
(Yale, NYU Stern, Stanford, Wharton, Columbia) and top Vietnamese institutions
(NEU, FTU, UEH, SSI Academy, Vietstock) with canonical identifiers, levels,
and verified finance topics.
"""
from __future__ import annotations

import json
import sqlite3

from ..common import ResourceRow, stable_id, upsert_resource
from ..runner import CrawlResult
from .open_courses_data import OPEN_COURSES

KIND = "course"
SOURCE = "open_courses"


def crawl(conn: sqlite3.Connection, *, limit: int, run_id: str) -> CrawlResult:  # noqa: ARG001
    result = CrawlResult(source=SOURCE, kind=KIND)

    for item in OPEN_COURSES[:limit]:
        code = item["code"]
        external_id = code
        resource_id = f"course_{code}"
        sections = item.get("sections", [])
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
                "provider": item.get("provider"),
                "instructor": item.get("instructor"),
                "description": item.get("description", ""),
                "thumbnail_url": item.get("thumbnail_url"),
                "level": item.get("level"),
                "duration_minutes": item.get("duration_minutes"),
                "sections_json": json.dumps(sections, ensure_ascii=False) if sections else None,
                "published_at": None,
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
