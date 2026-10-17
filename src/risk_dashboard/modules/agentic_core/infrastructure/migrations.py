from __future__ import annotations

AGENTIC_CORE_SQL = """
CREATE TABLE IF NOT EXISTS agentic_runs (
  run_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  surface TEXT NOT NULL,
  status TEXT NOT NULL,
  correlation_id TEXT,
  idempotency_key TEXT,
  capability_id TEXT,
  task_input_json TEXT NOT NULL DEFAULT '{}',
  result_payload_json TEXT,
  usage_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_runs_account_created
  ON agentic_runs(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agentic_runs_idempotency
  ON agentic_runs(account_id, idempotency_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_agentic_runs_account_idempotency_unique
  ON agentic_runs(account_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS agentic_steps (
  step_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  step_index INTEGER NOT NULL,
  agent_id TEXT NOT NULL,
  node_name TEXT NOT NULL,
  status TEXT NOT NULL,
  input_payload_json TEXT NOT NULL DEFAULT '{}',
  output_payload_json TEXT NOT NULL DEFAULT '{}',
  started_at TEXT NOT NULL,
  completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_agentic_steps_run_step
  ON agentic_steps(run_id, step_index);

CREATE TABLE IF NOT EXISTS agentic_tool_calls (
  tool_call_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  latency_ms INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_tool_calls_run
  ON agentic_tool_calls(run_id, created_at);

CREATE TABLE IF NOT EXISTS agentic_artifacts (
  artifact_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  authoring_run_id TEXT NOT NULL,
  artifact_type TEXT NOT NULL,
  domain TEXT NOT NULL,
  review_status TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_agentic_artifacts_account_created
  ON agentic_artifacts(account_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agentic_action_proposals (
  proposal_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  operation TEXT NOT NULL,
  target_ref_json TEXT NOT NULL,
  payload_preview_json TEXT NOT NULL,
  risk_class TEXT NOT NULL,
  requires_confirmation INTEGER NOT NULL DEFAULT 1,
  policy_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_action_proposals_account
  ON agentic_action_proposals(account_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agentic_action_receipts (
  receipt_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL UNIQUE,
  account_id TEXT NOT NULL,
  status TEXT NOT NULL,
  executed_at TEXT NOT NULL,
  result_ref_json TEXT,
  error_code TEXT
);
CREATE INDEX IF NOT EXISTS idx_agentic_action_receipts_account
  ON agentic_action_receipts(account_id, executed_at DESC);

CREATE TABLE IF NOT EXISTS agentic_memory_proposals (
  proposal_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  memory_type TEXT NOT NULL,
  content TEXT NOT NULL,
  provenance TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  sensitivity TEXT NOT NULL DEFAULT 'normal',
  ttl_days INTEGER,
  status TEXT NOT NULL DEFAULT 'proposed',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_memory_proposals_account
  ON agentic_memory_proposals(account_id, created_at DESC);

CREATE VIEW IF NOT EXISTS agentic_core_runs AS SELECT * FROM agentic_runs;
CREATE VIEW IF NOT EXISTS agentic_core_artifacts AS SELECT * FROM agentic_artifacts;
CREATE VIEW IF NOT EXISTS agentic_core_action_proposals AS SELECT * FROM agentic_action_proposals;
"""


def ensure_agentic_tables(conn) -> None:
    conn.executescript(AGENTIC_CORE_SQL)
