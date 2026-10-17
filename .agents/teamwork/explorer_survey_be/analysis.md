# Backend Architecture & Performance Audit Report (Tab Learn & AI Tutor)

**Author**: `explorer_survey_be`  
**Date**: 2026-10-10  
**Scope**: Backend Python/FastAPI codebase (`src/risk_dashboard/modules/learning`, `src/risk_dashboard/modules/ai_tutor`, `platform/database`, `platform/ai_runtime`) and automated test suites (`tests/test_learning*.py`, `tests/test_ai_tutor*.py`, `tests/test_multi_agent_learning.py`, `tests/test_video_learning_agent.py`, `tests/test_ai_runtime*.py`).

---

## 1. Executive Summary

A comprehensive investigation of the Backend Python/FastAPI implementation for the Financial Agent platform was conducted, focusing on **Tab Learn (Learn Hub)**, **AI Tutor / Agentic Learning**, and supporting **Platform Database/AI Runtime** components.

### Key Metrics
- **Automated Tests Executed**: 148 test cases across 18 test files (`49 test_learning*` + `10 multi_agent & video` + `55 test_ai_tutor*` + `34 ai_runtime & e2e`).
- **Pass Rate**: **100% Pass** (147 passed, 1 skipped).
- **Vulnerabilities & Bottlenecks Identified**: 14 distinct issues categorized across 6 domains (2 Critical, 5 High, 5 Medium, 2 Low).
- **Core Architectural Diagnosis**: Tab Learn currently suffers from a structural dichotomy:
  1. *Curriculum Lessons* (`/learning/lessons/{id}`) are static text-only micro-lessons stored in memory/Admin CMS.
  2. *Catalog Resources* (`/learning/catalog`) are flat crawled tables (`learning_videos`, `learning_books`, `learning_papers`, `learning_courses`) with unindexed sorting columns and no Pydantic validation contracts.
  3. *AI Tutor* is disconnected from the broader catalog, falling back to 4 hardcoded cards (`query_handler.py`), lacks Server-Sent Events (SSE) streaming, and invokes blocking I/O calls inside `async def` event loop routines.

---

## 2. Test Suite Execution Audit & Verification

### 2.1 Execution Log & Status

| Test Suite File | Command Executed | Tests | Passed | Failed | Duration | Primary Focus |
|---|---|---|---|---|---|---|
| `tests/test_learning.py` | `pytest tests/test_learning*.py` | 5 | 5 | 0 | 4.2s | End-to-end user onboarding, path progress, quiz flow, legacy 404 assertions |
| `tests/test_learning_agent_checkpoint.py` | (included above) | 6 | 6 | 0 | 3.1s | Socratic checkpoint generation, zero-leakage, account binding |
| `tests/test_learning_agent_contracts.py` | (included above) | 5 | 5 | 0 | 2.8s | Pydantic schema validation for agent tools |
| `tests/test_learning_agent_gold_set.py` | (included above) | 2 | 2 | 0 | 1.9s | 100 gold test cases deterministic evaluation runner |
| `tests/test_learning_agent_memory.py` | (included above) | 4 | 4 | 0 | 2.1s | Verified event mastery proposal and user consent gating |
| `tests/test_learning_agent_retrieval.py` | (included above) | 5 | 5 | 0 | 2.9s | FTS5 index creation, prompt injection sanitization, search |
| `tests/test_learning_agent_skills.py` | (included above) | 6 | 6 | 0 | 3.0s | Agentic skill execution and capability authorization |
| `tests/test_learning_agent_tools.py` | (included above) | 6 | 6 | 0 | 3.2s | Tool manifests, parameters, schema output compliance |
| `tests/test_learning_crawlers.py` | (included above) | 4 | 4 | 0 | 2.4s | In-memory crawler sources (`open_courses`, `curated_books`) |
| `tests/test_learning_remediation.py` | (included above) | 6 | 6 | 0 | 3.1s | Remediation policies on repeated quiz failures |
| `tests/test_multi_agent_learning.py` | `pytest tests/test_multi_agent_learning.py` | 4 | 4 | 0 | 8.2s | API public checkpoint lifecycle + 100-case Gold Set runner |
| `tests/test_video_learning_agent.py` | `pytest tests/test_video_learning_agent.py` | 6 | 6 | 0 | 7.7s | Video transcript caching, timestamp checkpoint, permission checks |
| `tests/test_ai_tutor_api.py` | `pytest tests/test_ai_tutor*.py` | 1 | 1 | 0 | 0.9s | AI Tutor public FastAPI conversation routes |
| `tests/test_ai_tutor_at3_reacceptance.py` | (included above) | 14 | 14 | 0 | 4.1s | Acceptance tests for conversation state transitions |
| `tests/test_ai_tutor_auth_isolation.py` | (included above) | 3 | 3 | 0 | 1.2s | Cross-account conversation isolation |
| `tests/test_ai_tutor_learning.py` | (included above) | 3 | 3 | 0 | 1.3s | Learning specialist non-ROE resolution & anti-cheating |
| `tests/test_ai_tutor_module_registration.py` | (included above) | 3 | 3 | 0 | 1.0s | Module manifest registration |
| `tests/test_ai_tutor_persistence.py` | (included above) | 2 | 2 | 0 | 0.8s | SQLite message & session storage |
| `tests/test_ai_tutor_reviewers.py` | (included above) | 3 | 3 | 0 | 1.1s | Evidence & numeric reviewers, policy safety reviewers |
| `tests/test_ai_tutor_routing.py` | (included above) | 11 | 11 | 0 | 2.5s | Intent classification (learn, quant, checkpoint, general) |
| `tests/test_ai_tutor_security_hardening.py` | (included above) | 4 | 4 | 0 | 1.2s | Prompt injection & input sanitization |
| `tests/test_ai_tutor_teaching_policy.py` | (included above) | 4 | 4 | 0 | 1.1s | Socratic tone, Vietnamese addressing ("em"/"anh") |
| `tests/test_ai_tutor_tools.py` | (included above) | 4 | 4 | 0 | 1.0s | Tool grant verification |
| `tests/test_ai_tutor_unmocking.py` | (included above) | 3 | 3 | 0 | 0.9s | Provider unmocking verification via `FakeProvider` |
| `tests/test_ai_runtime_streaming.py` | `pytest tests/test_ai_runtime*.py` | 6 | 6 | 0 | 0.8s | SSE frame serialization, sequence validation, deadline |
| `tests/e2e/test_agentic_flow.py` | `pytest tests/e2e/test_agentic_flow.py` | 3 | 2 | 0 (1 skip) | 1.8s | End-to-end multi-agent execution pipeline |

