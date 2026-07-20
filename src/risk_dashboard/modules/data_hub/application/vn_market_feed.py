from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
import threading
from pathlib import Path
from typing import Any

import pandas as pd


_PROJECT_ROOT = Path(__file__).resolve().parents[5]
VN_MARKET_CACHE_DIR = _PROJECT_ROOT / "data" / "vn_market"
UNIVERSE_PATH = VN_MARKET_CACHE_DIR / "universe.json"
SNAPSHOT_PATH = VN_MARKET_CACHE_DIR / "snapshot.json"

UNIVERSE_TTL_SECONDS = 24 * 3600
SNAPSHOT_TTL_SECONDS = 15

_LOG = logging.getLogger(__name__)

# Fallback share-count registry used when the quote provider does not include
# listed shares in its price-board response. Prices remain live; this registry
# is only the slower-moving denominator needed to calculate market cap.
KNOWN_SHARES_OUTSTANDING: dict[str, float] = {
    "VIC": 7_762_186_000,
    "VHM": 4_107_409_000,
    "VCB": 8_355_084_000,
    "BID": 7_280_593_000,
    "VGI": 3_044_000_000,
    "CTG": 7_767_000_000,
    "TCB": 7_088_000_000,
    "VPB": 7_934_000_000,
    "MBB": 8_055_000_000,
    "HPG": 8_442_000_000,
}


@dataclass(frozen=True)
class VnTicker:
    symbol: str
    name: str
    exchange: str


