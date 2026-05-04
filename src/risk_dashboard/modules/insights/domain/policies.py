from __future__ import annotations

from datetime import date

from risk_dashboard.modules.insights.domain.entities import InsightCard, InsightDriver, InsightMetric


def infer_level(*, session_level: str | None, knowledge_level: str | None, persona_segment: str | None) -> str:
    if session_level in {"basic", "intermediate", "pro"}:
        return session_level
    if knowledge_level == "advanced" or persona_segment == "advanced_pro":
        return "pro"
    if knowledge_level in {"basic", "intermediate"} or persona_segment == "beginner_investor":
        return "intermediate"
    return "basic"


def freshness_status_from_date(value: str | None) -> str:
    if not value:
        return "unavailable"
    try:
        as_of = date.fromisoformat(value)
    except ValueError:
        return "unavailable"
    age_days = (date.today() - as_of).days
    if age_days <= 2:
        return "fresh"
    if age_days <= 7:
        return "delayed"
    return "stale"


def quality_banner(*, freshness_status: str, quality_state: str, fallback_reason: str | None = None) -> str | None:
    if quality_state == "fallback":
        return fallback_reason or "Insight này đang ở chế độ fallback giáo dục vì dữ liệu hoặc model chưa sẵn."
    if freshness_status == "stale":
        return "Dữ liệu đang cũ hơn kỳ vọng. Hãy đọc insight này như bối cảnh tham khảo, không phải trạng thái mới nhất."
    if freshness_status == "delayed":
        return "Dữ liệu đầu vào hơi trễ so với nhịp cập nhật thường lệ."
    if quality_state == "low_confidence":
        return "Một số tín hiệu hiện chưa đủ mạnh hoặc nhất quán. Nên dùng insight này để học bối cảnh hơn là kết luận quá tay."
    return None


def _level_text(*, level: str, basic: str, intermediate: str, pro: str) -> str:
    mapping = {
        "basic": basic,
        "intermediate": intermediate,
        "pro": pro,
    }
    return mapping.get(level, basic)


def _trim_metrics(level: str, metrics: list[InsightMetric]) -> list[InsightMetric]:
    if level == "basic":
        return metrics[:2]
    if level == "intermediate":
        return metrics[:4]
    return metrics


def _trim_drivers(level: str, drivers: list[InsightDriver]) -> list[InsightDriver]:
    if level == "basic":
        return drivers[:2]
    return drivers[:3]


def build_insight_card(
    *,
    insight_id: str,
    title: str,
    level: str,
    headline: str,
    summary: str,
    what_changed: str,
    why_it_matters: str,
    who_should_care: str,
    what_to_learn_next: str,
    action_category: str,
    action_path: str | None,
    caution: str,
    freshness_at: str | None,
    quality_state: str,
    metrics: list[InsightMetric] | None = None,
    drivers: list[InsightDriver] | None = None,
    fallback_reason: str | None = None,
) -> InsightCard:
    freshness_status = freshness_status_from_date(freshness_at)
    return InsightCard(
        insight_id=insight_id,
        title=title,
        level=level,
        headline=headline,
        summary=summary,
        what_changed=what_changed,
        why_it_matters=why_it_matters,
        who_should_care=who_should_care,
        what_to_learn_next=what_to_learn_next,
        action_category=action_category,
        action_path=action_path,
        caution=caution,
        freshness_status=freshness_status,
        freshness_at=freshness_at,
        quality_state=quality_state,
        risk_banner=quality_banner(
            freshness_status=freshness_status,
            quality_state=quality_state,
            fallback_reason=fallback_reason,
        ),
        metrics=_trim_metrics(level, metrics or []),
        drivers=_trim_drivers(level, drivers or []),
    )


