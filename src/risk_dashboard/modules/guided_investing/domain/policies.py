from __future__ import annotations

from collections import Counter

from risk_dashboard.modules.guided_investing.domain.entities import (
    GuidedCompanyHealth,
    GuidedEligibility,
    GuidedMarketContext,
    GuidedMarketDriver,
    GuidedPortfolioReview,
    GuidedSafeReply,
    GuidedWatchlistFlag,
    GuidedWatchlistItem,
    GuidedWatchlistReview,
)
from risk_dashboard.schemas.financials import FinancialAnalysisResponse


def build_guided_eligibility(
    *,
    persona_segment: str,
    onboarding_eligible: bool,
    financial_health_eligible: bool,
    completed_lessons: int,
) -> GuidedEligibility:
    reasons: list[str] = []
    if persona_segment not in {"beginner_investor", "advanced_pro", "household_manager"}:
        reasons.append("Hành trình hiện tại của bạn vẫn nên đi từ Financial Health và Learn trước.")
    if not onboarding_eligible:
        reasons.append("Bạn chưa mở Guided Investing từ onboarding path.")
    if not financial_health_eligible:
        reasons.append("Financial Health của bạn chưa đủ ổn để đi sâu hơn vào investing.")
    if completed_lessons < 2:
        reasons.append("Bạn nên hoàn thành ít nhất 2 bài nền tảng về investing và risk trước.")

    if reasons:
        return GuidedEligibility(
            eligible=False,
            reasons=reasons,
            next_step_title="Hoàn thành nền tảng trước",
            next_step_path="/learn",
            caution="Guided Investing là lớp giải thích rủi ro, không phải tín hiệu mua bán.",
        )

    return GuidedEligibility(
        eligible=True,
        reasons=["Bạn đã có đủ nền tảng cơ bản để dùng Guided Investing Lite."],
        next_step_title="Mở Guided Investing Home",
        next_step_path="/guided-investing",
        caution="Hãy dùng module này để hiểu bối cảnh và rủi ro, không để tìm chắc chắn ngắn hạn.",
    )


def build_market_context(
    *,
    risk_regime: str,
    decision_score_pct: float,
    expected_drawdown_pct: float,
    drivers: list[GuidedMarketDriver],
    data_freshness: str,
    scenario_note: str | None = None,
) -> GuidedMarketContext:
    if decision_score_pct >= 75:
        headline = "Môi trường hiện nghiêng về phòng thủ hơn là vội vàng tăng rủi ro."
        so_what = "Nếu bạn là người mới, đây là lúc hiểu drawdown và pace của mình trước khi mở rộng vị thế."
        now_what = "Rà soát watchlist, học thêm Risk Basics, và tránh đọc score như một lệnh hành động."
    elif decision_score_pct >= 55:
        headline = "Rủi ro thị trường đang ở mức cần chú ý, nhưng chưa phải tín hiệu chắc chắn."
        so_what = "Biến động có thể cao hơn bình thường, nên cách bạn phản ứng quan trọng hơn việc đoán đúng ngắn hạn."
        now_what = "Dùng watchlist hygiene và scenario explainer để hiểu mình nhạy với điều gì."
    else:
        headline = "Môi trường hiện tương đối ổn định hơn, nhưng không có nghĩa rủi ro biến mất."
        so_what = "Đây là lúc tốt để học cách đọc company health và diversification đúng cách."
        now_what = "Tiếp tục xây watchlist gọn, thêm thesis, và giữ kỷ luật quan sát."

    return GuidedMarketContext(
        risk_regime=risk_regime,
        decision_score_pct=decision_score_pct,
        expected_drawdown_pct=expected_drawdown_pct,
        headline=headline,
        summary=(
            f"Decision score hiện ở mức {decision_score_pct:.1f}%, regime = {risk_regime}. "
            f"Expected drawdown ngắn hạn khoảng {expected_drawdown_pct:.1f}%."
        ),
        so_what=so_what,
        now_what=now_what,
        caution="Đây là lớp giải thích bối cảnh rủi ro, không phải dự báo chắc chắn hay khuyến nghị giao dịch.",
        data_freshness=data_freshness,
        drivers=drivers[:3],
        scenario_note=scenario_note,
    )


