from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_ops_event, emit_product_event
from risk_dashboard.data.cross_asset_prices import build_cross_asset_dashboard
from risk_dashboard.data.financials import FinancialDataError, get_financial_dataset
from risk_dashboard.data.sector_connector import load_sector_panel_csv, sector_winners_losers
from risk_dashboard.modules.admin_cms.application.runtime_reader import ContentOpsRuntimeReader
from risk_dashboard.modules.guided_investing.application.services import (
    GetGuidedCompanyHealth,
    GetGuidedMarketContext,
)
from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import (
    SqliteOnboardingProfileRepository,
)
from risk_dashboard.modules.insights.domain.entities import InsightCard, InsightDriver, InsightMetric
from risk_dashboard.modules.insights.domain.policies import (
    build_company_health_card,
    build_cross_asset_card,
    build_explainability_card,
    build_macro_context_card,
    build_market_regime_card,
    build_scenario_card,
    build_sector_pulse_card,
    infer_level,
)
from risk_dashboard.modules.insights.schemas.responses import (
    InsightCardResponse,
    InsightContextualExplainerResponse,
    AiCompanionContextResponse,
    AiCompanionPromptResponse,
    CrossAssetPointResponse,
    CrossAssetPulseResponse,
    CrossAssetSeriesResponse,
    InsightNarrativeResponse,
    InsightSourceQualityResponse,
    InsightsDashboardResponse,
    InsightsDataQualityResponse,
    InsightDisclaimerResponse,
    InsightDriverResponse,
    InsightMetricResponse,
    InsightsSafetyResponse,
    InsightsHomeResponse,
    LearnLinkResponse,
    MacroEventResponse,
    MarketSummaryResponse,
    ScenarioItemResponse,
    SectorRotationItemResponse,
    SnapshotCardResponse,
    TrendRadarItemResponse,
    WatchlistImpactResponse,
)
from risk_dashboard.modules.trust_safety.application.services import TrustSafetyService
from risk_dashboard.platform.runtime.panel_store import PanelUnavailableError, get_panel
from risk_dashboard.quant.eod_pipeline import run_quant_eod


class GetInsightsHome:
    def execute(
        self,
        *,
        session_id: str | None = None,
        level: str | None = None,
        ticker: str = "FPT",
        usd_vnd_rate: float | None = None,
        sbv_interest_rate_pct: float | None = None,
    ) -> InsightsHomeResponse:
        resolved_level = _resolve_level(session_id=session_id, level=level)
        market_regime = _build_market_regime(resolved_level)
        macro_context = _build_macro_context(resolved_level)
        cross_asset = _build_cross_asset_context(resolved_level)
        sector_pulse = _build_sector_pulse(resolved_level)
        company_health = _build_company_health(resolved_level, ticker=ticker)
        scenario = _build_scenario_context(
            resolved_level,
            usd_vnd_rate=usd_vnd_rate,
            sbv_interest_rate_pct=sbv_interest_rate_pct,
        )
        explainability = _build_explainability(resolved_level)
        emit_product_event(
            event_name="insights_home_viewed",
            module="insights",
            surface="insights",
            session_id=session_id,
            user_id=session_id,
            properties={"level": resolved_level, "ticker": ticker.upper()},
        )
        return InsightsHomeResponse(
            session_id=session_id,
            level=resolved_level,
            market_regime_snapshot=_to_card_response(market_regime),
            macro_context=_to_card_response(macro_context),
            cross_asset_context=_to_card_response(cross_asset),
            sector_pulse=_to_card_response(sector_pulse),
            company_health_insight=_to_card_response(company_health),
            scenario_what_if=_to_card_response(scenario),
            explainability_top_drivers=_to_card_response(explainability),
        )