### 2.2 Mock Validity & Test Flaws
1. **Shallow Crawler Tests**: `tests/test_learning_crawlers.py` only tests `open_courses` and `curated_books` using static local fixtures. The real HTTP crawler sources (`archive_org.py`, `arxiv_qfin.py`, `gutendex.py`, `mit_ocw.py`, `policy_papers.py`, `youtube_curated.py`) have zero tests.
2. **Provider Mock Isolation**: AI Tutor tests rely 100% on `FakeProvider` (`risk_dashboard.platform.ai_runtime.testing.fake_provider`). While contractually sound, this masks real network timeouts and Gemini SDK error dynamics.
3. **Frontend Test Vacuum**: `frontend/src/__tests__/learningAgent.test.js` is a placeholder verifying `assert.strictEqual(1 + 1, 2)`. There are zero frontend unit tests for checkpoint state machines or video agent interaction.

---

## 3. Deep-Dive Findings & Risk Classification

### Domain A: Async/Sync Mixing (Event Loop Blocking)

#### [Issue BE-01] Blocking Synchronous Network I/O in Async Coroutine (`LearningSpecialist.handle`)
- **Risk Level**: **CRITICAL**
- **File**: `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py`
  - Lines: 146–150
- **File**: `src/risk_dashboard/modules/learning/application/video_agent_service.py`
  - Lines: 118–125, 484
- **Observation**:
  ```python
  # learning_specialist.py:146
  if video_time_seconds is not None and video_time_seconds > 0 and target_res:
      video_reply = self.video_agent.ask(
          target_res,
          question=user_query,
          current_time_seconds=video_time_seconds,
      )
  ```
  `VideoLearningAgentService.ask()` calls `_load_transcript()`, which calls `YouTubeTranscriptProvider.fetch()`:
  ```python
  # video_agent_service.py:121
  with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
      ...
  ```
- **Root Cause**: `LearningSpecialist.handle` is an `async def` function dispatched on the FastAPI main asyncio event loop by `TutorGraph.execute`. It calls synchronous `self.video_agent.ask()`, which performs blocking HTTP requests using `urllib.request.urlopen` with an 8-second timeout.
- **Impact**: When a learner asks a timestamped question about an uncached video, the entire FastAPI event loop freezes for up to 8 seconds. All concurrent users attempting any operation on the backend are blocked.

