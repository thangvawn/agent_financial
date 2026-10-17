from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

_PROJECT_ROOT = Path(__file__).resolve().parents[5]
VN_MARKET_CACHE_DIR = _PROJECT_ROOT / "data" / "vn_market"
UNIVERSE_PATH = VN_MARKET_CACHE_DIR / "universe.json"
SNAPSHOT_PATH = VN_MARKET_CACHE_DIR / "snapshot.json"

UNIVERSE_TTL_SECONDS = 24 * 3600
SNAPSHOT_TTL_SECONDS = 15

_LOG = logging.getLogger(__name__)

_VCI_TRADING_BASE_URL = "https://trading.vietcap.com.vn/api"
_VCI_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
    "Origin": "https://trading.vietcap.com.vn",
    "Referer": "https://trading.vietcap.com.vn/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36",
}

_SSI_IBOARD_BASE_URL = "https://iboard-query.ssi.com.vn"
_SSI_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

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
    _universe_refresh_lock = threading.Lock()

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
        # Separate admission locks prevent a burst of requests from spawning
        # duplicate daemon threads before the shared refresh lock is acquired.
        self._refresh_thread_lock = threading.Lock()
        self._universe_thread_lock = threading.Lock()

    @property
    def universe_path(self) -> Path:
        """Return the cache path owned by this producer instance.

        Keeping this instance-scoped is important for tests, Docker volumes and
        deployments that route different feeds to different cache directories.
        """
        return self.cache_dir / "universe.json"

    @property
    def snapshot_path(self) -> Path:
        return self.cache_dir / "snapshot.json"

    # ----- Universe -------------------------------------------------------
    def universe(self, *, force_refresh: bool = False) -> dict[str, Any]:
        cached = self._load_json(self.universe_path)
        if not force_refresh and self._is_fresh(cached, self.universe_ttl_seconds):
            return cached

        # Serve stale data immediately and refresh it in the background.  A
        # cold start without a cache still performs one synchronous fetch so
        # the first API response can contain a complete universe.
        if cached and not force_refresh:
            self.refresh_universe_in_background()
            return self._mark_stale(cached, reason="universe_live_feed_unavailable_using_cache")

        if not self._universe_refresh_lock.acquire(blocking=False):
            return cached or {"as_of": None, "tickers": [], "source": "vnstock", "freshness": "degraded"}
        try:
            live = self._fetch_universe_live()
            if live.get("tickers"):
                live["freshness"] = "fresh"
                self._write_json(self.universe_path, live)
                return live
            return self._mark_stale(cached, reason="universe_live_feed_unavailable_using_cache") if cached else live
        finally:
            self._universe_refresh_lock.release()

    def _fetch_universe_live(self) -> dict[str, Any]:
        provider = os.getenv("VN_MARKET_PROVIDER", "ssi").strip().lower()
        if provider in {"ssi", "auto", "default"}:
            ssi_uni = self._fetch_universe_ssi()
            if ssi_uni.get("tickers"):
                return ssi_uni

        try:
            from vnstock import Listing  # type: ignore

            listing = Listing()
            frame = listing.all_symbols()
        except Exception as exc:
            _LOG.info("vnstock universe unavailable (%s); trying fallbacks", exc)
            vci_uni = self._fetch_universe_vci()
            if vci_uni.get("tickers"):
                return vci_uni
            return self._fetch_universe_ssi()

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

    def _fetch_universe_vci(self) -> dict[str, Any]:
        """Fetch the public VCI listing endpoint without the optional vnstock package."""
        try:
            response = requests.get(
                f"{_VCI_TRADING_BASE_URL}/price/symbols/getAll",
                headers=_VCI_HEADERS,
                timeout=20,
            )
            response.raise_for_status()
            rows = response.json()
        except (OSError, ValueError, requests.RequestException) as exc:
            _LOG.warning("VCI universe fallback failed: %s", exc)
            return {"as_of": _utc_now_iso(), "tickers": [], "source": "vci_http"}

        tickers = []
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            symbol = str(row.get("symbol") or "").strip().upper()
            if not symbol or not symbol.isalpha() or not (3 <= len(symbol) <= 5):
                continue
            if str(row.get("type") or "").upper() not in {"", "STOCK"}:
                continue
            tickers.append(
                {
                    "symbol": symbol,
                    "name": str(row.get("organName") or row.get("organShortName") or symbol).strip(),
                    "exchange": str(row.get("board") or "").strip().upper(),
                }
            )
        return {"as_of": _utc_now_iso(), "tickers": tickers, "source": "vci_http"}

    def _fetch_universe_ssi(self) -> dict[str, Any]:
        """Fetch universe listing from SSI iBoard API."""
        items = _fetch_ssi_price_board()
        if not items:
            return {"as_of": _utc_now_iso(), "tickers": [], "source": "ssi"}
        tickers = [
            {
                "symbol": item["symbol"],
                "name": item.get("name") or item["symbol"],
                "exchange": item.get("exchange") or "",
            }
            for item in items
            if item.get("symbol")
        ]
        return {"as_of": _utc_now_iso(), "tickers": tickers, "source": "ssi"}

    # ----- Snapshot -------------------------------------------------------
    def snapshot(self, *, force_refresh: bool = False) -> dict[str, Any]:
        cached = self._load_json(self.snapshot_path)
        ttl = self._effective_snapshot_ttl()
        if not force_refresh and self._is_fresh(cached, ttl):
            self._enrich_market_cap(cached)
            return cached

        # Do not make a user request wait on vnstock after the TTL expires.
        # The scheduler and this background refresh keep the cache warm while
        # the API continues serving the last known good snapshot.
        if cached and not force_refresh:
            self.refresh_in_background()
            self._enrich_market_cap(cached)
            return self._mark_stale(cached)

        if not self._refresh_lock.acquire(blocking=False):
            self._enrich_market_cap(cached)
            return self._mark_stale(cached) if cached else {
                "as_of": None,
                "items": [],
                "source": "vnstock",
                "freshness": "degraded",
                "stale_reason": "live_feed_refresh_in_progress",
            }
        try:
            live = self._fetch_snapshot_live()
            if live["items"]:
                self._write_json(self.snapshot_path, live)
                return live
            if cached:
                self._enrich_market_cap(cached)
                return self._mark_stale(cached)
            return live
        finally:
            self._refresh_lock.release()

    def _effective_snapshot_ttl(self) -> int:
        """Use the fast TTL during the session and the scheduler cadence off-hours.

        A fixed 15-second TTL outside trading hours would mark an unchanged
        previous-close snapshot stale on every browser poll and create a
        provider stampede. Custom TTLs remain deterministic for tests and
        specialised consumers.
        """
        if self.snapshot_ttl_seconds != SNAPSHOT_TTL_SECONDS or _is_vn_market_hours():
            return self.snapshot_ttl_seconds
        return max(
            self.snapshot_ttl_seconds,
            int(os.getenv("VN_MARKET_INTERVAL_SLOW_SEC", "300")),
        )

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

        preferred_provider = os.getenv("VN_MARKET_PROVIDER", "ssi").strip().lower()

        # 1. Primary SSI fast realtime feed (~0.6s for all exchanges, no guest rate limits)
        if preferred_provider in {"ssi", "auto", "default"}:
            items = _fetch_ssi_price_board()
            if items:
                return self._finish_live_items(items, universe)
            _LOG.info("SSI price board unavailable; falling back to vnstock/VCI")

        symbols = [t["symbol"] for t in universe]
        # Use the shared rate limiter + SystemExit shield from global_market_feed
        from risk_dashboard.modules.data_hub.application.global_market_feed import (
            _VNSTOCK_RATE_LIMITER,
            _vnstock_safe,
            _VnstockRateExceeded,
        )
        try:
            _VNSTOCK_RATE_LIMITER.acquire()
            with _vnstock_safe():
                from vnstock import Trading  # type: ignore

                board = Trading(source="VCI").price_board(symbols)
            items = _normalize_price_board(board)
            if items:
                return self._finish_live_items(items, universe)
        except _VnstockRateExceeded:
            _LOG.warning("VN price_board rate-limited (vnstock guest tier); attempting fallbacks")
        except ModuleNotFoundError as exc:
            _LOG.info("vnstock price_board unavailable (%s); attempting fallbacks", exc)
        except Exception as exc:
            _LOG.warning("VN price_board failed (%s); attempting fallbacks", exc)

        # 2. Secondary fallback: SSI if preferred_provider was vnstock
        if preferred_provider not in {"ssi", "auto", "default"}:
            items = _fetch_ssi_price_board()
            if items:
                return self._finish_live_items(items, universe)

        # 3. Tertiary fallback: VCI direct HTTP
        items = _fetch_vci_price_board(symbols)
        if items:
            return self._finish_live_items(items, universe)

        return {"as_of": _utc_now_iso(), "items": [], "source": "all_failed", "freshness": "degraded"}

    def _finish_live_items(self, items: list[dict[str, Any]], universe: list[dict[str, Any]]) -> dict[str, Any]:
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
            "source": items[0].get("source", "vnstock") if items else "vnstock",
            "freshness": "fresh",
            "count": len(items),
            "items": items,
        }

    def refresh_in_background(self) -> threading.Thread | None:
        """Trigger a one-shot snapshot refresh in a background thread.

        Returns the thread so callers can join() or ignore. The class-level
        lock avoids stampedes when multiple requests trip the TTL together.
        """

        if not self._refresh_thread_lock.acquire(blocking=False):
            return None

        def _run() -> None:
            try:
                self.snapshot(force_refresh=True)
            finally:
                self._refresh_thread_lock.release()

        thread = threading.Thread(target=_run, name="vn-market-snapshot", daemon=True)
        thread.start()
        return thread

    def refresh_universe_in_background(self) -> threading.Thread | None:
        """Refresh the listing without blocking a request serving stale data."""
        if not self._universe_thread_lock.acquire(blocking=False):
            return None

        def _run() -> None:
            try:
                self.universe(force_refresh=True)
            finally:
                self._universe_thread_lock.release()

        thread = threading.Thread(target=_run, name="vn-market-universe", daemon=True)
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
        tmp_path: Path | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}.{threading.get_ident()}")
            tmp_path.write_text(
                json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8"
            )
            os.replace(tmp_path, path)
        except Exception as exc:
            _LOG.warning("Write %s failed: %s", path, exc)
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    @staticmethod
    def _mark_stale(payload: dict[str, Any], *, reason: str = "live_feed_unavailable_using_cache") -> dict[str, Any]:
        stale = dict(payload)
        stale["freshness"] = "stale"
        stale["stale_reason"] = reason
        stale.setdefault("last_success_at", stale.get("as_of"))
        return stale

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


