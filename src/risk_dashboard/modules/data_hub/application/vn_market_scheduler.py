from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone, timedelta

from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer
from risk_dashboard.modules.data_hub.application.global_market_feed import GlobalMarketFeedProducer

_START_LOCK = threading.Lock()
_STARTED = False

# Vietnam stock exchange hours (ICT = UTC+7)
# HOSE/HNX: continuous trading 09:00-11:30 + 13:00-14:45, ATC 14:45-15:00
# We poll aggressively 08:50-15:10 to cover pre-open + ATC, slower outside.
_ICT_OFFSET = timedelta(hours=7)
_MARKET_OPEN_HOUR = 8   # 08:50 ICT to allow warmup before 09:00
_MARKET_OPEN_MIN = 50
_MARKET_CLOSE_HOUR = 15
_MARKET_CLOSE_MIN = 10

# Tickers to prefetch — most-viewed VN large caps so user clicks hit warm cache
_PREFETCH_TICKERS = (
    "VNINDEX", "VN30", "HNXINDEX",
    "FPT", "VIC", "VHM", "VCB", "HPG", "MWG", "TCB",
)
_PREFETCH_INTERVALS = (("6mo", "1d"), ("1mo", "1d"), ("1d", "5m"))


def start_vn_market_scheduler(logger: logging.Logger) -> None:
    """Background daemon that refreshes the VN equity snapshot.

    Variable cadence: fast (10-15s) during VN market hours, slow (300s) off-hours.
    Controlled by env vars:
      - ENABLE_VN_MARKET_SCHEDULER: "0"/"false"/"off" to disable (default on)
      - VN_MARKET_INTERVAL_FAST_SEC: in-market refresh cadence (default 12s, min 5s)
      - VN_MARKET_INTERVAL_SLOW_SEC: off-market refresh cadence (default 300s, min 60s)
      - VN_MARKET_UNIVERSE_INTERVAL_SEC: universe refresh cadence (default 6h)
    Skipped under PYTEST_CURRENT_TEST.
    """
    global _STARTED
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    enabled = os.getenv("ENABLE_VN_MARKET_SCHEDULER", "1").strip().lower() not in {"0", "false", "off"}
    if not enabled:
        return
    with _START_LOCK:
        if _STARTED:
            return
        _STARTED = True
    thread = threading.Thread(target=_run_loop, args=(logger,), daemon=True, name="vn-market-scheduler")
    thread.start()
    logger.info("vn_market scheduler started")


def _is_market_hours(now_utc: datetime) -> bool:
    """True if current time is within VN trading hours window (with pre/post buffer)."""
    ict = now_utc + _ICT_OFFSET
    # Skip weekends (Vietnam trading is Mon-Fri only)
    if ict.weekday() >= 5:
        return False
    open_t = ict.replace(hour=_MARKET_OPEN_HOUR, minute=_MARKET_OPEN_MIN, second=0, microsecond=0)
    close_t = ict.replace(hour=_MARKET_CLOSE_HOUR, minute=_MARKET_CLOSE_MIN, second=0, microsecond=0)
    # Lunch break 11:30-13:00 — still poll but at fast cadence since brokers stream cached prices
    return open_t <= ict <= close_t


def _run_loop(logger: logging.Logger) -> None:
    producer = VnMarketFeedProducer()
    history_producer = GlobalMarketFeedProducer(max_cache_age_seconds=3600)
    fast_interval = max(int(os.getenv("VN_MARKET_INTERVAL_FAST_SEC", "12")), 5)
    slow_interval = max(int(os.getenv("VN_MARKET_INTERVAL_SLOW_SEC", "300")), 60)
    universe_interval = max(int(os.getenv("VN_MARKET_UNIVERSE_INTERVAL_SEC", "21600")), 3600)
    prefetch_interval = max(int(os.getenv("VN_MARKET_PREFETCH_INTERVAL_SEC", "7200")), 600)
    next_snapshot = 0.0
    next_universe = 0.0
    next_prefetch = 0.0
    last_log_state: str | None = None
    while True:
        now = time.time()
        now_utc = datetime.now(timezone.utc)
        in_market = _is_market_hours(now_utc)
        state = "market" if in_market else "off-hours"
        if state != last_log_state:
            logger.info("vn_market scheduler switched to %s mode (interval=%ds)", state, fast_interval if in_market else slow_interval)
            last_log_state = state
        try:
            if now >= next_universe:
                producer.universe()
                next_universe = now + universe_interval
            if now >= next_snapshot:
                producer.snapshot(force_refresh=True)
                next_snapshot = now + (fast_interval if in_market else slow_interval)
            if now >= next_prefetch:
                _prefetch_popular_history(history_producer, logger)
                next_prefetch = now + prefetch_interval
        except Exception as exc:
            logger.exception("vn_market scheduler iteration failed: %s", exc)
            next_snapshot = now + (fast_interval if in_market else slow_interval)
            next_universe = now + universe_interval
            next_prefetch = now + prefetch_interval
        time.sleep(min(5, fast_interval))


def _prefetch_popular_history(producer: GlobalMarketFeedProducer, logger: logging.Logger) -> None:
    """Pre-warm history cache for top tickers across popular intervals.

    Each call goes through the producer cache so already-fresh files are skipped.
    Spaces requests 1s apart to be polite to vnstock VCI rate limiter.
    """
    ok = 0
    fail = 0
    for symbol in _PREFETCH_TICKERS:
        for period, interval in _PREFETCH_INTERVALS:
            try:
                data = producer.history(symbol=symbol, period=period, interval=interval)
                if data.get("points"):
                    ok += 1
                else:
                    fail += 1
            except Exception:
                fail += 1
            time.sleep(1.0)
    logger.info("vn_market prefetch: %d ok, %d empty/failed across %d tickers", ok, fail, len(_PREFETCH_TICKERS))
