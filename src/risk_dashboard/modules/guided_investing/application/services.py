from __future__ import annotations

from datetime import date

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_ops_event, emit_product_event
from risk_dashboard.modules.admin_cms.application.runtime_reader import ContentOpsRuntimeReader
from risk_dashboard.data.financials import FinancialDataError, get_financial_dataset
from risk_dashboard.modules.guided_investing.domain.entities import (
    GuidedJournalEntry,
    GuidedMarketDriver,
    GuidedPortfolioHolding,
    GuidedPortfolioReviewRecord,
    GuidedSavedPortfolio,
    GuidedWatchlistItem,
    utc_now_iso,
)
from risk_dashboard.modules.guided_investing.domain.policies import (
    build_company_health,
    build_guided_eligibility,
    build_market_context,
    build_portfolio_review,
    build_safe_reply,
    build_watchlist_review,
)
from risk_dashboard.modules.guided_investing.domain.ports import (
    GuidedJournalRepository,
    GuidedPortfolioRepository,
    GuidedWatchlistRepository,
)
from risk_dashboard.modules.guided_investing.infrastructure.repositories.sqlite import (
    new_journal_entry_id,
    new_portfolio_id,
    new_review_id,
    new_watchlist_item_id,
)
from risk_dashboard.modules.guided_investing.schemas.responses import (
    GuidedCompanyHealthResponse,
    GuidedContextualExplainerResponse,
    GuidedDisclaimerResponse,
    GuidedEligibilityResponse,
    GuidedInvestingHomeResponse,
    GuidedJournalEntryResponse,
    GuidedMarketContextResponse,
    GuidedPortfolioReviewResponse,
    GuidedPortfolioReviewHistoryResponse,
    GuidedSavedPortfolioResponse,
    GuidedSafeReplyResponse,
    GuidedWatchlistItemResponse,
    GuidedWatchlistReviewResponse,
)
from risk_dashboard.modules.trust_safety.application.services import TrustSafetyService
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.runtime.panel_store import PanelUnavailableError, get_panel
from risk_dashboard.engines.quant.eod_pipeline import run_quant_eod
from risk_dashboard.engines.quant.financial_analysis import analyze_financial_dataset
from risk_dashboard.engines.quant.peer_compare import compare_peers
from risk_dashboard.engines.quant.scenario import rerun_with_macro_override


class GetGuidedEligibility:
    def execute(self, *, user_id: str) -> GuidedEligibilityResponse:
        context = _load_user_context(user_id)
        eligibility = build_guided_eligibility(
            persona_segment=context["persona_segment"],
            onboarding_eligible=context["onboarding_eligible"],
            financial_health_eligible=context["financial_health_eligible"],
            completed_lessons=context["completed_lessons"],
        )
        return GuidedEligibilityResponse(
            eligible=eligibility.eligible,
            reasons=eligibility.reasons,
            next_step_title=eligibility.next_step_title,
            next_step_path=eligibility.next_step_path,
            caution=eligibility.caution,
        )


