from __future__ import annotations

import sqlite3
from pathlib import Path

from risk_dashboard.app.config.settings import get_settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS onboarding_sessions (
  session_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  last_step TEXT NOT NULL,
  answers_json TEXT NOT NULL,
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS onboarding_profiles (
  session_id TEXT PRIMARY KEY,
  primary_goal TEXT NOT NULL,
  knowledge_level TEXT NOT NULL,
  risk_tolerance_prelim TEXT NOT NULL,
  primary_interest TEXT NOT NULL,
  current_state TEXT NOT NULL,
  persona_segment TEXT NOT NULL,
  guided_investing_eligible INTEGER NOT NULL,
  pro_eligible INTEGER NOT NULL,
  primary_route TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS home_states (
  session_id TEXT PRIMARY KEY,
  persona_segment TEXT NOT NULL,
  primary_route TEXT NOT NULL,
  next_best_action_type TEXT NOT NULL,
  next_best_action_ref TEXT NOT NULL,
  trust_message TEXT NOT NULL,
  blocks_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_health_inputs (
  session_id TEXT PRIMARY KEY,
  monthly_income_range TEXT NOT NULL,
  income_stability_level TEXT NOT NULL,
  expense_discipline_level TEXT NOT NULL,
  emergency_fund_months_band TEXT NOT NULL,
  monthly_debt_payment_ratio_band TEXT NOT NULL,
  savings_rate_band TEXT NOT NULL,
  liquidity_stress_level TEXT NOT NULL,
  has_basic_insurance INTEGER NOT NULL,
  has_high_interest_debt INTEGER NOT NULL,
  wants_to_start_investing INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_health_snapshots (
  session_id TEXT PRIMARY KEY,
  health_score INTEGER NOT NULL,
  score_band TEXT NOT NULL,
  guided_investing_eligible INTEGER NOT NULL,
  subscores_json TEXT NOT NULL,
  flags_json TEXT NOT NULL,
  actions_json TEXT NOT NULL,
  educational_links_json TEXT NOT NULL,
  transparency_note TEXT NOT NULL,
  compliance_note TEXT NOT NULL,
  computed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_home_states (
  user_id TEXT PRIMARY KEY,
  path_id TEXT NOT NULL,
  path_label TEXT NOT NULL,
  next_lesson_id TEXT NOT NULL,
  next_lesson_title TEXT NOT NULL,
  recommendation_summary TEXT NOT NULL,
  completed_lessons INTEGER NOT NULL,
  completion_pct INTEGER NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_lesson_progress (
  user_id TEXT NOT NULL,
  path_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  status TEXT NOT NULL,
  quiz_score INTEGER,
  attempt_count INTEGER NOT NULL,
  completed_at TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (user_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS learning_cms_documents (
  doc_type TEXT NOT NULL,
  doc_id TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  published_at TEXT,
  PRIMARY KEY (doc_type, doc_id)
);

CREATE TABLE IF NOT EXISTS news_articles (
  article_id TEXT PRIMARY KEY,
  headline TEXT NOT NULL,
  summary TEXT NOT NULL,
  source TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_tier INTEGER NOT NULL,
  source_flag TEXT NOT NULL,
  region TEXT NOT NULL,
  category TEXT NOT NULL,
  url TEXT NOT NULL,
  published_at TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  sort_ts INTEGER NOT NULL,
  priority INTEGER NOT NULL,
  sentiment TEXT NOT NULL,
  impact TEXT NOT NULL,
  tickers_json TEXT NOT NULL,
  language TEXT NOT NULL,
  threat_level TEXT NOT NULL,
  threat_category TEXT,
  threat_confidence REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_news_articles_sort_ts ON news_articles(sort_ts DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_category ON news_articles(category);
CREATE INDEX IF NOT EXISTS idx_news_articles_source_id ON news_articles(source_id);

CREATE TABLE IF NOT EXISTS news_fetch_runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  completed_at TEXT NOT NULL,
  source_count INTEGER NOT NULL,
  successful_source_count INTEGER NOT NULL,
  article_count INTEGER NOT NULL,
  error_count INTEGER NOT NULL,
  errors_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_news_fetch_runs_completed_at ON news_fetch_runs(completed_at DESC);

CREATE TABLE IF NOT EXISTS goals (
  goal_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  goal_type TEXT NOT NULL,
  goal_name TEXT NOT NULL,
  target_amount REAL NOT NULL,
  current_amount REAL NOT NULL,
  currency TEXT NOT NULL,
  base_currency TEXT NOT NULL,
  deadline TEXT NOT NULL,
  priority TEXT NOT NULL,
  confidence_level TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);

CREATE TABLE IF NOT EXISTS goal_snapshots (
  goal_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  gap_amount REAL NOT NULL,
  months_remaining INTEGER NOT NULL,
  monthly_contribution_needed REAL NOT NULL,
  feasibility_band TEXT NOT NULL,
  delay_3m_monthly_needed REAL NOT NULL,
  inflation_sensitivity_band TEXT NOT NULL,
  inflation_adjusted_target_estimate REAL NOT NULL,
  fx_sensitivity_band TEXT NOT NULL,
  fx_upside_5pct_target REAL NOT NULL,
  fx_downside_5pct_target REAL NOT NULL,
  actions_json TEXT NOT NULL,
  educational_links_json TEXT NOT NULL,
  computed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goal_checkins (
  checkin_id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  current_amount REAL NOT NULL,
  note TEXT,
  checked_in_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goal_reminder_states (
  goal_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  reminder_frequency TEXT NOT NULL,
  last_status TEXT NOT NULL,
  last_reminder_at TEXT,
  next_reminder_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS guided_watchlist_items (
  item_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  ticker TEXT NOT NULL,
  label TEXT NOT NULL,
  reason_to_track TEXT NOT NULL,
  theme_tag TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_guided_watchlist_user_id ON guided_watchlist_items(user_id);

CREATE TABLE IF NOT EXISTS guided_journal_entries (
  entry_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  ticker TEXT NOT NULL,
  title TEXT NOT NULL,
  thesis TEXT NOT NULL,
  uncertainties TEXT NOT NULL,
  review_condition TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_guided_journal_user_id ON guided_journal_entries(user_id);

CREATE TABLE IF NOT EXISTS guided_saved_portfolios (
  portfolio_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  holdings_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_guided_saved_portfolios_user_id ON guided_saved_portfolios(user_id);

CREATE TABLE IF NOT EXISTS guided_portfolio_review_history (
  review_id TEXT PRIMARY KEY,
  portfolio_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  scenario_label TEXT NOT NULL,
  holdings_json TEXT NOT NULL,
  review_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_guided_portfolio_review_history_user_id ON guided_portfolio_review_history(user_id);

CREATE TABLE IF NOT EXISTS community_memberships (
  space_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  joined_at TEXT NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (space_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_community_memberships_user_id ON community_memberships(user_id);

CREATE TABLE IF NOT EXISTS community_posts (
  post_id TEXT PRIMARY KEY,
  space_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  post_type TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  linked_lesson_id TEXT,
  linked_goal_id TEXT,
  linked_case_id TEXT,
  moderation_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_community_posts_space_id ON community_posts(space_id);
CREATE INDEX IF NOT EXISTS idx_community_posts_user_id ON community_posts(user_id);

CREATE TABLE IF NOT EXISTS community_comments (
  comment_id TEXT PRIMARY KEY,
  post_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  parent_comment_id TEXT,
  thread_depth INTEGER NOT NULL DEFAULT 0,
  body TEXT NOT NULL,
  moderation_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS community_moderation_events (
  event_id TEXT PRIMARY KEY,
  content_type TEXT NOT NULL,
  content_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  ai_risk_labels_json TEXT NOT NULL,
  decision TEXT NOT NULL,
  reviewer_id TEXT,
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_community_moderation_user_id ON community_moderation_events(user_id);

CREATE TABLE IF NOT EXISTS community_challenge_progress (
  challenge_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  status TEXT NOT NULL,
  progress_pct INTEGER NOT NULL,
  last_active_at TEXT NOT NULL,
  PRIMARY KEY (challenge_id, user_id)
);

CREATE TABLE IF NOT EXISTS community_notification_states (
  notification_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  notification_type TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  cta_path TEXT NOT NULL,
  related_space_id TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  next_reminder_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_community_notifications_user_id ON community_notification_states(user_id);

CREATE TABLE IF NOT EXISTS pro_lab_blueprints (
  blueprint_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  objective TEXT NOT NULL,
  asset_universe_json TEXT NOT NULL,
  benchmark TEXT NOT NULL,
  rebalance_frequency TEXT NOT NULL,
  risk_constraints TEXT NOT NULL,
  assumptions_note TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pro_lab_blueprints_user_id ON pro_lab_blueprints(user_id);

CREATE TABLE IF NOT EXISTS pro_lab_experiments (
  experiment_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  blueprint_id TEXT,
  experiment_type TEXT NOT NULL,
  status TEXT NOT NULL,
  input_json TEXT NOT NULL,
  output_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  review_notes TEXT,
  reviewed_at TEXT,
  reviewer_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_pro_lab_experiments_user_id ON pro_lab_experiments(user_id);

CREATE TABLE IF NOT EXISTS pro_lab_experiment_runs (
  run_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  experiment_id TEXT,
  blueprint_id TEXT,
  provider_id TEXT NOT NULL,
  command_id TEXT NOT NULL,
  status TEXT NOT NULL,
  input_json TEXT NOT NULL,
  output_json TEXT NOT NULL,
  logs_json TEXT NOT NULL,
  progress_pct INTEGER NOT NULL,
  safety_flags_json TEXT NOT NULL,
  data_freshness_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_pro_lab_experiment_runs_user_id ON pro_lab_experiment_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_pro_lab_experiment_runs_provider ON pro_lab_experiment_runs(provider_id, command_id);

CREATE TABLE IF NOT EXISTS pro_lab_workspaces (
  workspace_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL UNIQUE,
  active_page TEXT NOT NULL,
  open_panels_json TEXT NOT NULL,
  selected_blueprint_id TEXT,
  selected_experiment_id TEXT,
  layout_json TEXT NOT NULL,
  notes TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pro_lab_workspaces_user_id ON pro_lab_workspaces(user_id);

CREATE TABLE IF NOT EXISTS pro_lab_audit_logs (
  audit_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  surface TEXT NOT NULL,
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pro_lab_audit_logs_actor_id ON pro_lab_audit_logs(actor_id);

CREATE TABLE IF NOT EXISTS access_role_assignments (
  actor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  scopes_json TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (actor_id, role)
);

CREATE INDEX IF NOT EXISTS idx_access_role_assignments_actor_id ON access_role_assignments(actor_id);

CREATE TABLE IF NOT EXISTS access_tokens (
  token_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  scopes_json TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_access_tokens_actor_id ON access_tokens(actor_id);

CREATE TABLE IF NOT EXISTS ai_conversation_sessions (
  conversation_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  surface TEXT NOT NULL,
  context_json TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  status TEXT NOT NULL,
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
  risk_labels_json TEXT NOT NULL,
  structured_output_json TEXT NOT NULL,
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
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_feedback_conversation_id ON ai_feedback(conversation_id);

CREATE TABLE IF NOT EXISTS ai_event_logs (
  event_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  surface TEXT NOT NULL,
  intent TEXT NOT NULL,
  route_decision TEXT NOT NULL,
  guardrail_triggered INTEGER NOT NULL,
  tool_calls_json TEXT NOT NULL,
  latency_ms INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_event_logs_conversation_id ON ai_event_logs(conversation_id);

CREATE TABLE IF NOT EXISTS cms_content_items (
  content_id TEXT PRIMARY KEY,
  content_type TEXT NOT NULL,
  slug TEXT NOT NULL,
  title TEXT NOT NULL,
  locale TEXT NOT NULL,
  owner_team TEXT NOT NULL,
  risk_category TEXT NOT NULL,
  workflow_state TEXT NOT NULL,
  current_version INTEGER NOT NULL,
  published_version INTEGER,
  created_by TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cms_content_items_type ON cms_content_items(content_type);

CREATE TABLE IF NOT EXISTS cms_content_versions (
  version_id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,
  version_number INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL,
  origin TEXT NOT NULL,
  change_summary TEXT,
  created_by TEXT NOT NULL,
  reviewed_by TEXT,
  compliance_reviewed_by TEXT,
  published_by TEXT,
  created_at TEXT NOT NULL,
  published_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_cms_content_versions_content_id ON cms_content_versions(content_id);

CREATE TABLE IF NOT EXISTS cms_review_tasks (
  task_id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,
  version_number INTEGER NOT NULL,
  review_type TEXT NOT NULL,
  assignee_role TEXT NOT NULL,
  status TEXT NOT NULL,
  created_by TEXT NOT NULL,
  reviewer_id TEXT,
  comments TEXT,
  created_at TEXT NOT NULL,
  completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_cms_review_tasks_status ON cms_review_tasks(status);

CREATE TABLE IF NOT EXISTS cms_publish_events (
  event_id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,
  version_number INTEGER NOT NULL,
  action TEXT NOT NULL,
  actor_role TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cms_publish_events_content_id ON cms_publish_events(content_id);

CREATE TABLE IF NOT EXISTS cms_ai_generation_logs (
  generation_id TEXT PRIMARY KEY,
  content_type TEXT NOT NULL,
  content_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  model_name TEXT NOT NULL,
  input_summary TEXT NOT NULL,
  output_summary TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cms_analytics_snapshots (
  content_id TEXT PRIMARY KEY,
  impression_count INTEGER NOT NULL DEFAULT 0,
  open_count INTEGER NOT NULL DEFAULT 0,
  completion_count INTEGER NOT NULL DEFAULT 0,
  clickthrough_count INTEGER NOT NULL DEFAULT 0,
  last_event_at TEXT
);

CREATE TABLE IF NOT EXISTS trust_safety_audit_logs (
  audit_id TEXT PRIMARY KEY,
  actor_id TEXT,
  surface TEXT NOT NULL,
  topic TEXT,
  channel TEXT NOT NULL,
  risk_classes_json TEXT NOT NULL,
  severity TEXT NOT NULL,
  route_decision TEXT NOT NULL,
  input_summary TEXT,
  output_summary TEXT,
  guardrails_json TEXT NOT NULL,
  disclaimer_injected INTEGER NOT NULL,
  freshness_status TEXT,
  confidence_label TEXT,
  escalation_action TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trust_safety_audit_surface ON trust_safety_audit_logs(surface);
CREATE INDEX IF NOT EXISTS idx_trust_safety_audit_created_at ON trust_safety_audit_logs(created_at);

CREATE TABLE IF NOT EXISTS trust_safety_incidents (
  incident_id TEXT PRIMARY KEY,
  source_audit_id TEXT,
  surface TEXT NOT NULL,
  topic TEXT,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  summary TEXT NOT NULL,
  owner_id TEXT,
  notes TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_trust_safety_incidents_surface ON trust_safety_incidents(surface);
CREATE INDEX IF NOT EXISTS idx_trust_safety_incidents_status ON trust_safety_incidents(status);

CREATE TABLE IF NOT EXISTS analytics_events (
  event_id TEXT PRIMARY KEY,
  event_name TEXT NOT NULL,
  event_category TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  module TEXT NOT NULL,
  surface TEXT NOT NULL,
  user_id TEXT,
  session_id TEXT,
  persona_segment TEXT,
  route TEXT,
  locale TEXT,
  device_type TEXT,
  source_surface TEXT,
  target_surface TEXT,
  properties_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_name_timestamp ON analytics_events(event_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_module_timestamp ON analytics_events(module, timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_surface_timestamp ON analytics_events(surface, timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_timestamp ON analytics_events(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_session_timestamp ON analytics_events(session_id, timestamp);

CREATE TABLE IF NOT EXISTS analytics_kpi_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  kpi_name TEXT NOT NULL,
  window_grain TEXT NOT NULL,
  window_start TEXT NOT NULL,
  window_end TEXT NOT NULL,
  value REAL NOT NULL,
  segment_key TEXT,
  segment_value TEXT,
  meta_json TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analytics_kpi_name_window ON analytics_kpi_snapshots(kpi_name, window_grain, window_end);

CREATE TABLE IF NOT EXISTS ops_metric_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  metric_name TEXT NOT NULL,
  metric_group TEXT NOT NULL,
  surface TEXT,
  status TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_ops_metric_name_time ON ops_metric_snapshots(metric_name, captured_at);
CREATE INDEX IF NOT EXISTS idx_ops_metric_group_time ON ops_metric_snapshots(metric_group, captured_at);

CREATE TABLE IF NOT EXISTS ops_alert_events (
  alert_id TEXT PRIMARY KEY,
  rule_name TEXT NOT NULL,
  severity_tier TEXT NOT NULL,
  surface TEXT,
  status TEXT NOT NULL,
  summary TEXT NOT NULL,
  details_json TEXT,
  triggered_at TEXT NOT NULL,
  resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_ops_alert_events_status_time ON ops_alert_events(status, triggered_at);
CREATE INDEX IF NOT EXISTS idx_ops_alert_events_severity_time ON ops_alert_events(severity_tier, triggered_at);
"""


def open_app_state_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or get_settings().app_state_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _ensure_schema_compatibility(conn)
    conn.commit()
    return conn


def _ensure_schema_compatibility(conn: sqlite3.Connection) -> None:
    comment_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(community_comments)").fetchall()
    }
    if comment_cols and "updated_at" not in comment_cols:
        conn.execute("ALTER TABLE community_comments ADD COLUMN updated_at TEXT")
        conn.execute("UPDATE community_comments SET updated_at = created_at WHERE updated_at IS NULL")
    if comment_cols and "parent_comment_id" not in comment_cols:
        conn.execute("ALTER TABLE community_comments ADD COLUMN parent_comment_id TEXT")
    if comment_cols and "thread_depth" not in comment_cols:
        conn.execute("ALTER TABLE community_comments ADD COLUMN thread_depth INTEGER NOT NULL DEFAULT 0")
        conn.execute("UPDATE community_comments SET thread_depth = 0 WHERE thread_depth IS NULL")
    pro_lab_experiment_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(pro_lab_experiments)").fetchall()
    }
    if pro_lab_experiment_cols and "review_status" not in pro_lab_experiment_cols:
        conn.execute("ALTER TABLE pro_lab_experiments ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending_review'")
    if pro_lab_experiment_cols and "review_notes" not in pro_lab_experiment_cols:
        conn.execute("ALTER TABLE pro_lab_experiments ADD COLUMN review_notes TEXT")
    if pro_lab_experiment_cols and "reviewed_at" not in pro_lab_experiment_cols:
        conn.execute("ALTER TABLE pro_lab_experiments ADD COLUMN reviewed_at TEXT")
    if pro_lab_experiment_cols and "reviewer_id" not in pro_lab_experiment_cols:
        conn.execute("ALTER TABLE pro_lab_experiments ADD COLUMN reviewer_id TEXT")
    trust_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(trust_safety_audit_logs)").fetchall()
    }
    if trust_cols and "topic" not in trust_cols:
        conn.execute("ALTER TABLE trust_safety_audit_logs ADD COLUMN topic TEXT")
    incident_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(trust_safety_incidents)").fetchall()
    }
    if incident_cols and "topic" not in incident_cols:
        conn.execute("ALTER TABLE trust_safety_incidents ADD COLUMN topic TEXT")


def reset_app_state_tables() -> None:
    with open_app_state_db() as conn:
        conn.executescript(
            """
            DELETE FROM onboarding_sessions;
            DELETE FROM onboarding_profiles;
            DELETE FROM home_states;
            DELETE FROM financial_health_inputs;
            DELETE FROM financial_health_snapshots;
            DELETE FROM learning_home_states;
            DELETE FROM learning_lesson_progress;
            DELETE FROM learning_cms_documents;
            DELETE FROM news_articles;
            DELETE FROM news_fetch_runs;
            DELETE FROM goals;
            DELETE FROM goal_snapshots;
            DELETE FROM goal_checkins;
            DELETE FROM goal_reminder_states;
            DELETE FROM guided_watchlist_items;
            DELETE FROM guided_journal_entries;
            DELETE FROM guided_saved_portfolios;
            DELETE FROM guided_portfolio_review_history;
            DELETE FROM community_memberships;
            DELETE FROM community_posts;
            DELETE FROM community_comments;
            DELETE FROM community_moderation_events;
            DELETE FROM community_challenge_progress;
            DELETE FROM community_notification_states;
            DELETE FROM pro_lab_blueprints;
            DELETE FROM pro_lab_experiments;
            DELETE FROM pro_lab_experiment_runs;
            DELETE FROM pro_lab_workspaces;
            DELETE FROM pro_lab_audit_logs;
            DELETE FROM access_role_assignments;
            DELETE FROM access_tokens;
            DELETE FROM ai_conversation_sessions;
            DELETE FROM ai_messages;
            DELETE FROM ai_feedback;
            DELETE FROM ai_event_logs;
            DELETE FROM cms_content_items;
            DELETE FROM cms_content_versions;
            DELETE FROM cms_review_tasks;
            DELETE FROM cms_publish_events;
            DELETE FROM cms_ai_generation_logs;
            DELETE FROM cms_analytics_snapshots;
            DELETE FROM trust_safety_audit_logs;
            DELETE FROM trust_safety_incidents;
            DELETE FROM analytics_events;
            DELETE FROM analytics_kpi_snapshots;
            DELETE FROM ops_metric_snapshots;
            DELETE FROM ops_alert_events;
            """
        )
        conn.commit()