def build_market_regime_card(
    *,
    level: str,
    headline: str,
    summary: str,
    risk_regime: str,
    decision_score_pct: float,
    expected_drawdown_pct: float,
    freshness_at: str | None,
    quality_state: str,
    caution: str,
    drivers: list[InsightDriver],
) -> InsightCard:
    return build_insight_card(
        insight_id="market_regime_snapshot",
        title="Market Regime Snapshot",
        level=level,
        headline=headline,
        summary=summary,
        what_changed=_level_text(
            level=level,
            basic=f"Risk regime hiện là {risk_regime} với decision score khoảng {decision_score_pct:.1f}%.",
            intermediate=(
                f"Risk regime đang ở {risk_regime}; decision score khoảng {decision_score_pct:.1f}% "
                f"và expected drawdown ngắn hạn khoảng {expected_drawdown_pct:.1f}%."
            ),
            pro=(
                f"Decision score {decision_score_pct:.1f}% với risk regime = {risk_regime}; "
                f"expected drawdown 2w khoảng {expected_drawdown_pct:.1f}%."
            ),
        ),
        why_it_matters=_level_text(
            level=level,
            basic="Điều này giúp bạn hiểu môi trường hiện thiên về quan sát cẩn trọng hay có thể học sâu hơn về doanh nghiệp.",
            intermediate="Mức regime này ảnh hưởng đến cách bạn đọc biến động, drawdown và concentration risk của watchlist.",
            pro="Regime hiện tại là context để đọc concentration, beta và sensitivity của thesis chứ không phải tín hiệu giao dịch.",
        ),
        who_should_care="Người mới bắt đầu đầu tư, người có watchlist, và người đang theo dõi rủi ro danh mục.",
        what_to_learn_next=_level_text(
            level=level,
            basic="Risk Basics và Drawdown Basics.",
            intermediate="Risk Score Literacy và Drawdown Basics.",
            pro="Scenario literacy và portfolio hygiene.",
        ),
        action_category="review_market_context",
        action_path="/guided-investing?card=market_context",
        caution=caution,
        freshness_at=freshness_at,
        quality_state=quality_state,
        metrics=[
            InsightMetric(label="Risk regime", value=risk_regime),
            InsightMetric(label="Decision score", value=f"{decision_score_pct:.1f}%"),
            InsightMetric(label="Expected drawdown", value=f"{expected_drawdown_pct:.1f}%"),
        ],
        drivers=drivers,
    )


def build_macro_context_card(
    *,
    level: str,
    usd_vnd_rate: float | None,
    usd_vnd_1m_change_pct: float | None,
    sbv_interest_rate_pct: float | None,
    cpi_yoy_pct: float | None,
    freshness_at: str | None,
    quality_state: str,
    fallback_reason: str | None = None,
) -> InsightCard:
    usd_vnd_text = f"{usd_vnd_rate:.0f}" if usd_vnd_rate is not None else "N/A"
    usd_vnd_change_text = f"{usd_vnd_1m_change_pct:.1f}%" if usd_vnd_1m_change_pct is not None else "N/A"
    sbv_rate_text = f"{sbv_interest_rate_pct:.2f}%" if sbv_interest_rate_pct is not None else "N/A"
    cpi_text = f"{cpi_yoy_pct:.1f}%" if cpi_yoy_pct is not None else "N/A"
    return build_insight_card(
        insight_id="macro_context",
        title="Macro Context",
        level=level,
        headline=_level_text(
            level=level,
            basic="Môi trường vĩ mô nên được đọc như nền của rủi ro, không phải tín hiệu hành động nhanh.",
            intermediate="Tỷ giá và lãi suất đang là hai biến cần chú ý khi đọc risk context.",
            pro="Macro context hiện xoay quanh tỷ giá, lãi suất và độ bền của thanh khoản.",
        ),
        summary=_level_text(
            level=level,
            basic="Hãy xem tỷ giá, lãi suất và lạm phát như những biến giúp giải thích vì sao thị trường nhạy hơn hoặc ổn hơn.",
            intermediate="Khi USD/VND và lãi suất thay đổi, market regime và scenario sensitivity thường đổi theo.",
            pro="Macro variables không quyết định mọi thứ, nhưng chúng giải thích phần lớn sự thay đổi trong market risk context ngắn hạn.",
        ),
            what_changed=_level_text(
                level=level,
                basic="Tỷ giá, lãi suất và lạm phát là ba biến nền bạn nên theo dõi trước khi cố đoán giá.",
                intermediate=(
                f"USD/VND khoảng {usd_vnd_text}; biến động 1 tháng {usd_vnd_change_text}. "
                f"Lãi suất SBV khoảng {sbv_rate_text}."
                ),
                pro=(
                f"USD/VND={usd_vnd_text} | 1m change={usd_vnd_change_text} | "
                f"SBV rate={sbv_rate_text} | CPI YoY={cpi_text}."
                ),
            ),
        why_it_matters="Những biến này giúp bạn hiểu market regime đổi vì bối cảnh gì, thay vì chỉ nhìn chart và phản ứng cảm tính.",
        who_should_care="Người theo dõi thị trường Việt Nam, người có goal dài hạn, người muốn hiểu scenario risk.",
        what_to_learn_next="FX Basics, Inflation Basics, và Scenario Thinking Basics.",
        action_category="learn",
        action_path="/learn",
        caution="Macro context giúp bạn hiểu nền rủi ro, không phải dự báo chính xác thị trường sẽ đi đâu.",
        freshness_at=freshness_at,
        quality_state=quality_state,
        metrics=[
            InsightMetric(label="USD/VND", value=usd_vnd_text),
            InsightMetric(label="USD/VND 1m change", value=usd_vnd_change_text),
            InsightMetric(label="SBV interest rate", value=sbv_rate_text),
            InsightMetric(label="CPI YoY", value=cpi_text),
        ],
        fallback_reason=fallback_reason,
    )


