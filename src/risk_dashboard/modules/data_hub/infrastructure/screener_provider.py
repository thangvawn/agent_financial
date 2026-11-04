"""Explicit provider capability boundary. No credential tricks or fabricated fields.

Vnstock Market.trade_history schema:
https://www.vnstocks.com/docs/vnstock/thi-truong-market (sections 2.7/2.8).
Old chart caches do not meet this contract and are not silently promoted.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean

from risk_dashboard.modules.data_hub.domain.screener.indicators import number

ICT = timezone(timedelta(hours=7))
REFERENCE = "https://www.vnstocks.com/docs/vnstock/thi-truong-market"


class ProviderUnavailable(RuntimeError):
    pass


def from_trade_history(symbol, records, *, source, now=None):
    """Provider's raw/adjusted VND prices and actual matched turnover, not C×V."""
    now = now or datetime.now(ICT)
    cutoff = (
        now.date().isoformat() if now.hour >= 16 else (now.date() - timedelta(days=1)).isoformat()
    )
    bars = []
    factors = []
    for r in records:
        day = str(r.get("trading_date", ""))[:10]
        if not day or day > cutoff:
            continue
        bar = {
            "date": day,
            "is_final": True,
            "volume": number(r.get("matched_volume")),
            "matched_turnover_vnd": number(r.get("matched_value")),
        }
        for k in ("open", "high", "low", "close"):
            bar[k] = number(r.get(k + "_adjusted"))
        bars.append(bar)
        raw, adjusted = number(r.get("close")), bar["close"]
        factors.append((day, adjusted / raw if adjusted and raw and raw > 0 else None))
    bars.sort(key=lambda b: b["date"])
    factors.sort()
    recent = [factor for _, factor in factors[-25:]]
    # Without an explicit share adjustment factor, conservatively withhold
    # volume-based signals across ANY adjustment-factor change in the 25-day window.
    comparable = (
        len(recent) == 25
        and all(x is not None and x > 0 for x in recent)
        and max(recent) - min(recent) <= mean(recent) * 0.001
    )
    return {
        "source": source,
        "price_unit": "VND",
        "price_basis": "corporate_action_adjusted",
        "adjustment_reference": REFERENCE,
        "return_basis": "corporate_action_adjusted",
        "volume_basis": "as_traded_no_splits" if comparable else "unverified",
        "volume_comparison_window": 25,
        "fetched_at": now.isoformat(),
        "bars": bars,
    }


class VnstockScreenerProvider:
    def __init__(self):
        try:
            from vnstock import Market
        except ImportError as exc:
            raise ProviderUnavailable(
                "provider_capability_missing: "
                "vnstock Market.trade_history chưa có trong bản cài đặt."
            ) from exc
        self.market = Market()
        if not callable(getattr(self.market.equity("FPT"), "trade_history", None)):
            raise ProviderUnavailable(
                "provider_capability_missing: bản vnstock đang cài chưa có trade_history."
            )

    def calendar(self):
        from vnstock import Reference

        now = datetime.now(ICT)
        start = now.date() - timedelta(days=750)
        events = Reference().events.market()
        rows = events.to_dict("records")
        event_dates = [str(r.get("date", ""))[:10] for r in rows]
        # A table that doesn't cover the current year cannot certify this year's holidays.
        if not event_dates or max(event_dates)[:4] < str(now.year):
            raise ProviderUnavailable("calendar_coverage_missing")
        closed = {
            str(r.get("date", ""))[:10]
            for r in rows
            if r.get("type") in ("Holiday", "Compensation")
        }
        end = now.date() + timedelta(days=7)
        end = min(end, now.date().replace(month=12, day=31))
        days = []
        current = start
        while current <= end:
            if current.weekday() < 5 and current.isoformat() not in closed:
                days.append(current.isoformat())
            current += timedelta(days=1)
        return {
            "source": "vnstock:Reference.events.market",
            "sessions": days,
            "valid_through": end.isoformat(),
        }

    def benchmark(self, symbol):
        frame = self.market.index(symbol).ohlcv(length="400b", source="vci")
        now = datetime.now(ICT)
        cutoff = (
            now.date().isoformat()
            if now.hour >= 16
            else (now.date() - timedelta(days=1)).isoformat()
        )
        bars = []
        for r in frame.to_dict("records"):
            day = str(r.get("time", ""))[:10]
            if day and day <= cutoff:
                bars.append(
                    {
                        **{k: number(r.get(k)) for k in ("open", "high", "low", "close", "volume")},
                        "date": day,
                        "is_final": True,
                    }
                )
        return {
            "history": {
                "source": "vnstock:vci:index",
                "bars": bars,
                "price_unit": "index_points",
                "price_basis": "index_price",
                "volume_basis": "index",
                "adjustment_reference": REFERENCE,
                "return_basis": "price",
            }
        }

    def equity(self, symbol):
        handle = self.market.equity(symbol)
        if not hasattr(handle, "trade_history"):
            raise ProviderUnavailable(
                "provider_capability_missing: cần lịch sử giá trị khớp và OHLC đã điều chỉnh."
            )
        frame = handle.trade_history(limit=400, source="vci")
        if frame is None or frame.empty:
            raise ProviderUnavailable("provider_empty_history")
        return {
            "security_type": "common_stock",
            "history": from_trade_history(
                symbol, frame.to_dict("records"), source="vnstock:vci:trade_history"
            ),
        }
