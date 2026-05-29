from __future__ import annotations

from typing import Any

from risk_dashboard.modules.data_hub.application.global_market_feed import GlobalMarketFeedProducer
from risk_dashboard.modules.data_hub.domain.entities import TopicPolicy, TopicSnapshot, utc_now_iso
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService


GLOBAL_TOPIC_POLICIES: tuple[TopicPolicy, ...] = (
    TopicPolicy("global:indices", ttl_seconds=300, min_interval_seconds=60, priority=10, source="yahoo_finance"),
    TopicPolicy("global:fx:majors", ttl_seconds=300, min_interval_seconds=60, priority=8, source="yahoo_finance"),
    TopicPolicy("global:commodities", ttl_seconds=300, min_interval_seconds=60, priority=8, source="yahoo_finance"),
    TopicPolicy("global:crypto", ttl_seconds=300, min_interval_seconds=60, priority=7, source="yahoo_finance"),
    TopicPolicy("global:market_pulse", ttl_seconds=180, min_interval_seconds=30, priority=12, source="derived"),
    TopicPolicy("global:news:pulse", ttl_seconds=600, min_interval_seconds=120, priority=4, source="editorial_context"),
)

TERMINAL_VIEWS: dict[str, dict[str, Any]] = {
    "dashboard": {
        "label": "Dashboard",
        "visible_widget_keys": ["global_indices", "fx_majors", "commodities", "crypto", "market_pulse", "global_snapshot", "market_news", "chart"],
        "default_symbol": "XAU",
    },
    "markets": {
        "label": "Markets",
        "visible_widget_keys": ["global_indices", "market_pulse", "global_snapshot", "market_news", "chart"],
        "default_symbol": "SPX",
    },
    "fx": {
        "label": "FX",
        "visible_widget_keys": ["fx_majors", "market_pulse", "global_snapshot", "chart"],
        "default_symbol": "DXY",
    },
    "commodities": {
        "label": "Commodities",
        "visible_widget_keys": ["commodities", "market_pulse", "market_news", "chart"],
        "default_symbol": "XAU",
    },
    "crypto": {
        "label": "Crypto",
        "visible_widget_keys": ["crypto", "market_pulse", "market_news", "chart"],
        "default_symbol": "BTC",
    },
    "ai_chat": {
        "label": "AI Chat",
        "visible_widget_keys": ["ai_chat", "market_pulse", "global_snapshot"],
        "default_symbol": "SPX",
    },
}