class GetInsightsDashboard:
    def execute(self, *, session_id: str | None = None, user_mode: str = "investor", range_key: str = "1M") -> InsightsDashboardResponse:
        as_of_dt = datetime.now(timezone(timedelta(hours=7))).replace(microsecond=0)
        as_of = as_of_dt.isoformat()
        quality = _build_dashboard_quality(as_of)
        trend_radar = _build_trend_radar()
        cross_asset = _build_cross_asset_pulse(range_key=range_key)
        scenarios = _build_scenario_monitor()
        sector_rotation = _build_sector_rotation()
        learn_links = _build_learn_links()
        watchlist = _build_watchlist_impact(session_id)
        safety = _build_insights_safety()
        narrative = InsightNarrativeResponse(
            headline="Thị trường thận trọng trước áp lực USD và lãi suất",
            summary=(
                "Thị trường đang trong trạng thái trung lập nghiêng thận trọng. USD duy trì sức mạnh, "
                "lãi suất toàn cầu còn cao và dòng tiền có xu hướng ưu tiên nhóm chất lượng/phòng thủ."
            ),
            key_points=[
                "USD mạnh lên gây áp lực lên tài sản rủi ro và nhóm nhạy với vốn ngoại.",
                "Lợi suất tăng khiến định giá cổ phiếu nhạy hơn với tin vĩ mô.",
                "Thanh khoản ổn định, nhưng độ rộng thị trường chưa xác nhận một pha risk-on rõ.",
            ],
            caveats=[
                "Insights là bối cảnh phân tích, không phải khuyến nghị mua/bán.",
                "Một số nguồn cross-asset đang dùng read-model fallback nếu live feed chưa sẵn sàng.",
            ],
            what_to_monitor=["USD/VND", "lợi suất", "độ rộng thị trường", "giá dầu", "thanh khoản"],
            confidence="medium",
            generated_at=as_of,
        )
        emit_product_event(
            event_name="insights_dashboard_requested",
            module="insights",
            surface="insights",
            session_id=session_id,
            user_id=session_id,
            properties={"user_mode": user_mode, "range": range_key},
        )
        return InsightsDashboardResponse(
            as_of=as_of,
            user_mode=user_mode,
            market_summary=MarketSummaryResponse(
                regime="neutral_cautious",
                risk_level="watch",
                cross_asset_theme="FX + Rates",
                top_driver="USD strength",
                alerts_count=2,
                summary="Thị trường trung lập nghiêng thận trọng do USD mạnh và kỳ vọng lãi suất còn cao.",
            ),
            snapshot_cards=[
                SnapshotCardResponse(
                    key="market_regime",
                    label="Market Regime",
                    value="Neutral to Cautious",
                    status="watch",
                    icon="pulse",
                    severity="medium",
                    explanation="Động lượng chưa xấu, nhưng áp lực tỷ giá và lãi suất làm bối cảnh thận trọng hơn.",
                ),
                SnapshotCardResponse(
                    key="risk_level",
                    label="Risk Level",
                    value="Watch",
                    status="watch",
                    icon="shield",
                    severity="medium",
                    explanation="Risk context cần theo dõi, chưa phải trạng thái stress.",
                ),
                SnapshotCardResponse(
                    key="cross_asset_theme",
                    label="Cross-Asset",
                    value="FX + Rates",
                    status="active",
                    icon="globe",
                    severity="medium",
                    explanation="Tỷ giá và lãi suất đang là hai theme chi phối cross-asset.",
                ),
                SnapshotCardResponse(
                    key="top_driver",
                    label="Top Driver",
                    value="USD strength",
                    status="active",
                    icon="bolt",
                    severity="medium",
                    explanation="USD mạnh làm tăng áp lực lên EM và tài sản rủi ro.",
                ),
                SnapshotCardResponse(
                    key="alerts",
                    label="Alerts",
                    value="2 active",
                    status="alert",
                    icon="bell",
                    severity="high",
                    explanation="Có cảnh báo về FX pressure và rate sensitivity.",
                ),
            ],
            market_narrative=narrative,
            trend_radar=trend_radar,
            cross_asset_pulse=cross_asset,
            scenario_monitor=scenarios,
            sector_rotation=sector_rotation,
            macro_calendar=_build_macro_calendar(as_of_dt),
            watchlist_impact=watchlist,
            learn_links=learn_links,
            ai_companion=AiCompanionContextResponse(
                context_id=f"insights-{as_of_dt.strftime('%Y%m%d%H%M')}",
                mode="public_safe_market_context",
                suggested_prompts=[
                    AiCompanionPromptResponse(label="Giải thích rủi ro hôm nay", intent="explain_risk_context"),
                    AiCompanionPromptResponse(label="Điều gì đang dẫn dắt thị trường?", intent="explain_top_drivers"),
                    AiCompanionPromptResponse(label="Kịch bản nào nên theo dõi?", intent="explain_scenarios"),
                ],
                context_bundle={
                    "market_summary": "neutral_cautious/watch",
                    "top_driver": "USD strength",
                    "safety": "no_buy_sell_recommendation",
                    "data_quality": quality.overall_freshness,
                },
            ),
            safety=safety,
            data_quality=quality,
        )