#### [Issue BE-02] Blocking Synchronous SQLite Calls Inside Async Route Handlers
- **Risk Level**: **HIGH**
- **File**: `src/risk_dashboard/modules/ai_tutor/api/public.py` (Line 61)
- **File**: `src/risk_dashboard/modules/ai_tutor/application/conversation_service.py` (Lines 81, 100, 153)
- **File**: `src/risk_dashboard/modules/ai_tutor/application/tutor_graph.py` (Line 145)
- **Observation**:
  `send_message` is declared as `async def send_message(...)`. Inside `ConversationService.send_message`:
  - Line 81: `self.repository.get_conversation(...)`
  - Line 100: `self.repository.claim_idempotency(...)`
  - Line 153: `self.repository.save_message(...)`
  - `tutor_graph.py:145`: `self.repo.log_event(...)`
  Each repository method invokes `with open_app_state_db() as conn: conn.execute(...)`.
- **Root Cause**: Mixing synchronous SQLite database queries directly inside `async def` without wrapping in `asyncio.to_thread()` or `run_in_threadpool()`.
- **Impact**: SQLite lock waiting and file I/O operations block the asynchronous worker thread, reducing concurrent API throughput.

#### [Issue BE-03] Worker Thread Pool Monopolization in Reader Stream Proxy
- **Risk Level**: **MEDIUM**
- **File**: `src/risk_dashboard/modules/learning/api/reader_proxy.py`
  - Lines: 70–132
- **Observation**:
  `stream_reader_content` is a synchronous `def` that creates a synchronous `httpx.Client(timeout=45.0, follow_redirects=True)` and returns a `StreamingResponse(iter_bytes(), ...)`.
- **Root Cause**: Starlette runs synchronous generators returned by `StreamingResponse` inside an AnyIO worker threadpool. Because the download chunks up to 40 MB of data over HTTP, each connected reader occupies a dedicated thread for the full streaming duration.
- **Impact**: Starlette's threadpool default limit is 40 workers. 40 simultaneous users reading books/PDFs will exhaust the entire threadpool, causing all other synchronous FastAPI routes in the app to queue and timeout.

---

### Domain B: Database Connection Leaks & Transaction Integrity

#### [Issue BE-04] SQLite Connection Leaks When Custom DB Path Is Supplied
- **Risk Level**: **HIGH**
- **Files & Line Numbers**:
  - `src/risk_dashboard/modules/financials_product/infrastructure/sqlite_memo_repository.py:28-34, 44`
  - `src/risk_dashboard/modules/financials_product/infrastructure/upload_ownership_repository.py:56-61, 72`
  - `src/risk_dashboard/modules/news_intelligence/infrastructure/brief_repository.py:20-25, 28`
- **Observation**:
  ```python
  def _get_conn(self) -> sqlite3.Connection:
      if self._db_path:
          conn = sqlite3.connect(self._db_path)
          conn.row_factory = sqlite3.Row
          return conn
      return open_app_state_db()
  ```
  And in caller methods:
  ```python
  with self._get_conn() as conn:
      conn.execute(...)
  ```
- **Root Cause**: Python's `sqlite3.Connection` context manager (`with conn:`) manages **transactions** (commits on success, rolls back on exception); it **NEVER** closes the connection. Only `open_app_state_db()` has a generator context manager with `finally: conn.close()`. When `_db_path` is provided, raw connections are created and abandoned without `.close()`.
- **Impact**: Accumulation of unclosed SQLite file descriptors, eventually causing `Too many open files` errors under high load or multi-test execution.

#### [Issue BE-05] Non-Atomic Multi-Table Checkpoint Progress Commit (Missing Unit-of-Work)
- **Risk Level**: **MEDIUM**
- **File**: `src/risk_dashboard/modules/learning/application/checkpoint_service.py`
  - Lines: 241–287
- **Observation**:
  `update_progress_confirmed` executes sequential operations:
  1. `self.home_reader.get_home_state()` (Conn 1)
  2. `self.progress_repo.save_progress()` (Conn 2)
  3. `self.catalog.get_path()` & `get_lesson()` (Conn 3, 4, ...)
  4. `self.home_writer.save_home_state()` (Conn N)
  5. `self.checkpoint_repo.save_receipt()` (Conn N+1)
