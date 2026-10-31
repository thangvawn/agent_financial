"""Account-owned PDF storage. No user paths; files are outside all static mounts."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.config import get_db_path

MAX_UPLOAD_BYTES = 40 * 1024 * 1024
MAX_ACCOUNT_BYTES = 500 * 1024 * 1024
MAX_ACCOUNT_ITEMS = 1000
_pdf_lock = threading.Lock()
_SCHEMA = """
CREATE TABLE IF NOT EXISTS learning_library_items (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    source_key TEXT NOT NULL,
    origin TEXT NOT NULL CHECK(origin IN ('upload','catalog')),
    title TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL CHECK(kind IN ('book','paper','document')),
    source_url TEXT NOT NULL DEFAULT '',
    source_id TEXT NOT NULL DEFAULT '',
    content_role TEXT NOT NULL DEFAULT 'fulltext',
    page_count INTEGER,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    storage_name TEXT,
    status TEXT NOT NULL DEFAULT 'want_to_read'
        CHECK(status IN ('want_to_read','reading','completed')),
    current_page INTEGER NOT NULL DEFAULT 1,
    read_count INTEGER NOT NULL DEFAULT 0,
    first_opened_at TEXT,
    last_opened_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(account_id, source_key)
);
CREATE INDEX IF NOT EXISTS idx_learning_library_owner
    ON learning_library_items(account_id, updated_at DESC);
