"""Read cached inputs, create a frozen full-universe evaluation, then query it."""

from __future__ import annotations

import base64
import json
import threading
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from risk_dashboard.modules.data_hub.domain.screener.engine import build_snapshot
from risk_dashboard.modules.data_hub.domain.screener.indicators import number
from risk_dashboard.modules.data_hub.domain.screener.rules import (
    PRESETS,
    TECHNICAL,
    VERSION,
    catalog,
)
from risk_dashboard.modules.data_hub.infrastructure.screener_store import ScreenerStore

ICT = timezone(timedelta(hours=7))


class ScreenerQueryError(ValueError):
    pass


class StockScreenerService:
    def __init__(self, store=None):
        self.store = store or ScreenerStore()
        self._lock = threading.Lock()
        self._cache = {}
        self._checked = 0

    def rebuild(self, quotes):
        """Offline and bounded. Provider collection belongs to a separate background job."""
        calendar = self.store.read("calendar.json")
        now = datetime.now(ICT)
        cutoff = (
            now.date().isoformat()
            if now.hour >= 16
            else (now.date() - timedelta(days=1)).isoformat()
        )
        sessions = sorted(d for d in calendar.get("sessions", []) if d <= cutoff)
        as_of = sessions[-1] if sessions else cutoff
        histories, benchmarks, fundamentals, dividends, foreign = {}, {}, {}, {}, {}
        universe = []
        seen = set()
        for q in quotes:
            if not isinstance(q, dict) or not q.get("symbol"):
                continue
            symbol = str(q["symbol"]).upper()
            if symbol in seen:
                continue
            seen.add(symbol)
            data = self.store.input(symbol)
            universe.append(
                {
                    **q,
                    "symbol": symbol,
                    "security_type": data.get("security_type", q.get("security_type")),
                    "industry": data.get("industry") or q.get("industry") or q.get("sector"),
                    "suspended": data.get("suspended", q.get("suspended")),
                }
            )
            histories[symbol] = data.get("history", {})
            fundamentals[symbol] = data.get("fundamentals", {})
            dividends[symbol] = data.get("dividends", {})
            foreign[symbol] = data.get("foreign", {})
        for key in ("VNINDEX", "HNXINDEX", "UPCOMINDEX"):
            benchmarks[key] = self.store.input(key).get("history", {})
        result = build_snapshot(
            universe,
            histories,
            benchmarks,
            as_of=as_of,
            calendar=calendar,
            fundamentals=fundamentals,
            dividends=dividends,
            foreign=foreign,
        )
        # Don't claim a weekday-inferred date is an observed final market session.
        result["session_verified"] = bool(
            sessions
            and calendar.get("source")
            and calendar.get("valid_through", "") >= now.date().isoformat()
        )
        future_sessions = sorted(d for d in calendar.get("sessions", []) if d > as_of)
        result["valid_until"] = (
            (future_sessions[0] + "T16:00:00+07:00")
            if future_sessions
            else (calendar.get("valid_through", as_of) + "T23:59:59+07:00")
        )
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        self.store.save_snapshot(result)
        self._cache = result
        self._checked = time.monotonic()
        return result

    def current(self, quotes):
        with self._lock:
            if self._cache and time.monotonic() - self._checked < 30:
                return self._cache
            latest = self.store.snapshot()
            if latest and latest.get("formula_version") == VERSION:
                self._cache = latest
                self._checked = time.monotonic()
                return latest
            return self.rebuild(quotes)

    def query(
        self,
        quotes,
        *,
        preset="",
        technical="all",
        sector="",
        exchange="",
        sort="score_desc",
        limit=50,
        cursor="",
        snapshot_id="",
    ):
        if preset and preset not in PRESETS:
            raise ScreenerQueryError("Tín hiệu không hợp lệ.")
        if technical not in ("all", *TECHNICAL):
            raise ScreenerQueryError("Chỉ báo không hợp lệ.")
        if sort not in (
            "score_desc",
            "market_cap_desc",
            "change_desc",
            "change_asc",
            "volume_desc",
            "value_desc",
            "foreign_net_buy_desc",
            "symbol_asc",
        ):
            raise ScreenerQueryError("Sắp xếp không hợp lệ.")
        params = {
            "preset": preset,
            "technical": technical,
            "sector": sector,
            "exchange": exchange,
            "sort": sort,
        }
        query_hash = sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
        offset = 0
        if cursor:
            try:
                c = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
                if (
                    c["query"] != query_hash
                    or type(c["offset"]) is not int
                    or not 0 <= c["offset"] <= 100000
                ):
                    raise ValueError()
                snapshot_id = c["snapshot"]
                offset = c["offset"]
            except (ValueError, KeyError, TypeError, UnicodeError) as e:
                raise ScreenerQueryError("Con trỏ phân trang không hợp lệ.") from e
        snapshot = self.store.snapshot(snapshot_id) if snapshot_id else self.current(quotes)
        if not snapshot or snapshot.get("formula_version") != VERSION:
            raise ScreenerQueryError("Phiên dữ liệu đã hết hạn. Hãy tải lại bộ lọc.")
        selected = [x for x in (preset, technical if technical != "all" else "") if x]
        live = {q["symbol"]: q for q in quotes}
        scoped = []
        for r in snapshot["rows"]:
            q = r["quote"]
            ex = str(q.get("exchange", "")).replace("HSX", "HOSE")
            if exchange and ex != exchange.replace("HSX", "HOSE"):
                continue
            if sector and sector != (q.get("industry") or q.get("sector")):
                continue
            states = [r["signals"][key]["status"] for key in selected]
            status = next(
                (x for x in ("not_eligible", "stale", "unknown") if x in states), "evaluated"
            )
            matches = all(r["signals"][key]["matched"] for key in selected)
            scoped.append((r, status, matches))
        counts = Counter(s for _, s, _ in scoped)
        result = []
        reasons = Counter()
        for row, status, match in scoped:
            row_reasons = set()
            for key in selected:
                if row["signals"][key]["status"] in ("unknown", "stale", "not_eligible"):
                    row_reasons.update(row["signals"][key]["reason_codes"])
            reasons.update(row_reasons)
            if selected and (status != "evaluated" or not match):
                continue
            signal = row["signals"].get(preset or (technical if technical != "all" else ""), {})
            result.append(
                {
                    **row["quote"],
                    **live.get(row["symbol"], {}),
                    "screening": {
                        **signal,
                        "data_as_of": row["data_as_of"],
                        "source": row["source"],
                        "metrics": row["features"],
                        "signals": {key: row["signals"][key] for key in selected},
                        "score_meaning": (
                            "Mức độ nổi bật theo tiêu chí, không phải xác suất tăng giá."
                        ),
                    },
                }
            )
        field = {
            "market_cap_desc": "market_cap",
            "change_desc": "change_pct",
            "change_asc": "change_pct",
            "volume_desc": "volume",
            "value_desc": "value",
            "foreign_net_buy_desc": "foreign_net_buy",
        }.get(sort)
        if sort == "symbol_asc":
            result.sort(key=lambda r: r["symbol"])
        else:
            # Freeze ordering with the quote at evaluation time for stable cursor pages.
            frozen = {r["symbol"]: r["quote"] for r, _, _ in scoped}

            def order(row):
                val = (
                    number(row["screening"].get("score"))
                    if sort == "score_desc"
                    else number(frozen[row["symbol"]].get(field))
                )
                return (
                    val is None,
                    (val if sort == "change_asc" else -val) if val is not None else 0,
                    row["symbol"],
                )

            result.sort(key=order)
        next_offset = offset + limit
        next_cursor = (
            base64.urlsafe_b64encode(
                json.dumps(
                    {
                        "snapshot": snapshot["snapshot_id"],
                        "query": query_hash,
                        "offset": next_offset,
                    }
                ).encode()
            ).decode()
            if next_offset < len(result)
            else None
        )
        now_day = datetime.now(ICT).date().isoformat()
        fresh = bool(
            snapshot.get("session_verified")
            and snapshot.get("calendar_valid_through", "") >= now_day
            and datetime.now(ICT)
            < datetime.fromisoformat(snapshot.get("valid_until", now_day + "T23:59:59+07:00"))
        )
        return {
            "snapshot_id": snapshot["snapshot_id"],
            "formula_version": snapshot["formula_version"],
            "as_of": snapshot["as_of"],
            "session_verified": snapshot.get("session_verified", False),
            "freshness": "fresh" if fresh else "stale",
            "universe_id": snapshot["universe_id"],
            "universe_total": snapshot["universe_total"],
            "scope_total": len(scoped),
            "eligible": sum(row["eligibility"] == "eligible" for row, _, _ in scoped),
            "evaluated": counts["evaluated"],
            "unknown": counts["unknown"],
            "stale": counts["stale"],
            "not_eligible": counts["not_eligible"],
            "matched": len(result),
            "returned": len(result[offset:next_offset]),
            "offset": offset,
            "next_cursor": next_cursor,
            "items": result[offset:next_offset],
            "catalog": catalog(),
            "missing_reasons": dict(reasons),
            "collection": self.store.read("collection.json"),
            "refresh_interval_seconds": 60,
        }