class GetGuidedInvestingHome:
    def __init__(
        self,
        watchlists: GuidedWatchlistRepository,
        journals: GuidedJournalRepository,
        portfolios: GuidedPortfolioRepository,
    ) -> None:
        self.watchlists = watchlists
        self.journals = journals
        self.portfolios = portfolios

    def execute(self, *, user_id: str) -> GuidedInvestingHomeResponse:
        runtime_reader = ContentOpsRuntimeReader()
        trust = TrustSafetyService()
        eligibility = GetGuidedEligibility().execute(user_id=user_id)
        items = self.watchlists.list_items(user_id=user_id)
        watchlist_review = build_watchlist_review(items)
        journals = self.journals.list_entries(user_id=user_id)
        saved_portfolio = self.portfolios.get_saved_portfolio(user_id=user_id)
        history = self.portfolios.list_review_history(user_id=user_id)
        market_context = None
        if eligibility.eligible:
            market_context = GetGuidedMarketContext().execute()

        if saved_portfolio is None:
            next_step_title = "Lưu portfolio đầu tiên"
            next_step_path = "/guided-investing?card=portfolio_review"
        elif not items:
            next_step_title = "Tạo watchlist đầu tiên"
            next_step_path = "/guided-investing?card=watchlist"
        elif not journals:
            next_step_title = "Viết thesis đầu tiên"
            next_step_path = "/guided-investing?card=journal"
        else:
            next_step_title = "Rà soát market context"
            next_step_path = "/guided-investing?card=market_context"

        presentation = trust.build_presentation(
            surface="guided_investing",
            topic="guided_investing_home",
            quality_state="good" if eligibility.eligible else "low_confidence",
            freshness_value=None,
            disclaimer=runtime_reader.get_disclaimer(surface="guided_investing", topic="guided_investing_home"),
        )
        trust.record_audit(
            actor_id=user_id,
            surface="guided_investing",
            topic="guided_investing_home",
            channel="runtime_card",
            risk_classes=tuple(
                label for label in ("missing_disclaimer" if presentation.disclaimer_injected else "",) if label
            ),
            route_decision="served_guided_home",
            output_summary=next_step_title,
            disclaimer_injected=presentation.disclaimer_injected,
            confidence_label=presentation.confidence_label,
        )
        emit_product_event(
            event_name="guided_investing_home_viewed",
            module="guided_investing",
            surface="guided_investing",
            user_id=user_id,
            session_id=user_id,
            properties={
                "eligible": eligibility.eligible,
                "watchlist_count": len(items),
                "next_step_path": next_step_path,
            },
        )
        emit_product_event(
            event_name="guided_investing_eligibility_checked",
            module="guided_investing",
            surface="guided_investing",
            user_id=user_id,
            session_id=user_id,
            properties={"eligible": eligibility.eligible, "reasons": list(eligibility.reasons)},
        )
        return GuidedInvestingHomeResponse(
            eligibility=eligibility,
            market_context=market_context,
            watchlist_review=_to_watchlist_review_response(watchlist_review),
            saved_portfolio=_to_saved_portfolio_response(saved_portfolio),
            latest_portfolio_review=_to_review_history_response(history[0]) if history else None,
            latest_journal=_to_journal_response(journals[0]) if journals else None,
            next_step_title=next_step_title,
            next_step_path=next_step_path,
            confidence_label=presentation.confidence_label,
            risk_banner=presentation.risk_banner,
            what_this_is=presentation.what_this_is,
            what_this_is_not=presentation.what_this_is_not,
            disclaimer=_to_disclaimer_response(presentation.disclaimer),
            contextual_explainer=_to_explainer_response(
                runtime_reader.get_contextual_explainer(surface="guided_investing", trigger_key="guided_investing_home")
            ),
        )


class CreateGuidedWatchlistItem:
    def __init__(self, watchlists: GuidedWatchlistRepository) -> None:
        self.watchlists = watchlists

    def execute(
        self,
        *,
        user_id: str,
        ticker: str,
        label: str,
        reason_to_track: str,
        theme_tag: str | None,
    ) -> GuidedWatchlistItemResponse:
        now = utc_now_iso()
        item = GuidedWatchlistItem(
            item_id=new_watchlist_item_id(),
            user_id=user_id,
            ticker=ticker.upper().strip(),
            label=label.strip(),
            reason_to_track=reason_to_track.strip(),
            theme_tag=theme_tag.strip() if theme_tag else None,
            created_at=now,
            updated_at=now,
        )
        saved = self.watchlists.save_item(item)
        emit_product_event(
            event_name="guided_watchlist_item_added",
            module="guided_investing",
            surface="guided_investing",
            user_id=user_id,
            session_id=user_id,
            properties={"ticker": saved.ticker, "theme_tag": saved.theme_tag},
        )
        return GuidedWatchlistItemResponse(
            item_id=saved.item_id,
            ticker=saved.ticker,
            label=saved.label,
            reason_to_track=saved.reason_to_track,
            theme_tag=saved.theme_tag,
        )


class ReviewGuidedWatchlist:
    def __init__(self, watchlists: GuidedWatchlistRepository) -> None:
        self.watchlists = watchlists

    def execute(self, *, user_id: str) -> GuidedWatchlistReviewResponse:
        review = build_watchlist_review(self.watchlists.list_items(user_id=user_id))
        return _to_watchlist_review_response(review)