CREATE TABLE IF NOT EXISTS learning_library_events (
    item_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    PRIMARY KEY(item_id, event_id)
);
"""


def now():
    return datetime.now(timezone.utc).isoformat()


def public_item(row):
    item = dict(row)
    for private in ("account_id", "source_key", "storage_name"):
        item.pop(private)
    item["file_url"] = (
        f"/api/v1/public/learning/library/items/{item['id']}/file.pdf"
        if item["origin"] == "upload"
        else None
    )
    return item


def inspect_pdf(path: Path) -> int:
    import pypdfium2 as pdfium

    with path.open("rb") as file:
        prefix = file.read(8)
        file.seek(max(0, path.stat().st_size - 2048))
        tail = file.read()
    if not prefix.startswith(b"%PDF-") or b"%%EOF" not in tail:
        raise HTTPException(422, "File không phải PDF đầy đủ hoặc đã bị hỏng.")
    try:
        # PDFium is not thread-safe; serialize parsing across worker threads.
        with _pdf_lock, pdfium.PdfDocument(path) as document:
            pages = len(document)
        if not 1 <= pages <= 10000:
            raise ValueError("Invalid page count")
        return pages
    except (pdfium.PdfiumError, ValueError) as exc:
        raise HTTPException(
            422, "Không đọc được PDF. Hãy chọn file hợp lệ, không khóa mật khẩu."
        ) from exc


class PersonalLibrary:
    def __init__(self):
        self.root = get_db_path().parent / "learning_library_files"
        with open_app_state_db() as conn:
            conn.executescript(_SCHEMA)

    @staticmethod
    def _row(conn, owner, item_id):
        row = conn.execute(
            "SELECT * FROM learning_library_items WHERE id=? AND account_id=?", (item_id, owner)
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Không tìm thấy tài liệu trong kệ sách của bạn.")
        return row

    @staticmethod
    def _quota(conn, owner, incoming=0):
        count, size = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(size_bytes),0) FROM learning_library_items "
            "WHERE account_id=?",
            (owner,),
        ).fetchone()
        if count >= MAX_ACCOUNT_ITEMS or size + incoming > MAX_ACCOUNT_BYTES:
            raise HTTPException(
                413, "Kệ sách đã đầy (1.000 tài liệu hoặc 500 MB). Hãy xóa bớt tài liệu."
            )

    def list(self, owner):
        with open_app_state_db() as conn:
            rows = conn.execute(
                "SELECT * FROM learning_library_items WHERE account_id=? "
                "ORDER BY updated_at DESC, id",
                (owner,),
            ).fetchall()
        return {
            "items": [public_item(row) for row in rows],
            "used_bytes": sum(row["size_bytes"] for row in rows),
            "max_bytes": MAX_ACCOUNT_BYTES,
            "max_file_bytes": MAX_UPLOAD_BYTES,
            "max_items": MAX_ACCOUNT_ITEMS,
        }

    def get(self, owner, item_id):
        with open_app_state_db() as conn:
            return public_item(self._row(conn, owner, item_id))

    def _insert(self, conn, owner, metadata, **extra):
        timestamp = now()
        values = {
            "id": uuid4().hex,
            "account_id": owner,
            **metadata,
            **extra,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        keys = ",".join(values)
        placeholders = ",".join("?" for _ in values)
        conn.execute(
            f"INSERT INTO learning_library_items ({keys}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        return public_item(self._row(conn, owner, values["id"]))

    def save_catalog(self, owner, metadata):
        source_key = "url:" + hashlib.sha256(metadata["source_url"].encode()).hexdigest()
        with open_app_state_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT * FROM learning_library_items WHERE account_id=? AND source_key=?",
                (owner, source_key),
            ).fetchone()
            if existing:
                return public_item(existing)
            self._quota(conn, owner)
            return self._insert(conn, owner, metadata, source_key=source_key, origin="catalog")

    def upload(self, owner, file, metadata):
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = None
        final = None
        committed = False
        try:
            digest = hashlib.sha256()
            size = 0
            with tempfile.NamedTemporaryFile(dir=self.root, suffix=".part", delete=False) as output:
                temporary = Path(output.name)
                while chunk := file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, "Mỗi PDF tối đa 40 MB.")
                    digest.update(chunk)
                    output.write(chunk)
            pages = inspect_pdf(temporary)
            source_key = "sha256:" + digest.hexdigest()
            with open_app_state_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                existing = conn.execute(
                    "SELECT * FROM learning_library_items WHERE account_id=? AND source_key=?",
                    (owner, source_key),
                ).fetchone()
                if existing:
                    return public_item(existing), False
                self._quota(conn, owner, size)
                storage_name = uuid4().hex + ".pdf"
                final = self.root / storage_name
                os.replace(temporary, final)
                result = self._insert(
                    conn,
                    owner,
                    metadata,
                    source_key=source_key,
                    origin="upload",
                    storage_name=storage_name,
                    page_count=pages,
                    size_bytes=size,
                )
            committed = True
            return result, True
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
            if final and not committed:
                final.unlink(missing_ok=True)

    def update(self, owner, item_id, patch):
        with open_app_state_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row(conn, owner, item_id)
            if patch.get("current_page", 1) > (row["page_count"] or 10000):
                raise HTTPException(422, "Trang đọc vượt quá số trang của tài liệu.")
            if "status" in patch:
                patch["completed_at"] = (
                    (row["completed_at"] or now()) if patch["status"] == "completed" else None
                )
            if patch:
                patch["updated_at"] = now()
                assignments = ",".join(f"{key}=?" for key in patch)
                conn.execute(
                    f"UPDATE learning_library_items SET {assignments} WHERE id=? AND account_id=?",
                    (*patch.values(), item_id, owner),
                )
            return public_item(self._row(conn, owner, item_id))

    def opened(self, owner, item_id, event_id):
        with open_app_state_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._row(conn, owner, item_id)
            inserted = conn.execute(
                "INSERT OR IGNORE INTO learning_library_events VALUES (?,?)", (item_id, event_id)
            ).rowcount
            if inserted:
                timestamp = now()
                conn.execute(
                    """UPDATE learning_library_items
                    SET read_count=read_count+1, first_opened_at=COALESCE(first_opened_at,?),
                    last_opened_at=?, updated_at=?,
                    status=CASE WHEN status='want_to_read' THEN 'reading' ELSE status END
                    WHERE id=? AND account_id=?""",
                    (timestamp, timestamp, timestamp, item_id, owner),
                )
                # Keep a bounded retry window per document; the aggregate history is durable.
                conn.execute(
                    """DELETE FROM learning_library_events WHERE item_id=? AND rowid NOT IN
                    (SELECT rowid FROM learning_library_events WHERE item_id=?
                    ORDER BY rowid DESC LIMIT 100)""",
                    (item_id, item_id),
                )
            return public_item(self._row(conn, owner, item_id))

    def _file_path(self, row):
        name = row["storage_name"] or ""
        path = self.root / name
        if (
            not re.fullmatch(r"[a-f0-9]{32}\.pdf", name)
            or path.resolve().parent != self.root.resolve()
        ):
            raise HTTPException(404, "Không tìm thấy file PDF.")
        return path

    def file_path(self, owner, item_id):
        with open_app_state_db() as conn:
            path = self._file_path(self._row(conn, owner, item_id))
        if not path.is_file():
            raise HTTPException(404, "Không tìm thấy file PDF.")
        return path

    def delete(self, owner, item_id):
        path = None
        with open_app_state_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row(conn, owner, item_id)
            if row["origin"] == "upload":
                path = self._file_path(row)
                # Failure leaves the row intact so a user can retry deletion.
                path.unlink(missing_ok=True)
            conn.execute("DELETE FROM learning_library_events WHERE item_id=?", (item_id,))
            conn.execute(
                "DELETE FROM learning_library_items WHERE id=? AND account_id=?", (item_id, owner)
            )