def build_watchlist_review(items: list[GuidedWatchlistItem]) -> GuidedWatchlistReview:
    item_count = len(items)
    with_reason = sum(1 for item in items if item.reason_to_track.strip())
    thesis_coverage_pct = round((with_reason / item_count) * 100) if item_count else 0
    theme_counter = Counter((item.theme_tag or "untagged") for item in items)
    top_theme_count = theme_counter.most_common(1)[0][1] if theme_counter else 0
    theme_ratio = (top_theme_count / item_count) if item_count else 0.0

    flags: list[GuidedWatchlistFlag] = []
    next_actions: list[str] = []

    if item_count == 0:
        flags.append(
            GuidedWatchlistFlag(
                code="empty_watchlist",
                title="Watchlist của bạn còn trống.",
                detail="Bắt đầu với 3-5 mã bạn thực sự muốn học và theo dõi.",
            )
        )
        next_actions.append("Thêm 3 mã đầu tiên với lý do theo dõi ngắn gọn.")

    if item_count > 8:
        flags.append(
            GuidedWatchlistFlag(
                code="too_many_items",
                title="Watchlist hiện hơi dài với người mới.",
                detail="Quá nhiều mã làm bạn khó theo dõi và dễ chuyển sang đọc tin thay vì hiểu doanh nghiệp.",
            )
        )
        next_actions.append("Rút watchlist về 5-8 mã trọng tâm.")

    if thesis_coverage_pct < 100 and item_count > 0:
        flags.append(
            GuidedWatchlistFlag(
                code="missing_thesis",
                title="Một số mã chưa có lý do theo dõi rõ.",
                detail="Không có thesis khiến watchlist dễ biến thành nơi lưu mã nóng thay vì công cụ học.",
            )
        )
        next_actions.append("Bổ sung 1 câu lý do theo dõi cho từng mã.")

    if theme_ratio >= 0.6 and item_count >= 3:
        flags.append(
            GuidedWatchlistFlag(
                code="theme_concentration",
                title="Watchlist đang dồn khá nhiều vào một theme.",
                detail="Điều này không sai, nhưng dễ làm góc nhìn của bạn bị lệch nếu chỉ nhìn một câu chuyện.",
            )
        )
        next_actions.append("Thêm 1-2 mã ở nhóm ngành khác để cân góc nhìn.")

    score = 80
    score -= max(item_count - 5, 0) * 5
    score -= 20 if thesis_coverage_pct < 100 else 0
    score -= 15 if theme_ratio >= 0.6 and item_count >= 3 else 0
    score = max(25, min(score, 100))

    if theme_ratio >= 0.6:
        theme_band = "high"
    elif theme_ratio >= 0.4:
        theme_band = "medium"
    else:
        theme_band = "low"

    if not next_actions:
        next_actions = [
            "Giữ watchlist gọn và tiếp tục thêm journal cho các mã quan trọng.",
            "Mở Company Health của 1 mã để đào sâu hơn thay vì thêm mã mới.",
        ]

    return GuidedWatchlistReview(
        item_count=item_count,
        thesis_coverage_pct=thesis_coverage_pct,
        theme_concentration_band=theme_band,
        watchlist_hygiene_score=score,
        flags=flags,
        next_actions=next_actions[:3],
    )


def build_company_health(
    *,
    analysis: FinancialAnalysisResponse,
    peer_result: dict,
) -> GuidedCompanyHealth:
    radar = analysis.health_radar
    avg_score = (
        radar.profitability
        + radar.growth
        + radar.efficiency
        + radar.liquidity
        + radar.leverage
        + radar.cash_quality
    ) / 6

    if avg_score >= 70:
        health_band = "healthy"
        headline = "Doanh nghiệp đang cho thấy nền tảng tương đối khỏe."
        so_what = "Điều này giúp bạn hiểu tại sao công ty đáng để theo dõi tiếp, nhưng không nói gì chắc chắn về giá ngắn hạn."
    elif avg_score >= 50:
        health_band = "mixed"
        headline = "Doanh nghiệp có điểm tốt nhưng chưa thật sự đồng đều."
        so_what = "Bạn nên nhìn kỹ các điểm yếu kéo chất lượng xuống trước khi hình thành góc nhìn chắc hơn."
    else:
        health_band = "fragile"
        headline = "Doanh nghiệp đang có một số dấu hiệu cần thận trọng hơn."
        so_what = "Đây là lúc đọc kỹ rủi ro kinh doanh và bảng cân đối trước khi gắn kỳ vọng lớn."

    peer_takeaways = []
    for metric in peer_result.get("metrics", [])[:3]:
        if metric.get("ticker_value") is None or metric.get("peer_avg") is None:
            continue
        peer_takeaways.append(
            f"{metric['label']}: {analysis.ticker} = {metric['ticker_value']}, peer avg = {metric['peer_avg']}."
        )

    return GuidedCompanyHealth(
        ticker=analysis.ticker,
        company_name=analysis.company_name,
        industry=analysis.industry,
        health_band=health_band,
        headline=headline,
        summary=" ".join(analysis.highlights[:3]) or analysis.provider_notes[0] if analysis.provider_notes else analysis.ticker,
        so_what=so_what,
        now_what="Đọc 1-2 flag chính, so với peers, rồi ghi lại thesis học được vào journal thay vì nhảy sang quyết định mua bán.",
        caution="Company health giúp bạn hiểu doanh nghiệp, không phải xác nhận cổ phiếu chắc chắn sẽ tăng.",
        highlights=analysis.highlights[:4],
        flags=[flag.title for flag in analysis.flags[:4]],
        peer_takeaways=peer_takeaways[:3],
    )


