from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.modules.news_intelligence.application.agent_tools import (
    CAPABILITY_MANIFEST,
    build_brief_evidence,
    compare_sources,
    get_cluster,
    get_enrichment,
    get_market_context,
    get_news_tool_manifests,
    get_source_health,
)
from risk_dashboard.modules.news_intelligence.application.enrichment import enrich_article
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    BuildBriefEvidenceInput,
    CompareSourcesInput,
    GetClusterInput,
    GetEnrichmentInput,
    GetMarketContextInput,
    GetSourceHealthInput,
)
from risk_dashboard.platform.database import (
    clear_db_path_cache,
    clear_migration_cache,
    open_app_state_db,
)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(tmp_path / "test_phase2.sqlite3"))
    clear_db_path_cache()
    clear_migration_cache()
    now_iso = datetime.now(timezone.utc).isoformat()

    art1 = enrich_article(
        NewsArticle(
            article_id="art_sbv_01",
            headline="Ngân hàng Nhà nước giữ nguyên lãi suất điều hành",
            summary="SBV duy trì lãi suất tái cấp vốn ở mức 4.5% nhằm hỗ trợ thanh khoản hệ thống.",
            source="State Bank of Vietnam",
            source_id="sbv",
            source_tier=1,
            source_flag="VN",
            region="VN",
            category="macro",
            url="https://sbv.gov.vn/rate-decision",
            published_at=now_iso,
            fetched_at=now_iso,
            sort_ts=1756814400,
            tickers=["VCB", "BID", "CTG"],
        )
    )
    art2 = enrich_article(
        NewsArticle(
            article_id="art_vne_02",
            headline="Lãi suất điều hành ổn định hỗ trợ thị trường chứng khoán",
            summary="Các chuyên gia đánh giá chính sách tiền tệ tiếp tục tạo điều kiện cho dòng tiền.",
            source="VnEconomy",
            source_id="vneconomy",
            source_tier=2,
            source_flag="VN",
            region="VN",
            category="macro",
            url="https://vneconomy.vn/rate-market-impact",
            published_at=now_iso,
            fetched_at=now_iso,
            sort_ts=1756814400,
            tickers=["VCB", "SSI"],
        )
    )
    svc = NewsIntelligenceService()
    with open_app_state_db() as conn:
        svc._upsert_article(conn, art1)
        svc._upsert_article(conn, art2)
        conn.commit()

    yield
    clear_db_path_cache()
    clear_migration_cache()


@pytest.fixture
def test_envelope() -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run_test_123",
        correlation_id="corr_test_123",
        idempotency_key="idem_test_123",
        account_id="acct_user_456",
        scopes=("public:news:read", "public:market_summary:read"),
        surface="news",
        consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        created_at="2026-09-02T12:00:00Z",
    )


@pytest.fixture
def unprivileged_envelope() -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run_test_unprivileged",
        correlation_id="corr_test_unprivileged",
        idempotency_key="idem_test_unprivileged",
        account_id="acct_user_unprivileged",
        scopes=("public:unrelated:read",),
        surface="news",
        consent=ConsentSnapshot(memory=False, analytics=False, policy_version="1.0.0"),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        created_at="2026-09-02T12:00:00Z",
    )


def test_get_cluster_tool(test_envelope: TrustedExecutionEnvelope):
    payload = GetClusterInput(cluster_id="art_sbv_01", max_articles=5)
    output = asyncio.run(get_cluster(payload, test_envelope))
    assert output.schema_version == "1.0.0"
    assert output.lead_article is not None
    assert output.importance.score >= 0
    assert output.importance.method_version == "1.0.0"
    assert len(output.articles) >= 1
    assert output.lead_article.is_untrusted_content is True


def test_get_cluster_not_found_raises(test_envelope: TrustedExecutionEnvelope):
    payload = GetClusterInput(cluster_id="non_existent_cluster_999")
    with pytest.raises(ValueError, match="NEWS_CLUSTER_NOT_FOUND"):
        asyncio.run(get_cluster(payload, test_envelope))


def test_get_source_health_tool(test_envelope: TrustedExecutionEnvelope):
    payload = GetSourceHealthInput(source_ids=("vneconomy", "sbv"))
    output = asyncio.run(get_source_health(payload, test_envelope))
    assert output.schema_version == "1.0.0"
    assert len(output.rows) == 2
    assert output.coverage_sufficient is True


