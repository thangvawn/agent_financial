"""Serialize yfinance.download, which uses process-global result dictionaries.

The lock is shared by the market feed and backtests. threads=False alone only
changes workers inside one download; it does not serialize concurrent callers.
"""

from threading import RLock

_DOWNLOAD_LOCK = RLock()


def download_yahoo(*args, **kwargs):
    import yfinance as yf

    with _DOWNLOAD_LOCK:
        # Initialize SQLite cache tables once before yf.download starts workers.
        # Concurrent lazy initialization on a fresh cache can lock the database.
        yf.cache.get_tz_cache().initialise()
        yf.cache.get_cookie_cache().initialise()
        return yf.download(*args, **kwargs)
