from __future__ import annotations

import contextlib
import json
import logging
import os
import tempfile
import threading
import time
from concurrent.futures import Future
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from risk_dashboard.data.yahoo_client import download_yahoo
from risk_dashboard.modules.data_hub.application.quote_quality import (
    finite_number,
    quote_health,
    quote_summary,
    timestamp,
)

logger = logging.getLogger(__name__)



_PROJECT_ROOT = Path(__file__).resolve().parents[5]
GLOBAL_MARKET_CACHE_DIR = _PROJECT_ROOT / "data" / "global_market_prices"
_SUPPORTED_HISTORY_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo", "1y"}
_DEFAULT_SNAPSHOT_CACHE_AGE_SECONDS = 75
_SNAPSHOT_INTRADAY_INTERVAL = "5m"
_REFRESH_LOCK = threading.Lock()
_REFRESH_IN_FLIGHT = False


@dataclass(frozen=True)
class FeedInstrument:
    symbol: str
    name: str
    yahoo_symbol: str
    group: str
    focus: str
    data_source: str = "yahoo"  # "yahoo" or "vnstock"
    vn_symbol: str = ""  # only used when data_source == "vnstock"
    category: str = ""
    unit: str = ""


GLOBAL_MARKET_INSTRUMENTS: tuple[FeedInstrument, ...] = (
    FeedInstrument("VNINDEX", "VN-Index", "", "indices", "Vietnam broad market", data_source="vnstock", vn_symbol="VNINDEX"),
    FeedInstrument("VN30", "VN30", "", "indices", "Vietnam large-cap", data_source="vnstock", vn_symbol="VN30"),
    FeedInstrument("HNXINDEX", "HNX-Index", "", "indices", "Vietnam HNX board", data_source="vnstock", vn_symbol="HNXIndex"),
    FeedInstrument("UPCOMINDEX", "UPCoM-Index", "", "indices", "Vietnam UPCOM board", data_source="vnstock", vn_symbol="UPCOMIndex"),
    FeedInstrument("SPX", "S&P 500", "^GSPC", "indices", "US large-cap breadth"),
    FeedInstrument("NDX", "Nasdaq 100", "^NDX", "indices", "US growth / tech beta"),
    FeedInstrument("RUT", "Russell 2000", "^RUT", "indices", "US small-cap risk appetite"),
    FeedInstrument("DJI", "Dow Jones Industrial Average", "^DJI", "indices", "US blue-chip breadth"),
    FeedInstrument("NASDAQ", "Nasdaq Composite", "^IXIC", "indices", "US technology breadth"),
    FeedInstrument("DAX", "DAX", "^GDAXI", "indices", "Europe growth pulse"),
    FeedInstrument("EUROSTOXX", "Euro Stoxx 50", "^STOXX50E", "indices", "Eurozone large-cap breadth"),
    FeedInstrument("CAC40", "CAC 40", "^FCHI", "indices", "France equity pulse"),
    FeedInstrument("FTSE", "FTSE 100", "^FTSE", "indices", "UK defensive mix"),
    FeedInstrument("NIKKEI", "Nikkei 225", "^N225", "indices", "Japan equity pulse"),
    FeedInstrument("HANGSENG", "Hang Seng", "^HSI", "indices", "China/HK sentiment"),
    FeedInstrument("KOSPI", "KOSPI", "^KS11", "indices", "South Korea technology cycle"),
    FeedInstrument("ASX200", "ASX 200", "^AXJO", "indices", "Australia equity pulse"),
    FeedInstrument("TSX", "S&P/TSX Composite", "^GSPTSE", "indices", "Canada equity pulse"),
    FeedInstrument("BOVESPA", "Bovespa", "^BVSP", "indices", "Brazil risk appetite"),
    FeedInstrument("NIFTY50", "NIFTY 50", "^NSEI", "indices", "India growth pulse"),
    FeedInstrument("SSEC", "Shanghai Composite", "000001.SS", "indices", "Mainland China breadth"),
    FeedInstrument("DXY", "Dollar Index", "DX-Y.NYB", "fx", "USD pressure"),
    FeedInstrument("EURUSD", "EUR/USD", "EURUSD=X", "fx", "Europe vs USD"),
    FeedInstrument("USDJPY", "USD/JPY", "JPY=X", "fx", "JPY carry stress"),
    FeedInstrument("AUDUSD", "AUD/USD", "AUDUSD=X", "fx", "Commodity FX"),
    FeedInstrument("USDCNH", "USD/CNH", "CNH=X", "fx", "China currency pressure"),
    FeedInstrument("GBPUSD", "GBP/USD", "GBPUSD=X", "fx", "UK vs USD"),
    FeedInstrument("USDCHF", "USD/CHF", "CHF=X", "fx", "Swiss franc haven"),
    FeedInstrument("USDCAD", "USD/CAD", "CAD=X", "fx", "Oil-linked currency"),
    FeedInstrument("NZDUSD", "NZD/USD", "NZDUSD=X", "fx", "New Zealand risk proxy"),
    FeedInstrument("USDHKD", "USD/HKD", "HKD=X", "fx", "Hong Kong currency regime"),
    FeedInstrument("USDMXN", "USD/MXN", "MXN=X", "fx", "Mexico carry proxy"),
    FeedInstrument("USDTRY", "USD/TRY", "TRY=X", "fx", "Turkey inflation stress"),
    FeedInstrument("USDINR", "USD/INR", "INR=X", "fx", "India currency pressure"),
    FeedInstrument("EURGBP", "EUR/GBP", "EURGBP=X", "fx", "Euro vs sterling"),
    FeedInstrument("EURJPY", "EUR/JPY", "EURJPY=X", "fx", "Euro carry cross"),
    FeedInstrument("XAU", "Gold", "GC=F", "commodities", "Safe-haven / inflation hedge", category="metals", unit="USD/oz"),
    FeedInstrument("SILVER", "Silver", "SI=F", "commodities", "Safe-haven and cyclicality", category="metals", unit="USD/oz"),
    FeedInstrument("COPPER", "Copper", "HG=F", "commodities", "Industrial cycle proxy", category="metals", unit="USD/lb"),
    FeedInstrument("PLATINUM", "Platinum", "PL=F", "commodities", "Auto and industrial demand", category="metals", unit="USD/oz"),
    FeedInstrument("PALLADIUM", "Palladium", "PA=F", "commodities", "Auto catalyst demand", category="metals", unit="USD/oz"),
    FeedInstrument("WTI", "Crude Oil WTI", "CL=F", "commodities", "Growth and energy pressure", category="energy", unit="USD/bbl"),
    FeedInstrument("BRENT", "Brent Crude", "BZ=F", "commodities", "Global oil benchmark", category="energy", unit="USD/bbl"),
    FeedInstrument("NATGAS", "Natural Gas", "NG=F", "commodities", "Power and heating demand", category="energy", unit="USD/MMBtu"),
    FeedInstrument("HEATINGOIL", "Heating Oil", "HO=F", "commodities", "Refining and winter demand", category="energy", unit="USD/gal"),
    FeedInstrument("GASOLINE", "RBOB Gasoline", "RB=F", "commodities", "US transport fuel demand", category="energy", unit="USD/gal"),
    FeedInstrument("CORN", "Corn", "ZC=F", "commodities", "Grain supply cycle", category="grains", unit="US cents/bu"),
    FeedInstrument("WHEAT", "Wheat", "ZW=F", "commodities", "Food inflation pressure", category="grains", unit="US cents/bu"),
    FeedInstrument("SOYBEAN", "Soybean", "ZS=F", "commodities", "Feed and oilseed cycle", category="grains", unit="US cents/bu"),
    FeedInstrument("OATS", "Oats", "ZO=F", "commodities", "Grain diversification", category="grains", unit="US cents/bu"),
    FeedInstrument("RICE", "Rough Rice", "ZR=F", "commodities", "Food supply cycle", category="grains", unit="USD/cwt"),
    FeedInstrument("LIVE_CATTLE", "Live Cattle", "LE=F", "commodities", "Meat and livestock cycle", category="livestock", unit="US cents/lb"),
    FeedInstrument("FEEDER_CATTLE", "Feeder Cattle", "GF=F", "commodities", "Livestock feed demand", category="livestock", unit="US cents/lb"),
    FeedInstrument("LEAN_HOGS", "Lean Hogs", "HE=F", "commodities", "Meat supply cycle", category="livestock", unit="US cents/lb"),
    FeedInstrument("SUGAR", "Sugar", "SB=F", "commodities", "Soft commodities", category="raw_materials", unit="US cents/lb"),
    FeedInstrument("COFFEE", "Coffee", "KC=F", "commodities", "Soft commodities", category="raw_materials", unit="US cents/lb"),
    FeedInstrument("COCOA", "Cocoa", "CC=F", "commodities", "Soft commodities", category="raw_materials", unit="USD/ton"),
    FeedInstrument("COTTON", "Cotton", "CT=F", "commodities", "Soft commodities", category="raw_materials", unit="US cents/lb"),
    FeedInstrument("ORANGE_JUICE", "Frozen Orange Juice", "OJ=F", "commodities", "Agricultural softs", category="raw_materials", unit="US cents/lb"),
    FeedInstrument("BTC", "Bitcoin", "BTC-USD", "crypto", "Global risk appetite"),
    FeedInstrument("ETH", "Ethereum", "ETH-USD", "crypto", "Crypto breadth"),
    FeedInstrument("USDT", "Tether", "USDT-USD", "crypto", "Dollar stablecoin liquidity"),
    FeedInstrument("BNB", "BNB", "BNB-USD", "crypto", "Exchange utility token"),
    FeedInstrument("XRP", "XRP", "XRP-USD", "crypto", "Cross-border payment"),
    FeedInstrument("USDC", "USD Coin", "USDC-USD", "crypto", "Dollar stablecoin liquidity"),
    FeedInstrument("SOL", "Solana", "SOL-USD", "crypto", "L1 network speed"),
    FeedInstrument("TRX", "TRON", "TRX-USD", "crypto", "High-throughput settlement"),
    FeedInstrument("DOGE", "Dogecoin", "DOGE-USD", "crypto", "Meme speculation pulse"),
    FeedInstrument("LINK", "Chainlink", "LINK-USD", "crypto", "Oracle infrastructure"),
    FeedInstrument("ADA", "Cardano", "ADA-USD", "crypto", "Proof-of-stake L1"),
    FeedInstrument("XLM", "Stellar", "XLM-USD", "crypto", "Cross-border settlement"),
    FeedInstrument("NEAR", "NEAR Protocol", "NEAR-USD", "crypto", "L1 developer activity"),
    FeedInstrument("BCH", "Bitcoin Cash", "BCH-USD", "crypto", "Bitcoin fork liquidity"),
    FeedInstrument("UNI", "Uniswap", "UNI7083-USD", "crypto", "DeFi activity"),
    FeedInstrument("HBAR", "Hedera", "HBAR-USD", "crypto", "Enterprise DLT adoption"),
    FeedInstrument("LTC", "Litecoin", "LTC-USD", "crypto", "Payments network"),
    FeedInstrument("AVAX", "Avalanche", "AVAX-USD", "crypto", "L1 subnet ecosystem"),
    FeedInstrument("SUI", "Sui", "SUI20947-USD", "crypto", "L1 growth beta"),
    FeedInstrument("TON", "Toncoin", "TON-USD", "crypto", "Messaging ecosystem"),
    FeedInstrument("CRO", "Cronos", "CRO-USD", "crypto", "Exchange ecosystem"),
    FeedInstrument("SHIB", "Shiba Inu", "SHIB-USD", "crypto", "Meme token breadth"),
    FeedInstrument("DOT", "Polkadot", "DOT-USD", "crypto", "Interoperability network"),
    FeedInstrument("PEPE", "Pepe", "PEPE24478-USD", "crypto", "Meme speculation pulse"),
    FeedInstrument("ICP", "Internet Computer", "ICP-USD", "crypto", "Decentralized compute"),
    FeedInstrument("ARB", "Arbitrum", "ARB-USD", "crypto", "Ethereum L2 activity"),
    FeedInstrument("FIL", "Filecoin", "FIL-USD", "crypto", "Decentralized storage"),
    FeedInstrument("APT", "Aptos", "APT21794-USD", "crypto", "L1 developer activity"),
    FeedInstrument("OP", "Optimism", "OP-USD", "crypto", "Ethereum L2 activity"),
    FeedInstrument("MKR", "Maker", "MKR-USD", "crypto", "DeFi credit protocol"),
    FeedInstrument("INJ", "Injective", "INJ-USD", "crypto", "On-chain markets"),
)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> bool:
    tmp_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name + ".tmp.", delete=False) as handle:
            tmp_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False)
        os.replace(tmp_path, path)
        return True
    except (PermissionError, OSError) as exc:
        logger.warning("Failed to write JSON cache to %s: %s", path, exc)
        return False
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


