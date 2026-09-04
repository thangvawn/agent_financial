from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.modules.news_intelligence.application.agent_tools import save_brief
from risk_dashboard.modules.news_intelligence.application.brief_builder import (
    build_brief,
    calculate_evidence_hash,
)
from risk_dashboard.modules.news_intelligence.infrastructure.brief_repository import SqliteBriefRepository
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    BuildBriefEvidenceOutput,
    EvidenceRow,
    NewsEvidenceBriefArtifact,
    SaveBriefInput,
)


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test_briefs.sqlite3")


@pytest.fixture
def auth_envelope() -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run_brief_authoring",
        correlation_id="corr_brief_01",
        idempotency_key="idem_brief_01",
        account_id="user_alice",
        scopes=("public:news:write", "public:news:read"),
        surface="news",
        consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        created_at="2026-09-02T12:00:00Z",
    )


@pytest.fixture
def anon_envelope() -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run_brief_anon",
        correlation_id="corr_brief_anon",
        idempotency_key="idem_brief_anon",
        account_id="anonymous",
        scopes=("public:news:write",),
        surface="news",
        consent=ConsentSnapshot(memory=False, analytics=False, policy_version="1.0.0"),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        created_at="2026-09-02T12:00:00Z",
    )


@pytest.fixture
def sample_evidence_rows() -> tuple[EvidenceRow, ...]:
    return (
        EvidenceRow(
            claim_id="claim_001",
            statement="Chính phủ ban hành Nghị định hỗ trợ doanh nghiệp công nghệ.",
            kind="fact",
            source_ids=("vneconomy", "cafef"),
            article_ids=("art_101", "art_102"),
            published_at="2026-09-02T10:00:00Z",
            freshness="current",
        ),
    )


def test_save_brief_success(
    auth_envelope: TrustedExecutionEnvelope,
    sample_evidence_rows: tuple[EvidenceRow, ...],
    test_db_path: str,
):
    repo = SqliteBriefRepository(db_path=test_db_path)
    ev_hash = calculate_evidence_hash(sample_evidence_rows)

    payload = SaveBriefInput(
        proposal_id="prop_test_001",
        evidence_hash=ev_hash,
        title="Tóm tắt chính sách hỗ trợ công nghệ 2026",
        objective="Phân tích tác động chính sách đối với nhóm cổ phiếu IT",
        evidence_rows=sample_evidence_rows,
        limitations=("Chính sách đang trong giai đoạn triển khai dự thảo.",),
    )

    output = asyncio.run(save_brief(payload, auth_envelope, repo=repo))
    assert output.schema_version == "1.0.0"
    assert output.status == "saved"
    assert output.brief_id.startswith("brief_")
    assert output.receipt_id.startswith("rcpt_")

    # Verify persisted artifact
    saved_brief = repo.get(output.brief_id, account_id="user_alice")
    assert saved_brief is not None
    assert saved_brief.account_id == "user_alice"
    assert saved_brief.title == payload.title
    assert saved_brief.evidence_hash == ev_hash
    assert saved_brief.review_status == "reviewed"
    assert len(saved_brief.evidence_rows) == 1


def test_save_brief_stale_hash_rejected(
    auth_envelope: TrustedExecutionEnvelope,
    sample_evidence_rows: tuple[EvidenceRow, ...],
    test_db_path: str,
):
    repo = SqliteBriefRepository(db_path=test_db_path)
    tampered_hash = "bad_hash_1234567890abcdef"

    payload = SaveBriefInput(
        proposal_id="prop_test_002",
        evidence_hash=tampered_hash,
        title="Tóm tắt tài chính",
        objective="Phân tích thị trường",
        evidence_rows=sample_evidence_rows,
    )

    with pytest.raises(ValueError, match="NEWS_BRIEF_STALE"):
        asyncio.run(save_brief(payload, auth_envelope, repo=repo))


def test_idor_cross_account_isolation(
    sample_evidence_rows: tuple[EvidenceRow, ...],
    test_db_path: str,
):
    repo = SqliteBriefRepository(db_path=test_db_path)
    ev_hash = calculate_evidence_hash(sample_evidence_rows)

    brief_alice = NewsEvidenceBriefArtifact(
        schema_version="1.0.0",
        brief_id="brief_alice_secret",
        artifact_id="art_alice_secret",
        authoring_run_id="run_alice",
        account_id="user_alice",
        title="Private Research Alice",
        objective="Internal memo",
        cluster_ids=("cluster_1",),
        evidence_rows=sample_evidence_rows,
        source_coverage=1.0,
        limitations=(),
        review_status="reviewed",
        evidence_hash=ev_hash,
        version=1,
        created_at="2026-09-02T12:00:00Z",
        expires_at="2026-09-03T12:00:00Z",
    )
    repo.save(brief_alice)

    # User Bob attempts to access Alice's brief
    bob_view = repo.get("brief_alice_secret", account_id="user_bob")
    assert bob_view is None  # IDOR prevented

    # User Bob listing briefs only sees Bob's briefs
    bob_list = repo.list_by_account("user_bob")
    assert len(bob_list) == 0

    # User Alice sees her brief
    alice_view = repo.get("brief_alice_secret", account_id="user_alice")
    assert alice_view is not None
    assert alice_view.title == "Private Research Alice"


def test_anonymous_save_forbidden(
    anon_envelope: TrustedExecutionEnvelope,
    sample_evidence_rows: tuple[EvidenceRow, ...],
    test_db_path: str,
):
    repo = SqliteBriefRepository(db_path=test_db_path)
    ev_hash = calculate_evidence_hash(sample_evidence_rows)

    payload = SaveBriefInput(
        proposal_id="prop_anon",
        evidence_hash=ev_hash,
        title="Anonymous brief",
        objective="Research",
        evidence_rows=sample_evidence_rows,
    )

    with pytest.raises(PermissionError, match="Anonymous accounts are not permitted"):
        asyncio.run(save_brief(payload, anon_envelope, repo=repo))

