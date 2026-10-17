# Worker M3 Remediation: Fix DB Recovery, Checkpoint Schema, Stream Provider & Cache Policies

**Working Directory**: /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m3_blueprint_r2  
**Target File to Update**: `/Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_BLUEPRINT.md`

## Required Remediations
1. **Add Database Recovery / Re-seeding Step to Phase 0**:
   - Detail the automated recovery command and clean seeding script to fix corrupt/malformed SQLite database files (such as `data/db/northstar.db` returning malformed disk image).
2. **Synchronize Checkpoint Request Schema**:
   - In `POST /api/v1/public/learning/checkpoints/{id}/submit`, ensure the payload schema supports multi-question submissions: `selected_options: dict[str, str]` (mapping `question_id` -> `selected_option_id`).
3. **Add `<SocraticStreamProvider />` for Mobile Drawer Stream Persistence**:
   - In Section 3 (Frontend Architecture), specify a top-level `<SocraticStreamProvider />` context so that closing/opening the AI Tutor Drawer on screens < 1024px does NOT unmount or abort ongoing SSE streaming connections.
4. **Add `seekQueueRef` in `YouTubePlayerBridge.jsx`**:
   - Specify queueing mechanism in `YouTubePlayerBridge.jsx` to prevent seek race conditions when timestamp jump is triggered before `onReady`.
5. **Refine Cache-Control Policies**:
   - For user-specific endpoints (`/learning/courses/{id}`, `/learning/lessons/{id}`), set `Cache-Control: private, no-cache, must-revalidate` to prevent browsers from caching stale "incomplete" lesson progress.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.



## 2026-10-10T11:38:57Z
You are worker_m3_blueprint_r2. Your working directory is /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m3_blueprint_r2.
Please read:
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m3_blueprint_r2/DISPATCH.md
- /Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_BLUEPRINT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Apply all necessary remediations directly to /Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_BLUEPRINT.md:
1. Add automated Database Recovery / Re-seeding procedure to Phase 0 of the Migration Roadmap to resolve corrupt SQLite disk images (like northstar.db malformed).
2. Synchronize Checkpoint Request Schema in POST /learning/checkpoints/{id}/submit to support multi-question submissions: selected_options: dict[str, str].
3. Add <SocraticStreamProvider /> context wrapper in Section 3 to prevent stream connection teardown when the AI Tutor Drawer is closed on mobile (< 1024px).
4. Add seekQueueRef in YouTubePlayerBridge.jsx to prevent timestamp seek race conditions before player onReady.
5. Update Cache-Control header specification: Use 'private, no-cache, must-revalidate' for user progress and course details to prevent stale cached states.

Write your handoff report to handoff.md and send a completion message back to orchestrator (conversation ID: 97a90bba-b298-4ab1-be4b-07eacc3cdf32).
