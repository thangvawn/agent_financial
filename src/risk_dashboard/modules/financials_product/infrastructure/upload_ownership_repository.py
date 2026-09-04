from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from typing import Any

from risk_dashboard.modules.financials_product.domain.ports import UploadOwnershipPort
from risk_dashboard.platform.database import open_app_state_db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


import urllib.parse


def validate_upload_path(upload_id: str, base_dir: str) -> str:
    """Resolve upload path and reject directory traversal attempts."""
    decoded = urllib.parse.unquote(upload_id)
    if ".." in decoded or "/" in decoded or "\\" in decoded:
        # If traversal elements present after unquoting, check if resolving goes outside or violates clean basename
        clean_target = os.path.realpath(os.path.join(base_dir, decoded))
        safe_base = os.path.realpath(base_dir)
        if not clean_target.startswith(safe_base + os.sep) and clean_target != safe_base:
            raise PermissionError(f"Path traversal detected for upload_id: {upload_id}")
        if decoded != os.path.basename(decoded):
            raise PermissionError(f"Path traversal detected for upload_id: {upload_id}")

    safe_base = os.path.realpath(base_dir)
    target_path = os.path.realpath(os.path.join(base_dir, upload_id))
    if not target_path.startswith(safe_base + os.sep) and target_path != safe_base:
        raise PermissionError(f"Path traversal detected for upload_id: {upload_id}")
    return target_path


@dataclass(frozen=True)
class UploadRecord:
    upload_id: str
    account_id: str
    filename: str
    upload_path: str
    expires_at: str | None
    created_at: str


class UploadOwnershipRepository(UploadOwnershipPort):
    """SQLite repository for binding private uploads to accounts."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        if self._db_path:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            return conn
        return open_app_state_db()

    def bind_upload(
        self,
        upload_id: str,
        account_id: str,
        filename: str,
        upload_path: str,
        expires_at: str | None = None,
    ) -> None:
        now = _now_iso()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO bctc_upload_ownership (
                    upload_id, account_id, filename, upload_path, expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(upload_id) DO UPDATE SET
                    account_id = excluded.account_id,
                    filename = excluded.filename,
                    upload_path = excluded.upload_path,
                    expires_at = excluded.expires_at
                """,
                (upload_id, account_id, filename, upload_path, expires_at, now),
            )

    def check_ownership(self, upload_id: str, account_id: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM bctc_upload_ownership WHERE upload_id = ? AND account_id = ?",
                (upload_id, account_id),
            ).fetchone()
            return row is not None

    def get_upload(self, upload_id: str, account_id: str) -> UploadRecord | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM bctc_upload_ownership WHERE upload_id = ? AND account_id = ?",
                (upload_id, account_id),
            ).fetchone()
            if not row:
                return None
            return UploadRecord(
                upload_id=row["upload_id"],
                account_id=row["account_id"],
                filename=row["filename"],
                upload_path=row["upload_path"],
                expires_at=row["expires_at"],
                created_at=row["created_at"],
            )

    def delete_expired(self, now_iso: str | None = None) -> int:
        now = now_iso or _now_iso()
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM bctc_upload_ownership WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,),
            )
            return cursor.rowcount