class GetCompanyInsight:
    def execute(self, *, session_id: str | None = None, level: str | None = None, ticker: str) -> InsightCardResponse:
        emit_product_event(
            event_name="insight_company_viewed",
            module="insights",
            surface="insights",
            session_id=session_id,
            user_id=session_id,
            properties={"ticker": ticker.upper(), "level": _resolve_level(session_id=session_id, level=level)},
        )
        return _to_card_response(_build_company_health(_resolve_level(session_id=session_id, level=level), ticker=ticker))


class GetScenarioInsight:
    def execute(
        self,
        *,
        session_id: str | None = None,
        level: str | None = None,
        usd_vnd_rate: float | None = None,
        sbv_interest_rate_pct: float | None = None,
    ) -> InsightCardResponse:
        emit_product_event(
            event_name="insight_scenario_opened",
            module="insights",
            surface="insights",
            session_id=session_id,
            user_id=session_id,
            properties={"level": _resolve_level(session_id=session_id, level=level)},
        )
        return _to_card_response(
            _build_scenario_context(
                _resolve_level(session_id=session_id, level=level),
                usd_vnd_rate=usd_vnd_rate,
                sbv_interest_rate_pct=sbv_interest_rate_pct,
            )
        )


def _resolve_level(*, session_id: str | None, level: str | None) -> str:
    if session_id:
        profile = SqliteOnboardingProfileRepository().get(session_id)
        if profile is not None:
            return infer_level(
                session_level=level,
                knowledge_level=profile.knowledge_level,
                persona_segment=profile.persona_segment,
            )
    return infer_level(session_level=level, knowledge_level=None, persona_segment=None)


def _build_dashboard_quality(as_of: str) -> InsightsDataQualityResponse:
    return InsightsDataQualityResponse(
        overall_freshness="fresh",
        last_updated=as_of,
        sources=[
            InsightSourceQualityResponse(
                source="market_read_model",
                last_updated=as_of,
                freshness_status="fresh",
                confidence="medium",
            ),
            InsightSourceQualityResponse(
                source="cross_asset_cache",
                last_updated=as_of,
                freshness_status="fresh",
                confidence="medium",
                fallback_used=True,
            ),
            InsightSourceQualityResponse(
                source="sector_rotation_read_model",
                last_updated=as_of,
                freshness_status="delayed",
                confidence="medium",
            ),
        ],
        fallback_used=["cross_asset_cache"],
    )


def _build_insights_safety() -> InsightsSafetyResponse:
    return InsightsSafetyResponse(
        no_buy_sell_recommendation=True,
        disclaimer="Insights là bối cảnh phân tích, không phải khuyến nghị mua/bán.",
        allowed_actions=["review_exposure", "learn_more", "open_scenario", "ask_ai", "save_insight"],
        prohibited_actions=["buy", "sell", "all_in", "short_now"],
    )