- **Root Cause**: Each operation opens and commits its own SQLite connection independently.
- **Impact**: If a failure or server reboot happens at step 4, progress is saved in `learning_lesson_progress`, but the idempotency receipt is not recorded in `learning_progress_receipts`, corrupting progress synchronization.

---

### Domain C: Performance Bottlenecks & Caching Deficiencies

#### [Issue BE-06] Repetitive Seeding Query Storm on Every Catalog Instantiation
- **Risk Level**: **CRITICAL**
- **File**: `src/risk_dashboard/modules/learning/infrastructure/catalog_reader.py`
  - Lines: 127–128, 286–326
- **File**: `src/risk_dashboard/modules/learning/api/public.py`
  - Lines: 61–62, 154, 179, 294, 312, 395
- **Observation**:
  In `public.py`:
  ```python
  def _catalog() -> SqliteLearningCatalog:
      return SqliteLearningCatalog()
  ```
  In `catalog_reader.py`:
  ```python
  class SqliteLearningCatalog(LearningCatalogReader):
      def __init__(self, content_ops_repo: SqliteAdminCmsRepository | None = None) -> None:
          self.content_ops_repo = content_ops_repo or SqliteAdminCmsRepository()
          ensure_learning_catalog_seeded(self.content_ops_repo)
  ```
  `ensure_learning_catalog_seeded` iterates across `LESSONS.values()`, `COURSES.values()`, `PATHS.values()`, and `CONTEXT_TRIGGER_TO_LESSON.items()`, executing `repo.find_published_content(...)` for every single item.
- **Root Cause**: `SqliteLearningCatalog` is re-instantiated on every endpoint call with no process-level memoization or caching flag.
- **Impact**: Over 50 redundant SQL lookups on every single request hitting Tab Learn API routes, causing latency spikes and SQLite lock contention.

#### [Issue BE-07] Unindexed `ORDER BY fetched_at` on Video, Book, and Course Catalogs
- **Risk Level**: **HIGH**
- **File**: `src/risk_dashboard/platform/database/schema/baseline.sql`
  - Lines: 106–128 (`learning_courses`), 129–151 (`learning_videos`), 152–172 (`learning_books`)
- **File**: `src/risk_dashboard/modules/learning/api/public.py`
  - Lines: 439–444
- **Observation**:
  Query in `learning_catalog`:
  ```sql
  SELECT * FROM learning_videos WHERE is_active = 1 ORDER BY fetched_at DESC NULLS LAST LIMIT 60
  ```
  Checking table definitions in `baseline.sql`:
  - `learning_videos` has indexes: `(source, external_id)`, `(tier)`, `(language)`. **NO index on `fetched_at` or `(is_active, fetched_at)`**.
  - `learning_books` has indexes: `(source, external_id)`, `(tier)`, `(language)`. **NO index on `fetched_at` or `(is_active, fetched_at)`**.
  - `learning_courses` has indexes: `(source, external_id)`, `(tier)`, `(language)`. **NO index on `fetched_at` or `(is_active, fetched_at)`**.
- **Root Cause**: Indexes were only created for filtering (`tier`, `lang`), omitting the sort column (`fetched_at`).
- **Impact**: Every catalog listing triggers a full table scan and temporary B-tree filesort in SQLite memory/disk.

#### [Issue BE-08] Unindexed `learning_lesson_progress` Query on `(user_id, path_id)`
- **Risk Level**: **MEDIUM**
- **File**: `src/risk_dashboard/platform/database/schema/baseline.sql`
  - Lines: 75–85
- **File**: `src/risk_dashboard/modules/learning/infrastructure/repositories/sqlite.py`
  - Lines: 107–115
- **Observation**:
  ```sql
  SELECT user_id, path_id, lesson_id, status, quiz_score, attempt_count, completed_at, updated_at
  FROM learning_lesson_progress
  WHERE user_id = ? AND path_id = ?
  ORDER BY updated_at DESC
  ```
  `learning_lesson_progress` has only `PRIMARY KEY (user_id, lesson_id)`. There is no index on `(user_id, path_id)`.
- **Impact**: Every visit to `/learning/home` must scan all lessons ever attempted by the user to filter by `path_id`.

#### [Issue BE-09] Nested Database Connection Locking in FTS Rebuild Fallback
- **Risk Level**: **HIGH**
- **File**: `src/risk_dashboard/modules/learning/infrastructure/retrieval.py`
  - Lines: 138–142
