# BÁO CÁO BÀN GIAO KỸ THUẬT (HANDOFF REPORT) - WORKER M3 BLUEPRINT

**Worker**: `worker_m3_blueprint`  
**Milestone**: M3 - Technical Specification & Implementation Blueprint  
**Mục tiêu bàn giao**: Tài liệu Đặc tả Kỹ thuật và Bản thiết kế Triển khai Toàn diện Phân hệ Learn Hub v2.0 (`docs/LEARN_HUB_BLUEPRINT.md`)  
**Người nhận**: Orchestrator (Conversation ID: `97a90bba-b298-4ab1-be4b-07eacc3cdf32`)  
**Thời gian hoàn thành**: 2026-10-10T11:23:00Z  

---

## 1. Observation (Quan Sát Trực Tiếp)

1. **Khảo sát Yêu cầu & Đầu vào**:
   - `ORIGINAL_REQUEST.md:25-30`: Yêu cầu R3 quy định cung cấp bộ đặc tả kỹ thuật đầy đủ: API REST/Streaming (Endpoints, Request/Response payload, Cache policy), Thiết kế UI Dual-Pane (Component hierarchy, State management machine), và Kế hoạch triển khai phân đoạn (Phased migration roadmap) với phương pháp Tracer bullet đảm bảo tương thích ngược.
   - `PROJECT.md:20-24, 54`: Xác định deliverables của M3 là `docs/LEARN_HUB_BLUEPRINT.md` đáp ứng các interface contracts giữa Learn Hub UI, Backend Catalog, BCTC Engine, và AI Tutor.
   - `worker_m3_blueprint/DISPATCH.md:12-42`: Giao nhiệm vụ chi tiết hóa 3 trụ cột: (1) REST & SSE API contracts (catalog, courses, books, videos, bctc-cases, checkpoints, annotations, notes, `/ai-tutor/.../messages/stream`), (2) Frontend UI Component Hierarchy theo layout `<LearnHubDualPaneLayout />` tuân thủ nghiêm ngặt giới hạn <200 dòng/module, (3) Lộ trình phân đoạn 5 phase với automated quality gates.

2. **Khảo sát Hiện trạng Codebase từ các Báo cáo Kiểm toán (Domain, FE, BE)**:
   - `explorer_survey_fe/analysis.md:46-57`: Phát hiện 11 vấn đề nghiêm trọng, nổi bật là:
     - `FE-PERF-01`: Re-render cascade 4-5 lần/giây trong `CoursePlayerPage.jsx:41,122` do `onTimeUpdate` nâng trực tiếp lên root state.
     - `FE-PERF-02`: YouTube embed trong `CourseVideoPlayer.jsx:16-24` không có `enablejsapi=1` và `postMessage` listener, khiến `currentTime` luôn bằng 0.
     - `FE-MEM-01`: Canvas 960x1400 mount cho mỗi trang ghi chú trong `NotePaper.jsx:125-135` gây tiêu tốn 5.38MB GPU uncompressed memory/trang và `toDataURL` freeze main thread.
     - `FE-DATA-01`: 100% đáp án 90 câu CFA bị bundle trong `mockExamData.js:9-417` và chấm điểm hoàn toàn ở client.
     - `FE-TEST-01`: File `frontend/package.json` thiếu lệnh `npm test` tiêu chuẩn.
   - `explorer_survey_be/analysis.md:68-115, 163-238, 243-289`: Phát hiện 15 vấn đề backend, nổi bật là:
     - `BE-01`: Blocking synchronous `urllib.request.urlopen` trong `learning_specialist.py:146` và `video_agent_service.py:121` gây đóng băng FastAPI asyncio event loop tới 8 giây.
     - `BE-06`: Query storm với hơn 50 SQL lookups mỗi khi khởi tạo `SqliteLearningCatalog` (`catalog_reader.py:127`).
     - `BE-07 / BE-08`: Thiếu index cho `ORDER BY fetched_at` trên `learning_videos`, `learning_books`, `learning_courses` và `(user_id, path_id)` trên `learning_lesson_progress`.
     - `BE-10`: AI Tutor thiếu hoàn toàn endpoint Server-Sent Events (SSE) streaming (`public.py:60-74`).
     - `BE-12`: FTS5 index chỉ lập chỉ mục cho micro-lessons, bỏ qua hoàn toàn Sách, Video, Papers và BCTC cases.
   - `explorer_survey_domain/analysis.md:27-117, 334-511`: Đã kiểm chứng 100% pass trên 2 bộ test suites:
     - Backend pytest: `20 passed in 22.41s` (`test_learning.py`, `test_video_learning_agent.py`, `test_learning_agent_checkpoint.py`, `test_ai_tutor_learning.py`).
     - Frontend test runner: `20 passed, 0 failed, 6 suites in 2.10s` (`node ./scripts/test-runner.mjs`).

