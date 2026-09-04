from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.modules.news_intelligence.application.agent_tools import (
    build_brief_evidence,
    compare_sources,
)
from risk_dashboard.modules.news_intelligence.application.brief_builder import (
    build_evidence_rows_from_articles,
    calculate_evidence_hash,
)
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.modules.news_intelligence.infrastructure.source_registry import InMemorySourceRegistry
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    BuildBriefEvidenceInput,
    CompareSourcesInput,
    EvidenceRow,
)


@pytest.fixture
def envelope() -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run_test_phase4",
        correlation_id="corr_test_phase4",
        idempotency_key="idem_test_phase4",
        account_id="acct_user_phase4",
        scopes=("public:news:read",),
        surface="news",
        consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        created_at="2026-09-02T12:00:00Z",
    )


def test_fact_classification_with_multiple_sources():
    now_iso = datetime.now(timezone.utc).isoformat()
    art1 = NewsArticle(
        article_id="art_1",
        headline="Thặng dư thương mại Việt Nam đạt 19 tỷ USD",
        summary="Số liệu từ Tổng cục Thống kê cho thấy xuất siêu đạt kỷ lục.",
        source="VnEconomy",
        source_id="vneconomy",
        source_tier=2,
        source_flag="VN",
        region="VN",
        category="macro",
        url="https://vneconomy.vn/trade-1",
        published_at=now_iso,
        fetched_at=now_iso,
        sort_ts=1756814400,
    )
    art2 = NewsArticle(
        article_id="art_2",
        headline="Xuất siêu 8 tháng ước đạt hơn 19 tỷ USD",
        summary="Bộ Công Thương xác nhận kim ngạch xuất khẩu tăng mạnh.",
        source="CafeF",
        source_id="cafef",
        source_tier=2,
        source_flag="VN",
        region="VN",
        category="macro",
        url="https://cafef.vn/trade-2",
        published_at=now_iso,
        fetched_at=now_iso,
        sort_ts=1756814400,
    )
    art3 = NewsArticle(
        article_id="art_3",
        headline="Vietnam trade surplus tops $19 billion",
        summary="Official statistics confirm strong trade surplus performance.",
        source="Reuters",
        source_id="reuters",
        source_tier=1,
        source_flag="GLOBAL",
        region="GLOBAL",
        category="macro",
        url="https://reuters.com/trade-3",
        published_at=now_iso,
        fetched_at=now_iso,
        sort_ts=1756814400,
    )

    evidence_rows, unresolved, coverage, limitations, expires_at = build_evidence_rows_from_articles(
        [art1, art2, art3]
    )

    assert len(evidence_rows) >= 1
    lead_row = evidence_rows[0]
    assert lead_row.kind == "fact"
    assert len(lead_row.source_ids) == 3
    assert set(lead_row.source_ids) == {"vneconomy", "cafef", "reuters"}
    assert lead_row.freshness == "current"


def test_single_source_is_labeled_source_claim():
    now_iso = datetime.now(timezone.utc).isoformat()
    art_single = NewsArticle(
        article_id="art_single",
        headline="Công ty ABC sắp sáp nhập với đối tác nước ngoài",
        summary="Tin đồn trên diễn đàn về thương vụ M&A lớn.",
        source="Vietstock",
        source_id="vietstock",
        source_tier=3,
        source_flag="VN",
        region="VN",
        category="markets",
        url="https://vietstock.vn/ma-rumor",
        published_at=now_iso,
        fetched_at=now_iso,
        sort_ts=1756814400,
    )

    evidence_rows, unresolved, coverage, limitations, expires_at = build_evidence_rows_from_articles(
        [art_single]
    )
    assert len(evidence_rows) == 1
    assert evidence_rows[0].kind == "source_claim"
    assert any("nguồn đơn lẻ" in lim.lower() for lim in limitations)


def test_stale_article_marked_stale():
    stale_dt = datetime.now(timezone.utc) - timedelta(hours=36)
    stale_iso = stale_dt.isoformat()
    art_stale = NewsArticle(
        article_id="art_stale",
        headline="Giá vàng thế giới lập đỉnh tuần trước",
        summary="Diễn biến thị trường vàng từ phiên cuối tuần trước.",
        source="VnEconomy",
        source_id="vneconomy",
        source_tier=2,
        source_flag="VN",
        region="VN",
        category="commodities",
        url="https://vneconomy.vn/gold-stale",
        published_at=stale_iso,
        fetched_at=stale_iso,
        sort_ts=int(stale_dt.timestamp()),
    )

    evidence_rows, unresolved, coverage, limitations, expires_at = build_evidence_rows_from_articles(
        [art_stale]
    )
    assert len(evidence_rows) == 1
    assert evidence_rows[0].freshness == "stale"
    assert any("24 giờ" in lim for lim in limitations)


def test_evidence_hash_stability():
    row1 = EvidenceRow(
        claim_id="claim_001",
        statement="Lãi suất điều hành giữ nguyên 4.5%",
        kind="fact",
        source_ids=("sbv", "vneconomy"),
        article_ids=("art_1", "art_2"),
        published_at="2026-09-02T10:00:00Z",
        freshness="current",
    )
    row2 = EvidenceRow(
        claim_id="claim_002",
        statement="Tín dụng tăng trưởng 7.2% trong 8 tháng",
        kind="fact",
        source_ids=("sbv",),
        article_ids=("art_3",),
        published_at="2026-09-02T10:00:00Z",
        freshness="current",
    )

    hash_a = calculate_evidence_hash([row1, row2])
    hash_b = calculate_evidence_hash([row2, row1])  # Reversed order
    assert hash_a == hash_b  # Stable deterministic hash

    # Modified statement should change hash
    row2_mod = EvidenceRow(
        claim_id="claim_002",
        statement="Tín dụng tăng trưởng 8.0% trong 8 tháng",
        kind="fact",
        source_ids=("sbv",),
        article_ids=("art_3",),
        published_at="2026-09-02T10:00:00Z",
        freshness="current",
    )
    hash_c = calculate_evidence_hash([row1, row2_mod])
    assert hash_a != hash_c

