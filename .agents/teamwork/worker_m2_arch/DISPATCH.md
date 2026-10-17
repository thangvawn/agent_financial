# Worker M2: Author Full Architectural Redesign of Tab Learn Hub

**Working Directory**: /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch  
**Target Output**: `/Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_ARCHITECTURE.md`  
**Mandatory Inputs**:
- `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/mac/Documents/Dự án Agent Tài chính/PROJECT.md`
- `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_domain/analysis.md`
- `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_fe/analysis.md`
- `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_be/analysis.md`

## Task Objectives
Fulfill Requirement R2 from `ORIGINAL_REQUEST.md` by writing the comprehensive Architecture Document (`docs/LEARN_HUB_ARCHITECTURE.md`).
The architectural design must include:
1. **Target Architecture & Design Philosophy**: Modern, high-performance financial learning platform integrating 4 core pillars:
   - (1) Ebook/PDF Reader with page anchoring, bookmarking, and text highlighting.
   - (2) Video Lecture Player with synchronized timestamps, key takeaways, and time-marked notes.
   - (3) Hierarchical Courses (Course -> Module -> Lesson -> Checkpoint) with server-side progress tracking & verified receipts.
   - (4) Financial Statements (BCTC) Case-Studies integrating authentic VN30 data (120+ cached companies like FPT, VNM, HPG), ratio analysis, and sandbox challenges.
2. **Relational Data Model & DDL Specifications**:
   - Complete SQL DDL for SQLite / PostgreSQL:
     - `learning_courses_v2`, `learning_course_modules`, `learning_course_lessons`, `learning_checkpoints`, `learning_user_progress`.
     - `learning_book_metadata`, `learning_book_annotations`, `learning_book_bookmarks`.
     - `learning_video_metadata`, `learning_video_timestamps`, `learning_video_notes`.
     - `learning_bctc_cases`, `learning_bctc_case_steps`, `learning_bctc_submissions`.
     - Indexes on `(is_active, fetched_at)`, foreign keys with ON DELETE CASCADE, integrity constraints.
3. **Pydantic v2 Domain Models**: Production-grade type definitions with strict validation for all multi-format entities, request/response schemas, and progress payloads.
4. **Taxonomy, Tagging & VN30 Stock Cross-Linking Architecture**:
   - Difficulty tiers: Beginner (Nhập môn), Intermediate (Cơ bản), Advanced (Chuyên sâu), Expert (Thực chiến).
   - Multi-dimensional taxonomy: Topics (Phân tích cơ bản, Phân tích kỹ thuật, Tài chính doanh nghiệp, Định giá, Quản trị rủi ro), Asset Classes, Competencies.
   - Dynamic ticker linking mechanism tying learning modules to real-world financial records in `data/financials/cache/` (e.g. HPG Capex cycle case study, VNM margin compression, FPT software growth).
5. **AI Tutor / Agentic Learning Socratic Architecture**:
   - Context Grounding Protocol: Payloads for document context (`page_number`, `selected_text`, `bounding_box`), video context (`timestamp_seconds`, `transcript_snippet`), and BCTC context (`ticker`, `report_type`, `period`, `line_item`).
   - Socratic Prompting & Zero-Leakage Policy: Guardrails against test answer leaks, generating scaffolding hints instead of raw answers.
   - Full-text search (FTS5) retrieval engine indexing all 4 media types.

Write your document to `/Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_ARCHITECTURE.md`, summary to `handoff.md`, and notify parent via `send_message`.

## 2026-10-10T11:18:06Z
You are worker_m2_arch. Your working directory is /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch.
Please read:
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/mac/Documents/Dự án Agent Tài chính/PROJECT.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch/DISPATCH.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_domain/analysis.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_fe/analysis.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_be/analysis.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task is to author the authoritative and comprehensive Architectural Redesign Document in /Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_ARCHITECTURE.md fulfilling Requirement R2 in full.
Cover in detail:
1. Architectural vision and 4-pillar multi-format model (Ebooks with page anchoring, Videos with timestamps & notes, 4-tier Hierarchical Courses, authentic BCTC Case-Studies).
2. Complete SQL DDL specifications (tables, foreign keys, indexes, triggers, constraints) for all multi-format entities, progress receipts, and bookmarks/notes.
3. Production-grade Pydantic v2 domain schemas with validation.
4. Comprehensive taxonomy & tagging system (difficulty tiers, topic taxonomy, asset classes) and dynamic cross-linking to VN30 financial data (FPT, HPG, VNM cache in data/financials/cache/).
5. Socratic AI Tutor & Agentic Learning Architecture (multi-modal context grounding protocol for documents, videos, and BCTC cells; Zero-Leakage guardrails; unified FTS5 multi-format search).

Ensure the output file docs/LEARN_HUB_ARCHITECTURE.md is written in professional Vietnamese with complete diagrams, DDL, code schemas, and architectural clarity.
Write a summary handoff to /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch/handoff.md and send a completion message back to orchestrator (conversation ID: 97a90bba-b298-4ab1-be4b-07eacc3cdf32).