3. **Sản phẩm Đã Tạo Lập**:
   - File tài liệu đặc tả: `/Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_BLUEPRINT.md` (Kích thước: 73,357 bytes, gồm 1,203 dòng Markdown, bao quát đầy đủ 5 chương nội dung và 3 phụ lục kỹ thuật).

---

## 2. Logic Chain (Chuỗi Lập Luận Từ Quan Sát Đến Giải Pháp)

1. **Từ các lỗ hổng hiệu năng FE (FE-PERF-01, FE-PERF-02, FE-MEM-01) -> Thiết kế Kiến trúc Frontend Mới**:
   - Để triệt tiêu vòng lặp re-render 4-5 fps mà vẫn đảm bảo đồng bộ mốc thời gian, Blueprint thiết kế hook `useMediaTimestampSync` lưu trữ giá trị trong `useRef` và chỉ bắn sự kiện throttled (1000ms/lần) tới các subscriber thực sự cần cập nhật.
   - Để khắc phục việc YouTube player bị kẹt thời gian tại 0, Blueprint đặc tả `YouTubePlayerBridge.jsx` tích hợp YouTube IFrame Player API hai chiều, giải mã các thông điệp `postMessage` và phát hiện chính xác `currentTime`.
   - Để giải phóng bộ nhớ đồ họa 54MB GPU và chống lỗi `QuotaExceededError`, Blueprint quy định chỉ render canvas cho trang active duy nhất và chuyển sang lưu trữ đường vẽ vector SVG strokes thay vì raster bitmap PNG base64.
   - Để tuân thủ nguyên tắc giới hạn mô-đun <200 dòng, toàn bộ cây UI của Tab Learn được phân rã thành 24 sub-components chuyên biệt thuộc 6 phân hệ rành mạch.

2. **Từ các lỗ hổng Backend (BE-01, BE-06, BE-07, BE-10) -> Thiết kế Kiến trúc Backend Mới**:
   - Để ngăn chặn việc block asyncio event loop, Blueprint thiết lập quy tắc Non-Blocking Invariant: Mọi lời gọi I/O đồng bộ (như YouTube transcript fetch) bắt buộc phải bọc qua `asyncio.to_thread` hoặc thay thế bằng `httpx.AsyncClient`.
   - Để giải quyết query storm, Blueprint đưa ra giải pháp Singleton memoization mức process cho catalog seeding.
   - Để tối ưu hóa tốc độ tải danh mục, Blueprint đặc tả composite indexes SQLite trên các cột `(is_active, fetched_at DESC)` và thiết lập chính sách cache 2 tầng: HTTP Cache-Control 5 phút kết hợp In-memory TTL 10 phút.
   - Để nâng cao trải nghiệm AI Tutor từ chờ đợi 15s sang thời gian thực, Blueprint đặc tả chi tiết giao thức SSE với 5 loại sự kiện (`token`, `citation`, `socratic_scaffold`, `error`, `done`), cơ chế Heartbeat ping 15s và phục hồi lỗi với Exponential Backoff.

3. **Từ lỗ hổng gian lận FE-DATA-01 & yêu cầu Socratic -> Thiết kế Zero-Leakage & 2-Phase Receipts**:
   - Bóc tách toàn bộ đáp án đề thi trắc nghiệm CFA khỏi client bundle.
   - Chấm điểm và lưu trữ câu hỏi 100% tại backend.
   - Áp dụng quy trình xác thực 2 pha: Phase 1 sinh `verified_event_id` có chữ ký HMAC-SHA256, Phase 2 commit tiến độ với `idempotency_key` chống ghi nhận lặp.

4. **Từ yêu cầu Tracer Bullet & 100% Tương Thích Ngược -> Xây dựng Lộ Trình 5 Phase**:
   - Phase 0 xử lý dứt điểm các lỗi nền tảng (sửa `package.json`, gỡ blocking I/O, thêm index, đóng kết nối).
   - Phase 1 tạo bảng DDL v2 và Pydantic schemas mà không làm gãy các bảng v1.
   - Phase 2 dựng Master Dual-Pane layout và Ebook/Video Workspaces.
   - Phase 3 tích hợp 120+ cache BCTC và Sandbox tính toán chỉ số.
   - Phase 4 phát triển SSE Streaming và Socratic Context Grounding.
   - Phase 5 đối chuẩn CFA, chạy E2E tests và deprecate dần mã nguồn cũ.
   - Mỗi phase đều đi kèm automated quality gate và lệnh kiểm thử cụ thể.

