from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.modules.news_intelligence.application.agent_tools import get_market_context
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import GetMarketContextInput
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService


@pytest.fixture
def envelope() -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run_market_bridge",
        correlation_id="corr_market_bridge",
        idempotency_key="idem_market_bridge",
        account_id="acct_market_test",
        scopes=("public:market_summary:read", "public:news:read"),
        surface="news",
        consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        created_at="2026-09-02T12:00:00Z",
    )


def test_time_misaligned_market_context_marked_stale(envelope: TrustedExecutionEnvelope):
    old_time = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    payload = GetMarketContextInput(
        event_time=old_time,
        markets=("VN Equity",),
    )
    output = asyncio.run(get_market_context(payload, envelope))
    assert output.schema_version == "1.0.0"
    assert output.time_aligned is False
    assert output.data_quality == "stale"
    assert output.provenance["event_time"] == old_time


def test_time_aligned_market_context(envelope: TrustedExecutionEnvelope):
    recent_time = datetime.now(timezone.utc).isoformat()
    payload = GetMarketContextInput(
        event_time=recent_time,
        markets=("VN Equity",),
    )
    output = asyncio.run(get_market_context(payload, envelope))
    assert output.schema_version == "1.0.0"
    assert output.time_aligned is True
    assert output.data_quality == "complete"
    assert len(output.index_metrics) >= 1
    assert output.breadth is not None
    assert output.capital_flow is not None


def test_existing_feed_and_endpoints_unaffected():
    """Verify that NewsIntelligenceService public endpoints remain operational."""
    service = NewsIntelligenceService()
    feed = service.get_feed(limit=5)
    assert "articles" in feed
    assert "clusters" in feed
    assert "pulse" in feed
    assert "safety" in feed
    assert feed["safety"]["no_buy_sell_recommendation"] is True