class VnMarketFeedProducer:
    """Single source of truth for VN equity universe + intraday snapshot.

    Uses vnstock 4.x: Listing.all_symbols() and Listing.symbols_by_exchange()
    for the universe, Trading(source='VCI').price_board(symbols) for the snapshot.
    Persists results to data/vn_market/{universe,snapshot}.json with TTL refresh.
    """

    _refresh_lock = threading.Lock()

    def __init__(
        self,
        *,
        cache_dir: Path = VN_MARKET_CACHE_DIR,
        universe_ttl_seconds: int = UNIVERSE_TTL_SECONDS,
        snapshot_ttl_seconds: int = SNAPSHOT_TTL_SECONDS,
    ) -> None:
        self.cache_dir = cache_dir
        self.universe_ttl_seconds = universe_ttl_seconds
        self.snapshot_ttl_seconds = snapshot_ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "history").mkdir(parents=True, exist_ok=True)

    # ----- Universe -------------------------------------------------------
    def universe(self) -> dict[str, Any]:
        cached = self._load_json(UNIVERSE_PATH)
        if self._is_fresh(cached, self.universe_ttl_seconds):
            return cached
        live = self._fetch_universe_live()
        if live["tickers"]:
            self._write_json(UNIVERSE_PATH, live)
            return live
        return cached or live

    def _fetch_universe_live(self) -> dict[str, Any]:
        try:
            from vnstock import Listing  # type: ignore

            listing = Listing()
            frame = listing.all_symbols()
        except Exception as exc:
            _LOG.warning("VN universe fetch failed: %s", exc)
            return {"as_of": _utc_now_iso(), "tickers": [], "source": "vnstock"}

        # Try to enrich with exchange via symbols_by_exchange (single call returns all)
        exchange_map: dict[str, str] = {}
        try:
            from vnstock import Listing  # type: ignore

            ex_frame = Listing().symbols_by_exchange()
            sym_col = "symbol" if "symbol" in ex_frame.columns else ex_frame.columns[0]
            ex_col = next((c for c in ("exchange", "exchange_code", "exchange_name") if c in ex_frame.columns), None)
            if ex_col is not None:
                for _, row in ex_frame.iterrows():
                    sym = str(row.get(sym_col, "")).strip().upper()
                    ex = str(row.get(ex_col, "")).strip().upper() or ""
                    if sym:
                        exchange_map[sym] = ex
        except Exception as exc:
            _LOG.info("VN exchange enrichment skipped: %s", exc)

        tickers: list[dict[str, str]] = []
        for _, row in frame.iterrows():
            sym = str(row.get("symbol", "")).strip().upper()
            if not sym or not sym.isalpha() or not (3 <= len(sym) <= 5):
                continue
            tickers.append(
                {
                    "symbol": sym,
                    "name": str(row.get("organ_name", "") or "").strip() or sym,
                    "exchange": exchange_map.get(sym, ""),
                }
            )
        return {"as_of": _utc_now_iso(), "tickers": tickers, "source": "vnstock"}

    # ----- Snapshot -------------------------------------------------------
    def snapshot(self, *, force_refresh: bool = False) -> dict[str, Any]:
        cached = self._load_json(SNAPSHOT_PATH)
        if not force_refresh and self._is_fresh(cached, self.snapshot_ttl_seconds):
            self._enrich_market_cap(cached)
            return cached
        live = self._fetch_snapshot_live()
        if live["items"]:
            self._write_json(SNAPSHOT_PATH, live)
            return live
        if cached:
            cached.setdefault("freshness", "stale")
            self._enrich_market_cap(cached)
            return cached
        return live

    def _enrich_market_cap(self, payload: dict[str, Any]) -> None:
        shares_map = _cached_profile_shares(self.cache_dir)
        for item in payload.get("items", []) or []:
            shares = shares_map.get(str(item.get("symbol") or "").upper())
            if shares:
                item["shares_outstanding"] = _round(shares, 0)
                if item.get("price") is not None:
                    item["market_cap"] = _round(float(item["price"]) * shares / 1_000_000_000, 2)
            if item.get("price") is not None:
                buy = float(item.get("foreign_buy_volume") or 0)
                sell = float(item.get("foreign_sell_volume") or 0)
                item["foreign_net_buy"] = _round((buy - sell) * float(item["price"]) / 1_000_000, 2)

    def _fetch_snapshot_live(self) -> dict[str, Any]:
        universe = self.universe().get("tickers", [])
        if not universe:
            return {"as_of": _utc_now_iso(), "items": [], "source": "vnstock", "freshness": "degraded"}

        symbols = [t["symbol"] for t in universe]
        # Use the shared rate limiter + SystemExit shield from global_market_feed
        from risk_dashboard.modules.data_hub.application.global_market_feed import (
            _VNSTOCK_RATE_LIMITER, _vnstock_safe, _VnstockRateExceeded,
        )
        try:
            _VNSTOCK_RATE_LIMITER.acquire()
            with _vnstock_safe():
                from vnstock import Trading  # type: ignore

                board = Trading(source="VCI").price_board(symbols)
        except _VnstockRateExceeded:
            _LOG.warning("VN price_board rate-limited (vnstock guest tier)")
            return {"as_of": _utc_now_iso(), "items": [], "source": "vnstock", "freshness": "degraded"}
        except Exception as exc:
            _LOG.warning("VN price_board failed: %s", exc)
            return {"as_of": _utc_now_iso(), "items": [], "source": "vnstock", "freshness": "degraded"}

        items = _normalize_price_board(board)
        # Recalculate market cap from the live matched price and the latest
        # available share count. This keeps ranking intraday without fetching
        # one company profile per ticker.
        shares_map = _cached_profile_shares(self.cache_dir)

        # Annotate with name from universe
        name_map = {t["symbol"]: t["name"] for t in universe}
        ex_map = {t["symbol"]: t["exchange"] for t in universe}
        for item in items:
            sym = item.get("symbol", "")
            if sym in name_map and not item.get("name"):
                item["name"] = name_map[sym]
            if not item.get("exchange") and sym in ex_map:
                item["exchange"] = ex_map[sym]
            shares = shares_map.get(sym)
            if shares:
                item["shares_outstanding"] = _round(shares, 0)
                if item.get("price") is not None:
                    item["market_cap"] = _round(float(item["price"]) * shares / 1_000_000_000, 2)
            if item.get("price") is not None:
                buy = float(item.get("foreign_buy_volume") or 0)
                sell = float(item.get("foreign_sell_volume") or 0)
                item["foreign_net_buy"] = _round((buy - sell) * float(item["price"]) / 1_000_000, 2)
        return {
            "as_of": _utc_now_iso(),
            "source": "vnstock",
            "freshness": "fresh",
            "count": len(items),
            "items": items,
        }

    def refresh_in_background(self) -> threading.Thread:
        """Trigger a one-shot snapshot refresh in a background thread.

        Returns the thread so callers can join() or ignore. The class-level
        lock avoids stampedes when multiple requests trip the TTL together.
        """

        def _run() -> None:
            if not self._refresh_lock.acquire(blocking=False):
                return
            try:
                self.snapshot(force_refresh=True)
            finally:
                self._refresh_lock.release()

        thread = threading.Thread(target=_run, name="vn-market-snapshot", daemon=True)
        thread.start()
        return thread

    # ----- Helpers --------------------------------------------------------
    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        try:
            path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
        except Exception as exc:
            _LOG.warning("Write %s failed: %s", path, exc)

    def _is_fresh(self, payload: dict[str, Any] | None, ttl: int) -> bool:
        if not isinstance(payload, dict):
            return False
        raw = payload.get("as_of")
        if not raw:
            return False
        try:
            as_of = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            return False
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - as_of <= timedelta(seconds=ttl)