class DataHubService:
    def list_topic_status(self) -> dict[str, Any]:
        snapshots = self._build_snapshots()
        return {
            "as_of": utc_now_iso(),
            "topics": [
                {
                    "topic": snapshot.topic,
                    "freshness": snapshot.freshness,
                    "confidence_label": snapshot.confidence_label,
                    "source": snapshot.source,
                    "last_success_at": snapshot.last_success_at,
                    "ttl_seconds": snapshot.ttl_seconds,
                    "stale_reason": snapshot.stale_reason,
                }
                for snapshot in snapshots
            ],
        }

    def get_topic(self, topic: str) -> TopicSnapshot | None:
        return next((snapshot for snapshot in self._build_snapshots() if snapshot.topic == topic), None)

    def get_global_terminal(self, *, view: str = "dashboard") -> dict[str, Any]:
        active_view = view if view in TERMINAL_VIEWS else "dashboard"
        view_config = TERMINAL_VIEWS[active_view]
        snapshots = {snapshot.topic: snapshot for snapshot in self._build_snapshots()}
        indices = snapshots["global:indices"].payload["items"]
        fx = snapshots["global:fx:majors"].payload["items"]
        commodities = snapshots["global:commodities"].payload["items"]
        crypto = snapshots["global:crypto"].payload["items"]
        pulse = _build_market_pulse(indices=indices, crypto=crypto, commodities=commodities)
        news = snapshots["global:news:pulse"].payload["items"]

        return {
            "terminal": {
                "name": "North Star Global Terminal",
                "session": "public-market-intelligence",
                "mode": "education-first",
                "active_view": active_view,
                "visible_widget_keys": view_config["visible_widget_keys"],
                "default_symbol": view_config["default_symbol"],
                "as_of": utc_now_iso(),
                "status": "ready",
            },
            "navigation": {
                "active_view": active_view,
                "tabs": [
                    {
                        "id": key,
                        "label": config["label"],
                        "visible_widget_keys": config["visible_widget_keys"],
                        "default_symbol": config["default_symbol"],
                    }
                    for key, config in TERMINAL_VIEWS.items()
                ],
                "actions": [
                    {"id": "insights", "label": "Open Insights", "target": "/insights"},
                    {"id": "news", "label": "News Desk", "target": "/news"},
                    {"id": "pro_lab", "label": "Pro Lab", "target": "/pro-lab"},
                    {"id": "home", "label": "Home", "target": "/home"},
                ],
            },
            "ticker_tape": _ticker_tape(indices[:4] + commodities[:2] + crypto[:2]),
            "widgets": {
                "global_indices": indices,
                "fx_majors": fx,
                "commodities": commodities,
                "crypto": crypto,
                "market_pulse": pulse,
                "global_snapshot": _global_snapshot(indices=indices, commodities=commodities, crypto=crypto),
                "market_news": news,
            },
            "topics": [snapshot.to_dict() for snapshot in snapshots.values()],
            "trust": {
                "what_this_is": "Dashboard giáo dục để đọc bối cảnh quốc tế, cross-asset và risk pulse.",
                "what_this_is_not": "Không phải bảng tín hiệu mua bán, không phải khuyến nghị đầu tư cá nhân hóa.",
                "freshness_label": _freshness_label(snapshots.values()),
            },
        }

    def get_instrument_history(self, *, symbol: str, period: str = "6mo", interval: str = "1d") -> dict[str, Any]:
        # Variable cache TTL by interval — intraday must refresh aggressively for near-realtime feel.
        ttl = _cache_ttl_for_interval(interval)
        return GlobalMarketFeedProducer(max_cache_age_seconds=ttl).history(symbol=symbol, period=period, interval=interval)

    def _build_snapshots(self) -> tuple[TopicSnapshot, ...]:
        now = utc_now_iso()
        feed = GlobalMarketFeedProducer().snapshot()
        news_feed = NewsIntelligenceService().get_feed(limit=40)
        groups = feed.get("groups", {})
        payload_by_topic = {
            "global:indices": {"items": groups.get("indices", [])},
            "global:fx:majors": {"items": groups.get("fx", [])},
            "global:commodities": {"items": groups.get("commodities", [])},
            "global:crypto": {"items": groups.get("crypto", [])},
            "global:market_pulse": {"items": []},
            "global:news:pulse": {
                "items": news_feed.get("articles", [])[:12],
                "clusters": news_feed.get("clusters", [])[:6],
                "pulse": news_feed.get("pulse", {}),
            },
        }
        snapshots: list[TopicSnapshot] = []
        for policy in GLOBAL_TOPIC_POLICIES:
            payload = payload_by_topic[policy.topic]
            freshness = str(feed.get("freshness") or "degraded") if policy.topic.startswith("global:") and policy.topic != "global:news:pulse" else "fresh"
            confidence = "high" if freshness == "fresh" else "limited"
            stale_reason = None
            last_success_at = str(feed.get("as_of") or now)
            if policy.topic == "global:news:pulse":
                freshness = str(news_feed.get("freshness") or "degraded")
                confidence = str(news_feed.get("confidence_label") or "limited")
                stale_reason = news_feed.get("stale_reason")
                last_success_at = str(news_feed.get("as_of") or now)
            if policy.topic == "global:market_pulse":
                has_market_inputs = bool(payload_by_topic["global:indices"]["items"] or payload_by_topic["global:crypto"]["items"] or payload_by_topic["global:commodities"]["items"])
                freshness = str(feed.get("freshness") or "degraded") if has_market_inputs else "degraded"
                confidence = "moderate" if has_market_inputs else "limited"
            if policy.topic != "global:news:pulse" and not payload["items"] and policy.topic != "global:market_pulse":
                freshness = "degraded"
                confidence = "limited"
                stale_reason = str(feed.get("stale_reason") or "live_feed_unavailable_no_cache")
            elif freshness != "fresh":
                stale_reason = str(feed.get("stale_reason") or "live_feed_unavailable_using_cache")
            snapshots.append(
                TopicSnapshot(
                    topic=policy.topic,
                    payload=payload,
                    freshness=freshness,
                    confidence_label=confidence,
                    source=policy.source,
                    last_success_at=last_success_at,
                    ttl_seconds=policy.ttl_seconds,
                    stale_reason=stale_reason,
                )
            )
        return tuple(snapshots)