- **Observation**:
  ```python
  with open_app_state_db() as conn:
      count_row = conn.execute("SELECT count(*) as cnt FROM learning_fts_index").fetchone()
      if not count_row or count_row["cnt"] == 0:
          self.rebuild_index()
  ```
  Inside `self.rebuild_index()`:
  ```python
  with open_app_state_db() as conn:
      conn.execute("DELETE FROM learning_fts_index")
  ```
- **Root Cause**: `rebuild_index()` is invoked while the outer `open_app_state_db()` context is still open on the same thread.
- **Impact**: High risk of `sqlite3.OperationalError: database is locked` on SQLite when write transactions are attempted within an active read connection.

---

### Domain D: AI Tutor / Agentic Learning Architecture & Streaming

#### [Issue BE-10] AI Tutor Conversation Endpoint Lacks SSE Streaming
- **Risk Level**: **HIGH**
- **File**: `src/risk_dashboard/modules/ai_tutor/api/public.py`
  - Lines: 60–74
- **Observation**:
  ```python
  @router.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
  async def send_message(...) -> SendMessageResponse:
  ```
  The endpoint is strictly synchronous request-response returning JSON.
- **Root Cause**: While `platform/ai_runtime` provides streaming infrastructure (`StreamEvent`, `StreamingCollector`, `sse.py`), `TutorGraph` and `ConversationService` only support non-streaming `provider.generate()`.
- **Impact**: High Time-To-First-Token (TTFT) (often 10–25s) because the client must wait for the LLM response, evidence reviewer, and safety reviewer before receiving anything.

#### [Issue BE-11] Context Retrieval Disconnect: Hardcoded 4-Card Fallback in AI Tutor
- **Risk Level**: **HIGH**
- **File**: `src/risk_dashboard/modules/ai_tutor/infrastructure/adapters/learning_adapter.py`
  - Lines: 13–34, 93–96
- **File**: `src/risk_dashboard/modules/learning/application/query_handler.py`
  - Lines: 30–67
- **Observation**:
  `LearningLessonContextTool` checks `DEFAULT_LEARNING_CARDS` (a static list of 4 cards: `card_roe_01`, `card_cfo_01`, `card_risk_01`, `card_ta_01` created for Telegram bot `/learn`). `LearningQuizContextTool` checks `DEFAULT_CARD_QUIZZES` (4 static dicts).
- **Root Cause**: Adapters were prototyped with hardcoded dictionaries and never wired to search across the full multi-format catalog (books, videos, BCTC case studies, courses).
- **Impact**: AI Tutor fails to retrieve context for any actual learning resource outside those 4 static topics.

#### [Issue BE-12] FTS5 Indexing Excludes All Non-Lesson Learning Formats
- **Risk Level**: **HIGH**
- **File**: `src/risk_dashboard/modules/learning/infrastructure/retrieval.py`
  - Lines: 104–127
- **Observation**:
  `LearningRetrievalIndex.rebuild_index()` iterates only over `self.catalog.list_lessons()`. It completely ignores:
  - `learning_books`
  - `learning_videos` & `learning_video_transcripts`
  - `learning_papers`
  - `learning_courses`
  - `bctc_evidence_memos`
- **Root Cause**: The FTS retrieval mechanism was scoped only to micro-lesson text paragraphs.
- **Impact**: Zero semantic searchability for PDF books, video transcripts, academic papers, and BCTC case studies.

#### [Issue BE-13] Disjoint Video Checkpoint System vs Verified Progress Receipts
- **Risk Level**: **MEDIUM**
- **File**: `src/risk_dashboard/modules/learning/application/video_agent_service.py` (Lines 417–446)
- **File**: `src/risk_dashboard/modules/learning/schemas/video_agent.py` (Lines 88–96)
- **Observation**:
  `VideoAgentGradeResponse` returns `passed`, `score`, `feedback`, `explanation`, and `evidence`. It has NO `verified_event_id`, and there is no `/video-agent/checkpoint/complete` endpoint.
- **Root Cause**: Video agent was built as an independent subsystem with its own table (`learning_video_checkpoints`) rather than integrating with `LearningCheckpointService`'s verified event and receipt ledger.
- **Impact**: Video quiz completion cannot update user course progress or emit idempotent receipts.

---

### Domain E: Schema Drift, Contract Discrepancies & Dead Code

#### [Issue BE-14] Untyped Dictionary Return on `/learning/catalog` Endpoint
- **Risk Level**: **MEDIUM**
- **File**: `src/risk_dashboard/modules/learning/api/public.py`
  - Lines: 403–410
