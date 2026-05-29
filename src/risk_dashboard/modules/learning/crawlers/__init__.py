"""Learning catalog crawlers (courses / videos / books / papers).

Each source under ``sources/`` exposes a ``crawl(conn, *, limit, run_id) -> CrawlResult``
function. Use ``run`` from ``runner`` to orchestrate them.
"""
from .runner import CrawlResult, run_source, run_all  # noqa: F401