class GetGuidedWatchlist:
    def __init__(self, watchlists: GuidedWatchlistRepository) -> None:
        self.watchlists = watchlists

    def execute(self, *, user_id: str) -> list[GuidedWatchlistItemResponse]:
        return [
            GuidedWatchlistItemResponse(
                item_id=item.item_id,
                ticker=item.ticker,
                label=item.label,
                reason_to_track=item.reason_to_track,
                theme_tag=item.theme_tag,
            )
            for item in self.watchlists.list_items(user_id=user_id)
        ]


class GetGuidedMarketContext:
    def execute(
        self,
        *,
        usd_vnd_rate: float | None = None,
        sbv_interest_rate_pct: float | None = None,
    ) -> GuidedMarketContextResponse:
        runtime_reader = ContentOpsRuntimeReader()
        trust = TrustSafetyService()
        try:
            panel = get_panel()
            as_of = panel["date"].max()
            as_of_date = as_of.date() if hasattr(as_of, "date") else date.fromisoformat(str(as_of))
            quant = run_quant_eod(panel, as_of_date)
            scenario_note = None
            if usd_vnd_rate is not None or sbv_interest_rate_pct is not None:
                rerun = rerun_with_macro_override(
                    panel,
                    as_of_date,
                    usd_vnd_rate=usd_vnd_rate,
                    sbv_interest_rate_pct=sbv_interest_rate_pct,
                )
                delta = (rerun.decision_score - quant.decision_score) * 100
                scenario_note = f"Kịch bản mới làm decision score thay đổi khoảng {delta:+.1f} điểm phần trăm."
                quant = rerun

            context = build_market_context(
                risk_regime=quant.risk_regime,
                decision_score_pct=round(quant.decision_score * 100, 1),
                expected_drawdown_pct=round(float(quant.horizons.expected_drawdown_pct), 1),
                drivers=[
                    GuidedMarketDriver(
                        label=_humanize_feature(item.feature_name),
                        share_pct=round(item.share * 100, 1),
                        direction=item.direction,
                    )
                    for item in quant.shap_top[:3]
                ],
                data_freshness=str(as_of_date),
                scenario_note=scenario_note,
            )
        except (PanelUnavailableError, ValueError, KeyError, TypeError):
            context = build_market_context(
                risk_regime="unknown",
                decision_score_pct=50.0,
                expected_drawdown_pct=0.0,
                drivers=[],
                data_freshness="unavailable",
                scenario_note="Hiện chưa có panel/model sẵn để tính market context thời gian này.",
            )

        presentation = trust.build_presentation(
            surface="guided_investing",
            topic="market_context",
            quality_state="fallback" if context.data_freshness == "unavailable" else "good",
            freshness_value=context.data_freshness,
            disclaimer=runtime_reader.get_disclaimer(surface="guided_investing", topic="market_context"),
        )
        trust.record_audit(
            actor_id=None,
            surface="guided_investing",
            topic="market_context",
            channel="runtime_card",
            risk_classes=tuple(
                label
                for label in (
                    "stale_data_risk" if presentation.freshness_status in {"stale", "unavailable"} else "",
                    "missing_disclaimer" if presentation.disclaimer_injected else "",
                )
                if label
            ),
            route_decision="served_market_context",
            output_summary=context.headline,
            disclaimer_injected=presentation.disclaimer_injected,
            freshness_status=presentation.freshness_status,
            confidence_label=presentation.confidence_label,
        )
        emit_product_event(
            event_name="guided_market_context_viewed",
            module="guided_investing",
            surface="guided_investing",
            properties={
                "risk_regime": context.risk_regime,
                "freshness_status": presentation.freshness_status,
            },
        )
        emit_ops_event(
            event_name="ops_data_refresh_logged",
            module="guided_investing",
            surface="guided_investing",
            properties={
                "source": "guided_market_context",
                "freshness_status": presentation.freshness_status,
                "quality_state": "fallback" if context.data_freshness == "unavailable" else "good",
            },
        )
        return GuidedMarketContextResponse(
            risk_regime=context.risk_regime,
            decision_score_pct=context.decision_score_pct,
            expected_drawdown_pct=context.expected_drawdown_pct,
            headline=context.headline,
            summary=context.summary,
            so_what=context.so_what,
            now_what=context.now_what,
            caution=context.caution,
            data_freshness=presentation.freshness_status,
            confidence_label=presentation.confidence_label,
            what_this_is=presentation.what_this_is,
            what_this_is_not=presentation.what_this_is_not,
            drivers=[
                {"label": item.label, "share_pct": item.share_pct, "direction": item.direction}
                for item in context.drivers
            ],
            scenario_note=context.scenario_note,
            disclaimer=_to_disclaimer_response(presentation.disclaimer),
            contextual_explainer=_to_explainer_response(
                runtime_reader.get_contextual_explainer(surface="guided_investing", trigger_key="market_context")
            ),
        )


