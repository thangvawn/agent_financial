# HANDOFF REPORT — FRONTEND & TAB LEARN AUDIT
**Agent**: `explorer_survey_fe`  
**Working Directory**: `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_fe`  
**Milestone**: R1 - System Audit & Survey  
**Target Recipient**: Orchestrator (`97a90bba-b298-4ab1-be4b-07eacc3cdf32`)

---

## 1. OBSERVATION

1. **Test Runner Scripts & Failure**:
   - `frontend/package.json:6-14`: Script block contains `"test:unit": "node ./scripts/test-runner.mjs"`, but missing `"test"` script.
   - Command `npm test` inside `frontend/` exited with Code 1:
     ```
     npm error Missing script: "test"
     npm error To see a list of scripts, run: npm run
     ```
   - Command `npm run test:unit` exited with Code 0 (20 passed, 6 suites in 2.18s).
   - Test `src/__tests__/learningAgent.test.js:6`: Assertion contains verbatim `assert.strictEqual(1 + 1, 2)`.
   - Test helper `src/__tests__/test-helpers.js:30`: Loads components using `server.ssrLoadModule` and asserts against `renderToString` HTML text. No jsdom, no event dispatching, no async hook lifecycle.
   - Backend tests:
     - `.venv/bin/pytest tests/test_learning.py tests/test_ai_tutor_learning.py`: 8 passed in 15.40s.
     - `.venv/bin/pytest tests/test_learning_agent_checkpoint.py tests/test_learning_agent_contracts.py tests/test_video_learning_agent.py tests/test_learning_remediation.py`: 23 passed in 15.23s.
     - `.venv/bin/pytest tests/test_ai_tutor_api.py tests/test_ai_tutor_security_hardening.py`: 5 passed in 10.06s.

2. **Video Player Re-Render Loop & YouTube Disconnection**:
   - `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx:41,122`:
     ```javascript
     const [currentTimeSeconds, setCurrentTimeSeconds] = useState(0)
     ...
     onTimeUpdate={(event) => setCurrentTimeSeconds(event.currentTarget.currentTime)}
     ```
     HTML5 video fires `timeupdate` 4-5 times/sec, triggering continuous re-renders of the entire `CoursePlayerPage` hierarchy.
   - `frontend/src/features/learn-hub/pages/CourseVideoPlayer.jsx:16-24`:
     YouTube player is rendered as a plain `<iframe src={youtubeEmbed} ...>` without `enablejsapi=1` or YouTube postMessage bridge. `currentTimeSeconds` remains permanently `0` for all YouTube lectures.

3. **Memory Leak & Unhandled LocalStorage Quota**:
   - `frontend/src/features/learn-hub/pages/NotePaper.jsx:125-135`: Each notebook page instantiates a `<canvas width={960} height={1400} />` occupying ~5.38MB uncompressed GPU bitmap RAM. Ten pages require >53.8MB.
   - `frontend/src/features/learn-hub/pages/useBookReaderState.js:157`: `window.localStorage.setItem(...)` saves full base64 images and drawing PNGs without `try-catch`, causing unhandled `QuotaExceededError` crashes once storage exceeds ~5MB.

4. **Client-Side Answer Key Leakage in CFA Mock Exam**:
   - `frontend/src/features/learn-hub/content/mockExamData.js:1-417`: 59.5KB file contains all 90 questions with raw `correctOptionId`, `explanation`, and `takeaway` bundled in production JS.
   - `frontend/src/features/learn-hub/pages/MockExamRoomPage.jsx:153-178`: Grading is computed 100% client-side via `.reduce((count, item) => count + (answers[item.id] === item.correctOptionId ? 1 : 0), 0)`.
   - `MockExamRoomPage.jsx:219-234`: Serializes and writes 90 question answers to `localStorage` every 1000ms on timer tick.

5. **API Contract Drift**:
   - Backend `src/risk_dashboard/modules/learning/schemas/agent_tools.py:57-64`: `GetQuizItemOutput` does not contain `socratic_coaching`.
   - Frontend `features/learn-hub/types/learningTypes.js:14`: expects `socratic_coaching?: { focus_concept?: string, hint?: string }`. As a result, `SocraticHintWidget.jsx` always falls back to generic default text.
   - Backend `src/risk_dashboard/modules/learning/schemas/video_agent.py:100`: `source_url: HttpUrl | None = None` rejects local relative URLs (`/learning-assets/...`) with HTTP 422.
   - Frontend `CoursePlayerPage.jsx:73-82`: Writes lesson completion only to `localStorage`, never calling backend `POST /api/v1/public/learning/lessons/{id}/complete`.

6. **Orphaned Dead Code**:
   - Unused hooks: `useLearningHome.js`, `useLearningAssets.js`, `useLearningMutations.js`, `useLearningNextLessonBundle.js`, `useMasteryProposal.js`.
   - Unused components/schemas: `LibraryMedia.jsx`, `LearnHubPage.jsx`, `learningSchemas.js`.