def build_cross_asset_card(
    *,
    level: str,
    summary: str,
    top_assets: list[InsightMetric],
    freshness_at: str | None,
    quality_state: str,
    fallback_reason: str | None = None,
) -> InsightCard:
    return build_insight_card(
        insight_id="cross_asset_context",
        title="Cross-Asset Context",
        level=level,
        headline="Cross-asset giúp bạn đọc nhiệt độ risk-on / risk-off rộng hơn thị trường cổ phiếu.",
        summary=summary,
        what_changed=_level_text(
            level=level,
            basic="Nhìn thêm vàng và crypto giúp bạn đỡ bị kẹt trong một màn hình chart.",
            intermediate="Nếu tài sản trú ẩn mạnh lên còn crypto yếu đi, nên đọc đó như tín hiệu thận trọng về khẩu vị rủi ro.",
            pro="Cross-asset context bổ sung cho market regime bằng tín hiệu trú ẩn, beta toàn cầu và độ rộng của risk appetite.",
        ),
        why_it_matters="Nó giúp bạn hiểu môi trường đang thiên về phòng thủ hay mở rộng rủi ro, mà không cần biến thành hot take.",
        who_should_care="Người đang học market context, người có watchlist tập trung, người theo dõi scenario.",
        what_to_learn_next="Cross-asset Basics và Risk-on / Risk-off explainer.",
        action_category="pause_and_observe",
        action_path="/guided-investing?card=market_context",
        caution="Cross-asset context chỉ là lớp bối cảnh, không phải tín hiệu giao dịch tức thời.",
        freshness_at=freshness_at,
        quality_state=quality_state,
        metrics=top_assets,
        fallback_reason=fallback_reason,
    )


def build_sector_pulse_card(
    *,
    level: str,
    summary: str,
    quality_state: str,
    freshness_at: str | None,
    metrics: list[InsightMetric],
    fallback_reason: str | None = None,
) -> InsightCard:
    return build_insight_card(
        insight_id="sector_pulse",
        title="Sector Pulse",
        level=level,
        headline=_level_text(
            level=level,
            basic="Sector pulse nên được đọc như sự đổi động lực giữa các nhóm ngành, không phải bảng xếp hạng để nhảy vào ngay.",
            intermediate="Nhóm ngành mạnh hay yếu nói lên câu chuyện bối cảnh, chứ không đủ để kết luận cổ phiếu nào đáng mua.",
            pro="Sector pulse là lớp context cho rotation và sensitivity, không phải top picks engine.",
        ),
        summary=summary,
        what_changed="Khi có panel ngành chuẩn, bạn sẽ thấy nhóm nào đang dẫn và nhóm nào đang hụt hơi trong cửa sổ gần nhất.",
        why_it_matters="Nó giúp bạn hiểu một company thesis đang đi cùng hay đi ngược câu chuyện ngành.",
        who_should_care="Người đang học company analysis, người theo dõi watchlist theo theme/ngành.",
        what_to_learn_next="Sector basics, peer comparison literacy và company health literacy.",
        action_category="review_watchlist",
        action_path="/guided-investing?card=watchlist",
        caution="Không nên đọc sector pulse như lời gọi ý chase theo nhóm nóng.",
        freshness_at=freshness_at,
        quality_state=quality_state,
        metrics=metrics,
        fallback_reason=fallback_reason,
    )


