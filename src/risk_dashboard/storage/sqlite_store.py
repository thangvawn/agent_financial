from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS ingest_runs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  market_label TEXT,
  macro_label TEXT,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  parquet_path TEXT NOT NULL,
  manifest_path TEXT,
  n_rows INTEGER,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingest_created ON ingest_runs(created_at DESC);
"""


@dataclass
class IngestRecord:
    id: str
    created_at: str
    market_label: str | None
    macro_label: str | None
    start_date: str
    end_date: str
    parquet_path: str
    manifest_path: str | None
    n_rows: int | None
    meta: dict[str, Any]


def open_registry(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


class IngestRegistry:
    """Đăng ký kết quả ingest (Parquet + manifest) để API/job tra cứu."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = open_registry(self.db_path)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def register(
        self,
        *,
        parquet_path: str | Path,
        manifest_path: str | Path | None = None,
        market_label: str = "",
        macro_label: str = "",
        start_date: str = "",
        end_date: str = "",
        n_rows: int | None = None,
        meta: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> str:
        rid = run_id or str(uuid.uuid4())
        created = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(meta or {}, ensure_ascii=False)
        self.conn().execute(
            """
            INSERT INTO ingest_runs (
              id, created_at, market_label, macro_label, start_date, end_date,
              parquet_path, manifest_path, n_rows, meta_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rid,
                created,
                market_label,
                macro_label,
                start_date,
                end_date,
                str(parquet_path),
                str(manifest_path) if manifest_path else None,
                n_rows,
                meta_json,
            ),
        )
        self.conn().commit()
        return rid

    def latest(self) -> IngestRecord | None:
        cur = self.conn().execute(
            "SELECT * FROM ingest_runs ORDER BY created_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def _row_to_record(self, row: sqlite3.Row) -> IngestRecord:
        d = dict(row)
        meta = json.loads(d.get("meta_json") or "{}")
        return IngestRecord(
            id=d["id"],
            created_at=d["created_at"],
            market_label=d.get("market_label"),
            macro_label=d.get("macro_label"),
            start_date=d["start_date"],
            end_date=d["end_date"],
            parquet_path=d["parquet_path"],
            manifest_path=d.get("manifest_path"),
            n_rows=d.get("n_rows"),
            meta=meta,
        )
