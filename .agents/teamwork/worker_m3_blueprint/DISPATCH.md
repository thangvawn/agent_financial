# Worker M3: Author Technical Specification & Implementation Blueprint

**Working Directory**: /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m3_blueprint  
**Target Output**: `/Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_BLUEPRINT.md`  
**Mandatory Inputs**:
- `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/mac/Documents/Dự án Agent Tài chính/PROJECT.md`
- `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_domain/analysis.md`
- `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_fe/analysis.md`
- `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_be/analysis.md`

## Task Objectives
Fulfill Requirement R3 from `ORIGINAL_REQUEST.md` by writing the comprehensive Blueprint Document (`docs/LEARN_HUB_BLUEPRINT.md`).
The technical blueprint must include:
1. **REST & Streaming API Contracts**:
   - Catalog APIs: `GET /api/v1/public/learning/catalog`, `GET /api/v1/public/learning/courses/{id}`, `GET /api/v1/public/learning/books/{id}`, `GET /api/v1/public/learning/videos/{id}`, `GET /api/v1/public/learning/bctc-cases/{id}` with full request/response schemas, query filters (ticker, topic, level), and caching policies (HTTP Cache-Control & Redis/in-memory TTL).
   - User Progress & Checkpoints: `POST /api/v1/public/learning/lessons/{id}/complete`, `POST /api/v1/public/learning/checkpoints/{id}/submit` with server-side validation and cryptographic receipts.
   - User Annotations & Notes: CRUD APIs for book annotations, bookmarks, and video timestamped notes.
   - AI Tutor Server-Sent Events (SSE) Streaming API:
     - `POST /api/v1/public/ai-tutor/conversations/{id}/messages/stream`
     - Detailed SSE event specification: `event: token`, `event: citation`, `event: socratic_scaffold`, `event: error`, `event: done`.
     - Connection lifecycle, reconnection, backoff, and heartbeat.
2. **Frontend UI Component Hierarchy & Dual-Pane Layout**:
   - Layout architecture: `<LearnHubDualPaneLayout />` with Left Pane (Reader/Player/Case-Study Sandbox) and Right Pane (AI Socratic Companion).
   - Component Tree breakdown strictly adhering to modularity rules (<200 lines per component):
     - `LearnHubHeader.jsx`, `LearnCatalogGrid.jsx`, `LearnFilterBar.jsx`.
     - `EbookReaderWorkspace.jsx`, `PdfDocumentViewer.jsx`, `PdfAnnotationLayer.jsx`, `PdfBookmarkDrawer.jsx`.
     - `VideoPlayerWorkspace.jsx`, `Html5VideoPlayer.jsx`, `YouTubePlayerBridge.jsx`, `VideoTimestampNotes.jsx`, `VideoTakeawaysList.jsx`.
     - `CoursePlayerWorkspace.jsx`, `CourseCurriculumSidebar.jsx`, `LessonContentPane.jsx`, `CheckpointQuizModal.jsx`.
     - `BctcCaseStudyWorkspace.jsx`, `BctcFinancialsViewer.jsx`, `BctcRatioChallenge.jsx`, `BctcSubmissionFeedback.jsx`.
     - `SocraticAiCompanion.jsx`, `AiTutorMessageList.jsx`, `AiTutorInputBox.jsx`, `SocraticContextBadge.jsx`.
   - Client-side State Machine & Custom Hooks: `useDualPaneLayout`, `useMediaTimestampSync`, `useBookReader`, `useSocraticStream`. Elimination of re-render loops and local storage write storms.
3. **Phased Migration Roadmap (Tracer Bullet Approach)**:
   - Phase 0: Quick Wins & Bug Remediation (fix `npm test` script, remove blocking urllib I/O, fix catalog query storm, add DB indexes, close connection leaks, strip CFA answers from bundle).
   - Phase 1: Tracer Bullet #1 - Multi-Format DDL & Catalog v2 (hierarchical courses, DDL migration, Pydantic schemas, catalog endpoint).
   - Phase 2: Tracer Bullet #2 - Dual-Pane Layout & Ebook/Video Workspaces (PDF reader with page anchoring, YouTube JS API player, synchronized notes).
   - Phase 3: Tracer Bullet #3 - BCTC Case-Study Sandbox & Stock Symbol Cross-Linking (connect financials cache, ratio challenges, stock linking).
   - Phase 4: Tracer Bullet #4 - SSE Streaming AI Tutor with Multi-Modal Context Grounding (SSE stream endpoint, Socratic zero-leakage prompt guardrails).
   - Phase 5: Production Hardening, E2E Testing, & Legacy Deprecation.
   - For every phase: concrete deliverables, files touched, automated test verification commands, and pass criteria.

Write your document to `/Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_BLUEPRINT.md`, summary to `handoff.md`, and notify parent via `send_message`.


## 2026-10-10T11:18:06Z
[Message] timestamp=2026-10-10T11:18:06Z sender=97a90bba-b298-4ab1-be4b-07eacc3cdf32 priority=MESSAGE_PRIORITY_HIGH content=You are worker_m3_blueprint. Your working directory is /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m3_blueprint.
Please read:
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/mac/Documents/Dự án Agent Tài chính/PROJECT.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m3_blueprint/DISPATCH.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_domain/analysis.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_fe/analysis.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_be/analysis.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task is to author the authoritative and comprehensive Technical Specification & Implementation Blueprint in /Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_BLUEPRINT.md fulfilling Requirement R3 in full.
Cover in detail:
1. Exhaustive REST & SSE Streaming API contracts (endpoints, request/response JSON schemas, error codes, HTTP Cache-Control & in-memory TTL caching policies, SSE event stream specification for AI Tutor with connection lifecycle).
2. Frontend UI Component Hierarchy & Dual-Pane Layout (<LearnHubDualPaneLayout /> with Left Pane Reader/Player/BCTC sandbox and Right Pane Socratic Companion; component tree breakdown strictly <200 lines per module; custom hooks and state machines eliminating re-render loops and local storage bottlenecks).
3. 5-Phase Tracer-Bullet Migration Roadmap with automated quality gates and verification commands per phase, ensuring 100% backward compatibility.

Ensure the output file docs/LEARN_HUB_BLUEPRINT.md is written in professional Vietnamese with technical precision, API schemas, component trees, and actionable tracer bullets.
Write a summary handoff to /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m3_blueprint/handoff.md and send a completion message back to orchestrator (conversation ID: 97a90bba-b298-4ab1-be4b-07eacc3cdf32).