def _build_trend_radar() -> list[TrendRadarItemResponse]:
    return [
        TrendRadarItemResponse(
            theme="Rates",
            category="rates",
            status="deteriorating",
            short_summary="Lợi suất tăng nhẹ, áp lực chưa giảm.",
            sparkline_series=[42, 45, 44, 48, 53, 49, 55, 51],
            signal_strength=62,
            confidence="medium",
        ),
        TrendRadarItemResponse(
            theme="FX",
            category="fx",
            status="volatile",
            short_summary="USD duy trì mạnh, áp lực lên tiền tệ EM.",
            sparkline_series=[50, 48, 52, 46, 49, 47, 51, 50],
            signal_strength=72,
            confidence="medium",
        ),
        TrendRadarItemResponse(
            theme="Energy",
            category="commodities",
            status="volatile",
            short_summary="Dầu biến động trong biên rộng.",
            sparkline_series=[48, 52, 50, 55, 49, 47, 45, 46],
            signal_strength=54,
            confidence="medium",
        ),
        TrendRadarItemResponse(
            theme="Equity Breadth",
            category="equity",
            status="improving",
            short_summary="Độ rộng thị trường cải thiện nhẹ.",
            sparkline_series=[38, 42, 46, 51, 49, 45, 47, 50],
            signal_strength=58,
            confidence="medium",
        ),
    ]


def _build_cross_asset_pulse(*, range_key: str) -> CrossAssetPulseResponse:
    base_date = datetime(2026, 4, 21, tzinfo=timezone(timedelta(hours=7)))
    raw = {
        "vn_index": ("VN-Index", "%", [1000, 1008, 1012, 1009, 1018, 1026, 1032, 1032]),
        "usd_vnd": ("USD/VND", "%", [25400, 25430, 25410, 25470, 25520, 25510, 25560, 25552]),
        "gold": ("Gold (USD/oz)", "%", [2300, 2325, 2348, 2360, 2378, 2395, 2408, 2463]),
        "brent_oil": ("Brent Oil (USD/bbl)", "%", [86, 84, 82, 80, 79, 81, 80, 82.3]),
    }
    series: list[CrossAssetSeriesResponse] = []
    for key, (label, unit, values) in raw.items():
        start = float(values[0])
        points = [
            CrossAssetPointResponse(
                date=(base_date + timedelta(days=index * 7)).date().isoformat(),
                raw_value=float(value),
                normalized_value=round(float(value) / start * 100.0, 2),
            )
            for index, value in enumerate(values)
        ]
        latest_change = round((float(values[-1]) / start - 1.0) * 100.0, 2)
        series.append(
            CrossAssetSeriesResponse(
                asset_key=key,
                label=label,
                unit=unit,
                values=points,
                latest_change_pct=latest_change,
                freshness_status="fresh",
                confidence="medium",
            )
        )
    return CrossAssetPulseResponse(range=range_key, series=series)


def _build_scenario_monitor() -> list[ScenarioItemResponse]:
    return [
        ScenarioItemResponse(
            scenario_key="base_case",
            label="Base case",
            probability=0.60,
            impact_level="low",
            affected_themes=["liquidity", "quality"],
            summary="Tăng trưởng chậm lại, lạm phát hạ nhiệt dần.",
            assumptions=["USD không tăng sốc", "lãi suất đi ngang", "thanh khoản ổn định"],
            recommended_review="Theo dõi xác nhận từ thanh khoản và độ rộng.",
        ),
        ScenarioItemResponse(
            scenario_key="fx_stress",
            label="FX stress",
            probability=0.25,
            impact_level="medium",
            affected_themes=["USD strength", "Emerging Outflow"],
            summary="USD mạnh lên, dòng vốn rút khỏi EM.",
            assumptions=["DXY tăng", "USD/VND chịu áp lực", "khẩu vị rủi ro giảm"],
            recommended_review="Review exposure với nhóm nhạy tỷ giá.",
        ),
        ScenarioItemResponse(
            scenario_key="rate_shock",
            label="Rate shock",
            probability=0.15,
            impact_level="high",
            affected_themes=["Rates Up", "Liquidity"],
            summary="Lợi suất tăng mạnh, thanh khoản thắt chặt.",
            assumptions=["lợi suất tăng", "duration assets bị chiết khấu", "risk premium tăng"],
            recommended_review="Mở scenario để xem độ nhạy lãi suất.",
        ),
    ]