def _fetch_vci_price_board(symbols: list[str]) -> list[dict[str, Any]]:
    """Normalize VCI's public JSON quote board to the internal item contract."""
    try:
        response = requests.post(
            f"{_VCI_TRADING_BASE_URL}/price/symbols/getList",
            headers=_VCI_HEADERS,
            json={"symbols": symbols},
            timeout=25,
        )
        response.raise_for_status()
        rows = response.json()
    except (OSError, ValueError, requests.RequestException) as exc:
        _LOG.warning("VCI price board fallback failed: %s", exc)
        return []

    items: list[dict[str, Any]] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        listing = row.get("listingInfo") or {}
        match = row.get("matchPrice") or {}
        depth = row.get("bidAsk") or {}
        symbol = _safe_str(listing.get("symbol") or match.get("symbol"))
        if not symbol:
            continue
        ref = _safe_num(listing.get("refPrice") or match.get("referencePrice"))
        price = next(
            (
                _safe_num(match.get(key))
                for key in ("matchPrice", "matchPriceATC", "matchPriceATO")
                if _safe_num(match.get(key)) not in (None, 0)
            ),
            ref,
        )
        change = (price - ref) if price is not None and ref else None
        change_pct = (change / ref * 100) if change is not None and ref else None
        bids = depth.get("bidPrices") or []
        asks = depth.get("askPrices") or []
        item: dict[str, Any] = {
            "symbol": symbol,
            "name": _safe_str(listing.get("organName") or listing.get("organShortName")),
            "exchange": _safe_str(listing.get("board")),
            "price": _round(price),
            "ref_price": _round(ref),
            "ceiling": _round(_safe_num(listing.get("ceiling"))),
            "floor": _round(_safe_num(listing.get("floor"))),
            "change": _round(change),
            "change_pct": _round(change_pct, 3),
            "open": _round(_safe_num(match.get("openPrice"))),
            "high": _round(_safe_num(match.get("highest"))),
            "low": _round(_safe_num(match.get("lowest"))),
            "match_vol": _round(_safe_num(match.get("matchVol")), 0),
            "volume": _round(_safe_num(match.get("accumulatedVolume")), 0),
            "value": _round(_safe_num(match.get("accumulatedValue")), 0),
            "shares_outstanding": _round(_safe_num(listing.get("listedShare")), 0),
            "foreign_buy_volume": _round(_safe_num(match.get("foreignBuyVolume")), 0),
            "foreign_sell_volume": _round(_safe_num(match.get("foreignSellVolume")), 0),
            "source": "vci_http",
        }
        for side, levels in (("bid", bids), ("ask", asks)):
            for index in range(3):
                level = levels[index] if index < len(levels) and isinstance(levels[index], dict) else {}
                item[f"{side}_{index + 1}_price"] = _round(_safe_num(level.get("price")))
                item[f"{side}_{index + 1}_volume"] = _round(_safe_num(level.get("volume")), 0)
        shares = item.get("shares_outstanding")
        if price is not None and shares:
            item["market_cap"] = _round(price * shares / 1_000_000_000, 2)
        items.append(item)
    return items