def build_portfolio_review(holdings: list[dict[str, float]]) -> GuidedPortfolioReview:
    if not holdings:
        return GuidedPortfolioReview(
            concentration_band="unknown",
            top_holding_pct=0.0,
            concentration_score=0,
            warnings=["Bạn chưa nhập holdings để hệ thống giải thích concentration risk."],
            next_actions=["Nhập 3-5 khoản nắm giữ gần đúng để xem portfolio hygiene."],
        )

    total_weight = sum(max(float(item.get("weight_pct", 0.0)), 0.0) for item in holdings)
    normalized = [
        {"ticker": str(item.get("ticker", "")).upper(), "weight_pct": (float(item.get("weight_pct", 0.0)) / total_weight) * 100}
        for item in holdings
        if item.get("ticker")
    ] if total_weight > 0 else []
    top_holding = max((item["weight_pct"] for item in normalized), default=0.0)

    warnings: list[str] = []
    next_actions: list[str] = []
    if top_holding >= 50:
        band = "very_high"
        score = 25
        warnings.append("Danh mục đang dồn quá mạnh vào một mã hoặc một ý tưởng lớn.")
        next_actions.append("Xem lại diversification basics trước khi tăng thêm cam kết.")
    elif top_holding >= 30:
        band = "high"
        score = 45
        warnings.append("Mức tập trung hiện khá cao với một nhà đầu tư retail mới.")
        next_actions.append("Soát lại lý do vì sao bạn chấp nhận mức tập trung này.")
    elif top_holding >= 20:
        band = "medium"
        score = 65
        warnings.append("Danh mục có một trọng tâm rõ, cần theo dõi rủi ro kéo theo.")
        next_actions.append("Theo dõi scenario và company health của mã lớn nhất.")
    else:
        band = "balanced"
        score = 80
        warnings.append("Mức tập trung hiện tương đối cân hơn với người mới.")
        next_actions.append("Giữ kỷ luật journal và tránh thêm vị thế chỉ vì tin nóng.")

    if len(normalized) < 3:
        warnings.append("Danh mục còn ít vị thế, nên đọc kỹ rủi ro doanh nghiệp riêng lẻ.")
        next_actions.append("Học thêm Diversification Basics trước khi mở rộng danh mục.")

    return GuidedPortfolioReview(
        concentration_band=band,
        top_holding_pct=round(top_holding, 1),
        concentration_score=score,
        warnings=warnings[:3],
        next_actions=next_actions[:3],
    )


def build_safe_reply(*, prompt: str, eligible: bool) -> GuidedSafeReply:
    lowered = prompt.strip().lower()
    unsafe_markers = ("mua", "ban", "top pick", "pick", "ma nao", "chac tang", "entry", "exit")
    if any(marker in lowered for marker in unsafe_markers):
        return GuidedSafeReply(
            allowed=False,
            headline="Public mode không đưa khuyến nghị mua bán trực tiếp.",
            message=(
                "Mình có thể giúp bạn hiểu market context, company health, concentration risk "
                "hoặc cách đọc watchlist an toàn hơn."
            ),
            suggested_path="/guided-investing",
            linked_lesson_id="tool-risk-score-101",
        )

    if not eligible:
        return GuidedSafeReply(
            allowed=False,
            headline="Bạn nên hoàn thành phần nền tảng trước.",
            message="Hãy quay lại Learn Hub và Financial Health trước khi dùng Guided Investing sâu hơn.",
            suggested_path="/learn",
            linked_lesson_id="risk-basics-101",
        )

    return GuidedSafeReply(
        allowed=True,
        headline="Bạn đang ở public-safe guided mode.",
        message="Hãy dùng module này để hiểu rủi ro, company health và watchlist discipline, không tìm tín hiệu chắc chắn.",
        suggested_path="/guided-investing",
        linked_lesson_id="drawdown-basics-101",
    )
