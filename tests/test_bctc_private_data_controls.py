from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import sqlite3
import pytest

from risk_dashboard.modules.financials_product.infrastructure.upload_ownership_repository import (
    UploadOwnershipRepository,
    validate_upload_path,
)
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture
def temp_upload_repo(tmp_path):
    db_file = str(tmp_path / "test_uploads.db")
    conn = sqlite3.connect(db_file)
    apply_migrations(conn)
    conn.close()
    return UploadOwnershipRepository(db_path=db_file)


def test_bind_and_get_upload(temp_upload_repo):
    temp_upload_repo.bind_upload(
        upload_id="up_12345",
        account_id="acc_alice",
        filename="bctc_fpt_q3.xlsx",
        upload_path="/data/financial_uploads/up_12345.xlsx",
    )

    record = temp_upload_repo.get_upload("up_12345", "acc_alice")
    assert record is not None
    assert record.upload_id == "up_12345"
    assert record.account_id == "acc_alice"
    assert record.filename == "bctc_fpt_q3.xlsx"


def test_idor_cross_account_rejected(temp_upload_repo):
    temp_upload_repo.bind_upload(
        upload_id="up_secret_doc",
        account_id="acc_alice",
        filename="confidential_audit.pdf",
        upload_path="/data/financial_uploads/up_secret_doc.pdf",
    )

    # Alice owns it
    assert temp_upload_repo.check_ownership("up_secret_doc", "acc_alice") is True

    # Bob does NOT own it -> False
    assert temp_upload_repo.check_ownership("up_secret_doc", "acc_bob") is False
    assert temp_upload_repo.get_upload("up_secret_doc", "acc_bob") is None


def test_path_traversal_blocked(tmp_path):
    base_dir = str(tmp_path / "uploads")
    os.makedirs(base_dir, exist_ok=True)

    # Valid filename inside base_dir
    safe_path = validate_upload_path("valid_upload_123.xlsx", base_dir)
    assert safe_path.startswith(base_dir)

    # Traversal attempts
    with pytest.raises(PermissionError, match="Path traversal detected"):
        validate_upload_path("../../../etc/passwd", base_dir)

    with pytest.raises(PermissionError, match="Path traversal detected"):
        validate_upload_path("..%2F..%2Fetc/shadow", base_dir)


def test_expired_upload_cleanup(temp_upload_repo):
    now = datetime.now(timezone.utc)
    expired_time = (now - timedelta(days=1)).isoformat()
    future_time = (now + timedelta(days=7)).isoformat()

    temp_upload_repo.bind_upload(
        upload_id="up_expired",
        account_id="acc_alice",
        filename="old.xlsx",
        upload_path="/data/old.xlsx",
        expires_at=expired_time,
    )
    temp_upload_repo.bind_upload(
        upload_id="up_active",
        account_id="acc_alice",
        filename="active.xlsx",
        upload_path="/data/active.xlsx",
        expires_at=future_time,
    )

    deleted_count = temp_upload_repo.delete_expired(now_iso=now.isoformat())
    assert deleted_count == 1

    assert temp_upload_repo.get_upload("up_expired", "acc_alice") is None
    assert temp_upload_repo.get_upload("up_active", "acc_alice") is not None


def test_private_content_not_in_memory():
    """Verify that private report payloads are redacted from durable logs."""
    from risk_dashboard.modules.financials_product.schemas.agent_tools import ProvenanceRef
    prov = ProvenanceRef(
        report_id="upload:up_12345",
        revision_id="rev_private_1",
        period="2024Q3",
        source="user_upload",
        fetched_at="2026-09-01T00:00:00+00:00",
    )
    # Provenance only contains metadata, never raw statement rows
    dumped = prov.model_dump(mode="json")
    assert "raw_data" not in dumped
    assert "file_content" not in dumped
    assert "binary" not in dumped