def _fetch_ssi_price_board(
    exchanges: tuple[str, ...] = ("hose", "hnx", "upcom"),
) -> list[dict[str, Any]]:
    """Fetch live quote board from SSI iBoard API across specified exchanges.

    Performs concurrent HTTP GET requests per exchange, mapping SSI fields directly
    to the internal item contract. Typically completes in ~0.5-0.7s for 1500+ stocks.
    """
    from concurrent.futures import ThreadPoolExecutor

    def _fetch_ex(ex: str) -> list[dict[str, Any]]:
        try:
            resp = requests.get(
                f"{_SSI_IBOARD_BASE_URL}/stock/exchange/{ex}",
                headers=_SSI_HEADERS,
                timeout=12,
            )
            resp.raise_for_status()
            payload = resp.json()
            return payload.get("data", []) or []
        except (OSError, ValueError, requests.RequestException) as exc:
            _LOG.warning("SSI price board fetch failed for exchange %s: %s", ex, exc)
            return []

    all_rows: list[dict[str, Any]] = []
    try:
        with ThreadPoolExecutor(max_workers=len(exchanges)) as executor:
            futures = [executor.submit(_fetch_ex, ex) for ex in exchanges]
            for fut in futures:
                all_rows.extend(fut.result())
    except Exception as exc:
        _LOG.warning("SSI price board concurrent fetch failed: %s", exc)
        return []

    items: list[dict[str, Any]] = []
    seen_symbols: set[str] = set()

    for row in all_rows:
        if not isinstance(row, dict):
            continue
        symbol = _safe_str(row.get("stockSymbol")).upper()
        if not symbol or symbol in seen_symbols:
            continue
        seen_symbols.add(symbol)

        ref = _safe_num(row.get("refPrice"))
        price = _safe_num(row.get("matchedPrice"))
        if price in (None, 0):
            price = ref

        change = _safe_num(row.get("priceChange"))
        if change is None and price is not None and ref is not None:
            change = price - ref

        change_pct = _safe_num(row.get("priceChangePercent"))
        if change_pct is None and change is not None and ref:
            change_pct = (change / ref) * 100

        item: dict[str, Any] = {
            "symbol": symbol,
            "name": _safe_str(row.get("companyNameVi") or row.get("companyNameEn") or symbol),
            "exchange": _safe_str(row.get("exchange")).upper(),
            "price": _round(price),
            "ref_price": _round(ref),
            "ceiling": _round(_safe_num(row.get("ceiling"))),
            "floor": _round(_safe_num(row.get("floor"))),
            "change": _round(change),
            "change_pct": _round(change_pct, 3),
            "open": _round(_safe_num(row.get("openPrice"))),
            "high": _round(_safe_num(row.get("highest"))),
            "low": _round(_safe_num(row.get("lowest"))),
            "match_vol": _round(_safe_num(row.get("matchedVolume")), 0),
            "volume": _round(_safe_num(row.get("nmTotalTradedQty")), 0),
            "value": _round(_safe_num(row.get("nmTotalTradedValue")), 0),
            "foreign_buy_volume": _round(_safe_num(row.get("buyForeignQtty")), 0),
            "foreign_sell_volume": _round(_safe_num(row.get("sellForeignQtty")), 0),
            "bid_1_price": _round(_safe_num(row.get("best1Bid"))),
            "bid_1_volume": _round(_safe_num(row.get("best1BidVol")), 0),
            "bid_2_price": _round(_safe_num(row.get("best2Bid"))),
            "bid_2_volume": _round(_safe_num(row.get("best2BidVol")), 0),
            "bid_3_price": _round(_safe_num(row.get("best3Bid"))),
            "bid_3_volume": _round(_safe_num(row.get("best3BidVol")), 0),
            "ask_1_price": _round(_safe_num(row.get("best1Offer"))),
            "ask_1_volume": _round(_safe_num(row.get("best1OfferVol")), 0),
            "ask_2_price": _round(_safe_num(row.get("best2Offer"))),
            "ask_2_volume": _round(_safe_num(row.get("best2OfferVol")), 0),
            "ask_3_price": _round(_safe_num(row.get("best3Offer"))),
            "ask_3_volume": _round(_safe_num(row.get("best3OfferVol")), 0),
            "source": "ssi",
        }
        items.append(item)

    return items


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


def _is_vn_market_hours() -> bool:
    """Match the scheduler's weekday warm-up/trading window (ICT)."""
    ict = datetime.now(timezone.utc) + timedelta(hours=7)
    if ict.weekday() >= 5:
        return False
    opening = ict.replace(hour=8, minute=50, second=0, microsecond=0)
    closing = ict.replace(hour=15, minute=10, second=0, microsecond=0)
    return opening <= ict <= closing
