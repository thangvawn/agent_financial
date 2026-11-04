"""Ordered SQLite migrations for the shared Northstar DB."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from risk_dashboard.platform.database.social_schema import SOCIAL_SQL

_PACKAGE = Path(__file__).resolve().parent
_SCHEMA_DIR = _PACKAGE / "schema"

# (migration_id, sql_text_or_path)
def _load_baseline() -> str:
    return (_SCHEMA_DIR / "baseline.sql").read_text(encoding="utf-8")


INGEST_RUNS_SQL = """
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

COMMODITIES_SQL = """
CREATE TABLE IF NOT EXISTS commodity_instruments (
  symbol TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  provider_symbol TEXT,
  category TEXT NOT NULL,
  unit TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commodity_quotes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL REFERENCES commodity_instruments(symbol),
  as_of TEXT NOT NULL,
  price REAL,
  change REAL,
  change_pct REAL,
  high_24h REAL,
  low_24h REAL,
  volume_24h REAL,
  source TEXT NOT NULL,
  freshness TEXT NOT NULL,
  raw_json TEXT,
  UNIQUE(symbol, as_of)
);
CREATE INDEX IF NOT EXISTS idx_commodity_quotes_symbol_time ON commodity_quotes(symbol, as_of DESC);
"""

NEWS_HIGHLIGHT_SNAPSHOTS_SQL = """
CREATE TABLE IF NOT EXISTS news_highlight_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  period_kind TEXT NOT NULL CHECK (period_kind IN ('day', 'week', 'month')),
  period_key TEXT NOT NULL,
  timezone TEXT NOT NULL,
  window_start TEXT NOT NULL,
  window_end TEXT NOT NULL,
  items_json TEXT NOT NULL,
  item_count INTEGER NOT NULL CHECK (item_count BETWEEN 0 AND 10),
  generated_at TEXT NOT NULL,
  source_run_id TEXT,
  UNIQUE(period_kind, period_key)
);
CREATE INDEX IF NOT EXISTS idx_news_highlight_snapshots_period
ON news_highlight_snapshots(period_kind, period_key);
"""

TELEGRAM_NEWS_DELIVERIES_SQL = """
CREATE TABLE IF NOT EXISTS telegram_news_deliveries (
  delivery_key TEXT PRIMARY KEY,
  period_kind TEXT NOT NULL CHECK (period_kind IN ('day', 'week', 'month')),
  period_key TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  telegram_message_ids TEXT,
  delivered_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_telegram_news_deliveries_period
ON telegram_news_deliveries(period_kind, period_key, chat_id);
"""

TELEGRAM_NEWS_TRANSLATIONS_SQL = """
CREATE TABLE IF NOT EXISTS telegram_news_translations (
  fingerprint TEXT PRIMARY KEY,
  headline_vi TEXT NOT NULL,
  summary_vi TEXT NOT NULL,
  translated_at TEXT NOT NULL
);
"""

TELEGRAM_MARKET_DELIVERIES_SQL = """
CREATE TABLE IF NOT EXISTS telegram_market_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    attempt_no INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL,
    locked_by TEXT,
    lock_expires_at TEXT,
    heartbeat_at TEXT,
    payload_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sent_at TEXT,
    last_error TEXT,
    UNIQUE(report_date, chat_id, mode, attempt_no)
);

CREATE TABLE IF NOT EXISTS telegram_market_delivery_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    payload_hash TEXT,
    status TEXT NOT NULL,
    telegram_message_id INTEGER,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(delivery_id, chunk_index),
    FOREIGN KEY(delivery_id) REFERENCES telegram_market_deliveries(id) ON DELETE CASCADE
);
"""

