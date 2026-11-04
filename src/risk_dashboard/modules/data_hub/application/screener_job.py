"""Resumable background collection, separately from interactive screener reads."""

from __future__ import annotations

import fcntl
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone

from risk_dashboard.modules.data_hub.application.stock_screener import ICT, StockScreenerService
from risk_dashboard.modules.data_hub.domain.screener.indicators import canonical_bars
from risk_dashboard.modules.data_hub.infrastructure.screener_provider import VnstockScreenerProvider
from risk_dashboard.modules.data_hub.infrastructure.screener_store import ScreenerStore

LOG = logging.getLogger(__name__)


def collection_session(now, calendar):
    local = now.astimezone(ICT)
    cutoff = local.date() if local.hour >= 16 else local.date() - timedelta(days=1)
    if calendar.get("valid_through", "") < local.date().isoformat():
        return cutoff.isoformat()
    sessions = [d for d in calendar.get("sessions", []) if d <= cutoff.isoformat()]
    return max(sessions) if sessions else cutoff.isoformat()


def import_bundle(bundle, store):
    """Local operator ingestion only; not an unauthenticated public write endpoint."""
    if not isinstance(bundle, dict) or not isinstance(bundle.get("calendar"), dict):
        raise ValueError("Bundle cần calendar dạng object.")
    calendar = bundle.get("calendar", {})
    sessions = calendar.get("sessions", [])
    try:
        if not isinstance(sessions, list):
            raise ValueError()
        for session in [*sessions, calendar.get("valid_through")]:
            date.fromisoformat(session)
    except (ValueError, TypeError):
        raise ValueError("Lịch phiên cần ngày hợp lệ YYYY-MM-DD.") from None
    if (
        not sessions
        or sorted(set(sessions)) != sessions
        or not calendar.get("source")
        or calendar.get("valid_through", "") < sessions[-1]
    ):
        raise ValueError("Bundle cần lịch phiên có nguồn và valid_through.")
    as_of = sessions[-1]
    records = bundle.get("inputs", {})
    if not isinstance(records, dict) or not records or len(records) > 5000:
        raise ValueError("Bundle phải có từ 1 đến 5000 mã.")
    import re

    # Validate every input before any mutation; importing bad data cannot erase good data.
    for symbol, data in records.items():
        if not re.fullmatch(r"[A-Z0-9]{2,12}", symbol):
            raise ValueError("Mã không hợp lệ.")
        if not isinstance(data, dict):
            raise ValueError(f"{symbol}: dữ liệu phải là object.")
        bars, errors = canonical_bars(data.get("history", {}), as_of)
        if errors or not bars:
            raise ValueError(f"{symbol}: {', '.join(errors) or 'history_empty'}")
    for symbol, data in records.items():
        store.write(f"inputs/{symbol}.json", data)
    store.write("calendar.json", calendar)
    store.write(
        "collection.json",
        {
            "status": "imported",
            "symbols": len(records),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def collect(
    quote_loader, store=None, provider_factory=VnstockScreenerProvider, *, max_symbols=30, delay=4.1
):
    store = store or ScreenerStore()
    store.root.mkdir(parents=True, exist_ok=True)
    # Process lock protects checkpoints when API workers each start a scheduler.
    with (store.root / "job.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "running"}
        quotes = quote_loader()
        now = datetime.now(timezone.utc)
        checkpoint = store.read("collection.json")
        if checkpoint.get("retry_after", 0) > time.time():
            return checkpoint
        day = collection_session(now, store.read("calendar.json"))
        if checkpoint.get("collection_day") == day and checkpoint.get("status") == "ready":
            return checkpoint
        queue = store.read("collection-queue.json")
        if queue.get("collection_day") != day:
            ordered = sorted(
                (q for q in quotes if len(q.get("symbol", "")) == 3 and q["symbol"].isalpha()),
                key=lambda q: (-(q.get("market_cap") or 0), q["symbol"]),
            )
            queue = {
                "collection_day": day,
                "symbols": list(dict.fromkeys(q["symbol"] for q in ordered)),
            }
            store.write("collection-queue.json", queue)
        ordered = queue["symbols"]
        offset = int(checkpoint.get("offset", 0)) if checkpoint.get("collection_day") == day else 0
        try:
            provider = provider_factory()
            calendar = provider.calendar()
            store.write("calendar.json", calendar)
            target_session = collection_session(now, calendar)
            if day != target_session:
                day, offset = target_session, 0
                queue["collection_day"] = day
                store.write("collection-queue.json", queue)
            for symbol in ("VNINDEX", "HNXINDEX", "UPCOMINDEX"):
                store.write(f"inputs/{symbol}.json", provider.benchmark(symbol))
                if delay:
                    time.sleep(delay)
        except Exception as exc:
            result = {
                **checkpoint,
                "status": "provider_unavailable",
                "reason": type(exc).__name__,
                "updated_at": now.isoformat(),
                "retry_after": time.time() + 3600,
            }
            store.write("collection.json", result)
            StockScreenerService(store).rebuild(quotes)
            return result
        errors = 0
        processed = 0
        for symbol in ordered[offset : offset + max_symbols]:
            try:
                data = provider.equity(symbol)
                history = data.get("history", {})
                final_days = [
                    b.get("date", "")
                    for b in history.get("bars", [])
                    if b.get("is_final") is True and b.get("date", "") <= target_session
                ]
                if not final_days or max(final_days) != target_session:
                    raise ValueError("history_stale")
                current = store.input(symbol)
                store.write(f"inputs/{symbol}.json", {**current, **data})
            except Exception as exc:
                errors += 1
                LOG.info("Screener collection %s: %s", symbol, type(exc).__name__)
                # Retry this symbol after backoff, never silently advance past missing data.
                break
            processed += 1
            store.write(
                "collection.json",
                {
                    "status": "collecting",
                    "offset": offset + processed,
                    "total": len(ordered),
                    "collection_day": day,
                    "updated_at": now.isoformat(),
                },
            )
            if delay:
                time.sleep(delay)
        result = {
            "status": "partial"
            if errors
            else "ready"
            if offset + processed >= len(ordered)
            else "collecting",
            "offset": offset + processed,
            "total": len(ordered),
            "failed": errors,
            "collection_day": day,
            "updated_at": now.isoformat(),
            "retry_after": time.time()
            + (3600 if errors or offset + processed >= len(ordered) else 60),
        }
        store.write("collection.json", result)
        StockScreenerService(store).rebuild(quotes)
        return result


def start_screener_job(quote_loader):
    import threading

    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("ENABLE_VN_SCREENER", "1").lower() in {
        "0",
        "false",
        "off",
    }:
        return

    def loop():
        while True:
            try:
                collect(quote_loader)
            except Exception:
                LOG.exception("Screener job failed; previous snapshot remains available")
            time.sleep(300)

    threading.Thread(target=loop, name="vn-eod-screener", daemon=True).start()
