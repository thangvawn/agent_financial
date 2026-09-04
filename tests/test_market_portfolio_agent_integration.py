from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import pytest

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.market_portfolio.application.agent_service import MarketPortfolioAgentService
from risk_dashboard.modules.market_portfolio.domain.entities import PaperOrder
from risk_dashboard.modules.market_portfolio.infrastructure.artifact_repository import ArtifactRepository
from risk_dashboard.modules.market_portfolio.infrastructure.repository import MarketPortfolioRepository
from risk_dashboard.modules.market_portfolio.schemas.agent_api import (
    StartPortfolioReviewRequestV1,
)
from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    PriceShockV1,
    RunScenarioInputV1,
)
from risk_dashboard.platform.ai_runtime.contracts import ModelError, ModelResult
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider
from risk_dashboard.platform.database import open_app_state_db


@pytest.fixture(autouse=True)
def mock_feed(monkeypatch):
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.vn_market_feed.VnMarketFeedProducer.snapshot",
        lambda self: {
            "items": [{"symbol": "HPG", "price": 25000.0, "last": 25000.0}],
            "indices": [{"symbol": "VNINDEX", "close": 1250.0, "change_pct": 0.5}],
            "as_of": "2026-09-03T10:00:00Z",
        },
    )


def test_full_integration_flow_with_fake_provider():

    account_id = "test-integration-acc-1"
    principal = AuthPrincipal(account_id=account_id, session_id="sess-integ", resolved_at="2026-09-03T10:00:00Z")

    # Seed an account and holding
    repo = MarketPortfolioRepository()
    repo.ensure_account(account_id)
    with open_app_state_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO mp_holdings (user_id, symbol, quantity, avg_cost, updated_at)
            VALUES (?, 'HPG', 100.0, 25000.0, '2026-09-03T09:00:00Z')
            """,
            (account_id,),
        )
        conn.commit()

    artifact_repo = ArtifactRepository()

    fake_text = (
        "Báo cáo phân tích paper portfolio cho thấy tỷ trọng tiền mặt và tài sản đã được tính toán xác định. "
        "Đây là mô phỏng học tập, không phải khuyến nghị đầu tư."
    )
    fake_provider = FakeProvider(
        scripted=[
            ModelResult(
                text=fake_text,
                provider="fake",
                model="gemini-3.5-flash",
                latency_ms=45,
                finish_reason="stop",
            )
        ]
    )

    service = MarketPortfolioAgentService(artifact_repo=artifact_repo, provider=fake_provider)

    req = StartPortfolioReviewRequestV1(
        portfolio_id=account_id,
        review_type="exposure",
        idempotency_key="idemp-integ-key-001",
    )

    async def _run():
        res = await service.start_review(req, principal)
        assert res.schema_version == "1.0.0"
        assert res.artifact is not None
        assert res.artifact.account_id == account_id
        assert res.artifact.portfolio_kind == "paper"
        assert res.artifact.review_status == "reviewed"
        assert res.artifact.narrative_status == "generated"
        assert res.artifact.narrative == fake_text
        assert len(res.artifact.evidence) >= 1
        assert res.artifact.evidence[0].tool_name == "portfolio.get_exposure.v1"
        assert "invested_pct" in res.artifact.calculations

        # Test Idempotency: Calling with identical idempotency_key returns cached artifact
        res_cached = await service.start_review(req, principal)
        assert res_cached.artifact is not None
        assert res_cached.artifact.artifact_id == res.artifact.artifact_id

    asyncio.run(_run())


def test_fallback_resilience_when_llm_provider_offline():
    account_id = "test-fallback-acc-2"
    principal = AuthPrincipal(account_id=account_id, session_id="sess-fall", resolved_at="2026-09-03T10:00:00Z")

    repo = MarketPortfolioRepository()
    repo.ensure_account(account_id)

    failing_provider = FakeProvider(
        scripted=[ModelError("network_timeout", "Connection timed out to Gemini API.")]
    )
    service = MarketPortfolioAgentService(provider=failing_provider)

    req = StartPortfolioReviewRequestV1(
        portfolio_id=account_id,
        review_type="market_context",
        idempotency_key="idemp-fallback-002",
    )

    async def _run():
        res = await service.start_review(req, principal)
        assert res.schema_version == "1.0.0"
        assert res.artifact is not None
        # Narrative must be None and status unavailable, but calculations & observed facts preserved!
        assert res.artifact.narrative is None
        assert res.artifact.narrative_status == "unavailable"
        assert res.artifact.review_status == "reviewed"
        assert len(res.artifact.observed_facts) >= 1
        assert len(res.artifact.evidence) >= 1

    asyncio.run(_run())


def test_scenario_review_integration():
    account_id = "test-scenario-acc-3"
    principal = AuthPrincipal(account_id=account_id, session_id="sess-scen", resolved_at="2026-09-03T10:00:00Z")

    repo = MarketPortfolioRepository()
    repo.ensure_account(account_id)
    with open_app_state_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO mp_holdings (user_id, symbol, quantity, avg_cost, updated_at)
            VALUES (?, 'HPG', 100.0, 25000.0, '2026-09-03T09:00:00Z')
            """,
            (account_id,),
        )
        conn.commit()

    fake_text = "Kịch bản sốc giá paper portfolio cho thấy biến động PnL. Đây là mô phỏng rủi ro giáo dục."
    fake_provider = FakeProvider(
        scripted=[
            ModelResult(
                text=fake_text,
                provider="fake",
                model="gemini-3.5-flash",
                latency_ms=50,
                finish_reason="stop",
            )
        ]
    )
    service = MarketPortfolioAgentService(provider=fake_provider)

    req = StartPortfolioReviewRequestV1(
        portfolio_id=account_id,
        review_type="scenario",
        idempotency_key="idemp-scen-key-003",
        scenario=RunScenarioInputV1(
            portfolio_id=account_id,
            shocks=(PriceShockV1(symbol="HPG", shock_pct=-10.0),),
        ),
    )

    async def _run():
        res = await service.start_review(req, principal)
        assert res.artifact is not None
        assert res.artifact.review_type == "scenario"
        assert "pnl_delta" in res.artifact.calculations
        assert res.artifact.scenario_assumptions[0].symbol == "HPG"
        assert res.artifact.scenario_assumptions[0].shock_pct == -10.0

    asyncio.run(_run())