def test_get_enrichment_tool(test_envelope: TrustedExecutionEnvelope):
    payload = GetEnrichmentInput(article_id="art_sbv_01")
    output = asyncio.run(get_enrichment(payload, test_envelope))
    assert output.schema_version == "1.0.0"
    assert output.article_id == "art_sbv_01"
    assert output.sentiment in ("positive", "neutral", "negative")
    assert output.impact in ("high", "medium", "low")
    assert output.enrichment_method_version == "1.0.0"


def test_get_enrichment_not_found_raises(test_envelope: TrustedExecutionEnvelope):
    payload = GetEnrichmentInput(article_id="non_existent_article_999")
    with pytest.raises(ValueError, match="NEWS_ARTICLE_NOT_FOUND"):
        asyncio.run(get_enrichment(payload, test_envelope))


def test_compare_sources_tool(test_envelope: TrustedExecutionEnvelope):
    payload = CompareSourcesInput(cluster_id="art_sbv_01")
    output = asyncio.run(compare_sources(payload, test_envelope))
    assert output.schema_version == "1.0.0"
    assert output.cluster_id == "art_sbv_01"
    assert len(output.claims) >= 1
    assert 0.0 <= output.agreement_rate <= 1.0


def test_compare_sources_not_found_raises(test_envelope: TrustedExecutionEnvelope):
    payload = CompareSourcesInput(cluster_id="non_existent_cluster_999")
    with pytest.raises(ValueError, match="NEWS_CLUSTER_NOT_FOUND"):
        asyncio.run(compare_sources(payload, test_envelope))


def test_get_market_context_tool(test_envelope: TrustedExecutionEnvelope):
    payload = GetMarketContextInput(
        event_time="2026-09-02T12:00:00Z",
        markets=("VN Equity", "Rates"),
    )
    output = asyncio.run(get_market_context(payload, test_envelope))
    assert output.schema_version == "1.0.0"
    assert output.provenance["source"] == "market_summary"
    assert output.time_aligned is True


def test_build_brief_evidence_tool(test_envelope: TrustedExecutionEnvelope):
    payload = BuildBriefEvidenceInput(
        cluster_ids=("macro",),
        objective="Tóm tắt tác động vĩ mô tới thị trường chứng khoán Việt Nam",
    )
    output = asyncio.run(build_brief_evidence(payload, test_envelope))
    assert output.schema_version == "1.0.0"
    assert len(output.evidence_rows) >= 1
    assert output.source_coverage > 0.0


def test_build_brief_evidence_not_found_raises(test_envelope: TrustedExecutionEnvelope):
    payload = BuildBriefEvidenceInput(
        cluster_ids=("non_existent_category_999",),
        objective="Research unknown topic",
    )
    with pytest.raises(ValueError, match="NEWS_CLUSTER_NOT_FOUND"):
        asyncio.run(build_brief_evidence(payload, test_envelope))


def test_tool_scope_enforcement(unprivileged_envelope: TrustedExecutionEnvelope):
    payload = GetClusterInput(cluster_id="art_sbv_01")
    with pytest.raises(PermissionError, match="Missing required scope"):
        asyncio.run(get_cluster(payload, unprivileged_envelope))


def test_scope_escalation_prevented():
    envelope_read_only = TrustedExecutionEnvelope(
        run_id="run_read_only",
        correlation_id="corr_1",
        idempotency_key="idem_1",
        account_id="user_read",
        scopes=("public:news:agent:read",),
        surface="news",
        consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        created_at="2026-09-02T12:00:00Z",
    )
    from risk_dashboard.modules.news_intelligence.agent_tools.helpers import check_scope
    with pytest.raises(PermissionError, match="Missing required scope"):
        check_scope(envelope_read_only, ("public:news:write",))


def test_capability_manifest_and_tool_manifests():
    manifests = get_news_tool_manifests()
    assert len(manifests) == 7
    read_manifests = [m for m in manifests if m.risk_class == RiskClass.READ]
    assert len(read_manifests) == 6

    # Verify CAPABILITY_MANIFEST
    assert CAPABILITY_MANIFEST["capability_id"] == "news.evidence_brief.v1"
    assert CAPABILITY_MANIFEST["risk_class"] == "read"
    assert len(CAPABILITY_MANIFEST["allowed_tools"]) == 6
    assert "news.save_brief" not in CAPABILITY_MANIFEST["allowed_tools"]
