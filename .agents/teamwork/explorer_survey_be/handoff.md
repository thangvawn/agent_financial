# Handoff Report — Backend Codebase & Tests Audit (Tab Learn & AI Tutor)

**Author**: `explorer_survey_be`  
**Recipient**: `orchestrator_1` / System Architect  
**Date**: 2026-10-10  
**Scope**: Backend Python/FastAPI codebase, SQLite persistence, AI Runtime integration, and automated test suites.

---

## 1. Observation

1. **Automated Test Runs**:
   - `pytest tests/test_learning*.py`: 49 passed in 30.73s.
   - `pytest tests/test_multi_agent_learning.py tests/test_video_learning_agent.py`: 10 passed in 15.91s.
   - `pytest tests/test_ai_tutor*.py`: 55 passed in 16.19s.
   - `pytest tests/test_ai_runtime_*.py tests/e2e/test_agentic_flow.py`: 33 passed, 1 skipped in 4.26s.
   - Total: **147 passed, 1 skipped** out of 148 test cases.
2. **Blocking I/O in Async Coroutines**:
   - In `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py:146-150`, `handle()` is an `async def` function that calls synchronous `self.video_agent.ask(target_res, ...)`.
   - In `src/risk_dashboard/modules/learning/application/video_agent_service.py:121`, `YouTubeTranscriptProvider.fetch` invokes `with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:`.
   - In `src/risk_dashboard/modules/ai_tutor/api/public.py:61` and `src/risk_dashboard/modules/ai_tutor/application/conversation_service.py:81, 100, 153`, synchronous `open_app_state_db()` SQLite calls are executed directly inside `async def send_message()`.
3. **Repeated Seeding Query Storm**:
   - In `src/risk_dashboard/modules/learning/api/public.py:61-62`, every route dependency calls `_catalog() -> SqliteLearningCatalog()`.
   - In `src/risk_dashboard/modules/learning/infrastructure/catalog_reader.py:127-128`, `SqliteLearningCatalog.__init__` executes `ensure_learning_catalog_seeded(self.content_ops_repo)`.
   - Lines 286–326 iterate over all `LESSONS`, `COURSES`, `PATHS`, and `CONTEXT_TRIGGER_TO_LESSON`, executing 50+ database lookups on every single HTTP request.
4. **Database Connection Leaks**:
   - In `src/risk_dashboard/modules/financials_product/infrastructure/sqlite_memo_repository.py:28-34, 44`, `upload_ownership_repository.py:56-61, 72`, and `brief_repository.py:20-25, 28`:
     `if self._db_path: conn = sqlite3.connect(self._db_path); return conn`.
     Callers use `with self._get_conn() as conn:`, which manages transaction commit but **never calls `conn.close()`**.
5. **Missing Indexes on Order Columns**:
   - In `src/risk_dashboard/platform/database/schema/baseline.sql:106-172`, `learning_videos`, `learning_books`, and `learning_courses` lack an index on `fetched_at` or `(is_active, fetched_at)`.
   - In `src/risk_dashboard/modules/learning/api/public.py:441`, `SELECT * FROM {table} WHERE is_active = 1 ORDER BY fetched_at DESC LIMIT ?` triggers an unindexed table scan and filesort.
6. **Streaming & Context Retrieval Architecture**:
   - `src/risk_dashboard/modules/ai_tutor/api/public.py:61-74` exposes only unary `POST /ai-tutor/conversations/{id}/messages` without SSE streaming.
   - `src/risk_dashboard/modules/ai_tutor/infrastructure/adapters/learning_adapter.py:13-34, 93-96` queries `DEFAULT_LEARNING_CARDS` (4 static cards from `query_handler.py:30-67`) and misses all books, video transcripts, papers, and BCTC case studies.
   - `src/risk_dashboard/modules/learning/infrastructure/retrieval.py:106-125` FTS5 index only indexes `lesson.body`, omitting all other learning assets.
   - `src/risk_dashboard/modules/learning/api/public.py:403` `learning_catalog` returns untyped `dict` without a Pydantic response model.

---

## 2. Logic Chain

1. **From Observation 2 to Conclusion on System Freezes**:
   FastAPI uses a single thread for its asyncio event loop. Calling `urllib.request.urlopen` (synchronous network request with 8s timeout) directly inside `LearningSpecialist.handle` blocks the event loop thread entirely. Therefore, any video query with an uncached transcript blocks all concurrent requests for the duration of the network round-trip.
