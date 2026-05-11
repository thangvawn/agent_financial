"""Build Insights dashboard payload from real market data (panel, yfinance, Finnhub, quant)."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from risk_dashboard.data.cross_asset_prices import CROSS_ASSET_PRESETS, sync_cross_asset_history
from risk_dashboard.data.sector_connector import load_sector_panel_csv, sector_winners_losers
from risk_dashboard.modules.guided_investing.application.services import GetGuidedMarketContext
from risk_dashboard.modules.insights.schemas.responses import (
    CrossAssetPointResponse,
    CrossAssetPulseResponse,
    CrossAssetSeriesResponse,
    InsightNarrativeResponse,
    MacroEventResponse,
    MarketSummaryResponse,
    ScenarioItemResponse,
    SectorRotationItemResponse,
    SnapshotCardResponse,
    TrendRadarItemResponse,
)
from risk_dashboard.modules.news_intelligence.application.finnhub_desk import get_finnhub_desk_snapshot
from risk_dashboard.platform.runtime.panel_store import PanelUnavailableError, get_panel
from risk_dashboard.quant.eod_pipeline import run_quant_eod

logger = logging.getLogger(__name__)

_RANGE_DAYS: dict[str, int] = {
    "1M": 35,
    "3M": 95,
    "6M": 185,
    "YTD": 400,
}
_MAX_CHART_POINTS = 18

_VN7 = timezone(timedelta(hours=7))


def _as_of_hcm() -> datetime:
    return datetime.now(_VN7).replace(microsecond=0)


def _range_calendar_days(range_key: str) -> int:
    return _RANGE_DAYS.get(range_key, 35)


def _download_yf_closes(symbol: str, *, calendar_days: int) -> pd.Series | None:
    try:
        import yfinance as yf

        end = date.today()
        start = end - timedelta(days=max(7, min(calendar_days, 800)))
        hist = yf.Ticker(symbol).history(start=start, end=end + timedelta(days=1), auto_adjust=True)
        if hist is None or hist.empty or "Close" not in hist.columns:
            return None
        s = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
        return s.sort_index()
    except Exception as exc:  # noqa: BLE001
        logger.info("Yahoo %s: %s", symbol, exc)
        return None


def _downsample_index(s: pd.Series, max_points: int) -> pd.Series:
    if len(s) <= max_points:
        return s
    step = max(1, len(s) // max_points)
    return s.iloc[::step].tail(max_points)


def _series_to_cross_asset(
    *,
    asset_key: str,
    label: str,
    unit: str,
    closes: pd.Series,
    freshness: str,
    confidence: str,
) -> CrossAssetSeriesResponse | None:
    if closes is None or closes.empty or len(closes) < 2:
        return None
    s = _downsample_index(closes, _MAX_CHART_POINTS)
    start = float(s.iloc[0])
    if start == 0:
        return None
    points: list[CrossAssetPointResponse] = []
    for idx, raw in s.items():
        ts = pd.Timestamp(idx)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        d = ts.date().isoformat()
        rv = float(raw)
        points.append(
            CrossAssetPointResponse(
                date=d,
                raw_value=rv,
                normalized_value=round(rv / start * 100.0, 4),
            )
        )
    latest_change = round((float(s.iloc[-1]) / start - 1.0) * 100.0, 3)
    return CrossAssetSeriesResponse(
        asset_key=asset_key,
        label=label,
        unit=unit,
        values=points,
        latest_change_pct=latest_change,
        freshness_status=freshness,
        confidence=confidence,
    )


def build_snapshot_cards(ms: MarketSummaryResponse) -> list[SnapshotCardResponse]:
    regime_display = ms.regime.replace("_", " ").title()
    risk_display = str(ms.risk_level).replace("_", " ").title()
    theme = ms.cross_asset_theme
    driver = ms.top_driver
    alerts = max(0, int(ms.alerts_count))
    return [
        SnapshotCardResponse(
            key="market_regime",
            label="Market Regime",
            value=regime_display,
            status="watch",
            icon="pulse",
            severity="medium",
            explanation="Ước lượng từ risk regime + decision score trên macro panel.",
        ),
        SnapshotCardResponse(
            key="risk_level",
            label="Risk Level",
            value=risk_display,
            status="watch",
            icon="shield",
            severity="medium",
            explanation="Theo độ nhạy drawdown/score hiện tại — không phải stress test margin.",
        ),
        SnapshotCardResponse(
            key="cross_asset_theme",
            label="Cross-Asset",
            value=theme,
            status="active",
            icon="globe",
            severity="medium",
            explanation="Theme chính suy ra từ top drivers SHAP / cross-asset.",
        ),
        SnapshotCardResponse(
            key="top_driver",
            label="Top Driver",
            value=driver,
            status="active",
            icon="bolt",
            severity="medium",
            explanation="Driver có phần đóng góp lớn nhất vào risk score.",
        ),
        SnapshotCardResponse(
            key="alerts",
            label="Alerts",
            value=f"{alerts} active",
            status="alert",
            icon="bell",
            severity="high" if alerts >= 3 else "medium",
            explanation="Heuristic từ score + drawdown — xem narrative để hiểu chi tiết.",
        ),
    ]


def build_cross_asset_pulse_real(*, range_key: str) -> tuple[CrossAssetPulseResponse, list[str]]:
    """VN-Index + USD/VND from macro panel; gold/BTC from cache; oil + US10Y from Yahoo."""
    days = _range_calendar_days(range_key)
    series: list[CrossAssetSeriesResponse] = []
    fallbacks: list[str] = []

    try:
        panel = get_panel().copy()
        panel["date"] = pd.to_datetime(panel["date"])
        end = panel["date"].max()
        start = end - pd.Timedelta(days=days)
        win = panel[panel["date"] >= start].sort_values("date")
        if "vn_index" in win.columns and win["vn_index"].notna().any():
            vn = pd.Series(win["vn_index"].astype(float).values, index=win["date"].values)
            vn.index = pd.to_datetime(vn.index)
            vn = vn.groupby(vn.index).last().sort_index()
            item = _series_to_cross_asset(
                asset_key="vn_index",
                label="VN-Index",
                unit="idx",
                closes=_downsample_index(vn, 400),
                freshness="fresh",
                confidence="medium",
            )
            if item:
                series.append(item)
        if "usd_vnd_rate" in win.columns and win["usd_vnd_rate"].notna().any():
            fx = pd.Series(win["usd_vnd_rate"].astype(float).values, index=win["date"].values)
            fx.index = pd.to_datetime(fx.index)
            fx = fx.groupby(fx.index).last().sort_index()
            item = _series_to_cross_asset(
                asset_key="usd_vnd",
                label="USD/VND",
                unit="VND",
                closes=_downsample_index(fx, 400),
                freshness="fresh",
                confidence="medium",
            )
            if item:
                series.append(item)
    except (PanelUnavailableError, KeyError, ValueError, TypeError) as exc:
        logger.info("Panel cross-asset slice: %s", exc)
        fallbacks.append("macro_panel")

    for aid, label_key in (("gold", "Vàng"), ("bitcoin", "BTC")):
        preset = next((p for p in CROSS_ASSET_PRESETS if p.id == aid), None)
        if preset is None:
            continue
        try:
            df = sync_cross_asset_history(preset)
            tail = df.tail(max(40, days))
            item = _series_to_cross_asset(
                asset_key=aid,
                label=label_key,
                unit="USD",
                closes=tail["close"],
                freshness="fresh",
                confidence="medium",
            )
            if item:
                series.append(item)
        except Exception as exc:  # noqa: BLE001
            logger.info("Cross-asset %s: %s", aid, exc)
            fallbacks.append(aid)

    oil = _download_yf_closes("CL=F", calendar_days=days)
    if oil is not None:
        item = _series_to_cross_asset(
            asset_key="oil",
            label="Crude Oil (WTI)",
            unit="USD/bbl",
            closes=oil,
            freshness="fresh",
            confidence="medium",
        )
        if item:
            series.append(item)
    else:
        fallbacks.append("oil_yahoo")

    ust = _download_yf_closes("^TNX", calendar_days=days)
    if ust is not None:
        item = _series_to_cross_asset(
            asset_key="us10y",
            label="US 10Y Yield",
            unit="%",
            closes=ust,
            freshness="fresh",
            confidence="low",
        )
        if item:
            series.append(item)
    else:
        fallbacks.append("us10y_yahoo")

    if not series:
        return (
            CrossAssetPulseResponse(
                range=range_key,
                series=[
                    CrossAssetSeriesResponse(
                        asset_key="placeholder",
                        label="Đang tải dữ liệu",
                        unit="—",
                        values=[
                            CrossAssetPointResponse(
                                date=date.today().isoformat(),
                                raw_value=100.0,
                                normalized_value=100.0,
                            )
                        ],
                        latest_change_pct=0.0,
                        freshness_status="unavailable",
                        confidence="low",
                    )
                ],
            ),
            ["empty_cross_asset"],
        )

    return CrossAssetPulseResponse(range=range_key, series=series[:6]), fallbacks


def _slug_regime(risk_regime: str, decision_score_pct: float) -> str:
    r = (risk_regime or "").lower()
    if r in {"stress", "high_risk", "risk_off"}:
        return "risk_off"
    if r in {"risk_on", "complacent"}:
        return "risk_on"
    if decision_score_pct < 42:
        return "risk_off"
    if decision_score_pct > 62:
        return "risk_on"
    return "neutral_cautious"


def _risk_band(score: float, dd: float) -> str:
    if dd >= 18 or score < 38:
        return "elevated"
    if score < 48:
        return "watch"
    if score > 65 and dd < 8:
        return "stable"
    return "watch"


def _theme_from_drivers(drivers: list[dict[str, Any]]) -> str:
    if not drivers:
        return "Mixed macro"
    top = drivers[0].get("label") or ""
    if any("usd" in str(d.get("label", "")).lower() or "vnd" in str(d.get("label", "")).lower() for d in drivers[:2]):
        return "FX + Rates"
    if any("lãi" in str(d.get("label", "")).lower() or "rate" in str(d.get("label", "")).lower() for d in drivers[:2]):
        return "Rates-driven"
    return "Macro cross-currents"


def _top_driver_label(drivers: list[dict[str, Any]]) -> str:
    if not drivers:
        return "Macro mix"
    return str(drivers[0].get("label") or "Macro drivers")


def build_market_summary_real(guided: Any) -> MarketSummaryResponse:
    drivers = guided.drivers if hasattr(guided, "drivers") else []
    dlist = [d.model_dump() if hasattr(d, "model_dump") else dict(d) for d in drivers]
    score = float(guided.decision_score_pct)
    dd = float(guided.expected_drawdown_pct)
    alerts = min(5, max(0, int(round((72 - score) / 14 + (dd / 25)))))
    return MarketSummaryResponse(
        regime=_slug_regime(guided.risk_regime, score),
        risk_level=_risk_band(score, dd),
        cross_asset_theme=_theme_from_drivers(dlist),
        top_driver=_top_driver_label(dlist),
        alerts_count=alerts,
        summary=(guided.summary or guided.headline or "")[:900],
    )


def build_market_narrative_real(guided: Any, *, as_of: str) -> InsightNarrativeResponse:
    drivers = guided.drivers if hasattr(guided, "drivers") else []
    bullets: list[str] = []
    for d in drivers[:4]:
        label = getattr(d, "label", None) or (d.get("label") if isinstance(d, dict) else "")
        share = getattr(d, "share_pct", None) or (d.get("share_pct") if isinstance(d, dict) else 0)
        direction = getattr(d, "direction", None) or (d.get("direction") if isinstance(d, dict) else "")
        if label:
            bullets.append(f"{label}: ~{share}% đóng góp vào risk score ({direction}).")
    if guided.so_what:
        bullets.append(guided.so_what)
    if not bullets:
        bullets = [guided.summary[:320] + ("…" if len(guided.summary) > 320 else "")]

    conf = (guided.confidence_label or "moderate").lower()
    if "high" in conf:
        confidence = "high"
    elif "low" in conf:
        confidence = "low"
    else:
        confidence = "medium"

    monitors = ["USD/VND", "VN-Index", "US 10Y", "Thanh khoản"]
    if drivers:
        lbl0 = getattr(drivers[0], "label", None) or ""
        if lbl0 and lbl0 not in monitors:
            monitors.insert(0, str(lbl0)[:48])

    return InsightNarrativeResponse(
        headline=guided.headline,
        summary=guided.summary,
        key_points=bullets[:6],
        caveats=[
            "Insights là bối cảnh phân tích, không phải khuyến nghị mua/bán.",
            "Một số chuỗi giá dùng Yahoo Finance / cache; độ trễ có thể vài phiên.",
        ],
        what_to_monitor=monitors[:8],
        confidence=confidence,
        generated_at=as_of,
    )


def _spark_from_series(closes: pd.Series | None, n: int = 8) -> list[float]:
    if closes is None or closes.empty:
        return [50.0] * n
    tail = closes.dropna().tail(max(n * 3, n))
    if len(tail) < 2:
        return [50.0, 52.0, 51.0, 53.0, 52.0, 54.0, 53.0, 55.0][:n]
    v0 = float(tail.iloc[0])
    if v0 == 0:
        v0 = 1e-9
    raw = [float(x) / v0 * 50.0 + 50.0 for x in tail.iloc[-n:]]
    if len(raw) < n:
        pad = raw[-1]
        raw = [pad] * (n - len(raw)) + raw
    return raw[-n:]


def build_trend_radar_real(*, range_key: str) -> list[TrendRadarItemResponse]:
    days = _range_calendar_days(range_key)
    rows: list[TrendRadarItemResponse] = []
    try:
        panel = get_panel().copy()
        panel["date"] = pd.to_datetime(panel["date"])
        end = panel["date"].max()
        start = end - pd.Timedelta(days=days)
        win = panel[panel["date"] >= start].sort_values("date")
        fx_s = win["usd_vnd_rate"].astype(float) if "usd_vnd_rate" in win.columns else None
        vn_s = win["vn_index"].astype(float) if "vn_index" in win.columns else None
        vol_s = win["volume"].astype(float) if "volume" in win.columns else None
        sbv_s = win["sbv_interest_rate_pct"].astype(float) if "sbv_interest_rate_pct" in win.columns else None
    except Exception:  # noqa: BLE001
        fx_s = vn_s = vol_s = sbv_s = None

    oil = _download_yf_closes("CL=F", calendar_days=days)
    ust = _download_yf_closes("^TNX", calendar_days=days)

    def row(cat: str, theme: str, status: str, summary: str, spark: list[float], strength: int) -> TrendRadarItemResponse:
        return TrendRadarItemResponse(
            theme=theme,
            category=cat,
            status=status,
            short_summary=summary,
            sparkline_series=spark,
            signal_strength=strength,
            confidence="medium",
        )

    fx_spark = _spark_from_series(fx_s if fx_s is not None else None)
    if fx_s is not None and len(fx_s) >= 2:
        chg = (float(fx_s.iloc[-1]) / float(fx_s.iloc[0]) - 1.0) * 100.0
        fx_status = "volatile" if abs(chg) > 0.25 else "stable"
        fx_note = f"USD/VND biến động ~{chg:+.2f}% trong cửa sổ."
        fx_strength = min(95, 45 + int(abs(chg) * 80))
    else:
        fx_status = "unknown"
        fx_note = "Chưa đủ chuỗi USD/VND trong panel."
        fx_strength = 40
    rows.append(row("fx", "FX Pressure", fx_status, fx_note, fx_spark if fx_s is not None and len(fx_s) >= 2 else [48, 49, 50, 51, 50, 52, 51, 53], fx_strength))

    if sbv_s is not None and len(sbv_s) >= 2:
        r_spark = _spark_from_series(sbv_s)
        rows.append(
            row(
                "rates",
                "Rates (policy)",
                "mixed",
                f"SBV điều hành ~{float(sbv_s.iloc[-1]):.2f}% (cuối chuỗi panel).",
                r_spark,
                min(90, 50 + int(abs(float(sbv_s.iloc[-1]) - float(sbv_s.iloc[0])) * 12)),
            )
        )
    elif ust is not None and len(ust) >= 2:
        r_spark = _spark_from_series(ust)
        rows.append(
            row(
                "rates",
                "Rates (US 10Y)",
                "volatile" if float(ust.iloc[-1]) > float(ust.iloc[0]) else "stable",
                "Proxy lãi suất dài hạn Mỹ (^TNX) trong cửa sổ.",
                r_spark,
                58,
            )
        )
    else:
        rows.append(
            row("rates", "Rates", "unknown", "Chưa có đủ chuỗi lãi suất (panel / Yahoo).", [51.0] * 8, 42)
        )

    oil_spark = _spark_from_series(oil)
    if oil is not None and len(oil) >= 2:
        och = (float(oil.iloc[-1]) / float(oil.iloc[0]) - 1.0) * 100.0
        rows.append(
            row(
                "commodities",
                "Energy (Oil)",
                "volatile" if abs(och) > 3 else "stable",
                f"WTI biến động ~{och:+.1f}% (proxy CL=F).",
                oil_spark,
                min(92, 48 + int(abs(och) * 3)),
            )
        )
    else:
        rows.append(row("commodities", "Energy (Oil)", "unknown", "Chưa tải được giá dầu (Yahoo).", [50.0] * 8, 44))

    vn_spark = _spark_from_series(vn_s)
    if vn_s is not None and len(vn_s) >= 2:
        vch = (float(vn_s.iloc[-1]) / float(vn_s.iloc[0]) - 1.0) * 100.0
        rows.append(
            row(
                "equity",
                "Equity Breadth",
                "improving" if vch > 0 else "deteriorating",
                f"VN-Index ~{vch:+.2f}% trong cửa sổ.",
                vn_spark,
                min(90, 52 + int(min(8, abs(vch) * 5))),
            )
        )
    else:
        rows.append(row("equity", "Equity Breadth", "unknown", "Thiếu chuỗi VN-Index trong panel.", [49.0, 50.0, 51.0, 50.5, 52.0, 51.0, 52.5, 53.0], 46))

    liq_spark = _spark_from_series(vol_s)
    if vol_s is not None and len(vol_s) >= 2:
        vch = (float(vol_s.iloc[-1]) / float(vol_s.iloc[0]) - 1.0) * 100.0
        rows.append(
            row(
                "liquidity",
                "Liquidity (volume)",
                "stable" if abs(vch) < 15 else "volatile",
                f"Thanh khoản VN thay đổi ~{vch:+.1f}% so đầu cửa sổ.",
                liq_spark,
                55,
            )
        )
    else:
        rows.append(row("liquidity", "Liquidity", "unknown", "Không có volume trong panel macro.", [52.0] * 8, 45))

    return rows[:6]


def build_scenario_monitor_real(guided: Any) -> list[ScenarioItemResponse]:
    score = float(guided.decision_score_pct) if guided else 50.0
    base_p = max(25.0, min(65.0, 55.0 - (score - 50.0) * 0.35))
    fx_p = max(8.0, min(40.0, (72 - score) * 0.45))
    rate_p = max(5.0, min(28.0, (60 - score) * 0.35 + 6))
    risk_p = max(3.0, min(18.0, float(guided.expected_drawdown_pct) * 0.35))
    commodity_p = max(2.0, 12.0 - fx_p * 0.08)
    total = base_p + fx_p + rate_p + risk_p + commodity_p
    scale = 100.0 / total

    def pct(x: float) -> float:
        return round(x * scale, 1)

    return [
        ScenarioItemResponse(
            scenario_key="base_case",
            label="Base case",
            probability=pct(base_p),
            impact_level="low",
            affected_themes=["liquidity", "quality"],
            summary="Tăng trưởng chậm; định giá phụ thuộc dòng tiền và lãi suất.",
            assumptions=["Không sốc FX", "Thanh khoản không co đột ngột"],
            recommended_review="Theo dõi độ rộng và risk score tuần.",
        ),
        ScenarioItemResponse(
            scenario_key="fx_stress",
            label="FX stress",
            probability=pct(fx_p),
            impact_level="medium",
            affected_themes=["USD strength", "EM flows"],
            summary="Áp lực tỷ giá / USD mạnh ảnh hưởng dòng vốn và nhóm nhạy FX.",
            assumptions=["USD/VND biến động nhanh", "Risk premium tăng"],
            recommended_review="Rà soát phơi nhiễm FX và biên lãi doanh nghiệp.",
        ),
        ScenarioItemResponse(
            scenario_key="rate_shock",
            label="Rate shock",
            probability=pct(rate_p),
            impact_level="high",
            affected_themes=["Rates", "Duration"],
            summary="Lãi suất tăng nhanh hơn kỳ vọng — chiết khấu tài sản dài hạn.",
            assumptions=["Lợi suất thực dương kéo dài"],
            recommended_review="Kiểm tra độ nhạm lãi suất danh mục.",
        ),
        ScenarioItemResponse(
            scenario_key="risk_off",
            label="Risk-off",
            probability=pct(risk_p),
            impact_level="high",
            affected_themes=["Growth", "Credit"],
            summary="Tăng trưởng suy yếu / tâm lý phòng thủ.",
            assumptions=["Risk score xuống thấp", "Thanh khoản co"],
            recommended_review="Ưu tiên chất lượng và kịch bản downside.",
        ),
        ScenarioItemResponse(
            scenario_key="commodity_spike",
            label="Commodity spike",
            probability=pct(commodity_p),
            impact_level="medium",
            affected_themes=["Inflation", "Margins"],
            summary="Giá hàng hóa tăng — áp lực biên lãi và kỳ vọng lạm phát.",
            assumptions=["Nguồn cung/cầu hàng hóa căng"],
            recommended_review="Theo dõi nhóm ngành nhạy năng lượng/chi phí đầu vào.",
        ),
    ]


def build_sector_rotation_real() -> list[SectorRotationItemResponse]:
    sector_path = Path("data/sector_panel.csv")
    if not sector_path.exists():
        return [
            SectorRotationItemResponse(
                sector="Market",
                short_term_view="trung tính",
                medium_term_view="trung tính",
                relative_strength=0.5,
                momentum_score=50,
                breadth_score=50,
                flow_score=None,
                status="neutral",
                explanation="Chưa có sector_panel.csv — thêm dữ liệu ngành để rotation thực.",
            )
        ]
    try:
        panel = load_sector_panel_csv(sector_path)
        latest = panel["month_end"].max().date()
        pulse = sector_winners_losers(panel, latest, window_months=6, top_k=4)
        out: list[SectorRotationItemResponse] = []
        for code, ret in pulse.winners[:3]:
            rs = max(0.0, min(1.0, 0.5 + float(ret) / 80.0))
            mom = max(0, min(100, 50 + int(float(ret) * 1.2)))
            out.append(
                SectorRotationItemResponse(
                    sector=str(code),
                    short_term_view="tích cực" if ret > 3 else "trung tính",
                    medium_term_view="trung tính",
                    relative_strength=round(rs, 3),
                    momentum_score=mom,
                    breadth_score=min(100, mom + 5),
                    flow_score=None,
                    status="positive" if ret > 2 else "watch",
                    explanation=f"Cửa sổ {pulse.window_months} tháng tới {latest}: hiệu suất ~{ret:.1f}%.",
                )
            )
        for code, ret in pulse.losers[:2]:
            rs = max(0.0, min(1.0, 0.5 + float(ret) / 80.0))
            mom = max(0, min(100, 50 + int(float(ret) * 1.2)))
            out.append(
                SectorRotationItemResponse(
                    sector=str(code),
                    short_term_view="tiêu cực" if ret < -3 else "trung tính",
                    medium_term_view="trung tính",
                    relative_strength=round(rs, 3),
                    momentum_score=mom,
                    breadth_score=max(0, mom - 5),
                    flow_score=None,
                    status="negative" if ret < -2 else "watch",
                    explanation=f"Cửa sổ {pulse.window_months} tháng: hiệu suất ~{ret:.1f}%.",
                )
            )
        return out[:6]
    except Exception as exc:  # noqa: BLE001
        logger.info("Sector rotation: %s", exc)
        return [
            SectorRotationItemResponse(
                sector="Market",
                short_term_view="unknown",
                medium_term_view="unknown",
                relative_strength=0.5,
                momentum_score=50,
                breadth_score=50,
                flow_score=None,
                status="neutral",
                explanation="Không đọc được sector panel.",
            )
        ]


def build_macro_calendar_real(*, as_of: datetime, limit: int = 6) -> list[MacroEventResponse]:
    snap = get_finnhub_desk_snapshot(force=False, calendar_days=21, include_quotes=False)
    if not snap.get("enabled"):
        return [
            MacroEventResponse(
                event_id="finnhub-disabled",
                event_name="Bật FINNHUB_API_KEY để đồng bộ lịch kinh tế",
                event_time=as_of.isoformat(),
                region="—",
                impact_level="low",
                related_themes=[],
                time_remaining="—",
                source="finnhub",
            )
        ]
    cal = snap.get("calendar") or {}
    events = cal.get("events") or []
    if not events:
        return [
            MacroEventResponse(
                event_id="placeholder",
                event_name="Thêm FINNHUB_API_KEY để xem lịch vĩ mô",
                event_time=as_of.isoformat(),
                region="—",
                impact_level="low",
                related_themes=[],
                time_remaining="—",
                source="finnhub",
            )
        ]
    out: list[MacroEventResponse] = []
    for row in events[:limit]:
        raw_date = str(row.get("date") or "")[:10]
        ev = str(row.get("event") or "Event")[:120]
        cc = str(row.get("country") or "")
        imp = str(row.get("impact") or "").lower()
        impact_level = "high" if imp == "high" else "medium" if imp == "medium" else "low"
        event_time = f"{raw_date}T09:30:00+07:00"
        out.append(
            MacroEventResponse(
                event_id=f"fh-{raw_date}-{hash(ev) % 100000}",
                event_name=ev,
                event_time=event_time,
                region=cc or "Global",
                impact_level=impact_level,
                related_themes=["Macro"],
                time_remaining="",
                source="finnhub",
            )
        )
    return out


def load_guided_and_quant() -> tuple[Any, Any | None]:
    guided = GetGuidedMarketContext().execute()
    quant = None
    try:
        panel = get_panel()
        as_of = panel["date"].max()
        as_of_date = as_of.date() if hasattr(as_of, "date") else date.fromisoformat(str(as_of))
        quant = run_quant_eod(panel, as_of_date)
    except Exception:  # noqa: BLE001
        quant = None
    return guided, quant


def build_dashboard_quality_real(*, as_of: str, fallbacks: list[str]) -> Any:
    from risk_dashboard.modules.insights.schemas.responses import InsightSourceQualityResponse, InsightsDataQualityResponse

    has_yahoo_fb = bool({"oil_yahoo", "us10y_yahoo"} & set(fallbacks))
    overall = "fresh" if not fallbacks else "delayed"
    sources = [
        InsightSourceQualityResponse(
            source="macro_panel",
            last_updated=as_of,
            freshness_status="fresh",
            confidence="medium",
            fallback_used="macro_panel" in fallbacks,
        ),
        InsightSourceQualityResponse(
            source="yahoo_cross_asset",
            last_updated=as_of,
            freshness_status="fresh",
            confidence="medium",
            fallback_used=has_yahoo_fb,
        ),
        InsightSourceQualityResponse(
            source="finnhub_calendar",
            last_updated=as_of,
            freshness_status="fresh",
            confidence="medium",
            fallback_used=not (os.environ.get("FINNHUB_API_KEY") or "").strip(),
        ),
    ]
    return InsightsDataQualityResponse(
        overall_freshness=overall,
        last_updated=as_of,
        sources=sources,
        stale_fields=[],
        missing_fields=[],
        fallback_used=fallbacks or [],
    )