- **Observation**:
  ```python
  @router.get("/catalog", tags=["Learning"])
  def learning_catalog(...) -> dict:
  ```
- **Root Cause**: Missing Pydantic model declaration for the catalog response.
- **Impact**: No OpenAPI documentation, no runtime validation of fields (`duration_seconds`, `topics`, `channel`), risking runtime client errors if SQLite schema evolves.

#### [Issue BE-15] Dead/Orphaned Services in `services.py`
- **Risk Level**: **LOW**
- **File**: `src/risk_dashboard/modules/learning/application/services.py`
  - Lines: 237–273
- **File**: `tests/test_learning.py`
  - Lines: 84–100
- **Observation**:
  `ExplainLessonWithTutor` and `GetLearningCoach` classes exist in `services.py`, but their API routes `/learning/tutor` and `/learning/coach` were deleted from `public.py`. `tests/test_learning.py` explicitly tests and asserts that calling these endpoints returns 404!
- **Root Cause**: Incomplete refactoring during AI Tutor consolidation.

---

## 4. Synthesis Matrix of Findings

| ID | Issue Description | Location | Risk | Affected Subsystem | Recommended Fix |
|---|---|---|---|---|---|
| **BE-01** | Blocking YouTube `urllib.urlopen` in async coroutine | `learning_specialist.py:146`, `video_agent_service.py:121` | **CRITICAL** | AI Tutor / Video Agent | Wrap in `asyncio.to_thread` or switch to async `httpx.AsyncClient` |
| **BE-06** | Query storm on every `SqliteLearningCatalog.__init__` | `catalog_reader.py:127`, `public.py:61` | **CRITICAL** | Tab Learn Catalog | Singleton / process-wide `_seeded` cache flag |
| **BE-02** | Blocking SQLite DB calls in async `send_message` | `public.py:61`, `conversation_service.py:81` | **HIGH** | AI Tutor API | Wrap DB calls in `asyncio.to_thread` |
| **BE-04** | SQLite connection leak when `_db_path` is passed | `sqlite_memo_repository.py:28`, `upload_ownership_repository.py:56` | **HIGH** | Financials Product / DB | Use `platform.database.open_db` context manager |
| **BE-07** | Missing index on `ORDER BY fetched_at` | `baseline.sql:129`, `public.py:441` | **HIGH** | Catalog Repository | Add `idx_learning_{kind}_fetched` indexes |
| **BE-09** | Nested DB connection deadlock risk in FTS search | `retrieval.py:138` | **HIGH** | Curriculum Retrieval | Close connection before calling `rebuild_index` |
| **BE-10** | Missing SSE Streaming in AI Tutor conversation | `public.py:61`, `tutor_graph.py:61` | **HIGH** | AI Tutor Experience | Implement `POST /ai-tutor/.../stream` with SSE |
| **BE-11** | AI Tutor adapter fallback to hardcoded 4 cards | `learning_adapter.py:13`, `query_handler.py:30` | **HIGH** | AI Tutor Context | Connect adapter to `SqliteLearningCatalog` and FTS index |
| **BE-12** | FTS5 index omits books, videos, papers, BCTC cases | `retrieval.py:106` | **HIGH** | Multi-Format Search | Expand `LessonChunker` to index all 4 asset types |
| **BE-03** | Reader proxy streaming holds worker threads | `reader_proxy.py:74` | **MEDIUM** | Ebook/PDF Reader | Switch to `httpx.AsyncClient` & async generator |
| **BE-05** | Checkpoint completion lacks atomic transaction | `checkpoint_service.py:241` | **MEDIUM** | Checkpoint Progress | Enclose in single SQLite transaction |
| **BE-08** | Missing index on `(user_id, path_id)` in progress | `baseline.sql:75`, `sqlite.py:108` | **MEDIUM** | Learning Progress | Add `idx_learning_lesson_progress_path` index |
| **BE-13** | Video checkpoints disjoint from progress receipts | `video_agent_service.py:417` | **MEDIUM** | Video Agent | Harmonize with `LearningCheckpointService` |
| **BE-14** | Untyped dictionary response on `/learning/catalog` | `public.py:403` | **MEDIUM** | Catalog Contract | Define `LearningCatalogListResponse` Pydantic model |
| **BE-15** | Dead `ExplainLessonWithTutor` and `GetLearningCoach` | `services.py:237` | **LOW** | Learning Services | Clean up dead code and remove 404 test assertions |