AI_TUTOR_SQL = """
CREATE TABLE IF NOT EXISTS ai_conversation_sessions (
  conversation_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  surface TEXT NOT NULL DEFAULT 'learn',
  context_id TEXT,
  context_json TEXT NOT NULL DEFAULT '{}',
  prompt_version TEXT NOT NULL DEFAULT 'v1',
  policy_version TEXT NOT NULL DEFAULT 'v1',
  status TEXT NOT NULL DEFAULT 'active',
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_conversation_sessions_user_id ON ai_conversation_sessions(user_id);

CREATE TABLE IF NOT EXISTS ai_messages (
  message_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  sender TEXT NOT NULL,
  content TEXT NOT NULL,
  classified_intent TEXT,
  risk_labels_json TEXT NOT NULL DEFAULT '[]',
  structured_output_json TEXT NOT NULL DEFAULT '{}',
  citations_json TEXT NOT NULL DEFAULT '[]',
  numeric_claims_json TEXT NOT NULL DEFAULT '[]',
  tool_calls_json TEXT NOT NULL DEFAULT '[]',
  trace_id TEXT,
  idempotency_key TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation_id ON ai_messages(conversation_id);

CREATE TABLE IF NOT EXISTS ai_feedback (
  feedback_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  message_id TEXT NOT NULL,
  rating INTEGER NOT NULL,
  reason_code TEXT NOT NULL,
  free_text TEXT,
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(message_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_conversation_id ON ai_feedback(conversation_id);

CREATE TABLE IF NOT EXISTS ai_event_logs (
  event_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  surface TEXT NOT NULL,
  intent TEXT NOT NULL,
  route_decision TEXT NOT NULL,
  guardrail_triggered INTEGER NOT NULL DEFAULT 0,
  tool_calls_json TEXT NOT NULL DEFAULT '[]',
  latency_ms INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_event_logs_conversation_id ON ai_event_logs(conversation_id);
"""

LEARNING_AGENT_SQL = """
CREATE TABLE IF NOT EXISTS learning_agent_checkpoints (
  checkpoint_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  prompt TEXT NOT NULL,
  options_json TEXT NOT NULL DEFAULT '[]',
  correct_answer TEXT NOT NULL,
  explanation TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_learning_agent_checkpoints_account ON learning_agent_checkpoints(account_id);

CREATE TABLE IF NOT EXISTS learning_verified_events (
  event_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  checkpoint_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  score INTEGER NOT NULL,
  passed INTEGER NOT NULL,
  rubric_evidence_json TEXT NOT NULL DEFAULT '[]',
  misconceptions_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_learning_verified_events_account ON learning_verified_events(account_id);

CREATE TABLE IF NOT EXISTS learning_progress_receipts (
  receipt_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  verified_event_id TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  confirmation_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  status TEXT NOT NULL,
  quiz_score INTEGER,
  created_at TEXT NOT NULL,
  UNIQUE(account_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_learning_progress_receipts_account ON learning_progress_receipts(account_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_receipts_event ON learning_progress_receipts(verified_event_id);

CREATE VIRTUAL TABLE IF NOT EXISTS learning_fts_index USING fts5(
  lesson_id UNINDEXED,
  section_id UNINDEXED,
  source_id UNINDEXED,
  content_version UNINDEXED,
  title,
  content
);

CREATE TABLE IF NOT EXISTS learning_video_transcripts (
  lesson_id TEXT NOT NULL,
  source_key TEXT NOT NULL,
  status TEXT NOT NULL,
  source TEXT NOT NULL,
  language TEXT NOT NULL,
  transcript_hash TEXT NOT NULL,
  segments_json TEXT NOT NULL,
  duration_seconds REAL NOT NULL DEFAULT 0,
  warnings_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (lesson_id, source_key)
);
CREATE INDEX IF NOT EXISTS idx_learning_video_transcripts_hash
  ON learning_video_transcripts(transcript_hash);
CREATE TABLE IF NOT EXISTS learning_video_quizzes (
  lesson_id TEXT NOT NULL,
  transcript_hash TEXT NOT NULL,
  questions_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (lesson_id, transcript_hash)
);
CREATE TABLE IF NOT EXISTS learning_video_checkpoints (
  checkpoint_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  transcript_hash TEXT NOT NULL,
  question_json TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_learning_video_checkpoints_account
  ON learning_video_checkpoints(account_id, lesson_id);
"""