class GetGuidedCompanyHealth:
    def execute(self, *, ticker: str) -> GuidedCompanyHealthResponse:
        runtime_reader = ContentOpsRuntimeReader()
        trust = TrustSafetyService()
        try:
            dataset = get_financial_dataset(ticker.upper(), refresh=False)
        except FinancialDataError as exc:
            raise ValueError(exc.message) from exc
        analysis = analyze_financial_dataset(dataset)
        peer_result = compare_peers(ticker.upper()).to_dict()
        company = build_company_health(analysis=analysis, peer_result=peer_result)
        presentation = trust.build_presentation(
            surface="guided_investing",
            topic="company_health",
            quality_state="good",
            freshness_value=None,
            disclaimer=runtime_reader.get_disclaimer(surface="guided_investing", topic="company_health"),
        )
        trust.record_audit(
            actor_id=None,
            surface="guided_investing",
            topic="company_health",
            channel="runtime_card",
            risk_classes=tuple(
                label for label in ("missing_disclaimer" if presentation.disclaimer_injected else "",) if label
            ),
            route_decision="served_company_health",
            output_summary=company.headline,
            disclaimer_injected=presentation.disclaimer_injected,
            confidence_label=presentation.confidence_label,
        )
        emit_product_event(
            event_name="guided_company_health_viewed",
            module="guided_investing",
            surface="guided_investing",
            properties={"ticker": company.ticker, "health_band": company.health_band},
        )
        return GuidedCompanyHealthResponse(
            ticker=company.ticker,
            company_name=company.company_name,
            industry=company.industry,
            health_band=company.health_band,
            headline=company.headline,
            summary=company.summary,
            so_what=company.so_what,
            now_what=company.now_what,
            caution=company.caution,
            confidence_label=presentation.confidence_label,
            risk_banner=presentation.risk_banner,
            what_this_is=presentation.what_this_is,
            what_this_is_not=presentation.what_this_is_not,
            highlights=company.highlights,
            flags=company.flags,
            peer_takeaways=company.peer_takeaways,
            disclaimer=_to_disclaimer_response(presentation.disclaimer),
            contextual_explainer=_to_explainer_response(
                runtime_reader.get_contextual_explainer(surface="guided_investing", trigger_key="company_health")
            ),
        )


class ReviewGuidedPortfolio:
    def __init__(self, portfolios: GuidedPortfolioRepository | None = None) -> None:
        self.portfolios = portfolios

    def execute(
        self,
        *,
        user_id: str,
        holdings: list[dict[str, float]],
        scenario_label: str = "base_case",
        persist_history: bool = True,
    ) -> GuidedPortfolioReviewResponse:
        review = build_portfolio_review(holdings)
        if self.portfolios is not None and persist_history:
            portfolio = self.portfolios.get_saved_portfolio(user_id=user_id)
            portfolio_id = portfolio.portfolio_id if portfolio is not None else "unsaved-portfolio"
            self.portfolios.save_review_record(
                GuidedPortfolioReviewRecord(
                    review_id=new_review_id(),
                    portfolio_id=portfolio_id,
                    user_id=user_id,
                    scenario_label=scenario_label,
                    holdings=[GuidedPortfolioHolding(ticker=item["ticker"], weight_pct=item["weight_pct"]) for item in holdings],
                    review=review,
                    created_at=utc_now_iso(),
                )
            )
        emit_product_event(
            event_name="guided_portfolio_review_submitted",
            module="guided_investing",
            surface="guided_investing",
            user_id=user_id,
            session_id=user_id,
            properties={
                "scenario_label": scenario_label,
                "portfolio_concentration_band": review.concentration_band,
            },
        )
        return GuidedPortfolioReviewResponse(
            concentration_band=review.concentration_band,
            top_holding_pct=review.top_holding_pct,
            concentration_score=review.concentration_score,
            warnings=review.warnings,
            next_actions=review.next_actions,
        )


