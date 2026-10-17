# Project: Tab Learn Hub - System Audit, Architectural Redesign & Implementation Blueprint

## Architecture
- **Ecosystem**: Agent Tài chính (Full-Stack AI Financial Analytics & Socratic Learning System).
- **Frontend Architecture**: React 18, Vite, Tailwind CSS, Lucide icons, unified Dual-Pane Split Layout (`<LearnHubDualPaneLayout />` with Left Pane: Content Reader/Player & Right Pane: AI Socratic Companion).
- **Backend Architecture**: Python 3.10/3.11, FastAPI, AnyIO, SQLite (WAL mode, persistent connection pools), LangGraph agentic runtime, FTS5 unified multi-format retrieval, Server-Sent Events (SSE) streaming for AI Tutor.
- **Cross-Module Interfaces**: Clean Pydantic v2 schemas and TypeScript definitions connecting Learn Hub UI, Catalog Service, Socratic AI Tutor, and Financials Product (BCTC Analyzer).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Full Codebase Audit & Bottleneck Catalog | Audit frontend (re-renders, memory leaks, client-side answer leaks) & backend (blocking I/O, query storm, connection leaks) | M1 | Survey (FE & BE) |
| 2 | Automated Test Suite Execution & Gap Analysis | Execution of pytest (147 passed, 1 skipped) and npm test (missing script, unit runner pass 20) with root causes | M1 | Survey (FE & BE) |
| 3 | Root Cause & Risk Matrix (R1) | Systematic classification of all issues into Critical, High, Medium, Low with exact file:line citations | M1 | Survey (FE & BE) |
| 4 | Multi-Format Content Data Model (R2) | Relational DDL & Pydantic schemas for 4 formats: Ebook/PDF, Video timestamps, Hierarchical Courses, BCTC Case-Studies | M2 | Survey (Domain) |
| 5 | Hierarchical Course & Checkpoint Engine | 4-tier model (Course -> Module -> Lesson -> Checkpoint) with server-side progress tracking & receipts | M2 | Survey (Domain) |
| 6 | Ebook & Document Reader Architecture | Page-level anchoring, PDF annotations, bookmarks, highlighted text context grounding | M2 | Survey (Domain) |
| 7 | Video Lecture Player & Timestamped Notes | YouTube JS API bridge, HTML5 timeupdate debounce, timestamped notes, chapter navigation | M2 | Survey (FE & Domain) |
| 8 | BCTC Case-Study Learning Engine | Integration of 120+ cached Vietnamese financial reports (FPT, HPG, VNM), financial ratio challenges, Socratic tutor | M2 | Survey (Domain) |
| 9 | Taxonomy, Tagging & VN30 Symbol Cross-Linking | Unified tagging hierarchy, difficulty levels (Beginner, Intermediate, Advanced), real ticker linking | M2 | Survey (Domain) |
| 10 | AI Tutor Socratic Companion Integration | Context grounding payloads (document_context, video_context, bctc_context), Zero-Leakage quiz policy | M2 | Survey (BE & Domain) |
| 11 | REST & SSE Streaming API Specifications (R3) | Comprehensive API contracts: catalog, player, progress, checkpoints, and `/ai-tutor/conversations/{id}/messages/stream` | M3 | Survey (BE & Domain) |
| 12 | Dual-Pane UI Component Hierarchy & State Machine | Modular React components (<200 lines each), responsive split pane, synchronized state management | M3 | Survey (FE & Domain) |
| 13 | Phased Migration Roadmap (Tracer Bullet Approach) | 5-phase migration plan with backward compatibility and automated quality gates per phase | M3 | Survey (Domain) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Comprehensive Codebase & Test Audit Report | Full audit deliverable synthesizing FE & BE findings, automated test execution, root causes, and risk matrix (`docs/LEARN_HUB_AUDIT_REPORT.md`) | none | DONE |
| M2 | Full Architectural Redesign of Tab Learn Hub | Relational ERD/DDL, Pydantic models, 4-pillar multi-format specs, taxonomy, and Socratic AI Tutor integration (`docs/LEARN_HUB_ARCHITECTURE.md`) | M1 | DONE |
| M3 | Technical Specification & Implementation Blueprint | REST & SSE API contracts, dual-pane component hierarchy, state machines, and tracer bullet migration roadmap (`docs/LEARN_HUB_BLUEPRINT.md`) | M2 | DONE |
| M4 | Final Verification, Adversarial Challenge & Forensic Audit | Reviewer multi-angle check, Challenger stress verification (17/17 empirical tests pass), and Forensic Integrity Audit gate (CLEAN) | M3 | DONE |

## Interface Contracts
### Learn Hub UI ↔ Backend Catalog API
- `GET /api/v1/public/learning/catalog`: Returns typed `LearningCatalogResponse` with categories, items (books, videos, courses, bctc_cases), and pagination.
- `GET /api/v1/public/learning/courses/{course_id}`: Returns hierarchical `CourseDetailResponse` (modules, lessons, checkpoints).
- `POST /api/v1/public/learning/lessons/{lesson_id}/complete`: Records server-side progress receipt with checksum.

### Learn Hub UI ↔ AI Tutor Service
- `POST /api/v1/public/ai-tutor/conversations/{conversation_id}/messages/stream`:
  - Request: `SendMessageRequest` with `content`, `mode` ("socratic" | "direct"), and `context_grounding`:
    - `document_context`: `{ book_id, page_number, selected_text, bounding_box }`
    - `video_context`: `{ video_id, timestamp_seconds, transcript_snippet }`
    - `bctc_context`: `{ ticker, report_type, period, line_item_id, cell_value }`
  - Response: Server-Sent Events (SSE) stream (`event: token`, `event: citation`, `event: socratic_scaffold`, `event: done`).

### Learn Hub UI ↔ BCTC Engine
- BCTC case study links to `BctcResolveReportTool` and `BctcResolveLineItemTool` with sandboxed calculation validation.

## Code Layout
- `docs/LEARN_HUB_AUDIT_REPORT.md`: Comprehensive audit report (R1).
- `docs/LEARN_HUB_ARCHITECTURE.md`: Full architectural redesign and multi-format data models (R2).
- `docs/LEARN_HUB_BLUEPRINT.md`: Technical specification, API contracts, UI hierarchy, and migration roadmap (R3).
- `src/risk_dashboard/modules/learning/`: Backend learning domain (schemas, services, repositories, API).
- `src/risk_dashboard/modules/ai_tutor/`: Backend AI Tutor domain (agents, specialists, streaming API).
- `frontend/src/features/learn-hub/`: Frontend Learn Hub components, hooks, pages, and services.