def build_company_health_card(
    *,
    level: str,
    ticker: str,
    headline: str,
    summary: str,
    health_band: str,
    highlights: list[str],
    flags: list[str],
    peer_takeaways: list[str],
    freshness_at: str | None,
    quality_state: str,
    caution: str,
    fallback_reason: str | None = None,
) -> InsightCard:
    return build_insight_card(
        insight_id="company_health_insight",
        title=f"Company Health: {ticker}",
        level=level,
        headline=headline,
        summary=summary,
        what_changed=_level_text(
            level=level,
            basic=f"Company health hiện được xếp vào nhóm {health_band}.",
            intermediate="Điểm mạnh/yếu hiện tại được tổng hợp từ profitability, growth, liquidity, leverage và cash quality.",
            pro="Company insight đang gom health band, operational quality và peer context vào một câu chuyện dễ đọc hơn cho public mode.",
        ),
        why_it_matters="Bạn cần hiểu chất lượng doanh nghiệp trước khi nhìn quá nhiều vào biến động giá.",
        who_should_care="Người đang xây watchlist, người mới học đọc doanh nghiệp, người muốn peer comparison mang tính giáo dục.",
        what_to_learn_next="Company Health literacy, peer comparison basics và cash flow basics.",
        action_category="review_watchlist",
        action_path="/guided-investing?card=company_health",
        caution=caution,
        freshness_at=freshness_at,
        quality_state=quality_state,
        metrics=[
            InsightMetric(label="Health band", value=health_band),
            InsightMetric(label="Highlights", value=str(len(highlights))),
            InsightMetric(label="Flags", value=str(len(flags))),
            InsightMetric(label="Peer takeaways", value=str(len(peer_takeaways))),
        ],
        drivers=[InsightDriver(label=item, value="highlight") for item in highlights[:3]],
        fallback_reason=fallback_reason,
    )


def build_scenario_card(
    *,
    level: str,
    headline: str,
    summary: str,
    scenario_note: str | None,
    decision_score_pct: float,
    expected_drawdown_pct: float,
    freshness_at: str | None,
    quality_state: str,
    caution: str,
    drivers: list[InsightDriver],
) -> InsightCard:
    return build_insight_card(
        insight_id="scenario_what_if",
        title="Scenario What-if",
        level=level,
        headline=headline,
        summary=summary,
        what_changed=scenario_note or "Scenario hiện chưa tạo thay đổi đủ lớn để kể thành một câu chuyện mới.",
        why_it_matters="Kịch bản giúp bạn hiểu độ nhạy, thay vì buộc mình phải tin vào một dự báo duy nhất.",
        who_should_care="Người có watchlist, người đang cân nhắc concentration risk, người muốn hiểu sensitivity với tỷ giá/lãi suất.",
        what_to_learn_next="Scenario Thinking Basics và Portfolio Hygiene.",
        action_category="review_concentration",
        action_path="/guided-investing?card=portfolio_review",
        caution=caution,
        freshness_at=freshness_at,
        quality_state=quality_state,
        metrics=[
            InsightMetric(label="Scenario score", value=f"{decision_score_pct:.1f}%"),
            InsightMetric(label="Scenario drawdown", value=f"{expected_drawdown_pct:.1f}%"),
        ],
        drivers=drivers,
    )


def build_explainability_card(
    *,
    level: str,
    freshness_at: str | None,
    quality_state: str,
    drivers: list[InsightDriver],
    dominant_feature: str,
    fallback_reason: str | None = None,
) -> InsightCard:
    return build_insight_card(
        insight_id="top_drivers",
        title="Explainability / Top Drivers",
        level=level,
        headline="Top drivers giúp bạn hiểu điều gì đang kéo rủi ro lên hoặc hạ xuống.",
        summary="Thay vì chỉ nhìn score, hãy nhìn 2-3 yếu tố chính đằng sau score đó.",
        what_changed=_level_text(
            level=level,
            basic=f"Yếu tố đang nổi bật nhất hiện tại là {dominant_feature}.",
            intermediate=f"Driver chi phối hiện tại là {dominant_feature}; các driver còn lại giúp giải thích mức độ nhạy của risk score.",
            pro=f"Dominant feature hiện là {dominant_feature}; phần còn lại của shap contributions cho thấy hướng thay đổi của risk context.",
        ),
        why_it_matters="Explainability tăng trust vì bạn không phải tin vào một con số đen hộp.",
        who_should_care="Người muốn hiểu logic của score, không muốn đọc output như black box.",
        what_to_learn_next="Risk Score literacy và explainability basics.",
        action_category="learn",
        action_path="/learn",
        caution="Top drivers giải thích score hiện tại, không đảm bảo driver đó sẽ tiếp tục chi phối trong tương lai.",
        freshness_at=freshness_at,
        quality_state=quality_state,
        drivers=drivers,
        fallback_reason=fallback_reason,
    )
