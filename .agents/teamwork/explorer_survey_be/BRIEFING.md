# BRIEFING — 2026-10-10T11:16:45Z

## Mission
Thoroughly investigate and audit Backend codebase (Python/FastAPI) and test suites for Tab Learn, AI Tutor, performance bottlenecks, async/sync issues, and schema drift.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_be
- Original parent: 97a90bba-b298-4ab1-be4b-07eacc3cdf32
- Milestone: backend-survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement / modify source code
- Only write files inside working directory (.agents/teamwork/explorer_survey_be/)
- Provide exact line numbers and root-cause analysis
- Execute backend test suites and verify mock fidelity

## Current Parent
- Conversation ID: 97a90bba-b298-4ab1-be4b-07eacc3cdf32
- Updated: 2026-10-10T11:16:45Z

## Investigation State
- **Explored paths**:
  - `src/risk_dashboard/modules/learning/` (api, application, infrastructure, crawlers, schemas, domain)
  - `src/risk_dashboard/modules/ai_tutor/` (api, application, infrastructure, specialists, schemas)
  - `src/risk_dashboard/platform/database/` (baseline.sql, migrate.py, connection.py, app_state.py)
  - `src/risk_dashboard/platform/ai_runtime/` (contracts, factory, sse, streaming)
  - `tests/test_learning*.py`, `tests/test_ai_tutor*.py`, `tests/test_multi_agent_learning.py`, `tests/test_video_learning_agent.py`, `tests/test_ai_runtime*.py`
  - `frontend/src/features/learn-hub/` (services/learningApi.js, schemas/learningSchemas.js, types/learningTypes.js, tests)
- **Key findings**:
  - Executed 148 backend tests: 147 passed, 1 skipped.
  - BE-01 (CRITICAL): Blocking `urllib.request.urlopen` network call inside `LearningSpecialist.handle` async coroutine.
  - BE-06 (CRITICAL): `SqliteLearningCatalog.__init__` executes 50+ DB lookups on every request via `ensure_learning_catalog_seeded`.
  - BE-02 (HIGH): Synchronous SQLite disk queries inside `async def send_message`.
  - BE-04 (HIGH): SQLite connection leak in repositories when custom `_db_path` is passed.
  - BE-07 (HIGH): Missing index on `ORDER BY fetched_at` in video, book, and course catalog tables.
  - BE-09 (HIGH): Nested DB connection risk in `LearningRetrievalIndex.search()`.
  - BE-10 (HIGH): AI Tutor lacks SSE streaming (unary blocking wait).
  - BE-11 (HIGH): AI Tutor context adapter falls back to 4 static Telegram cards.
  - BE-12 (HIGH): FTS5 curriculum search index excludes books, video transcripts, papers, and BCTC cases.
- **Unexplored areas**: None within backend scope.

## Key Decisions Made
- Executed all backend test suites using project virtual environment (`.venv/bin/pytest`).
- Documented all 15 issues with risk levels, file paths, line ranges, and reproduction evidence in `analysis.md` and `handoff.md`.

## Artifact Index
- DISPATCH.md — Assignment instructions
- BRIEFING.md — Working memory & identity
- progress.md — Heartbeat & status
- analysis.md — Comprehensive backend audit report (15 findings)
- handoff.md — 5-component handoff report