def test_artifact_repository_ttl_and_purge():
    artifact_repo = ArtifactRepository()
    account_id = "test-purge-acc"
    principal = AuthPrincipal(account_id=account_id, session_id="sess-pur", resolved_at="2026-09-03T10:00:00Z")

    service = MarketPortfolioAgentService(artifact_repo=artifact_repo)
    req = StartPortfolioReviewRequestV1(
        portfolio_id=account_id,
        review_type="market_context",
        idempotency_key="idemp-purge-key-004",
    )

    async def _run():
        res = await service.start_review(req, principal)
        art_id = res.artifact.artifact_id

        # Fetch active artifact
        fetched = artifact_repo.get_artifact(account_id, art_id)
        assert fetched is not None
        assert fetched.artifact_id == art_id

        # Purge with future cutoff -> should remove
        future_cutoff = "2099-01-01T00:00:00Z"
        purged = artifact_repo.purge_expired(now_iso=future_cutoff)
        assert purged >= 1

        # Now fetched should be None
        assert artifact_repo.get_artifact(account_id, art_id) is None

    asyncio.run(_run())


def test_reviewers_1_turn_repair_loop():
    """Verify that when the initial draft needs repair, a 1-turn repair loop is run."""
    account_id = "test-repair-acc"
    principal = AuthPrincipal(account_id=account_id, session_id="sess-rep", resolved_at="2026-09-03T10:00:00Z")

    repo = MarketPortfolioRepository()
    repo.ensure_account(account_id)

    # 1. Draft 1 lacks paper context (triggers SafetyReviewer repair)
    bad_draft = "Danh mục đang nắm giữ tiền mặt đầy đủ theo kế hoạch phân bổ."
    # 2. Draft 2 fixes the issue by explicitly mentioning paper portfolio
    repaired_draft = "Trong paper portfolio mô phỏng học tập này, danh mục nắm giữ tiền mặt đầy đủ."

    fake_provider = FakeProvider(
        scripted=[
            ModelResult(text=bad_draft, provider="fake", model="gemini-3.5-flash", latency_ms=10, finish_reason="stop"),
            ModelResult(text=repaired_draft, provider="fake", model="gemini-3.5-flash", latency_ms=10, finish_reason="stop"),
        ]
    )
    service = MarketPortfolioAgentService(provider=fake_provider)

    req = StartPortfolioReviewRequestV1(
        portfolio_id=account_id,
        review_type="exposure",
        idempotency_key="idemp-repair-005",
    )

    async def _run():
        res = await service.start_review(req, principal)
        assert res.artifact is not None
        assert res.artifact.narrative == repaired_draft
        assert res.artifact.narrative_status == "generated"
        assert res.artifact.review_status == "reviewed"

    asyncio.run(_run())