def _build_market_pulse(*, indices: list[dict[str, Any]], crypto: list[dict[str, Any]], commodities: list[dict[str, Any]]) -> dict[str, Any]:
    up_count = sum(1 for item in indices if float(item["change_pct"]) >= 0)
    down_count = max(0, len(indices) - up_count)
    average_index_change = sum(float(item["change_pct"]) for item in indices) / max(1, len(indices))
    risk_on = average_index_change + sum(float(item["change_pct"]) for item in crypto[:2]) / 4
    fear_greed = max(0, min(100, round(50 + risk_on * 12)))
    return {
        "fear_greed": fear_greed,
        "label": "Extreme greed" if fear_greed >= 75 else "Risk-on" if fear_greed >= 60 else "Neutral" if fear_greed >= 40 else "Risk-off",
        "breadth": [
            {"label": "Global indices", "up": up_count, "down": down_count},
            {"label": "Crypto beta", "up": sum(1 for item in crypto if float(item["change_pct"]) >= 0), "down": sum(1 for item in crypto if float(item["change_pct"]) < 0)},
            {"label": "Commodities", "up": sum(1 for item in commodities if float(item["change_pct"]) >= 0), "down": sum(1 for item in commodities if float(item["change_pct"]) < 0)},
        ],
        "top_gainers": sorted(indices + crypto + commodities, key=lambda item: float(item["change_pct"]), reverse=True)[:3],
        "top_losers": sorted(indices + crypto + commodities, key=lambda item: float(item["change_pct"]))[:3],
    }


def _global_snapshot(*, indices: list[dict[str, Any]], commodities: list[dict[str, Any]], crypto: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {item["symbol"]: item for item in indices + commodities + crypto}
    return [lookup[symbol] for symbol in ("SPX", "DXY", "XAU", "WTI", "BTC", "VNINDEX") if symbol in lookup]


def _ticker_tape(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"symbol": item["symbol"], "price": item["price"], "change_pct": item["change_pct"]} for item in items]


def _freshness_label(snapshots) -> str:
    values = {snapshot.freshness for snapshot in snapshots}
    if "degraded" in values:
        return "Một số topic đang dùng fallback/cache."
    if "stale" in values:
        return "Một số topic đã cũ."
    return "Các topic chính đang sẵn sàng."


# Cache TTL by chart interval — intraday gets aggressive refresh, daily+ caches longer
_INTERVAL_TTL_SECONDS: dict[str, int] = {
    "1m": 30,
    "5m": 60,
    "15m": 180,
    "30m": 300,
    "1h": 600,
    "4h": 900,
    "1d": 3600,
    "1wk": 6 * 3600,
    "1mo": 12 * 3600,
    "1y": 24 * 3600,
}


def _cache_ttl_for_interval(interval: str) -> int:
    return _INTERVAL_TTL_SECONDS.get(interval, 900)
