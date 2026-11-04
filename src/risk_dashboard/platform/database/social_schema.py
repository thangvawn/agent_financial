"""Additive Social storage; content and jobs are always scoped to an account."""

SOCIAL_SQL = """
CREATE TABLE IF NOT EXISTS social_sources (
  id TEXT NOT NULL, account_id TEXT NOT NULL, platform TEXT NOT NULL,
  label TEXT NOT NULL, query TEXT NOT NULL, market TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1, created_at REAL NOT NULL,
  last_success_at REAL, last_attempt_at REAL, last_error TEXT,
  next_run_at REAL NOT NULL DEFAULT 0,
  PRIMARY KEY(account_id, id)
);
CREATE TABLE IF NOT EXISTS social_jobs (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL, source_id TEXT,
  platform TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL,
  market TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
  created_at REAL NOT NULL, updated_at REAL NOT NULL,
  lease_until REAL NOT NULL DEFAULT 0, lease_token TEXT,
  attempts INTEGER NOT NULL DEFAULT 0, next_run_at REAL NOT NULL DEFAULT 0,
  error_code TEXT, result_count INTEGER NOT NULL DEFAULT 0,
  partial_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_social_jobs_due ON social_jobs(status, next_run_at, created_at);
CREATE INDEX IF NOT EXISTS idx_social_jobs_owner ON social_jobs(account_id, created_at DESC);
CREATE TABLE IF NOT EXISTS social_posts (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL, platform TEXT NOT NULL,
  native_id TEXT NOT NULL, url TEXT NOT NULL, content_hash TEXT NOT NULL,
  published_ts REAL, first_seen_at REAL NOT NULL, fetched_at REAL NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1, payload_json TEXT NOT NULL,
  UNIQUE(account_id, platform, native_id)
);
CREATE INDEX IF NOT EXISTS idx_social_posts_owner ON social_posts(account_id, fetched_at DESC);
CREATE TABLE IF NOT EXISTS social_post_sources (
  post_id TEXT NOT NULL, account_id TEXT NOT NULL, source_id TEXT NOT NULL,
  PRIMARY KEY(account_id, post_id, source_id)
);
CREATE TABLE IF NOT EXISTS social_post_revisions (
  post_id TEXT NOT NULL, revision INTEGER NOT NULL, created_at REAL NOT NULL,
  payload_json TEXT NOT NULL, PRIMARY KEY(post_id, revision)
);
CREATE TABLE IF NOT EXISTS social_saved_posts (
  account_id TEXT NOT NULL, post_id TEXT NOT NULL, saved_at REAL NOT NULL,
  PRIMARY KEY(account_id, post_id)
);
CREATE TABLE IF NOT EXISTS social_feed_snapshots (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL, filter_key TEXT NOT NULL,
  payload_json TEXT NOT NULL, expires_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_social_snapshots_expiry ON social_feed_snapshots(expires_at);
CREATE TABLE IF NOT EXISTS social_worker_state (
  id TEXT PRIMARY KEY, heartbeat_at REAL NOT NULL
);
"""