_MEM_HISTORY_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_HISTORY_GUARD = threading.Lock()
_HISTORY_IN_FLIGHT: dict[str, Future] = {}
_HISTORY_FORCED_AT: dict[str, float] = {}
_FORCE_REFRESH_MIN_SECONDS = 5


def _history_cache_ttl_seconds(interval: str) -> int:
    norm = (interval or "1d").lower()
    if norm == "1m":
        return 20
    if norm in {"5m", "15m", "30m"}:
        return 45
    if norm in {"1h", "4h"}:
        return 120
    return 600  # daily, weekly, monthly: 10 minutes cache


class GlobalMarketFeedProducer:
    def __init__(
        self,
        *,
        cache_dir: Path = GLOBAL_MARKET_CACHE_DIR,
        max_cache_age_seconds: int | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        configured_age = max_cache_age_seconds
        if configured_age is None:
            try:
                configured_age = int(os.getenv("GLOBAL_MARKET_CACHE_TTL_SEC", str(_DEFAULT_SNAPSHOT_CACHE_AGE_SECONDS)))
            except (TypeError, ValueError):
                configured_age = _DEFAULT_SNAPSHOT_CACHE_AGE_SECONDS
            # Never let an invalid/negative environment value make every
            # request hit the provider. The scheduler owns the refresh
            # cadence; this is only the maximum age accepted by a request.
            configured_age = max(configured_age, 30)
        else:
            # Preserve the explicit constructor contract: tests and callers
            # can pass 0 to require a provider check on every read.
            configured_age = max(int(configured_age), 0)
        self.max_cache_age_seconds = configured_age

    def snapshot(self, *, force_refresh: bool = False, read_only: bool = False) -> dict[str, Any]:
        cached = self._load_cache()
        if not read_only and (force_refresh or not self._is_cache_fresh(cached)):
            live = self._fetch_yahoo_snapshot()
            if not live.get("items"):
                live = {"items": []}  # keep the last successful fetch timestamp
            cached = _merge_snapshot(cached, live)
            self._write_cache(cached)

        items = cached.get("items", []) if isinstance(cached, dict) else []
        by_group = {"indices": [], "fx": [], "commodities": [], "crypto": []}
        for item in items:
            group = item.get("group")
            if group in by_group:
                by_group[group].append(quote_health(item, fallback_fetched_at=cached.get("as_of"),
                                                   max_fetch_age=self.max_cache_age_seconds))

        group_meta = {
            group: quote_summary(
                rows, expected=sum(i.group == group for i in GLOBAL_MARKET_INSTRUMENTS)
            )
            for group, rows in by_group.items()
        }

        return {
            "as_of": cached.get("as_of") if isinstance(cached, dict) else None,
            "source": cached.get("source", "yahoo_finance") if isinstance(cached, dict) else "yahoo_finance",
            "data_interval": cached.get("data_interval", "1d") if isinstance(cached, dict) else "1d",
            "freshness": "fresh" if self._is_cache_fresh(cached) else "stale" if items else "degraded",
            "stale_reason": None if self._is_cache_fresh(cached) else "live_feed_unavailable_using_cache" if items else "live_feed_unavailable_no_cache",
            "groups": by_group,
            "group_meta": group_meta,
        }

    def refresh_in_background(self) -> bool:
        """Start one provider refresh without blocking an HTTP request.

        The scheduler and the browser can both request a refresh at the same
        time. A process-wide guard collapses those requests into one provider
        call, which protects Yahoo/CoinGecko rate limits.
        """
        global _REFRESH_IN_FLIGHT
        with _REFRESH_LOCK:
            if _REFRESH_IN_FLIGHT:
                return False
            _REFRESH_IN_FLIGHT = True

        def worker() -> None:
            global _REFRESH_IN_FLIGHT
            try:
                self.snapshot(force_refresh=True)
            except Exception:
                logger.exception("Global market background refresh failed")
            finally:
                with _REFRESH_LOCK:
                    _REFRESH_IN_FLIGHT = False

        threading.Thread(target=worker, name="global-market-refresh", daemon=True).start()
        return True

    def refresh_crypto_in_background(self) -> bool:
        """Refresh only the CoinGecko group without waiting on Yahoo data.

        Crypto quotes are available 24/7 and have a different provider
        cadence from indices, FX and commodities. Keeping this path separate
        prevents a slow Yahoo download from making the crypto tab look frozen.
        The same process-wide guard serializes it with a full snapshot write.
        """
        global _REFRESH_IN_FLIGHT
        with _REFRESH_LOCK:
            if _REFRESH_IN_FLIGHT:
                return False
            _REFRESH_IN_FLIGHT = True

        def worker() -> None:
            global _REFRESH_IN_FLIGHT
            try:
                crypto_items = self._fetch_crypto_snapshot_items()
                if not crypto_items:
                    return
                cached = self._load_cache()
                merged = _merge_snapshot(cached, {"as_of": _utc_now_iso(), "items": crypto_items},
                                         refreshed_groups={"crypto"})
                # A crypto refresh does not renew the age of the full snapshot.
                merged["as_of"] = cached.get("as_of")
                self._write_cache(merged)
            except Exception:
                logger.exception("Crypto background refresh failed")
            finally:
                with _REFRESH_LOCK:
                    _REFRESH_IN_FLIGHT = False

        threading.Thread(target=worker, name="crypto-market-refresh", daemon=True).start()
        return True

    def history(self, *, symbol: str, period: str = "6mo", interval: str = "1d",
                force_refresh: bool = False) -> dict[str, Any]:
        instrument = find_instrument(symbol)
        if instrument is None:
            return {
                "symbol": symbol.upper(),
                "name": symbol.upper(),
                "points": [],
                "freshness": "degraded",
                "stale_reason": "unknown_symbol",
                "source": "yahoo_finance",
                "as_of": _utc_now_iso(),
            }

        interval = interval if interval in _SUPPORTED_HISTORY_INTERVALS else "1d"
        period = _normalize_history_period(period, interval)
        ttl = _history_cache_ttl_seconds(interval)
        cached = self._load_history_cache(instrument.symbol, period, interval)
        fresh = self._is_history_fresh(cached, ttl)
        if fresh and not force_refresh:
            return self._history_response(instrument, period, interval, cached, True, "cached")

        key = self._history_key(instrument.symbol, period, interval)
        with _HISTORY_GUARD:
            pending = _HISTORY_IN_FLIGHT.get(key)
            if pending is None:
                elapsed = time.monotonic() - _HISTORY_FORCED_AT.get(key, -float("inf"))
                if force_refresh and elapsed < _FORCE_REFRESH_MIN_SECONDS:
                    return self._history_response(
                        instrument, period, interval, cached, fresh, "throttled"
                    )
                pending = Future()
                _HISTORY_IN_FLIGHT[key] = pending
                owner = True
                if force_refresh:
                    _HISTORY_FORCED_AT[key] = time.monotonic()
                    if len(_HISTORY_FORCED_AT) > 4096:
                        _HISTORY_FORCED_AT.pop(next(iter(_HISTORY_FORCED_AT)))
            else:
                owner = False
        if not owner:
            return pending.result()
        try:
            # Recheck after owning the work: another caller may just have completed.
            cached = self._load_history_cache(instrument.symbol, period, interval)
            fresh = self._is_history_fresh(cached, ttl)
            if fresh and not force_refresh:
                result = self._history_response(
                    instrument, period, interval, cached, True, "cached"
                )
            else:
                try:
                    fetch = (
                        self._fetch_vnstock_history
                        if instrument.data_source == "vnstock"
                        else self._fetch_yahoo_history
                    )
                    live = fetch(instrument=instrument, period=period, interval=interval)
                except Exception:
                    logger.exception("History provider failed for %s", instrument.symbol)
                    live = {}
                success = bool(live.get("points"))
                if success:
                    self._write_history_cache(instrument.symbol, period, interval, live)
                    cached = live
                result = self._history_response(instrument, period, interval, cached, success,
                                                "updated" if success else "failed")
            pending.set_result(result)
            return result
        except BaseException as exc:
            pending.set_exception(exc)
            raise
        finally:
            with _HISTORY_GUARD:
                _HISTORY_IN_FLIGHT.pop(key, None)

    def _history_response(self, instrument, period, interval, cached, fresh, refresh_status):

        points = cached.get("points", []) if isinstance(cached, dict) else []
        return {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "yahoo_symbol": instrument.yahoo_symbol,
            "group": instrument.group,
            "focus": instrument.focus,
            "period": period,
            "interval": interval,
            "points": points,
            "source": instrument.data_source if instrument.data_source != "yahoo" else "yahoo_finance",
            "as_of": cached.get("as_of") if isinstance(cached, dict) else _utc_now_iso(),
            "freshness": "fresh" if fresh else "stale" if points else "degraded",
            "stale_reason": None if fresh else "history_live_feed_unavailable_using_cache" if points else "history_live_feed_unavailable_no_cache",
            "refresh_status": refresh_status,
            "retry_after_seconds": (
                _FORCE_REFRESH_MIN_SECONDS if refresh_status == "throttled" else 0
            ),
        }

    def _fetch_yahoo_snapshot(self) -> dict[str, Any]:
        yahoo_instruments = [i for i in GLOBAL_MARKET_INSTRUMENTS if i.data_source == "yahoo"]
        tickers = [instrument.yahoo_symbol for instrument in yahoo_instruments]
        daily_frame = pd.DataFrame()
        intraday_frame = pd.DataFrame()
        try:
            # Daily bars provide a stable previous close for the percentage
            # change. Intraday bars provide the latest tradable quote and
            # session high/low while the market is open. Yahoo may reject an
            # intraday request for a symbol or during an outage, so it is
            # deliberately independent from the daily fallback.
            daily_frame = download_yahoo(
                tickers=tickers,
                period="5d",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception:
            daily_frame = pd.DataFrame()
        try:
            intraday_frame = download_yahoo(
                tickers=tickers,
                period="1d",
                interval=_SNAPSHOT_INTRADAY_INTERVAL,
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception:
            intraday_frame = pd.DataFrame()

        items: list[dict[str, Any]] = []
        has_intraday = False
        for instrument in yahoo_instruments:
            daily_closes = _extract_close_series(daily_frame, instrument.yahoo_symbol) if not daily_frame.empty else pd.Series(dtype=float)
            intraday_closes = _extract_close_series(intraday_frame, instrument.yahoo_symbol) if not intraday_frame.empty else pd.Series(dtype=float)
            quote_series = intraday_closes if not intraday_closes.empty else daily_closes
            if quote_series.empty:
                continue
            has_intraday = has_intraday or not intraday_closes.empty
            exchange_timezone = _exchange_timezone(instrument)
            previous = _previous_close(daily_closes, quote_series, exchange_timezone)
            current = quote_series.iloc[-1]
            if finite_number(current) is None:
                continue
            change = float(current) - previous if previous is not None else None
            change_pct = change / abs(previous) * 100 if previous else None
            quote_frame = intraday_frame if not intraday_closes.empty else daily_frame
            highs = _extract_field_series(quote_frame, instrument.yahoo_symbol, "High") if not quote_frame.empty else pd.Series(dtype=float)
            lows = _extract_field_series(quote_frame, instrument.yahoo_symbol, "Low") if not quote_frame.empty else pd.Series(dtype=float)
            volumes = _extract_field_series(quote_frame, instrument.yahoo_symbol, "Volume") if not quote_frame.empty else pd.Series(dtype=float)
            if not intraday_closes.empty:
                highs = _same_exchange_day(highs, quote_series.index[-1], exchange_timezone)
                lows = _same_exchange_day(lows, quote_series.index[-1], exchange_timezone)
                volumes = _same_exchange_day(volumes, quote_series.index[-1], exchange_timezone)
            else:
                highs, lows, volumes = highs.tail(1), lows.tail(1), volumes.tail(1)
            items.append(
                {
                    "symbol": instrument.symbol,
                    "name": instrument.name,
                    "yahoo_symbol": instrument.yahoo_symbol,
                    "group": instrument.group,
                    "price": round(float(current), 6),
                    "change": round(change, 6) if change is not None else None,
                    "change_pct": round(change_pct, 3) if change_pct is not None else None,
                    "reference_price": previous,
                    "reference_basis": (
                        "previous_daily_close" if previous is not None else "unknown"
                    ),
                    "exchange_timezone": exchange_timezone,
                    "statistics_window": "exchange_day",
                    "high_24h": round(float(highs.max()), 6) if not highs.empty else None,
                    "low_24h": round(float(lows.min()), 6) if not lows.empty else None,
                    # Intraday volume is the current session's accumulated
                    # volume. Daily fallback keeps the old last-bar value.
                    "volume_24h": round(float(volumes.sum() if not intraday_closes.empty else volumes.iloc[-1]), 4) if not volumes.empty else None,
                    "category": instrument.category,
                    "unit": instrument.unit,
                    "focus": instrument.focus,
                    "source": "yahoo_finance",
                    "data_interval": _SNAPSHOT_INTRADAY_INTERVAL if not intraday_closes.empty else "1d",
                    "updated_at": _series_updated_at(quote_series),
                    "fetched_at": _utc_now_iso(),
                }
            )
        items.extend(self._fetch_vnstock_snapshot_items())
        crypto_items = self._fetch_crypto_snapshot_items()
        if crypto_items:
            items = [item for item in items if item.get("group") != "crypto"]
            items.extend(crypto_items)
        return {
            "as_of": _utc_now_iso(),
            "source": "mixed",
            "data_interval": _SNAPSHOT_INTRADAY_INTERVAL if has_intraday else "1d",
            "items": items,
        }

    def _fetch_crypto_snapshot_items(self) -> list[dict[str, Any]]:
        """Use a market-data feed with 24h stats instead of daily-only crypto bars."""
        ids = {
            "BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether", "BNB": "binancecoin",
            "XRP": "ripple", "USDC": "usd-coin", "SOL": "solana", "TRX": "tron",
            "DOGE": "dogecoin", "LINK": "chainlink", "ADA": "cardano", "XLM": "stellar",
            "NEAR": "near", "BCH": "bitcoin-cash", "UNI": "uniswap", "HBAR": "hedera-hashgraph",
            "LTC": "litecoin", "AVAX": "avalanche-2", "SUI": "sui", "TON": "the-open-network",
            "CRO": "crypto-com-chain", "SHIB": "shiba-inu", "DOT": "polkadot", "PEPE": "pepe",
            "ICP": "internet-computer", "ARB": "arbitrum", "FIL": "filecoin", "APT": "aptos",
            "OP": "optimism", "MKR": "maker", "INJ": "injective-protocol",
        }
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": ",".join(ids.values()),
                    "order": "market_cap_desc",
                    "per_page": len(ids),
                    "page": 1,
                    "sparkline": "true",
                    "price_change_percentage": "24h",
                },
                timeout=8,
                headers={"Accept": "application/json", "User-Agent": "risk-dashboard/1.0"},
            )
            response.raise_for_status()
            rows = response.json()
        except Exception:
            return []

        by_id = {value: key for key, value in ids.items()}
        canonical_names = {
            instrument.symbol: instrument.name
            for instrument in GLOBAL_MARKET_INSTRUMENTS
            if instrument.group == "crypto"
        }
        items: list[dict[str, Any]] = []
        for row in rows if isinstance(rows, list) else []:
            symbol = by_id.get(row.get("id"))
            price = _safe_float(row.get("current_price"))
            if not symbol or price is None:
                continue
            change = _safe_float(row.get("price_change_24h"))
            change_pct = _safe_float(row.get("price_change_percentage_24h"))
            sparkline = row.get("sparkline_in_7d", {}).get("price", [])
            items.append({
                "symbol": symbol,
                "name": canonical_names.get(symbol) or row.get("name") or symbol,
                "yahoo_symbol": f"{symbol}-USD",
                "group": "crypto",
                "price": round(price, 8),
                "change": round(change, 8) if change is not None else None,
                "change_pct": round(change_pct, 4) if change_pct is not None else None,
                "high_24h": _safe_float(row.get("high_24h")),
                "low_24h": _safe_float(row.get("low_24h")),
                "volume_24h": _safe_float(row.get("total_volume")),
                "market_cap": _safe_float(row.get("market_cap")),
                "market_cap_rank": row.get("market_cap_rank"),
                "circulating_supply": _safe_float(row.get("circulating_supply")),
                "sparkline": [round(float(value), 8) for value in sparkline if _safe_float(value) is not None][-48:],
                "focus": "24h market pulse",
                "source": "coingecko",
                "data_interval": "spot",
                "updated_at": row.get("last_updated") or _utc_now_iso(),
            })
        return items

    def _fetch_vnstock_snapshot_items(self) -> list[dict[str, Any]]:
        vn_instruments = [i for i in GLOBAL_MARKET_INSTRUMENTS if i.data_source == "vnstock"]
        if not vn_instruments:
            return []
        items: list[dict[str, Any]] = []
        for instrument in vn_instruments:
            frame = _fetch_vnstock_dataframe(instrument.vn_symbol or instrument.symbol, days=5, interval="1D")
            if frame is None or frame.empty or "close" not in frame.columns:
                continue
            closes = pd.to_numeric(frame["close"], errors="coerce").dropna()
            if closes.empty:
                continue
            previous = float(closes.iloc[-2]) if len(closes) >= 2 else float(closes.iloc[-1])
            current = float(closes.iloc[-1])
            change = current - previous
            change_pct = (change / previous) * 100 if previous else 0.0
            highs = pd.to_numeric(frame["high"], errors="coerce").dropna() if "high" in frame.columns else pd.Series(dtype=float)
            lows = pd.to_numeric(frame["low"], errors="coerce").dropna() if "low" in frame.columns else pd.Series(dtype=float)
            volumes = pd.to_numeric(frame["volume"], errors="coerce").dropna() if "volume" in frame.columns else pd.Series(dtype=float)
            items.append(
                {
                    "symbol": instrument.symbol,
                    "name": instrument.name,
                    "yahoo_symbol": instrument.vn_symbol,
                    "group": instrument.group,
                    "price": round(current, 6),
                    "change": round(change, 6),
                    "change_pct": round(change_pct, 3),
                    "high_24h": round(float(highs.iloc[-1]), 6) if not highs.empty else None,
                    "low_24h": round(float(lows.iloc[-1]), 6) if not lows.empty else None,
                    "volume_24h": round(float(volumes.iloc[-1]), 4) if not volumes.empty else None,
                    "focus": instrument.focus,
                    "source": "entrade",
                    "updated_at": _utc_now_iso(),
                }
            )
        return items


    def _fetch_yahoo_history(self, *, instrument: FeedInstrument, period: str, interval: str) -> dict[str, Any]:
        safe_period = _normalize_history_period(period, interval)
        safe_interval = _download_interval_for_history(interval)
        try:
            frame = download_yahoo(
                tickers=instrument.yahoo_symbol,
                period=safe_period,
                interval=safe_interval,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
        except Exception:
            return {"as_of": _utc_now_iso(), "source": "yahoo_finance", "points": []}

        normalized = _extract_ohlcv_frame(frame, instrument.yahoo_symbol)
        normalized = _resample_history_frame(normalized, interval)
        points: list[dict[str, Any]] = []
        previous: float | None = None
        for index, row in normalized.tail(_history_point_limit(interval)).iterrows():
            value = row.get("close")
            if pd.isna(value):
                continue
            price = float(value)
            change_pct = ((price - previous) / previous) * 100 if previous else 0.0
            previous = price
            points.append(
                {
                    "date": _timestamp_iso(index),
                    "price": round(price, 6),
                    "open": round(float(row.get("open", price)), 6),
                    "high": round(float(row.get("high", price)), 6),
                    "low": round(float(row.get("low", price)), 6),
                    "close": round(price, 6),
                    "volume": finite_number(row.get("volume")),
                    "change_pct": round(change_pct, 4),
                }
            )
        return {"as_of": _utc_now_iso(), "source": "yahoo_finance", "points": points}

    def _fetch_vnstock_history(self, *, instrument: FeedInstrument, period: str, interval: str) -> dict[str, Any]:
        days = _period_to_days(period)
        vn_interval = _vnstock_interval(interval)
        vn_symbol = instrument.vn_symbol or instrument.symbol
        frame = _fetch_vnstock_dataframe(vn_symbol, days=days, interval=vn_interval)
        if frame is None or frame.empty:
            return {"as_of": _utc_now_iso(), "source": "vnstock", "points": []}

        # vnstock returns VN equity prices in thousands of VND (e.g. 75.1 = 75,100 VND).
        # Multiply to raw VND so chart axes / OHLC strip stay aligned with snapshot.
        # Indices (VNINDEX/VN30/HNXINDEX) are quoted in index points — don't scale.
        scale = 1000.0 if _is_vn_stock_equity(instrument) else 1.0

        limit = _history_point_limit(interval)
        sub = frame.tail(limit)
        if sub.empty:
            return {"as_of": _utc_now_iso(), "source": "vnstock", "points": []}

        date_col = "time" if "time" in sub.columns else sub.columns[0]
        raw_dates = sub[date_col].tolist()
        raw_closes = sub["close"].tolist()
        raw_opens = sub["open"].tolist() if "open" in sub.columns else raw_closes
        raw_highs = sub["high"].tolist() if "high" in sub.columns else raw_closes
        raw_lows = sub["low"].tolist() if "low" in sub.columns else raw_closes
        raw_vols = sub["volume"].tolist() if "volume" in sub.columns else [0.0] * len(sub)

        points: list[dict[str, Any]] = []
        previous: float | None = None
        for i in range(len(sub)):
            close_val = raw_closes[i]
            if close_val is None or (isinstance(close_val, float) and pd.isna(close_val)):
                continue
            price = float(close_val) * scale
            change_pct = ((price - previous) / previous) * 100 if previous else 0.0
            previous = price
            points.append(
                {
                    "date": _timestamp_iso(raw_dates[i]),
                    "price": round(price, 6),
                    "open": round(float(raw_opens[i] if raw_opens[i] is not None and not pd.isna(raw_opens[i]) else close_val) * scale, 6),
                    "high": round(float(raw_highs[i] if raw_highs[i] is not None and not pd.isna(raw_highs[i]) else close_val) * scale, 6),
                    "low": round(float(raw_lows[i] if raw_lows[i] is not None and not pd.isna(raw_lows[i]) else close_val) * scale, 6),
                    "close": round(price, 6),
                    "volume": round(float(raw_vols[i] if raw_vols[i] is not None and not pd.isna(raw_vols[i]) else 0.0), 4),
                    "change_pct": round(change_pct, 4),
                }
            )
        return {"as_of": _utc_now_iso(), "source": "vnstock", "points": points}

    def _load_cache(self) -> dict[str, Any]:
        path = self.cache_dir / "global_market_snapshot.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _load_history_cache(self, symbol: str, period: str, interval: str) -> dict[str, Any]:
        key = self._history_key(symbol, period, interval)
        ttl = _history_cache_ttl_seconds(interval)
        import time as _t
        now = _t.time()
        if key in _MEM_HISTORY_CACHE:
            ts, payload = _MEM_HISTORY_CACHE[key]
            if now - ts <= ttl and payload:
                return payload

        path = self._history_path(symbol, period, interval)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            _MEM_HISTORY_CACHE[key] = (now, payload)
            return payload
        except Exception:
            return {}

    def _write_cache(self, payload: dict[str, Any]) -> None:
        path = self.cache_dir / "global_market_snapshot.json"
        _atomic_write_json(path, payload)

    def _write_history_cache(self, symbol: str, period: str, interval: str, payload: dict[str, Any]) -> None:
        key = self._history_key(symbol, period, interval)
        import time as _t
        _MEM_HISTORY_CACHE[key] = (_t.time(), payload)
        if len(_MEM_HISTORY_CACHE) > 4096:
            _MEM_HISTORY_CACHE.pop(next(iter(_MEM_HISTORY_CACHE)))
        path = self._history_path(symbol, period, interval)
        _atomic_write_json(path, payload)

    def _history_path(self, symbol, period, interval):
        # Version invalidates potentially mixed histories produced before CP-02.
        return self.cache_dir / "history" / f"v2_{symbol}_{period}_{interval}.json"

    def _history_key(self, symbol, period, interval):
        return str(self._history_path(symbol, period, interval).resolve())

    def _is_history_fresh(self, payload: dict[str, Any] | None, ttl_seconds: int) -> bool:
        as_of = timestamp((payload or {}).get("as_of"))
        return bool(
            as_of and 0 <= (datetime.now(timezone.utc) - as_of).total_seconds() <= ttl_seconds
        )



    def _is_cache_fresh(self, payload: dict[str, Any] | None) -> bool:
        return self._is_history_fresh(payload, self.max_cache_age_seconds)


def _merge_snapshot(cached, live, refreshed_groups=None):
    refreshed_groups = refreshed_groups or {"indices", "fx", "commodities", "crypto"}
    previous = {
        row["symbol"]: {**row, "fetched_at": row.get("fetched_at") or cached.get("as_of")}
        for row in cached.get("items", []) if row.get("symbol")
    }
    received = set()
    for row in live.get("items", []):
        symbol = row.get("symbol")
        if not symbol or finite_number(row.get("price")) is None:
            continue
        received.add(symbol)
        previous[symbol] = {**row, "fetched_at": row.get("fetched_at") or live.get("as_of"),
                            "refresh_failed": False}
    for symbol, row in previous.items():
        if symbol not in received and row.get("group") in refreshed_groups:
            previous[symbol] = {**row, "refresh_failed": True}
    return {**cached, **live, "items": list(previous.values())}


def _exchange_timezone(instrument):
    # Download warms Yahoo's timezone metadata cache. Do not guess a reference
    # for markets whose metadata is unavailable.
    try:
        import yfinance as yf
        value = yf.cache.get_tz_cache().lookup(instrument.yahoo_symbol)
        if value:
            return value
    except Exception:
        pass
    # Yahoo commodity futures in this catalog use the New York daily date.
    return "America/New_York" if instrument.group == "commodities" else None


def _same_exchange_day(series, quote_at, exchange_timezone):
    if series.empty or not exchange_timezone:
        return pd.Series(dtype=float)
    try:
        target = pd.Timestamp(quote_at)
        target = target.tz_convert(exchange_timezone) if target.tzinfo else target
        dates = pd.DatetimeIndex(series.index)
        if dates.tz is not None:
            dates = dates.tz_convert(exchange_timezone)
        return series[dates.date == target.date()]
    except (TypeError, ValueError, KeyError):
        return pd.Series(dtype=float)


def _extract_close_series(frame: pd.DataFrame, yahoo_symbol: str) -> pd.Series:
    if frame is None or frame.empty:
        return pd.Series(dtype=float)
    try:
        if isinstance(frame.columns, pd.MultiIndex):
            if ("Close", yahoo_symbol) in frame.columns:
                series = frame[("Close", yahoo_symbol)]
            elif (yahoo_symbol, "Close") in frame.columns:
                series = frame[(yahoo_symbol, "Close")]
            else:
                return pd.Series(dtype=float)
        elif "Close" in frame.columns:
            series = frame["Close"]
        else:
            return pd.Series(dtype=float)
        return pd.to_numeric(series, errors="coerce").dropna()
    except Exception:
        return pd.Series(dtype=float)


def _previous_close(daily_closes: pd.Series, quote_series: pd.Series, exchange_timezone=None):
    """Choose the prior session close for an intraday quote.

    Yahoo sometimes returns a daily bar for the current session and sometimes
    only the previous session (pre-market, after-hours, or a closed market).
    Compare dates in the provider's exchange timezone. Missing reference data
    stays unknown; an intraday bar must not be substituted for a daily close.
    """
    if daily_closes.empty or quote_series.empty:
        return None
    try:
        latest = pd.Timestamp(quote_series.index[-1])
        if latest.tzinfo is not None:
            if not exchange_timezone:
                return None
            latest = latest.tz_convert(exchange_timezone)
        daily_dates = pd.DatetimeIndex(daily_closes.index)
        if daily_dates.tz is not None:
            daily_dates = daily_dates.tz_convert(exchange_timezone or "UTC")
        prior = daily_closes[daily_dates.date < latest.date()]
        return finite_number(prior.iloc[-1]) if not prior.empty else None
    except (TypeError, ValueError, IndexError, KeyError):
        return None


def _extract_field_series(frame: pd.DataFrame, yahoo_symbol: str, field: str) -> pd.Series:
    if frame is None or frame.empty:
        return pd.Series(dtype=float)
    try:
        if isinstance(frame.columns, pd.MultiIndex):
            if (field, yahoo_symbol) in frame.columns:
                series = frame[(field, yahoo_symbol)]
            elif (yahoo_symbol, field) in frame.columns:
                series = frame[(yahoo_symbol, field)]
            else:
                return pd.Series(dtype=float)
        elif field in frame.columns:
            series = frame[field]
        else:
            return pd.Series(dtype=float)
        series = pd.to_numeric(series, errors="coerce")
        series.index = pd.to_datetime(series.index)
        return series.dropna().sort_index()
    except Exception:
        return pd.Series(dtype=float)


def _extract_ohlcv_frame(frame: pd.DataFrame, yahoo_symbol: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = {}
    for field in ("Open", "High", "Low", "Close", "Volume"):
        series = _extract_field_series(frame, yahoo_symbol, field)
        if series.empty and field != "Volume":
            return pd.DataFrame()
        data[field.lower()] = series
    out = pd.DataFrame(data).dropna(subset=["open", "high", "low", "close"]).sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return out


def _normalize_history_period(period: str, interval: str) -> str:
    safe_period = period if period in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "3y", "5y", "10y", "max"} else "6mo"
    if interval == "1m" and safe_period not in {"1d", "5d"}:
        return "5d"
    if interval in {"5m", "15m", "30m"} and safe_period not in {"1d", "5d", "1mo"}:
        return "1mo"
    if interval in {"1h", "4h"} and safe_period not in {"5d", "1mo", "3mo", "6mo", "1y"}:
        return "1y"
    if interval == "1y" and safe_period in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"}:
        return "5y"
    return safe_period


_PERIOD_TO_DAYS = {
    "1d": 5,      # account for weekends so we always land on at least 1 trading day
    "5d": 10,
    "1mo": 35,
    "3mo": 100,
    "6mo": 200,
    "1y": 380,
    "2y": 760,
    "3y": 1140,
    "5y": 1900,
    "10y": 3800,
    "max": 9000,  # vnstock historical depth ~ 2000-01-01
}


def _period_to_days(period: str) -> int:
    return _PERIOD_TO_DAYS.get(period, 200)


_VNSTOCK_INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1H",
    "4h": "1H",   # vnstock has no native 4h for indices — caller may resample
    "1d": "1D",
    "1wk": "1W",
    "1mo": "1M",
    "1y": "1M",   # vnstock has no yearly bucket — fall back to monthly
}


def _vnstock_interval(interval: str) -> str:
    return _VNSTOCK_INTERVAL_MAP.get(interval, "1D")


def _fetch_entrade_ohlcv(symbol: str, *, days: int = 5, interval: str = "1D") -> pd.DataFrame | None:
    """Fetch VN index or stock OHLCV from Entrade (DNSE) chart API.

    Direct HTTP REST API without third-party dependencies or rate limits.
    """
    sym_clean = symbol.upper().strip()
    index_map = {
        "VNINDEX": "VNINDEX",
        "VN-INDEX": "VNINDEX",
        "VN30": "VN30",
        "HNXINDEX": "HNX",
        "HNX-INDEX": "HNX",
        "HNX": "HNX",
        "HNXINDEX30": "HNX30",
        "UPCOMINDEX": "UPCOM",
        "UPCOM-INDEX": "UPCOM",
        "UPCOM": "UPCOM",
        "VN100": "VN100",
    }
    is_index = sym_clean in index_map
    entrade_sym = index_map.get(sym_clean, sym_clean)
    endpoint = "index" if is_index else "stock"

    res_map = {
        "1m": "1",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1h": "1H",
        "1H": "1H",
        "4h": "1H",
        "4H": "1H",
        "1d": "1D",
        "1D": "1D",
        "1wk": "1W",
        "1w": "1W",
        "1W": "1W",
        "1mo": "1W",
        "1M": "1W",
        "1y": "1W",
    }
    resolution = res_map.get(interval, res_map.get(interval.lower(), "1D"))

    import time
    now = int(time.time())
    max_days_by_res = {
        "1": 25,
        "5": 100,
        "15": 180,
        "30": 365,
        "1H": 2000,
        "1D": 10000,
        "1W": 10000,
    }
    effective_days = min(max(days, 5), max_days_by_res.get(resolution, 10000))
    start = now - effective_days * 86400
    url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{endpoint}?resolution={resolution}&symbol={entrade_sym}&from={start}&to={now}"
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            timeout=8,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        t = data.get("t", [])
        c = data.get("c", [])
        if not t or not c:
            return None
        return pd.DataFrame({
            "time": pd.to_datetime(t, unit="s"),
            "open": data.get("o", c),
            "high": data.get("h", c),
            "low": data.get("l", c),
            "close": c,
            "volume": data.get("v", [0.0] * len(t)),
        })
    except Exception as exc:
        logger.debug("Entrade OHLCV fetch failed for %s: %s", symbol, exc)
        return None


def _fetch_vnstock_dataframe(symbol: str, *, days: int, interval: str) -> pd.DataFrame | None:
    """Fetch VN OHLCV from Entrade primary source with vnstock/VCI fallback."""
    # 1. Primary: Entrade / DNSE fast public feed (no rate-limit lockout)
    entrade_frame = _fetch_entrade_ohlcv(symbol, days=days, interval=interval)
    if entrade_frame is not None and not entrade_frame.empty:
        return entrade_frame

    # 2. Secondary fallback: vnstock (if installed & within rate limit)
    from datetime import date

    end = date.today()
    start = end - timedelta(days=max(days, 5))
    start_s = start.isoformat()
    end_s = end.isoformat()

    _VNSTOCK_RATE_LIMITER.acquire()
    try:
        with _vnstock_safe():
            try:
                from vnstock import Quote  # type: ignore

                q = Quote(symbol=symbol, source="VCI")
                frame = q.history(start=start_s, end=end_s, interval=interval)
                if isinstance(frame, pd.DataFrame) and not frame.empty:
                    return frame
            except Exception:
                pass

            try:
                from vnstock import Vnstock  # type: ignore

                stock = Vnstock().stock(symbol=symbol, source="VCI")
                frame = stock.quote.history(start=start_s, end=end_s, interval=interval)
                if isinstance(frame, pd.DataFrame) and not frame.empty:
                    return frame
            except Exception:
                pass
    except _VnstockRateExceeded:
        return None

    return None



class _VnstockRateExceeded(RuntimeError):
    """Raised when vnstock library tries to terminate the process on rate limit."""


@contextlib.contextmanager
def _vnstock_safe():
    """Intercept vnstock's sys.exit()/os._exit() rate-limit kill so we degrade gracefully."""
    import os as _os
    import sys as _sys

    original_sys_exit = _sys.exit
    original_os_exit = _os._exit

    def _trap(code=0):
        raise _VnstockRateExceeded(f"vnstock attempted to terminate process (code={code})")

    _sys.exit = _trap
    _os._exit = _trap
    try:
        yield
    finally:
        _sys.exit = original_sys_exit
        _os._exit = original_os_exit


class _RateLimiter:
    """Sliding-window rate limiter. Blocks until under max_requests in window_seconds."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        import threading as _t

        self.max_requests = max_requests
        self.window = window_seconds
        self._lock = _t.Lock()
        self._timestamps: list[float] = []

    def acquire(self) -> None:
        import time as _time

        while True:
            with self._lock:
                now = _time.time()
                # Drop timestamps outside the window
                cutoff = now - self.window
                while self._timestamps and self._timestamps[0] < cutoff:
                    self._timestamps.pop(0)
                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return
                wait_for = max(0.0, (self._timestamps[0] + self.window) - now)
            _time.sleep(min(wait_for + 0.05, 2.0))


# Global rate limiter — vnstock guest tier allows 20 req/min, we cap at 15/min for safety.
_VNSTOCK_RATE_LIMITER = _RateLimiter(max_requests=15, window_seconds=60)


def _download_interval_for_history(interval: str) -> str:
    normalized = interval if interval in _SUPPORTED_HISTORY_INTERVALS else "1d"
    if normalized in {"1h", "4h"}:
        return "60m"
    if normalized == "1y":
        return "1mo"
    return normalized


def _resample_history_frame(frame: pd.DataFrame, interval: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    if interval == "4h":
        return (
            frame.resample("4h")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna(subset=["open", "high", "low", "close"])
        )
    if interval == "1y":
        return (
            frame.resample("YE")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna(subset=["open", "high", "low", "close"])
        )
    return frame


def _history_point_limit(interval: str) -> int:
    norm = interval.lower() if interval else "1d"
    if norm in {"1m", "5m", "15m", "30m"}:
        return 3000
    if norm in {"1h", "4h"}:
        return 2000
    if norm in {"1wk", "1mo", "1y", "1w", "1m"}:
        return 1500
    return 4000


def _series_updated_at(series: pd.Series) -> str:
    try:
        ts = pd.Timestamp(series.index[-1])
        if ts.tzinfo is None:
            ts = ts.tz_localize(timezone.utc)
        else:
            ts = ts.tz_convert(timezone.utc)
        return ts.isoformat()
    except Exception:
        return _utc_now_iso()


def find_instrument(symbol: str) -> FeedInstrument | None:
    normalized = symbol.strip().upper()
    hit = next(
        (instrument for instrument in GLOBAL_MARKET_INSTRUMENTS
         if instrument.symbol == normalized or instrument.yahoo_symbol.upper() == normalized),
        None,
    )
    if hit is not None:
        return hit
    # Fall through: arbitrary VN ticker (3-5 letters) routed to vnstock.
    if _looks_like_vn_ticker(normalized):
        return FeedInstrument(
            symbol=normalized,
            name=normalized,
            yahoo_symbol="",
            group="vn_stocks",
            focus="Vietnam equity",
            data_source="vnstock",
            vn_symbol=normalized,
        )
    return None


def _looks_like_vn_ticker(symbol: str) -> bool:
    if not symbol:
        return False
    if not (3 <= len(symbol) <= 5):
        return False
    return symbol.isalpha()


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


_VN_INDICES = frozenset({"VNINDEX", "VN30", "HNXINDEX", "HNXINDEX30", "UPCOMINDEX", "HNX", "UPCOM", "VN-INDEX", "HNX-INDEX", "UPCOM-INDEX", "VN100"})


def _is_vn_stock_equity(instrument: FeedInstrument) -> bool:
    """True only for individual VN listings (need ×1000 to raw VND scaling).

    VN indices stay in their natural index-point unit (VN-Index ~1877).
    Synthetic fallthrough instruments use group=vn_stocks → stock.
    """
    if instrument.data_source != "vnstock":
        return False
    sym = (instrument.symbol or "").upper()
    if sym in _VN_INDICES:
        return False
    return True


def _timestamp_iso(value) -> str:
    try:
        ts = pd.Timestamp(value)
        if ts.tzinfo is None:
            ts = ts.tz_localize(timezone.utc)
        else:
            ts = ts.tz_convert(timezone.utc)
        return ts.isoformat()
    except Exception:
        return _utc_now_iso()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