def _build_sector_rotation() -> list[SectorRotationItemResponse]:
    return [
        SectorRotationItemResponse(sector="Banking", short_term_view="tích cực", medium_term_view="trung tính", relative_strength=0.62, momentum_score=68, breadth_score=61, flow_score=None, status="positive", explanation="Ngắn hạn đang mạnh hơn VN-Index, nhưng trung hạn chưa bứt hẳn."),
        SectorRotationItemResponse(sector="Energy", short_term_view="trung tính", medium_term_view="tích cực", relative_strength=0.48, momentum_score=52, breadth_score=49, flow_score=None, status="watch", explanation="Biến động hàng hóa hỗ trợ trung hạn nhưng ngắn hạn còn nhiễu."),
        SectorRotationItemResponse(sector="Retail", short_term_view="trung tính", medium_term_view="trung tính", relative_strength=0.45, momentum_score=50, breadth_score=47, flow_score=None, status="neutral", explanation="Chưa có xác nhận rotation rõ."),
        SectorRotationItemResponse(sector="Real Estate", short_term_view="tiêu cực", medium_term_view="trung tính", relative_strength=0.34, momentum_score=38, breadth_score=35, flow_score=None, status="negative", explanation="Nhạy với lãi suất và thanh khoản, cần theo dõi rủi ro."),
    ]


def _build_macro_calendar(as_of: datetime) -> list[MacroEventResponse]:
    events = [
        ("us-cpi-may", "US CPI (MoM) - May", 2, "US", "high", ["Rates Up", "USD Strength"], "Fed/official calendar"),
        ("fed-chair-speech", "Fed Chair Powell Speech", 3, "US", "high", ["Global Risk", "Rates"], "Fed calendar"),
        ("sbv-policy-update", "SBV Policy Update", 5, "VN", "medium", ["USD/VND", "Liquidity"], "SBV/public calendar"),
    ]
    return [
        MacroEventResponse(
            event_id=event_id,
            event_name=name,
            event_time=(as_of + timedelta(days=days)).replace(hour=9, minute=30).isoformat(),
            region=region,
            impact_level=impact,
            related_themes=themes,
            time_remaining=f"{days} ngày còn lại",
            source=source,
        )
        for event_id, name, days, region, impact, themes, source in events
    ]


def _build_watchlist_impact(session_id: str | None) -> WatchlistImpactResponse:
    if not session_id:
        return WatchlistImpactResponse(
            state="empty",
            user_id=None,
            message="Thêm watchlist để xem insight nào liên quan đến tài sản bạn quan tâm.",
            cta="Create watchlist",
        )
    return WatchlistImpactResponse(
        state="ready",
        user_id=session_id,
        exposure_themes=["USD Strength", "Rates Up", "Commodity Volatility"],
        impacted_tickers=["FPT", "VCB", "HPG"],
        risk_notes=["Độ nhạy lãi suất: Trung bình", "Phơi nhiễm USD: Cao", "Chất lượng DN: Khá tốt"],
        action_suggestions=["review_exposure", "open_scenario", "learn_more"],
    )


def _build_learn_links() -> list[LearnLinkResponse]:
    return [
        LearnLinkResponse(lesson_id="risk-on-risk-off", title="Risk-on / Risk-off", concept="risk_sentiment", reason="Hiểu cách thị trường chuyển state.", difficulty="basic", estimated_minutes=6),
        LearnLinkResponse(lesson_id="fx-market-impact", title="Tỷ giá ảnh hưởng thị trường thế nào?", concept="fx_pressure", reason="USD strength là driver chính hiện tại.", difficulty="intermediate", estimated_minutes=8),
        LearnLinkResponse(lesson_id="macro-context-3min", title="Đọc bối cảnh vĩ mô trong 3 phút", concept="macro_context", reason="Tóm tắt framework đọc rates, FX và thanh khoản.", difficulty="basic", estimated_minutes=3),
    ]


