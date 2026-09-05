"""Baseline regression tests for legacy guided_investing module.
Captures current behavior WITHOUT HTTP (router unmounted / disabled).
Serves as behavioral contract that must not regress before reactivation.
"""
from __future__ import annotations

import pytest

from risk_dashboard.modules.guided_investing.domain.entities import (
    GuidedEligibility,
    GuidedMarketContext,
    GuidedMarketDriver,
    GuidedPortfolioReview,
    GuidedSafeReply,
    GuidedWatchlistItem,
    GuidedWatchlistReview,
)
from risk_dashboard.modules.guided_investing.domain.policies import (
    build_guided_eligibility,
    build_market_context,
    build_portfolio_review,
    build_safe_reply,
    build_watchlist_review,
)
from risk_dashboard.modules.guided_investing.schemas.requests import (
    GuidedJournalCreateRequest,
    GuidedPortfolioHoldingRequest,
    GuidedPortfolioReviewRequest,
    GuidedSafeChatRequest,
    GuidedSavePortfolioRequest,
    GuidedWatchlistItemCreateRequest,
)
from risk_dashboard.modules.guided_investing.schemas.responses import (
    GuidedEligibilityResponse,
    GuidedMarketContextResponse,
    GuidedPortfolioReviewResponse,
    GuidedSafeReplyResponse,
    GuidedWatchlistItemResponse,
)