BCTC_EVIDENCE_MEMOS_SQL = """
CREATE TABLE IF NOT EXISTS bctc_evidence_memos (
    memo_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    report_refs_json TEXT NOT NULL,
    scope TEXT NOT NULL,
    evidence_rows_json TEXT NOT NULL,
    calculations_json TEXT NOT NULL,
    interpretations_json TEXT NOT NULL,
    unresolved_questions_json TEXT NOT NULL,
    limitations_json TEXT NOT NULL,
    reviewer_status TEXT NOT NULL DEFAULT 'pending',
    is_stale INTEGER NOT NULL DEFAULT 0,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bctc_memos_account ON bctc_evidence_memos(account_id);
"""

BCTC_UPLOAD_OWNERSHIP_SQL = """
CREATE TABLE IF NOT EXISTS bctc_upload_ownership (
    upload_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    upload_path TEXT NOT NULL,
    expires_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bctc_upload_owner ON bctc_upload_ownership(account_id);
"""

SIMULATION_SPECS_SQL = """
CREATE TABLE IF NOT EXISTS simulation_experiment_specs (
    spec_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    schema_version TEXT NOT NULL DEFAULT '1.0.0',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sim_specs_account ON simulation_experiment_specs(account_id);
"""

SIMULATION_PROPOSALS_SQL = """
CREATE TABLE IF NOT EXISTS simulation_action_proposals (
    proposal_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    confirmation_token TEXT NOT NULL,
    idempotency_key TEXT,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sim_proposals_account ON simulation_action_proposals(account_id);
CREATE INDEX IF NOT EXISTS idx_sim_proposals_idempotency ON simulation_action_proposals(account_id, idempotency_key);
"""

SIMULATION_RECEIPTS_SQL = """
CREATE TABLE IF NOT EXISTS simulation_action_receipts (
    receipt_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    status TEXT NOT NULL,
    run_artifact_id TEXT,
    error_code TEXT,
    executed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sim_receipts_account ON simulation_action_receipts(account_id);
CREATE INDEX IF NOT EXISTS idx_sim_receipts_proposal ON simulation_action_receipts(proposal_id);
"""

HOME_JOURNEY_SQL = """
CREATE TABLE IF NOT EXISTS home_journey_cards (
    card_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    schema_version TEXT NOT NULL DEFAULT '1.0.0',
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    action_json TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    invalidated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_hjc_account ON home_journey_cards(account_id);

CREATE TABLE IF NOT EXISTS home_journey_feedback (
    receipt_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    action TEXT NOT NULL,
    snooze_until TEXT,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(account_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_hjf_account ON home_journey_feedback(account_id);
"""

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

AGENTIC_MEMORY_RETENTION_SQL = """
CREATE TABLE IF NOT EXISTS agentic_memory_items (
  memory_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  run_id TEXT,
  memory_type TEXT NOT NULL,
  content TEXT NOT NULL,
  provenance TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  sensitivity TEXT NOT NULL DEFAULT 'normal',
  ttl_days INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_memory_items_account
  ON agentic_memory_items(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agentic_memory_items_type
  ON agentic_memory_items(account_id, memory_type);
"""


def _add_column_if_not_exists(conn, table: str, column_def: str) -> None:
    col_name = column_def.strip().split()[0]
    cursor = conn.execute(f"PRAGMA table_info({table})")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if col_name not in existing_cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")


def _apply_retention_migration(conn) -> None:
    conn.executescript(AGENTIC_MEMORY_RETENTION_SQL)
    _add_column_if_not_exists(conn, "agentic_memory_proposals", "expires_at TEXT")
    _add_column_if_not_exists(conn, "agentic_memory_items", "expires_at TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agentic_mem_prop_expires ON agentic_memory_proposals(expires_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agentic_mem_items_expires ON agentic_memory_items(expires_at)")