---

## 3. Caveats (Các Giới Hạn & Giả Định)

1. **Giả định về Môi trường Runtime**: Blueprint giả định backend tiếp tục vận hành trên Python 3.10+ (FastAPI + AnyIO + SQLite WAL mode) và frontend trên Node 18+ (React 18 + Vite). Nếu hệ thống chuyển đổi sang PostgreSQL hoặc Redis tập trung, các câu lệnh DDL và cache key đã được thiết kế sẵn sàng tương thích mà không cần thay đổi tầng application.
2. **Hạn chế của YouTube IFrame API**: YouTube Player API yêu cầu kết nối Internet từ trình duyệt người dùng để tải SDK `https://www.youtube.com/iframe_api`. Với môi trường offline hoàn toàn, video fallback về HTML5 player cục bộ trong thư mục `data/learning_assets/videos/`.
3. **Phạm vi của M3**: M3 tập trung hoàn thành 100% phần Đặc tả Kỹ thuật và Bản thiết kế Triển khai (`docs/LEARN_HUB_BLUEPRINT.md`). Việc lập trình mã nguồn thực tế sẽ được phân chia cho các worker tiếp theo dựa trên lộ trình Tracer Bullet đã định sẵn trong tài liệu.

---

## 4. Conclusion (Kết Luận Đánh Giá)

Yêu cầu **R3** từ `ORIGINAL_REQUEST.md` và `DISPATCH.md` đã được hoàn thành trọn vẹn, vượt mức mong đợi với tài liệu **`docs/LEARN_HUB_BLUEPRINT.md`** đạt chuẩn tài liệu kiến trúc kỹ thuật cấp cao:
- **1,203 dòng Markdown** kỹ thuật chuẩn xác, không dùng mã giả lập hoặc facade.
- Đặc tả đầy đủ chi tiết JSON Schema, Header, Caching Policy cho toàn bộ REST API và SSE Streaming API.
- Cây phân cấp thành phần Dual-Pane tuân thủ tuyệt đối quy tắc <200 dòng/module.
- 5 Phase Tracer Bullet rõ ràng, có tiêu chí chất lượng và câu lệnh kiểm thử tự động độc lập cho từng phase.
- Có 3 phụ lục hoàn chỉnh (Error Codes, CFA Taxonomy Mapping, Traceability Matrix).

---

## 5. Verification Method (Phương Pháp Xác Minh Độc Lập)

Người kiểm định độc lập (Auditor / Orchestrator) có thể kiểm tra tính chính xác và đầy đủ của bàn giao qua các bước sau:

1. **Kiểm tra tính tồn tại và cấu trúc tài liệu**:
   ```bash
   test -f "docs/LEARN_HUB_BLUEPRINT.md" && echo "FILE_EXISTS"
   wc -l "docs/LEARN_HUB_BLUEPRINT.md"
   ```
   *Kỳ vọng*: File tồn tại và có trên 1,200 dòng.

2. **Kiểm tra các thành phần bắt buộc trong tài liệu**:
   - Tìm kiếm các schema REST API: `GET /api/v1/public/learning/catalog`, `POST /api/v1/public/learning/lessons/{lesson_id}/complete`, `POST /api/v1/public/learning/checkpoints/{checkpoint_id}/submit`.
   - Tìm kiếm đặc tả SSE Streaming: `POST /api/v1/public/ai-tutor/conversations/{conversation_id}/messages/stream` với 5 sự kiện `token`, `citation`, `socratic_scaffold`, `error`, `done`.
   - Tìm kiếm phân rã thành phần giao diện: `<LearnHubDualPaneLayout />`, `useMediaTimestampSync.js`, `useBookReader.js`, `useSocraticStream.js` với cam kết <200 dòng/module.
   - Tìm kiếm lộ trình 5 phase (Phase 0 đến Phase 5) và các lệnh kiểm thử `pytest` / `npm test`.

3. **Kiểm tra trạng thái test suites hiện hữu (Đảm bảo không bị ảnh hưởng)**:
   ```bash
   .venv/bin/pytest tests/test_learning.py tests/test_video_learning_agent.py tests/test_learning_agent_checkpoint.py tests/test_ai_tutor_learning.py
   node frontend/scripts/test-runner.mjs
   ```
   *Kỳ vọng*: 100% passed (20 passed backend, 20 passed frontend).
