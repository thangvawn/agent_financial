"""Crawler orchestrator. Tracks each run in ``learning_crawl_runs`` so we
have an audit trail of when each source was fetched and how many rows it
moved.
"""
from __future__ import annotations

import importlib
import sqlite3
import uuid
from dataclasses import dataclass

from .common import utc_now_iso

# Sources are registered by importing the module under sources/. The crawl()
# function in each module is expected to return a CrawlResult.
SOURCE_MODULES: dict[str, str] = {
    "arxiv": "risk_dashboard.modules.learning.crawlers.sources.arxiv_qfin",
    "gutendex": "risk_dashboard.modules.learning.crawlers.sources.gutendex",
    "archive_org": "risk_dashboard.modules.learning.crawlers.sources.archive_org",
    "fed_imf_wb": "risk_dashboard.modules.learning.crawlers.sources.policy_papers",
    "mit_ocw": "risk_dashboard.modules.learning.crawlers.sources.mit_ocw",
    "youtube": "risk_dashboard.modules.learning.crawlers.sources.youtube_curated",
}


@dataclass
class CrawlResult:
    source: str
    kind: str
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    error: str | None = None

    def total(self) -> int:
        return self.inserted + self.updated + self.skipped


def _open_run(conn: sqlite3.Connection, source: str, kind: str) -> str:
    run_id = f"learn_{source}_{uuid.uuid4().hex[:10]}"
    conn.execute(
        """
        INSERT INTO learning_crawl_runs(
            run_id, source, kind, started_at, status
        ) VALUES (?, ?, ?, ?, 'running')
        """,
        (run_id, source, kind, utc_now_iso()),
    )
    conn.commit()
    return run_id


def _close_run(conn: sqlite3.Connection, run_id: str, result: CrawlResult) -> None:
    conn.execute(
        """
        UPDATE learning_crawl_runs
        SET completed_at = ?, rows_inserted = ?, rows_updated = ?,
            rows_skipped = ?, status = ?, error = ?
        WHERE run_id = ?
        """,
        (
            utc_now_iso(),
            result.inserted,
            result.updated,
            result.skipped,
            "error" if result.error else "ok",
            result.error,
            run_id,
        ),
    )
    conn.commit()


def run_source(conn: sqlite3.Connection, source_name: str, *, limit: int) -> CrawlResult:
    if source_name not in SOURCE_MODULES:
        raise KeyError(f"unknown source: {source_name}")
    module = importlib.import_module(SOURCE_MODULES[source_name])
    if not hasattr(module, "crawl"):
        raise RuntimeError(f"source {source_name} missing crawl()")
    kind = getattr(module, "KIND", "paper")
    run_id = _open_run(conn, source_name, kind)
    try:
        result: CrawlResult = module.crawl(conn, limit=limit, run_id=run_id)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001 — surface error in run log
        result = CrawlResult(source=source_name, kind=kind, error=str(exc))
    finally:
        _close_run(conn, run_id, result)
    return result


def run_all(conn: sqlite3.Connection, *, limit_per_source: int = 150) -> list[CrawlResult]:
    results: list[CrawlResult] = []
    for source in SOURCE_MODULES:
        results.append(run_source(conn, source, limit=limit_per_source))
    return results
