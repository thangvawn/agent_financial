from __future__ import annotations

from unittest.mock import MagicMock
from dataclasses import dataclass

from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.bctc import (
    BctcSummaryReader,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.market import (
    MarketSummaryReader,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.news import (
    NewsSummaryReader,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.simulation import (
    SimulationSummaryReader,
)


@dataclass
class DummyMemo:
    memo_id: str = "memo_101"
    subject: str = "FPT Financial Report Q2"
    interpretations: tuple[str, ...] = ("Biên lợi nhuận gộp duy trì ở mức cao 38%.",)
    unresolved_questions: tuple[str, ...] = ()
    reviewer_status: str = "approved"
    is_stale: bool = False
    expires_at: str = "2026-10-01T00:00:00Z"
    created_at: str = "2026-09-01T00:00:00Z"
    updated_at: str = "2026-09-01T00:00:00Z"


@dataclass
class DummyExperiment:
    experiment_id: str = "exp_202"
    experiment_type: str = "monte_carlo"
    status: str = "completed"
    review_status: str = "approved"
    review_notes: str = "Phân tích VaR danh mục đạt chuẩn."
    created_at: str = "2026-09-01T00:00:00Z"
    reviewed_at: str = "2026-09-01T01:00:00Z"


@dataclass
class DummyBrief:
    brief_id: str = "brief_303"
    title: str = "Tổng quan thị trường phiên chiều"
    objective: str = "VN-Index tăng điểm nhờ nhóm cổ phiếu công nghệ."
    version: int = 1
    review_status: str = "reviewed"
    created_at: str = "2026-09-01T00:00:00Z"
    expires_at: str = "2026-10-01T00:00:00Z"


@dataclass
class DummyMarketArtifact:
    artifact_id: str = "art_404"
    portfolio_id: str = "growth_tech"
    summary: str = "Danh mục có độ biến động Sharpe Ratio đạt 1.8."
    created_at: str = "2026-09-01T00:00:00Z"
    expires_at: str = "2026-10-01T00:00:00Z"


def test_bctc_summary_reader_returns_valid_summary() -> None:
    mock_repo = MagicMock()
    mock_repo.list_memos_by_account.return_value = [DummyMemo()]
    reader = BctcSummaryReader(repo=mock_repo)

    summaries = reader.list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="2026-09-02T00:00:00Z"
    )
    assert len(summaries) == 1
    s = summaries[0]
    assert s.surface == "bctc"
    assert s.allowed_action_type == "view_research_memo"
    assert s.allowed_cta_path == "/bctc?memo_id=memo_101"
    assert s.review_status == "reviewed"


def test_bctc_summary_reader_skips_unreviewed_and_expired() -> None:
    unreviewed = DummyMemo(reviewer_status="pending")
    expired = DummyMemo(memo_id="exp_1", expires_at="2026-08-01T00:00:00Z")
    mock_repo = MagicMock()
    mock_repo.list_memos_by_account.return_value = [unreviewed, expired]
    reader = BctcSummaryReader(repo=mock_repo)

    summaries = reader.list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="2026-09-02T00:00:00Z"
    )
    assert len(summaries) == 0


def test_simulation_summary_reader() -> None:
    mock_repo = MagicMock()
    mock_repo.list_by_user.return_value = [DummyExperiment()]
    reader = SimulationSummaryReader(repo=mock_repo)

    summaries = reader.list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="2026-09-02T00:00:00Z"
    )
    assert len(summaries) == 1
    s = summaries[0]
    assert s.surface == "simulation"
    assert s.allowed_action_type == "refresh_artifact"
    assert s.allowed_cta_path == "/simulation?experiment_id=exp_202"


def test_news_summary_reader() -> None:
    mock_repo = MagicMock()
    mock_repo.list_by_account.return_value = [DummyBrief()]
    reader = NewsSummaryReader(repo=mock_repo)

    summaries = reader.list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="2026-09-02T00:00:00Z"
    )
    assert len(summaries) == 1
    s = summaries[0]
    assert s.surface == "news"
    assert s.allowed_action_type == "read_news_brief"
    assert s.allowed_cta_path == "/news?brief_id=brief_303"


def test_market_summary_reader() -> None:
    mock_repo = MagicMock()
    mock_repo.list_by_account.return_value = [DummyMarketArtifact()]
    reader = MarketSummaryReader(repo=mock_repo)

    summaries = reader.list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="2026-09-02T00:00:00Z"
    )
    assert len(summaries) == 1
    s = summaries[0]
    assert s.surface == "market"
    assert s.allowed_action_type == "read_market_education"
    assert s.allowed_cta_path == "/market?artifact_id=art_404"


def test_all_adapters_handle_exception_gracefully() -> None:
    failing_repo = MagicMock()
    failing_repo.list_memos_by_account.side_effect = RuntimeError("DB error")
    failing_repo.list_by_user.side_effect = RuntimeError("DB error")
    failing_repo.list_by_account.side_effect = RuntimeError("DB error")

    assert BctcSummaryReader(repo=failing_repo).list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="now"
    ) == ()
    assert SimulationSummaryReader(repo=failing_repo).list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="now"
    ) == ()
    assert NewsSummaryReader(repo=failing_repo).list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="now"
    ) == ()
    assert MarketSummaryReader(repo=failing_repo).list_reviewed_summaries(
        account_id="acc_1", scopes=(), as_of="now"
    ) == ()
