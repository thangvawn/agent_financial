from __future__ import annotations

import sqlite3

DDL_STATEMENTS = """
CREATE TABLE IF NOT EXISTS internal_ops_investigations (
  investigation_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  investigation_type TEXT NOT NULL,
  purpose TEXT NOT NULL,
  status TEXT NOT NULL,
  request_json TEXT NOT NULL,
  report_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ops_investigations_account ON internal_ops_investigations(account_id, created_at DESC);

CREATE TABLE IF NOT EXISTS internal_ops_reports (
  report_id TEXT PRIMARY KEY,
  investigation_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS internal_ops_evidence (
  evidence_id TEXT PRIMARY KEY,
  investigation_id TEXT NOT NULL,
  source_module TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  item_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ops_evidence_inv ON internal_ops_evidence(investigation_id);

CREATE TABLE IF NOT EXISTS internal_ops_access_audit (
  audit_id TEXT PRIMARY KEY,
  investigation_id TEXT,
  account_id TEXT NOT NULL,
  scope_snapshot TEXT NOT NULL,
  purpose TEXT NOT NULL,
  tool_id TEXT,
  decision TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


def init_ops_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL_STATEMENTS)
    conn.commit()