def _build_market_regime(level: str) -> InsightCard:
    guided = GetGuidedMarketContext().execute()
    return build_market_regime_card(
        level=level,
        headline=guided.headline,
        summary=guided.summary,
        risk_regime=guided.risk_regime,
        decision_score_pct=guided.decision_score_pct,
        expected_drawdown_pct=guided.expected_drawdown_pct,
        freshness_at=None if guided.data_freshness == "unavailable" else guided.data_freshness,
        quality_state="fallback" if guided.data_freshness == "unavailable" else "good",
        caution=guided.caution,
        drivers=[
            InsightDriver(label=item.label, value=f"{item.share_pct:.1f}%", direction=item.direction)
            for item in guided.drivers
        ],
    )


def _build_macro_context(level: str) -> InsightCard:
    try:
        panel = get_panel().copy()
        panel["date"] = panel["date"].astype(str)
        latest = panel.sort_values("date").iloc[-1]
        return build_macro_context_card(
            level=level,
            usd_vnd_rate=float(latest["usd_vnd_rate"]) if latest.get("usd_vnd_rate") is not None else None,
            usd_vnd_1m_change_pct=(
                float(latest["usd_vnd_1m_change_pct"]) if latest.get("usd_vnd_1m_change_pct") is not None else None
            ),
            sbv_interest_rate_pct=(
                float(latest["sbv_interest_rate_pct"]) if latest.get("sbv_interest_rate_pct") is not None else None
            ),
            cpi_yoy_pct=float(latest["cpi_yoy_pct"]) if latest.get("cpi_yoy_pct") is not None else None,
            freshness_at=str(latest["date"]),
            quality_state="good",
        )
    except (PanelUnavailableError, KeyError, IndexError, TypeError, ValueError):
        return build_macro_context_card(
            level=level,
            usd_vnd_rate=None,
            usd_vnd_1m_change_pct=None,
            sbv_interest_rate_pct=None,
            cpi_yoy_pct=None,
            freshness_at=None,
            quality_state="fallback",
            fallback_reason="Hiện chưa có macro panel đủ mới để build macro context chi tiết.",
        )


def _build_cross_asset_context(level: str) -> InsightCard:
    try:
        dashboard = build_cross_asset_dashboard(limit=90)
        assets = [item for item in dashboard.get("assets", []) if item.get("status") == "ok"]
        metrics = [
            InsightMetric(
                label=item["label"],
                value=(
                    f"1w {item['change_1w_pct']:.1f}% | 1m {item['change_1m_pct']:.1f}%"
                    if item.get("change_1w_pct") is not None and item.get("change_1m_pct") is not None
                    else "No change snapshot"
                ),
            )
            for item in assets[:4]
        ]
        updated_at = next((item.get("updated_at") for item in assets if item.get("updated_at")), dashboard.get("as_of"))
        summary = " | ".join(
            [
                f"{item['label']}: {item.get('decision_hint', 'Đọc như context bổ sung.')}"
                for item in assets[:2]
            ]
        ) or "Cross-asset context giúp đọc nhanh risk-on / risk-off ngoài thị trường cổ phiếu."
        quality_state = "good" if len(assets) >= 2 else "low_confidence"
        return build_cross_asset_card(
            level=level,
            summary=summary,
            top_assets=metrics,
            freshness_at=updated_at,
            quality_state=quality_state,
            fallback_reason="Cross-asset feeds hiện chưa đủ đầy để kể câu chuyện chắc tay hơn.",
        )
    except Exception:
        return build_cross_asset_card(
            level=level,
            summary="Cross-asset context hiện tạm unavailable.",
            top_assets=[],
            freshness_at=None,
            quality_state="fallback",
            fallback_reason="Hiện chưa đọc được cross-asset cache hoặc feed.",
        )


