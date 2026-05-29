"""CLI: ``risk-learning-crawl`` — populate the learning catalog.

Usage:
    risk-learning-crawl                 # run every source with default limit
    risk-learning-crawl --source arxiv  # one source only
    risk-learning-crawl --limit 50      # cap rows per source

The script opens the app-state SQLite DB (path is settings-driven), runs
the topic seeder, then dispatches to each crawler. Each run records to
``learning_crawl_runs`` so we have a full audit trail.
"""
from __future__ import annotations

import argparse
import sys

from risk_dashboard.modules.learning.crawlers import run_all, run_source
from risk_dashboard.modules.learning.crawlers.common import (
    ensure_topics_seeded,
    open_catalog_db,
)
from risk_dashboard.modules.learning.crawlers.runner import SOURCE_MODULES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Populate the learning catalog from public sources.")
    parser.add_argument(
        "--source",
        choices=sorted(SOURCE_MODULES.keys()),
        help="Run a single source instead of all.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=150,
        help="Max rows per source (default: 150).",
    )
    parser.add_argument(
        "--db-path",
        help="Override app-state DB path (defaults to settings).",
    )
    args = parser.parse_args(argv)

    conn = open_catalog_db(args.db_path)
    try:
        seeded = ensure_topics_seeded(conn)
        conn.commit()
        print(f"[topics] seeded/refreshed {seeded} rows")

        if args.source:
            results = [run_source(conn, args.source, limit=args.limit)]
        else:
            results = run_all(conn, limit_per_source=args.limit)

        for r in results:
            label = "OK" if not r.error else "ERR"
            extra = f" error={r.error}" if r.error else ""
            print(
                f"[{label}] {r.source:<14} {r.kind:<6} "
                f"inserted={r.inserted:>4} updated={r.updated:>4} skipped={r.skipped:>4}{extra}"
            )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
