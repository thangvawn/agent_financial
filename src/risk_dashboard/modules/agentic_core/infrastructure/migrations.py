from __future__ import annotations

AGENTIC_CORE_SQL = """
CREATE TABLE IF NOT EXISTS agentic_runs (
  run_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  surface TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_runs_account_created
  ON agentic_runs(account_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agentic_artifacts (
  artifact_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  authoring_run_id TEXT NOT NULL,
  artifact_type TEXT NOT NULL,
  domain TEXT NOT NULL,
  review_status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_artifacts_account_created
  ON agentic_artifacts(account_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agentic_action_receipts (
  receipt_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL UNIQUE,
  account_id TEXT NOT NULL,
  status TEXT NOT NULL,
  executed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agentic_memory_proposals (
  proposal_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  memory_type TEXT NOT NULL,
  provenance TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  created_at TEXT NOT NULL
);
"""


def ensure_agentic_tables(conn) -> None:
    conn.executescript(AGENTIC_CORE_SQL)