def _build_sector_pulse(level: str) -> InsightCard:
    sector_path = Path("data/sector_panel.csv")
    if sector_path.exists():
        try:
            panel = load_sector_panel_csv(sector_path)
            latest = panel["month_end"].max().date()
            pulse = sector_winners_losers(panel, latest, window_months=6, top_k=3)
            metrics = [
                InsightMetric(label=f"Winner: {code}", value=f"{ret:.1f}%")
                for code, ret in pulse.winners[:2]
            ] + [
                InsightMetric(label=f"Loser: {code}", value=f"{ret:.1f}%")
                for code, ret in pulse.losers[:2]
            ]
            summary = (
                f"Trong cửa sổ {pulse.window_months} tháng gần nhất, nhóm thắng và thua đang tách nhau rõ hơn. "
                "Đây là tín hiệu để đọc rotation, không phải top picks."
            )
            return build_sector_pulse_card(
                level=level,
                summary=summary,
                quality_state="good",
                freshness_at=latest.isoformat(),
                metrics=metrics,
            )
        except Exception:
            pass

    return build_sector_pulse_card(
        level=level,
        summary="Sector pulse hiện chưa có panel ngành chuẩn hóa đủ tin cậy để show public như insight mặc định.",
        quality_state="fallback",
        freshness_at=None,
        metrics=[],
        fallback_reason="Chưa có sector panel chuẩn hóa; module đang ưu tiên trust hơn là đẩy mock sector lên public.",
    )


def _build_company_health(level: str, *, ticker: str) -> InsightCard:
    try:
        dataset = get_financial_dataset(ticker.upper(), refresh=False)
        guided = GetGuidedCompanyHealth().execute(ticker=ticker)
        return build_company_health_card(
            level=level,
            ticker=guided.ticker,
            headline=guided.headline,
            summary=guided.summary,
            health_band=guided.health_band,
            highlights=guided.highlights,
            flags=guided.flags,
            peer_takeaways=guided.peer_takeaways,
            freshness_at=dataset.fetched_at.date().isoformat(),
            quality_state="good",
            caution=guided.caution,
        )
    except (FinancialDataError, ValueError):
        return build_company_health_card(
            level=level,
            ticker=ticker.upper(),
            headline=f"Chưa có company insight sẵn cho {ticker.upper()} lúc này.",
            summary="Bạn vẫn có thể dùng Learn Hub hoặc Guided Investing để hiểu framework đọc doanh nghiệp trước.",
            health_band="unknown",
            highlights=[],
            flags=[],
            peer_takeaways=[],
            freshness_at=None,
            quality_state="fallback",
            caution="Company health chỉ nên được hiển thị khi dataset đủ tin cậy và có thể giải thích được.",
            fallback_reason="Chưa có financial dataset cache hoặc live fetch phù hợp cho ticker này.",
        )


def _build_scenario_context(
    level: str,
    *,
    usd_vnd_rate: float | None = None,
    sbv_interest_rate_pct: float | None = None,
) -> InsightCard:
    guided = GetGuidedMarketContext().execute(
        usd_vnd_rate=usd_vnd_rate,
        sbv_interest_rate_pct=sbv_interest_rate_pct,
    )
    return build_scenario_card(
        level=level,
        headline="Scenario what-if giúp bạn nhìn độ nhạy trước khi nhìn kết luận.",
        summary=guided.summary,
        scenario_note=guided.scenario_note,
        decision_score_pct=guided.decision_score_pct,
        expected_drawdown_pct=guided.expected_drawdown_pct,
        freshness_at=None if guided.data_freshness == "unavailable" else guided.data_freshness,
        quality_state="fallback" if guided.data_freshness == "unavailable" else "good",
        caution="Scenario chỉ để hiểu độ nhạy của bối cảnh; không phải dự báo chắc chắn.",
        drivers=[
            InsightDriver(label=item.label, value=f"{item.share_pct:.1f}%", direction=item.direction)
            for item in guided.drivers
        ],
    )


def _build_explainability(level: str) -> InsightCard:
    try:
        panel = get_panel()
        as_of = panel["date"].max()
        as_of_date = as_of.date() if hasattr(as_of, "date") else as_of
        quant = run_quant_eod(panel, as_of_date)
        drivers = [
            InsightDriver(
                label=_humanize_feature(item.feature_name),
                value=f"{item.share * 100:.1f}%",
                direction=item.direction,
            )
            for item in quant.shap_top[:3]
        ]
        return build_explainability_card(
            level=level,
            freshness_at=str(as_of_date),
            quality_state="good",
            drivers=drivers,
            dominant_feature=_humanize_feature(quant.dominant_feature),
        )
    except Exception:
        return build_explainability_card(
            level=level,
            freshness_at=None,
            quality_state="fallback",
            drivers=[],
            dominant_feature="unknown",
            fallback_reason="Chưa có top drivers đủ tin cậy để giải thích risk score lúc này.",
        )