# ---- Helpers (module level) ----------------------------------------------
def _normalize_price_board(board: pd.DataFrame) -> list[dict[str, Any]]:
    """vnstock returns a MultiIndex-columns DataFrame: ('listing', col), ('match', col), ('bid_ask', col).

    We flatten to a list of dicts with the fields the frontend needs.
    """
    if board is None or not isinstance(board, pd.DataFrame) or board.empty:
        return []

    def col(group: str, name: str):
        key = (group, name)
        return board[key] if key in board.columns else pd.Series([None] * len(board), index=board.index)

    out: list[dict[str, Any]] = []
    for i in range(len(board)):
        symbol = _safe_str(col("listing", "symbol").iat[i])
        if not symbol:
            continue
        ref = _safe_num(col("listing", "ref_price").iat[i])
        ceiling = _safe_num(col("listing", "ceiling").iat[i])
        floor = _safe_num(col("listing", "floor").iat[i])
        match_price = _safe_num(col("match", "match_price").iat[i])
        # Fall back to ATC then ATO if regular match price missing
        if match_price is None or match_price == 0:
            match_price = _safe_num(col("match", "match_price_atc").iat[i]) or _safe_num(col("match", "match_price_ato").iat[i])
        # Treat match_price <= 0 as no-trade (avoid spurious -100% change_pct)
        if match_price is not None and match_price <= 0:
            match_price = None
        last_price = match_price if match_price is not None else ref
        change = (last_price - ref) if (match_price is not None and ref) else None
        change_pct = (change / ref * 100) if (change is not None and ref) else None
        market_cap = next(
            (value for value in (
                _safe_num(col("listing", "market_cap").iat[i]),
                _safe_num(col("listing", "market_capitalization").iat[i]),
                _safe_num(col("listing", "market_capitalisation").iat[i]),
            ) if value is not None),
            None,
        )
        shares_outstanding = next(
            (value for value in (
                _safe_num(col("listing", "outstanding_shares").iat[i]),
                _safe_num(col("listing", "listed_shares").iat[i]),
                _safe_num(col("listing", "listed_volume").iat[i]),
                _safe_num(col("listing", "issue_share").iat[i]),
            ) if value is not None),
            None,
        )
        out.append(
            {
                "symbol": symbol,
                "name": _safe_str(col("listing", "organ_name").iat[i]),
                "exchange": _safe_str(col("listing", "exchange").iat[i]),
                "price": _round(last_price),
                "ref_price": _round(ref),
                "ceiling": _round(ceiling),
                "floor": _round(floor),
                "change": _round(change),
                "change_pct": _round(change_pct, 3),
                "open": _round(_safe_num(col("match", "open_price").iat[i])),
                "high": _round(_safe_num(col("match", "highest").iat[i])),
                "low": _round(_safe_num(col("match", "lowest").iat[i])),
                "match_vol": _round(_safe_num(col("match", "match_vol").iat[i]), 0),
                "volume": _round(_safe_num(col("match", "accumulated_volume").iat[i]), 0),
                "value": _round(_safe_num(col("match", "accumulated_value").iat[i]), 0),
                "market_cap": _round(market_cap, 2),
                "shares_outstanding": _round(shares_outstanding, 0),
                "foreign_buy_volume": _round(_safe_num(col("match", "foreign_buy_volume").iat[i]), 0),
                "foreign_sell_volume": _round(_safe_num(col("match", "foreign_sell_volume").iat[i]), 0),
                "bid_1_price": _round(_safe_num(col("bid_ask", "bid_1_price").iat[i])),
                "bid_1_volume": _round(_safe_num(col("bid_ask", "bid_1_volume").iat[i]), 0),
                "bid_2_price": _round(_safe_num(col("bid_ask", "bid_2_price").iat[i])),
                "bid_2_volume": _round(_safe_num(col("bid_ask", "bid_2_volume").iat[i]), 0),
                "bid_3_price": _round(_safe_num(col("bid_ask", "bid_3_price").iat[i])),
                "bid_3_volume": _round(_safe_num(col("bid_ask", "bid_3_volume").iat[i]), 0),
                "ask_1_price": _round(_safe_num(col("bid_ask", "ask_1_price").iat[i])),
                "ask_1_volume": _round(_safe_num(col("bid_ask", "ask_1_volume").iat[i]), 0),
                "ask_2_price": _round(_safe_num(col("bid_ask", "ask_2_price").iat[i])),
                "ask_2_volume": _round(_safe_num(col("bid_ask", "ask_2_volume").iat[i]), 0),
                "ask_3_price": _round(_safe_num(col("bid_ask", "ask_3_price").iat[i])),
                "ask_3_volume": _round(_safe_num(col("bid_ask", "ask_3_volume").iat[i]), 0),
                "source": "vnstock",
            }
        )
    return out


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(f):
        return None
    return f


def _round(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _cached_profile_shares(cache_dir: Path) -> dict[str, float]:
    """Read cached share counts without a network request per ticker."""
    result: dict[str, float] = dict(KNOWN_SHARES_OUTSTANDING)
    profile_dirs = [
        cache_dir / "profiles",
        cache_dir.parent.parent / "src" / "data" / "vn_market" / "profiles",
    ]
    for profile_dir in profile_dirs:
        if not profile_dir.exists():
            continue
        for path in profile_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                symbol = str(payload.get("symbol") or path.stem).strip().upper()
                shares = _safe_num(payload.get("outstanding_shares"))
                if symbol and shares and shares > 0:
                    result[symbol] = shares
            except (OSError, ValueError, TypeError):
                continue
    return result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