class TestGuidedInvestingBaseline:
    def test_build_guided_eligibility_true(self) -> None:
        eligibility = build_guided_eligibility(
            persona_segment="beginner_investor",
            onboarding_eligible=True,
            financial_health_eligible=True,
            completed_lessons=3,
        )
        assert eligibility.eligible is True
        assert "Guided Investing Lite" in eligibility.reasons[0]
        assert eligibility.caution

    def test_build_guided_eligibility_false_when_lessons_insufficient(self) -> None:
        eligibility = build_guided_eligibility(
            persona_segment="beginner_investor",
            onboarding_eligible=True,
            financial_health_eligible=True,
            completed_lessons=1,
        )
        assert eligibility.eligible is False
        assert any("hoàn thành ít nhất 2 bài" in r for r in eligibility.reasons)
        assert eligibility.next_step_path == "/learn"

    def test_build_guided_eligibility_false_when_health_ineligible(self) -> None:
        eligibility = build_guided_eligibility(
            persona_segment="household_manager",
            onboarding_eligible=True,
            financial_health_eligible=False,
            completed_lessons=2,
        )
        assert eligibility.eligible is False
        assert any("Financial Health" in r for r in eligibility.reasons)

    def test_build_market_context_high_risk(self) -> None:
        drivers = [
            GuidedMarketDriver(label="Vĩ mô", share_pct=0.4, direction="negative"),
            GuidedMarketDriver(label="Định giá", share_pct=0.3, direction="neutral"),
        ]
        context = build_market_context(
            risk_regime="high_risk",
            decision_score_pct=80.0,
            expected_drawdown_pct=8.5,
            drivers=drivers,
            data_freshness="2026-09-05T10:00:00Z",
        )
        assert context.risk_regime == "high_risk"
        assert "phòng thủ" in context.headline
        assert context.caution
        assert len(context.drivers) == 2

    def test_build_market_context_medium_and_low_risk(self) -> None:
        drivers = [GuidedMarketDriver(label="Dòng tiền", share_pct=0.5, direction="positive")]
        ctx_med = build_market_context(
            risk_regime="moderate_risk",
            decision_score_pct=60.0,
            expected_drawdown_pct=5.0,
            drivers=drivers,
            data_freshness="2026-09-05T10:00:00Z",
        )
        assert "chú ý" in ctx_med.headline

        ctx_low = build_market_context(
            risk_regime="low_risk",
            decision_score_pct=40.0,
            expected_drawdown_pct=3.0,
            drivers=drivers,
            data_freshness="2026-09-05T10:00:00Z",
        )
        assert "tương đối ổn định" in ctx_low.headline

    def test_build_watchlist_review_metrics(self) -> None:
        items = [
            GuidedWatchlistItem(
                item_id="item-1",
                user_id="user-01",
                ticker="FPT",
                label="FPT Corp",
                reason_to_track="Tăng trưởng công nghệ và xuất khẩu phần mềm",
                theme_tag="tech",
            ),
            GuidedWatchlistItem(
                item_id="item-2",
                user_id="user-01",
                ticker="VNM",
                label="Vinamilk",
                reason_to_track="Dòng tiền đều và cổ tức ổn định",
                theme_tag="consumer",
            ),
        ]
        review = build_watchlist_review(items)
        assert review.item_count == 2
        assert review.thesis_coverage_pct == 100
        assert review.theme_concentration_band in {"medium", "high", "balanced", "very_high"}

    def test_build_portfolio_review_balanced_vs_concentrated(self) -> None:
        # Balanced portfolio (< 20% top holding)
        balanced_holdings = [
            {"ticker": f"SYM{i}", "weight_pct": 16.6}
            for i in range(6)
        ]
        rev_bal = build_portfolio_review(balanced_holdings)
        assert rev_bal.concentration_band == "balanced"
        assert rev_bal.top_holding_pct < 20.0
        assert rev_bal.concentration_score >= 70

        # Very high concentration (>= 50%)
        heavy_holdings = [
            {"ticker": "FPT", "weight_pct": 70.0},
            {"ticker": "VNM", "weight_pct": 30.0},
        ]
        rev_heavy = build_portfolio_review(heavy_holdings)
        assert rev_heavy.concentration_band == "very_high"
        assert rev_heavy.top_holding_pct == 70.0
        assert rev_heavy.concentration_score <= 35
        assert any("dồn quá mạnh" in w for w in rev_heavy.warnings)

    def test_build_portfolio_review_empty_holdings(self) -> None:
        rev_empty = build_portfolio_review([])
        assert rev_empty.concentration_band == "unknown"
        assert rev_empty.top_holding_pct == 0.0

    def test_build_safe_reply_blocks_unsafe_advisory_requests(self) -> None:
        reply_buy = build_safe_reply(prompt="Mã nào nên mua phiên mai?", eligible=True)
        assert reply_buy.allowed is False
        assert "không đưa khuyến nghị mua bán" in reply_buy.headline
        reply_buy = build_safe_reply(prompt="Khuyên mình mua mã nào hôm nay", eligible=True)
        assert reply_buy.allowed is False
        reply_pick = build_safe_reply(prompt="Cho mình top pick tuần này", eligible=True)
        assert reply_pick.allowed is False
        reply_certainty = build_safe_reply(prompt="Cổ phiếu này chac tang không?", eligible=True)
        assert reply_certainty.allowed is False

    def test_build_safe_reply_blocks_ineligible_users(self) -> None:
        reply = build_safe_reply(prompt="Giải thích bối cảnh vĩ mô", eligible=False)
        assert reply.allowed is False
        assert "hoàn thành phần nền tảng" in reply.headline

    def test_build_safe_reply_allows_educational_prompts_for_eligible(self) -> None:
        reply = build_safe_reply(prompt="Giải thích cách đọc drawdown của danh mục", eligible=True)
        assert reply.allowed is True
        assert "public-safe guided mode" in reply.headline

    def test_guided_investing_schemas(self) -> None:
        req = GuidedWatchlistItemCreateRequest(
            session_id="session-gi-001",
            ticker="FPT",
            label="FPT Corp",
            reason_to_track="Quan sát tăng trưởng doanh thu nước ngoài",
            theme_tag="tech",
        )
        assert req.ticker == "FPT"

        chat_req = GuidedSafeChatRequest(
            session_id="session-gi-001",
            prompt="Giải thích rủi ro tỷ giá đối với FPT",
        )
        assert chat_req.session_id == "session-gi-001"