class SaveGuidedPortfolio:
    def __init__(self, portfolios: GuidedPortfolioRepository) -> None:
        self.portfolios = portfolios

    def execute(self, *, user_id: str, name: str, holdings: list[dict[str, float]]) -> GuidedSavedPortfolioResponse:
        now = utc_now_iso()
        existing = self.portfolios.get_saved_portfolio(user_id=user_id)
        portfolio = GuidedSavedPortfolio(
            portfolio_id=existing.portfolio_id if existing is not None else new_portfolio_id(),
            user_id=user_id,
            name=name.strip(),
            holdings=[GuidedPortfolioHolding(ticker=item["ticker"], weight_pct=item["weight_pct"]) for item in holdings],
            created_at=existing.created_at if existing is not None else now,
            updated_at=now,
        )
        saved = self.portfolios.save_portfolio(portfolio)
        emit_product_event(
            event_name="guided_portfolio_saved",
            module="guided_investing",
            surface="guided_investing",
            user_id=user_id,
            session_id=user_id,
            properties={"portfolio_id": saved.portfolio_id, "holding_count": len(saved.holdings)},
        )
        return _to_saved_portfolio_response(saved)


class GetSavedGuidedPortfolio:
    def __init__(self, portfolios: GuidedPortfolioRepository) -> None:
        self.portfolios = portfolios

    def execute(self, *, user_id: str) -> GuidedSavedPortfolioResponse | None:
        return _to_saved_portfolio_response(self.portfolios.get_saved_portfolio(user_id=user_id))


class ListGuidedPortfolioReviewHistory:
    def __init__(self, portfolios: GuidedPortfolioRepository) -> None:
        self.portfolios = portfolios

    def execute(self, *, user_id: str) -> list[GuidedPortfolioReviewHistoryResponse]:
        return [_to_review_history_response(item) for item in self.portfolios.list_review_history(user_id=user_id)]


class CreateGuidedJournalEntry:
    def __init__(self, journals: GuidedJournalRepository) -> None:
        self.journals = journals

    def execute(
        self,
        *,
        user_id: str,
        ticker: str,
        title: str,
        thesis: str,
        uncertainties: str,
        review_condition: str,
    ) -> GuidedJournalEntryResponse:
        now = utc_now_iso()
        entry = GuidedJournalEntry(
            entry_id=new_journal_entry_id(),
            user_id=user_id,
            ticker=ticker.upper().strip(),
            title=title.strip(),
            thesis=thesis.strip(),
            uncertainties=uncertainties.strip(),
            review_condition=review_condition.strip(),
            created_at=now,
            updated_at=now,
        )
        saved = self.journals.save_entry(entry)
        emit_product_event(
            event_name="guided_journal_created",
            module="guided_investing",
            surface="guided_investing",
            user_id=user_id,
            session_id=user_id,
            properties={"entry_id": saved.entry_id, "ticker": saved.ticker},
        )
        return _to_journal_response(saved)


class ListGuidedJournalEntries:
    def __init__(self, journals: GuidedJournalRepository) -> None:
        self.journals = journals

    def execute(self, *, user_id: str) -> list[GuidedJournalEntryResponse]:
        return [_to_journal_response(item) for item in self.journals.list_entries(user_id=user_id)]


class GuidedSafeChat:
    def execute(self, *, user_id: str, prompt: str) -> GuidedSafeReplyResponse:
        eligibility = GetGuidedEligibility().execute(user_id=user_id)
        reply = build_safe_reply(prompt=prompt, eligible=eligibility.eligible)
        return GuidedSafeReplyResponse(
            allowed=reply.allowed,
            headline=reply.headline,
            message=reply.message,
            suggested_path=reply.suggested_path,
            linked_lesson_id=reply.linked_lesson_id,
        )