def _apply_ai_tutor_migration(conn) -> None:
    conn.executescript(AI_TUTOR_SQL)
    _add_column_if_not_exists(conn, "ai_conversation_sessions", "context_id TEXT")
    _add_column_if_not_exists(conn, "ai_conversation_sessions", "idempotency_key TEXT")
    _add_column_if_not_exists(conn, "ai_messages", "citations_json TEXT NOT NULL DEFAULT '[]'")
    _add_column_if_not_exists(conn, "ai_messages", "numeric_claims_json TEXT NOT NULL DEFAULT '[]'")
    _add_column_if_not_exists(conn, "ai_messages", "tool_calls_json TEXT NOT NULL DEFAULT '[]'")
    _add_column_if_not_exists(conn, "ai_messages", "trace_id TEXT")
    _add_column_if_not_exists(conn, "ai_messages", "idempotency_key TEXT")
    _add_column_if_not_exists(conn, "ai_feedback", "idempotency_key TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_conversation_sessions_idempotency ON ai_conversation_sessions(idempotency_key)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_messages_conv_idemp ON ai_messages(conversation_id, idempotency_key) WHERE idempotency_key IS NOT NULL")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_feedback_msg_idemp ON ai_feedback(message_id, idempotency_key)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_feedback_message_id ON ai_feedback(message_id)")


COMPANY_FINANCIALS_SQL = """
CREATE TABLE IF NOT EXISTS company_financial_datasets (
  ticker TEXT PRIMARY KEY,
  periods_count INTEGER NOT NULL,
  latest_period TEXT,
  latest_revenue REAL,
  latest_net_income REAL,
  dataset_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS company_financial_periods (
  ticker TEXT NOT NULL,
  period TEXT NOT NULL,
  year INTEGER NOT NULL,
  quarter INTEGER,
  revenue REAL,
  gross_profit REAL,
  operating_profit REAL,
  net_income REAL,
  total_assets REAL,
  total_liabilities REAL,
  equity REAL,
  cash REAL,
  short_term_debt REAL,
  long_term_debt REAL,
  operating_cash_flow REAL,
  investing_cash_flow REAL,
  financing_cash_flow REAL,
  raw_json TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (ticker, period)
);
CREATE INDEX IF NOT EXISTS idx_financial_periods_ticker ON company_financial_periods(ticker);
CREATE INDEX IF NOT EXISTS idx_financial_periods_time ON company_financial_periods(year DESC, quarter DESC);
"""


NEWS_FEED_SNAPSHOTS_SQL = """
CREATE TABLE IF NOT EXISTS news_feed_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  filter_key TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  expires_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_news_feed_snapshots_expiry ON news_feed_snapshots(expires_at);
"""

