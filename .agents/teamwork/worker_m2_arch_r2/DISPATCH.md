# Worker M2 Remediation: Fix DDL, Financial Cache Parsing & Anti-Cheating Guardrail

**Working Directory**: /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch_r2  
**Target File to Update**: `/Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_ARCHITECTURE.md`

## Required Remediations
1. **Fix DDL Bugs**:
   - In `idx_courses_v2_active_fetched` (around line 680-681), change `fetched_at` to `published_at` (`CREATE INDEX IF NOT EXISTS idx_courses_v2_active_published ON learning_courses_v2 (is_active, published_at DESC);`).
   - In `trg_courses_v2_updated_at` (around line 701-709), prevent infinite trigger recursion in SQLite by adding `WHEN OLD.updated_at = NEW.updated_at` (or `AFTER UPDATE OF title, description, thumbnail_url, difficulty_level, estimated_hours, status, is_active ON learning_courses_v2`).
   - In `learning_progress_receipts` table definition, make `verified_event_id` nullable (`verified_event_id TEXT REFERENCES learning_verified_events(event_id)`) so reading and video lessons without checkpoints can issue completion receipts.
   - Add FTS5 UPDATE and DELETE triggers for BCTC cases, courses, books, and videos to ensure index freshness upon data updates.
2. **Fix Financial Cache Data Parsing**:
   - In `FinancialCrossLinkService.load_ticker_financial_snapshot`, update the code to accurately handle `data/financials/cache/{ticker}.json` where `periods` is a `list[dict]` and reports are stored under `raw_statements` or `financial_ratios`.
3. **Harden Socratic Anti-Cheating Guardian**:
   - Replace basic regex with a multi-layered Prompt Isolation architecture:
     - System prompt boundary fence (Socratic Persona Fence).
     - Multi-lingual answer masking (intercepting both Vietnamese and English letters A, B, C, D, formatted markdown `**A**`, parenthesized `(A)`, direct numbers).
     - Socratic Scaffolding Engine that converts direct answers into conceptual questions.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Apply all edits directly to `docs/LEARN_HUB_ARCHITECTURE.md`, write summary to `handoff.md`, and notify orchestrator via `send_message`.


## 2026-10-10T11:38:57Z
You are worker_m2_arch_r2. Your working directory is /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch_r2.
Please read:
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch_r2/DISPATCH.md
- /Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_ARCHITECTURE.md

Apply all necessary remediations directly to /Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_ARCHITECTURE.md:
1. Fix DDL index: Change idx_courses_v2_active_fetched to idx_courses_v2_active_published on (is_active, published_at DESC).
2. Fix DDL trigger: Fix trg_courses_v2_updated_at by adding WHEN OLD.updated_at = NEW.updated_at (or AFTER UPDATE OF ...) to eliminate SQLite recursive trigger loop.
3. Fix progress receipt DDL: Make verified_event_id nullable (TEXT REFERENCES learning_verified_events(event_id)) so video/reading lessons without checkpoints can store completion receipts.
4. Add complete FTS5 UPDATE and DELETE triggers for all indexed tables (bctc cases, courses, books, videos).
5. Fix Financial Cache Parsing in FinancialCrossLinkService: Parse periods as list[dict] and extract reports from raw_statements or financial_ratios according to actual data/financials/cache/{ticker}.json.
6. Harden Socratic Anti-Cheating: Multi-layer prompt isolation architecture + multi-lingual (Vietnamese + English) answer interception (covering A, B, C, D, **A**, (A), and raw numbers) with Socratic scaffolding.

Write your handoff report to handoff.md and send a completion message back to orchestrator (conversation ID: 97a90bba-b298-4ab1-be4b-07eacc3cdf32).