def _humanize_feature(name: str) -> str:
    return (
        str(name)
        .replace("_", " ")
        .replace("pct", "%")
        .replace("sbv", "SBV")
        .replace("usd vnd", "USD/VND")
        .title()
    )


def _to_card_response(card: InsightCard) -> InsightCardResponse:
    runtime_reader = ContentOpsRuntimeReader()
    disclaimer = runtime_reader.get_disclaimer(surface="insights", topic=card.insight_id)
    trust = TrustSafetyService()
    presentation = trust.build_presentation(
        surface="insights",
        topic=card.insight_id,
        quality_state=card.quality_state,
        freshness_value=card.freshness_at or card.freshness_status,
        disclaimer=disclaimer,
        existing_banner=card.risk_banner,
    )
    contextual_explainer = runtime_reader.get_contextual_explainer(
        surface="insights",
        trigger_key=card.insight_id,
    )
    trust.record_audit(
        actor_id=None,
        surface="insights",
        topic=card.insight_id,
        channel="runtime_card",
        risk_classes=tuple(
            label
            for label in (
                "stale_data_risk" if presentation.freshness_status in {"stale", "unavailable"} else "",
                "missing_disclaimer" if presentation.disclaimer_injected else "",
            )
            if label
        ),
        route_decision="served_runtime_card",
        output_summary=card.headline,
        disclaimer_injected=presentation.disclaimer_injected,
        freshness_status=presentation.freshness_status,
        confidence_label=presentation.confidence_label,
    )
    emit_product_event(
        event_name="insight_card_opened",
        module="insights",
        surface="insights",
        properties={
            "insight_id": card.insight_id,
            "level": card.level,
            "freshness_status": presentation.freshness_status,
            "quality_state": card.quality_state,
            "confidence_label": presentation.confidence_label,
        },
    )
    emit_ops_event(
        event_name="ops_data_refresh_logged",
        module="insights",
        surface="insights",
        properties={
            "source": card.insight_id,
            "freshness_status": presentation.freshness_status,
            "quality_state": card.quality_state,
        },
    )
    return InsightCardResponse(
        insight_id=card.insight_id,
        title=card.title,
        level=card.level,
        headline=card.headline,
        summary=card.summary,
        what_changed=card.what_changed,
        why_it_matters=card.why_it_matters,
        who_should_care=card.who_should_care,
        what_to_learn_next=card.what_to_learn_next,
        action_category=card.action_category,
        action_path=card.action_path,
        caution=card.caution,
        freshness_status=presentation.freshness_status,
        freshness_at=card.freshness_at,
        quality_state=card.quality_state,
        confidence_label=presentation.confidence_label,
        risk_banner=presentation.risk_banner,
        what_this_is=presentation.what_this_is,
        what_this_is_not=presentation.what_this_is_not,
        metrics=[InsightMetricResponse(label=item.label, value=item.value) for item in card.metrics],
        drivers=[
            InsightDriverResponse(label=item.label, value=item.value, direction=item.direction)
            for item in card.drivers
        ],
        disclaimer=(
            InsightDisclaimerResponse(
                title=presentation.disclaimer.title,
                short_text=presentation.disclaimer.short_text,
                full_text=presentation.disclaimer.full_text,
                severity=presentation.disclaimer.severity,
            )
            if presentation.disclaimer is not None
            else None
        ),
        contextual_explainer=(
            InsightContextualExplainerResponse(
                explainer_id=contextual_explainer.explainer_id,
                title=contextual_explainer.title,
                body=contextual_explainer.body,
                linked_lesson_ids=contextual_explainer.linked_lesson_ids,
                guardrail_note=contextual_explainer.guardrail_note,
            )
            if contextual_explainer is not None
            else None
        ),
    )