MIGRATIONS: list[tuple[str, str]] = [
    ("001_baseline", ""),  # filled at runtime from baseline.sql
    ("002_ingest_runs", INGEST_RUNS_SQL),
    ("003_commodities", COMMODITIES_SQL),
    ("004_news_highlight_snapshots", NEWS_HIGHLIGHT_SNAPSHOTS_SQL),
    ("005_telegram_news_deliveries", TELEGRAM_NEWS_DELIVERIES_SQL),
    ("006_telegram_news_translations", TELEGRAM_NEWS_TRANSLATIONS_SQL),
    ("007_telegram_market_deliveries", TELEGRAM_MARKET_DELIVERIES_SQL),
    ("008_ai_tutor_conversations", ""),  # applied by _apply_ai_tutor_migration
    ("009_learning_agent_checkpoints", LEARNING_AGENT_SQL),
    ("010_bctc_evidence_memos", BCTC_EVIDENCE_MEMOS_SQL),
    ("011_bctc_upload_ownership", BCTC_UPLOAD_OWNERSHIP_SQL),
    ("012_simulation_experiment_specs", SIMULATION_SPECS_SQL),
    ("013_simulation_action_proposals", SIMULATION_PROPOSALS_SQL),
    ("014_simulation_action_receipts", SIMULATION_RECEIPTS_SQL),
    ("015_home_journey", HOME_JOURNEY_SQL),
    ("016_agentic_core", AGENTIC_CORE_SQL),
    ("017_agentic_memory_retention", ""),
    ("018_learning_video_agent", ""),
    ("019_company_financials", COMPANY_FINANCIALS_SQL),
    ("020_news_feed_snapshots", NEWS_FEED_SNAPSHOTS_SQL),
    ("021_social_intelligence", SOCIAL_SQL),
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_migrations_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          id TEXT PRIMARY KEY,
          applied_at TEXT NOT NULL
        )
        """
    )


def _applied_ids(conn) -> set[str]:
    rows = conn.execute("SELECT id FROM schema_migrations").fetchall()
    return {str(row[0]) for row in rows}


def _stamp_existing_baseline_if_needed(conn) -> None:
    """Existing app_state.db already has tables but no migration ledger."""
    applied = _applied_ids(conn)
    if "001_baseline" in applied:
        return
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='app_kv' LIMIT 1"
    ).fetchone()
    if row:
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (id, applied_at) VALUES (?, ?)",
            ("001_baseline", _now()),
        )


def apply_migrations(conn) -> list[str]:
    """Apply pending migrations. Returns list of newly applied ids."""
    ensure_migrations_table(conn)
    _stamp_existing_baseline_if_needed(conn)
    applied = _applied_ids(conn)
    newly: list[str] = []

    migrations = [
        ("001_baseline", _load_baseline()),
        ("002_ingest_runs", INGEST_RUNS_SQL),
        ("003_commodities", COMMODITIES_SQL),
        ("004_news_highlight_snapshots", NEWS_HIGHLIGHT_SNAPSHOTS_SQL),
        ("005_telegram_news_deliveries", TELEGRAM_NEWS_DELIVERIES_SQL),
        ("006_telegram_news_translations", TELEGRAM_NEWS_TRANSLATIONS_SQL),
        ("007_telegram_market_deliveries", TELEGRAM_MARKET_DELIVERIES_SQL),
        ("008_ai_tutor_conversations", ""),
        ("009_learning_agent_checkpoints", LEARNING_AGENT_SQL),
        ("010_bctc_evidence_memos", BCTC_EVIDENCE_MEMOS_SQL),
        ("011_bctc_upload_ownership", BCTC_UPLOAD_OWNERSHIP_SQL),
        ("012_simulation_experiment_specs", SIMULATION_SPECS_SQL),
        ("013_simulation_action_proposals", SIMULATION_PROPOSALS_SQL),
        ("014_simulation_action_receipts", SIMULATION_RECEIPTS_SQL),
        ("015_home_journey", HOME_JOURNEY_SQL),
        ("016_agentic_core", AGENTIC_CORE_SQL),
        ("017_agentic_memory_retention", ""),
        ("018_learning_video_agent", ""),
        ("019_company_financials", COMPANY_FINANCIALS_SQL),
        ("020_news_feed_snapshots", NEWS_FEED_SNAPSHOTS_SQL),
        ("021_social_intelligence", SOCIAL_SQL),
    ]
    for mid, sql in migrations:
        if mid in applied:
            continue
        if mid == "008_ai_tutor_conversations":
            _apply_ai_tutor_migration(conn)
        elif mid == "017_agentic_memory_retention":
            _apply_retention_migration(conn)
        elif mid == "018_learning_video_agent":
            conn.executescript(LEARNING_AGENT_SQL)
        else:
            conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (id, applied_at) VALUES (?, ?)",
            (mid, _now()),
        )
        newly.append(mid)
        applied.add(mid)
    conn.commit()
    return newly