2. **From Observation 3 to Conclusion on High Latency / Lock Contention**:
   FastAPI instantiates dependencies per request. Calling `ensure_learning_catalog_seeded` in `SqliteLearningCatalog.__init__` forces 50+ SQLite lookups per HTTP request. Because SQLite has single-writer locking, this query storm creates severe database contention and degrades API response time under load.
3. **From Observation 4 to Conclusion on Resource Starvation**:
   Python's `sqlite3.Connection` context manager does not close connections. When custom DB paths are used, connections remain open indefinitely until garbage collected, leaking operating system file descriptors.
4. **From Observation 5 to Conclusion on Scalability Bottlenecks**:
   Without an index on `fetched_at`, SQLite must perform an `O(N)` table scan and a temporary B-tree filesort for every catalog pagination request. As the crawler ingests thousands of resources, catalog endpoint latency will degrade linearly.
5. **From Observation 6 to Conclusion on Tab Learn Architecture**:
   Tab Learn currently operates as disconnected silos: text micro-lessons in one system, crawled links in another, and AI Tutor falling back to 4 Telegram cards. Redesigning Tab Learn into a unified multi-format repository (Books/PDFs, Videos with timestamps, Hierarchical courses, BCTC case studies) requires unifying the data schema, expanding the FTS5 retrieval engine to all media types, adding SSE streaming to the AI Tutor, and standardizing Pydantic API contracts.

---

## 3. Caveats

1. **External Network Crawlers Not Executed**: Crawlers connecting to external networks (`archive_org`, `mit_ocw`, `arxiv_qfin`, `gutendex`, `policy_papers`, `youtube_curated`) were not invoked against live external targets to respect network boundaries and read-only survey guidelines.
2. **LLM Provider API Keys**: Tests were run with `FakeProvider`. In production environments without `GEMINI_API_KEY` or `OPENAI_API_KEY`, the AI Tutor defaults to static fallback templates.
3. **Alternative Interpretation Considered**: The synchronous implementation of routes in `learning/api/public.py` (declared as `def` instead of `async def`) offloads execution to AnyIO worker threads, which avoids event loop blocking for pure CPU work; however, for long streaming operations (`reader_proxy`), this risks threadpool exhaustion.

---

## 4. Conclusion

The current Backend provides a functioning baseline for Tab Learn with 100% passing test coverage (147 passed, 1 skipped). However, it is not production-ready for a high-traffic, multi-format financial learning platform due to:
1. **Critical performance hazards**: Repetitive seeding query storms on every catalog initialization, unindexed sorting queries, and blocking `urllib` I/O on the asyncio event loop.
2. **Architectural fragmentation**: AI Tutor and FTS5 retrieval are decoupled from the broader catalog (books, videos, BCTC case studies), AI Tutor lacks SSE streaming, and video checkpoints are disconnected from progress receipts.
3. **Connection leaks**: Repositories using custom `_db_path` fail to close SQLite connections.

All identified issues are detailed with file citations and line numbers in `analysis.md`. A remediation blueprint is ready for implementation by the engineering team.

---

## 5. Verification Method

To independently reproduce and verify all observations:

1. **Execute All Backend Test Suites**:
   ```bash
   .venv/bin/pytest tests/test_learning*.py -v
   .venv/bin/pytest tests/test_multi_agent_learning.py tests/test_video_learning_agent.py -v
   .venv/bin/pytest tests/test_ai_tutor*.py -v
   .venv/bin/pytest tests/test_ai_runtime_*.py tests/e2e/test_agentic_flow.py -v
   ```
2. **Inspect Blocking I/O**:
   - View `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py:146-150`.
   - View `src/risk_dashboard/modules/learning/application/video_agent_service.py:121`.
3. **Inspect Catalog Seeding Storm**:
   - View `src/risk_dashboard/modules/learning/infrastructure/catalog_reader.py:127-128, 286-326`.
4. **Inspect Connection Leak**:
   - View `src/risk_dashboard/modules/financials_product/infrastructure/sqlite_memo_repository.py:28-34`.
5. **Inspect Missing Indexes**:
   - View `src/risk_dashboard/platform/database/schema/baseline.sql:125-127, 148-150, 169-171`.

**Invalidation Conditions**:
- If `SqliteLearningCatalog` is refactored into a singleton or cached with an in-memory process flag, Issue BE-06 is invalidated.
- If `video_agent_service.py` switches to `httpx.AsyncClient` or offloads to `asyncio.to_thread`, Issue BE-01 is invalidated.
