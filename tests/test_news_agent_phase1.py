from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.app.registry.registry import get_registered_modules
from risk_dashboard.modules.news_intelligence.domain.ports import BriefRepositoryPort, SourceRegistryPort
from risk_dashboard.modules.news_intelligence.domain.source_health import SourceHealthRecord
from risk_dashboard.modules.news_intelligence.infrastructure.source_registry import (
    InMemorySourceRegistry,
    get_default_source_registry,
)
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    ArticleRef,
    ImportanceBreakdownOut,
    ImportanceOut,
    SourceRef,
)


def test_source_ref_roundtrip():
    source = SourceRef(
        source_id="vneconomy",
        name="VnEconomy",
        url="https://vneconomy.vn",
        tier=2,
        region="VN",
        category="markets",
        license_class="attribution_required",
        attribution_text="Nguồn: VnEconomy",
    )
    dumped = source.model_dump()
    loaded = SourceRef.model_validate(dumped)
    assert loaded == source
    assert loaded.schema_version == "1.0.0"


def test_schema_rejects_unknown_fields():
    data = {
        "schema_version": "1.0.0",
        "source_id": "vneconomy",
        "name": "VnEconomy",
        "url": "https://vneconomy.vn",
        "tier": 2,
        "region": "VN",
        "category": "markets",
        "license_class": "attribution_required",
        "unknown_extra_field": "injected",
    }
    with pytest.raises(ValidationError):
        SourceRef.model_validate(data)


def test_source_registry_health_and_coverage():
    registry = InMemorySourceRegistry()
    health_rows = registry.get_health(("vneconomy", "sbv"))
    assert len(health_rows) == 2
    assert registry.evaluate_coverage(("vneconomy", "sbv")) is True

    # Register an unavailable/restricted source
    registry.register_source(
        source_id="bad_source",
        name="Bad Source",
        url="https://bad.com",
        tier=5,
        region="VN",
        category="noise",
        license_class="restricted",
        is_available=False,
        staleness_minutes=10000,
        error_rate_24h=0.8,
        quality_flag="unreliable",
        redistribution_allowed=False,
    )
    assert registry.evaluate_coverage(("vneconomy", "bad_source")) is False


def test_module_flags_and_scopes():
    registered = {m.slug: m for m in get_registered_modules()}
    news_module = registered.get("news_intelligence")
    assert news_module is not None
    assert "module.news_intelligence.agent.enabled" in news_module.feature_flags
    assert "public:news:agent:read" in news_module.permission_scopes
    assert "public:news:write" in news_module.permission_scopes
    assert news_module.slug == "news_intelligence"


def test_article_ref_immutability_and_untrusted():
    source = SourceRef(
        source_id="finnhub",
        name="Finnhub",
        url="https://finnhub.io",
        tier=2,
        region="GLOBAL",
        category="markets",
        license_class="licensed",
    )
    article = ArticleRef(
        article_id="art_123",
        headline="FED keeps rates steady",
        summary="FOMC decided to hold interest rates unchanged.",
        source=source,
        published_at="2026-09-02T12:00:00Z",
        fetched_at="2026-09-02T12:05:00Z",
        sort_ts=1756814400,
        language="en",
        tickers=("SPY", "QQQ"),
        content_hash="abc123hash",
        is_untrusted_content=True,
    )
    assert article.is_untrusted_content is True
    # Verify frozen
    with pytest.raises(ValidationError):
        article.headline = "Modified"  # type: ignore