---

## 2. LOGIC CHAIN

1. *From Obs 1*: Because `package.json` omits the `"test"` script, any CI/CD or developer running standard `npm test` fails immediately. Furthermore, because existing unit tests use `renderToString` without jsdom or React Testing Library, 0% of interactive DOM events, async hooks, or network failure paths are verified by tests.
2. *From Obs 2*: In `CoursePlayerPage`, hoisting `currentTimeSeconds` into the root page component while subscribing to HTML5 `timeupdate` causes the entire component tree to re-execute every 200ms. Conversely, for YouTube lectures, no event is wired, leaving `currentTimeSeconds` at 0, which breaks downstream timestamps in `VideoLearningAgentPanel` and `LearnTutorPanel`.
3. *From Obs 3*: Instantiating a 960x1400 canvas for every rendered page multiplies memory usage linearly with page count ($5.38\text{MB} \times N$). Serializing multiple canvas snapshots into `localStorage` inevitably triggers `QuotaExceededError`, and the lack of error handling causes application crashes.
4. *From Obs 4*: Because `mockExamData.js` embeds all 90 answers in the frontend bundle and grading occurs in `calculateResult` on the client, the exam integrity is compromised and results cannot be trusted or certified by the backend.
5. *From Obs 5*: The discrepancy between `GetQuizItemOutput` and `CheckpointItem` causes the Socratic coaching feature to degrade to generic hardcoded prompts, while the lack of backend completion calls prevents cross-device persistence.
6. *From Obs 6*: Orphaned files clutter the codebase, increase cognitive load, and obscure the active data paths.

---

## 3. CAVEATS

1. E2E browser tests (Playwright) for Tab Learn were not run live in this investigation turn because the local dev server was not spun up in persistent background mode; findings are derived from static AST, source analysis, Vite production build inspection, and Node test runner execution.
2. The current backend SQLite catalog tables (`learning_courses`, `learning_videos`, `learning_books`) depend on crawler population (`risk-learning-crawl`). When empty, the backend returns empty fallback items, which triggers frontend fallback to `DEMO_COURSES` and `DEMO_BOOKS`.

---

## 4. CONCLUSION

Phân hệ Tab Learn hiện tại có giao diện phong phú nhưng gặp phải 4 điểm nghẽn kiến trúc nghiêm trọng:
1. **Hiệu năng & Rò rỉ**: Re-render cascade từ video `timeupdate` (4-5 lần/s), memory bloat do canvas 960x1400 đa trang, và I/O nghẽn main thread trên `localStorage` mỗi giây.
2. **Bảo mật & Toàn vẹn dữ liệu**: Lộ 90 đáp án CFA trong client bundle, chấm thi hoàn toàn ở client, và tiến độ khóa học không đồng bộ về cơ sở dữ liệu backend.
3. **Lệch chuẩn API Contract**: Trường `socratic_coaching` bị thiếu ở Backend schema khiến Socratic Hint rơi vào fallback tĩnh; URL video local gây lỗi 422 trên Video Agent.
4. **Chất lượng kiểm thử**: `npm test` lỗi do thiếu script; bộ test hiện hữu dùng `renderToString` tĩnh với 0% độ phủ cho hooks, interactions, và API calls.

Toàn bộ chi tiết kỹ thuật, trích dẫn file và dòng đã được lập báo cáo đầy đủ tại:  
`/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_fe/analysis.md`.

---

## 5. VERIFICATION METHOD

1. **Verify npm test script error**:
   ```bash
   cd /Users/mac/Documents/Dự\ án\ Agent\ Tài\ chính/frontend
   npm test
   # Expected: Exit code 1 with "npm error Missing script: 'test'"
   ```
2. **Verify unit test runner execution**:
   ```bash
   cd /Users/mac/Documents/Dự\ án Agent\ Tài chính/frontend
   npm run test:unit
   # Expected: 20 pass in ~2.18s
   ```
3. **Verify backend learning test suite**:
   ```bash
   cd /Users/mac/Documents/Dự\ án Agent\ Tài chính
   .venv/bin/pytest tests/test_learning.py tests/test_learning_agent_checkpoint.py tests/test_video_learning_agent.py
   # Expected: All tests pass
   ```
4. **Inspect source citations**:
   - Video re-render: `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx:41,122`
   - YouTube iframe: `frontend/src/features/learn-hub/pages/CourseVideoPlayer.jsx:16-24`
   - Canvas memory: `frontend/src/features/learn-hub/pages/NotePaper.jsx:125-135`
   - CFA answer keys: `frontend/src/features/learn-hub/content/mockExamData.js:26-417`
   - Backend Quiz schema: `src/risk_dashboard/modules/learning/schemas/agent_tools.py:57-64`