def _load_user_context(user_id: str) -> dict[str, object]:
    with open_app_state_db() as conn:
        profile = conn.execute(
            """
            SELECT persona_segment, guided_investing_eligible
            FROM onboarding_profiles
            WHERE session_id = ?
            """,
            (user_id,),
        ).fetchone()
        if profile is None:
            raise ValueError("Unknown user session.")

        health = conn.execute(
            """
            SELECT guided_investing_eligible
            FROM financial_health_snapshots
            WHERE session_id = ?
            """,
            (user_id,),
        ).fetchone()
        lesson_progress = conn.execute(
            """
            SELECT COUNT(*) AS completed_count
            FROM learning_lesson_progress
            WHERE user_id = ? AND status = 'completed'
            """,
            (user_id,),
        ).fetchone()

    return {
        "persona_segment": profile["persona_segment"],
        "onboarding_eligible": bool(profile["guided_investing_eligible"]),
        "financial_health_eligible": bool(health["guided_investing_eligible"]) if health is not None else False,
        "completed_lessons": int(lesson_progress["completed_count"]) if lesson_progress is not None else 0,
    }


def _humanize_feature(feature_name: str) -> str:
    mapping = {
        "usd_vnd_rate": "Tỷ giá USD/VND",
        "usd_vnd_1m_change_pct": "Biến động tỷ giá 1 tháng",
        "sbv_interest_rate_pct": "Lãi suất điều hành",
        "vn_index": "VN-Index",
        "volume_1w_trend_pct": "Xu hướng thanh khoản 1 tuần",
    }
    return mapping.get(feature_name, feature_name.replace("_", " ").title())


def _to_watchlist_review_response(review) -> GuidedWatchlistReviewResponse:
    return GuidedWatchlistReviewResponse(
        item_count=review.item_count,
        thesis_coverage_pct=review.thesis_coverage_pct,
        theme_concentration_band=review.theme_concentration_band,
        watchlist_hygiene_score=review.watchlist_hygiene_score,
        flags=[{"code": flag.code, "title": flag.title, "detail": flag.detail} for flag in review.flags],
        next_actions=review.next_actions,
    )


def _to_journal_response(entry: GuidedJournalEntry) -> GuidedJournalEntryResponse:
    return GuidedJournalEntryResponse(
        entry_id=entry.entry_id,
        ticker=entry.ticker,
        title=entry.title,
        thesis=entry.thesis,
        uncertainties=entry.uncertainties,
        review_condition=entry.review_condition,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _to_saved_portfolio_response(portfolio: GuidedSavedPortfolio | None) -> GuidedSavedPortfolioResponse | None:
    if portfolio is None:
        return None
    return GuidedSavedPortfolioResponse(
        portfolio_id=portfolio.portfolio_id,
        name=portfolio.name,
        holdings=[{"ticker": item.ticker, "weight_pct": item.weight_pct} for item in portfolio.holdings],
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


def _to_review_history_response(record: GuidedPortfolioReviewRecord) -> GuidedPortfolioReviewHistoryResponse:
    return GuidedPortfolioReviewHistoryResponse(
        review_id=record.review_id,
        portfolio_id=record.portfolio_id,
        scenario_label=record.scenario_label,
        holdings=[{"ticker": item.ticker, "weight_pct": item.weight_pct} for item in record.holdings],
        review=GuidedPortfolioReviewResponse(
            concentration_band=record.review.concentration_band,
            top_holding_pct=record.review.top_holding_pct,
            concentration_score=record.review.concentration_score,
            warnings=record.review.warnings,
            next_actions=record.review.next_actions,
        ),
        created_at=record.created_at,
    )


def _to_disclaimer_response(disclaimer) -> GuidedDisclaimerResponse | None:
    if disclaimer is None:
        return None
    return GuidedDisclaimerResponse(
        title=disclaimer.title,
        short_text=disclaimer.short_text,
        full_text=disclaimer.full_text,
        severity=disclaimer.severity,
    )


def _to_explainer_response(explainer) -> GuidedContextualExplainerResponse | None:
    if explainer is None:
        return None
    return GuidedContextualExplainerResponse(
        explainer_id=explainer.explainer_id,
        title=explainer.title,
        body=explainer.body,
        linked_lesson_ids=explainer.linked_lesson_ids,
        guardrail_note=explainer.guardrail_note,
    )
