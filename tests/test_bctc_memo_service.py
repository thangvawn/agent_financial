from __future__ import annotations

import sqlite3
import pytest

from risk_dashboard.modules.financials_product.application.memo_service import MemoService
from risk_dashboard.modules.financials_product.infrastructure.sqlite_memo_repository import (
    SqliteMemoRepository,
)
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    EvidenceRow,
    NumericValue,
    ProvenanceRef,
)
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture
def temp_memo_repo(tmp_path):
    db_file = str(tmp_path / "test_memos.db")
    conn = sqlite3.connect(db_file)
    apply_migrations(conn)
    conn.close()
    return SqliteMemoRepository(db_path=db_file)


def _make_evidence_row(val: float = 50000.0, rev_id: str = "rev_100") -> EvidenceRow:
    prov = ProvenanceRef(
        report_id="report:fpt",
        revision_id=rev_id,
        period="2024Q3",
        source="fpt_ir",
        fetched_at="2026-09-01T00:00:00+00:00",
        statement="income_statement",
    )
    nv = NumericValue(value=val, unit="VND_bn", provenance=prov)
    return EvidenceRow(claim=f"Doanh thu đạt {val} tỷ", kind="fact", value=nv, citation=prov)


def test_create_and_get_memo(temp_memo_repo):
    service = MemoService(repo=temp_memo_repo)
    row = _make_evidence_row(50000.0)
    memo = service.create_memo(
        account_id="acc_user_1",
        subject="FPT Q3/2024 Revenue Memo",
        report_refs=(row.citation,),
        scope="Verify Q3 revenue growth",
        evidence_rows=(row,),
        interpretations=("Doanh thu tăng trưởng mạnh",),
        reviewer_status="approved",
    )
    assert memo.memo_id.startswith("memo_")
    assert memo.subject == "FPT Q3/2024 Revenue Memo"
    assert memo.is_stale is False

    retrieved = service.get_memo(account_id="acc_user_1", memo_id=memo.memo_id)
    assert retrieved.memo_id == memo.memo_id
    assert len(retrieved.evidence_rows) == 1
    assert retrieved.evidence_rows[0].claim == row.claim


def test_staleness_detection(temp_memo_repo):
    service = MemoService(repo=temp_memo_repo)
    row = _make_evidence_row(50000.0, rev_id="rev_old_version")
    memo = service.create_memo(
        account_id="acc_user_1",
        subject="FPT Memo",
        report_refs=(row.citation,),
        scope="Staleness test",
        evidence_rows=(row,),
    )
    # Check with same revision -> not stale
    is_stale = service.check_staleness(
        account_id="acc_user_1",
        memo_id=memo.memo_id,
        current_revision_id="rev_old_version",
    )
    assert is_stale is False

    # Check with new revision -> marked stale
    is_stale_new = service.check_staleness(
        account_id="acc_user_1",
        memo_id=memo.memo_id,
        current_revision_id="rev_new_updated_version",
    )
    assert is_stale_new is True

    # Check that repo now reflects is_stale
    updated_memo = service.get_memo(account_id="acc_user_1", memo_id=memo.memo_id)
    assert updated_memo.is_stale is True


def test_account_isolation(temp_memo_repo):
    service = MemoService(repo=temp_memo_repo)
    row = _make_evidence_row()
    memo = service.create_memo(
        account_id="acc_alice",
        subject="Alice's Private Memo",
        report_refs=(row.citation,),
        scope="Private analysis",
        evidence_rows=(row,),
    )

    # Bob tries to get Alice's memo -> KeyError
    with pytest.raises(KeyError, match="not found for account 'acc_bob'"):
        service.get_memo(account_id="acc_bob", memo_id=memo.memo_id)


def test_archive_memo(temp_memo_repo):
    service = MemoService(repo=temp_memo_repo)
    row = _make_evidence_row()
    memo = service.create_memo(
        account_id="acc_alice",
        subject="Memo to delete",
        report_refs=(row.citation,),
        scope="Delete test",
        evidence_rows=(row,),
    )

    deleted = service.archive_memo(account_id="acc_alice", memo_id=memo.memo_id)
    assert deleted is True

    with pytest.raises(KeyError):
        service.get_memo(account_id="acc_alice", memo_id=memo.memo_id)

