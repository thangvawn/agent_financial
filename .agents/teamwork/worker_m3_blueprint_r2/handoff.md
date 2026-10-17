# Handoff Report — worker_m3_blueprint_r2

## 1. Observation
1. **Lỗ hổng CSDL đĩa vật lý bị hỏng (Database Disk Image Malformed)**:
   - Các kiểm toán viên và người thử nghiệm độc lập (`challenger_1`, `reviewer_1`, `reviewer_2`, `auditor_1`) đã ghi nhận lỗi khi chạy kiểm thử backend trên file SQLite mặc định: `sqlite3.DatabaseError: database disk image is malformed (11)` tại `src/risk_dashboard/modules/learning/infrastructure/repositories/sqlite.py:51`. Nguyên nhân gốc rễ là do kết nối unclosed (BE-04), bão query nạp dữ liệu lặp lại (BE-06), và xung đột khóa ghi SQLite giữa các tiến trình chạy song song (BE-09) trên file dùng chung `data/db/northstar.db`. Trong phiên bản blueprint trước, Phase 0 chưa có quy trình phục hồi/tái tạo CSDL sạch tự động.
2. **Lệch pha Schema Checkpoint Submit (Checkpoint Schema Drift)**:
   - Trong `docs/LEARN_HUB_ARCHITECTURE.md:1034`, schema Pydantic ban đầu khai báo đơn lẻ `user_selected_option_id: str`. Trong khi đó, các bài đánh giá cuối chương hoặc quiz video thực tế cần hỗ trợ kiểm tra liên hoàn đa câu hỏi (`selected_options: dict[str, str]`). Endpoint `POST /api/v1/public/learning/checkpoints/{id}/submit` trong blueprint trước chưa cung cấp định nghĩa Pydantic v2 chuẩn hóa và thuật toán chấm điểm đa câu hỏi tương ứng.
3. **Ngắt dòng SSE Stream khi đóng AI Tutor Drawer trên Mobile (< 1024px)**:
   - Trên màn hình di động (`< 1024px`), Right Pane thu gọn thành Floating Action Button (FAB) và mở ra bằng Drawer / BottomSheet. Nếu state `useSocraticStream` và kết nối SSE `ReadableStreamDefaultReader` được khởi tạo bên trong component của Drawer, việc người học vuốt đóng Drawer sẽ unmount component và hủy kết nối SSE dở dang (`fetch abort`), làm mất token phản hồi của AI Tutor.
4. **Race Condition khi Seek Video trước sự kiện `onReady`**:
   - Khi người học bấm mốc thời gian từ ghi chú (`VideoTimestampNotes`) hoặc URL có query time trước khi YouTube IFrame Player API tải xong, lệnh `player.seekTo()` gọi lên đối tượng chưa khởi tạo hoặc `postMessage` channel chưa sẵn sàng, dẫn đến việc lệnh seek bị mất và video phát từ 0:00 (FE-PERF-02).
5. **Rủi ro Trình duyệt Cache sai lệch Tiến độ Học tập**:
   - Tại `docs/LEARN_HUB_BLUEPRINT.md:264`, endpoint `GET /learning/courses/{id}` từng đặt cache `Cache-Control: private, max-age=60` khi có `X-Session-ID`. Header `max-age=60` khiến trình duyệt tự phục vụ bản sao cached cũ trong 60 giây, làm người học thấy bài học vừa hoàn thành vẫn ở trạng thái chưa hoàn thành (`in_progress` hoặc `locked`).

---

## 2. Logic Chain
1. **Từ Quan sát 1 đến Khắc phục DB Recovery trong Phase 0**:
   - Để ngăn chặn việc các lệnh migration tạo index và regression tests bị đổ vỡ ngay tại bước đầu tiên của roadmap, Phase 0 (`Section 4.1`) phải tích hợp quy trình phục hồi tự động 4 bước: (1) `PRAGMA integrity_check`, (2) Cách ly & sao lưu file hỏng vào `data/db/northstar.db.corrupt.<timestamp>`, (3) Tái tạo schema sạch qua `migrate.py` với WAL mode, và (4) Tái nạp hạt giống dữ liệu mặc định qua `SqliteLearningCatalog` và `sync_bctc_to_db.py`. Đồng thời, quy định chuẩn kiểm thử: mọi test suite phải cô lập DB thông qua biến môi trường `RISK_DASHBOARD_DB_PATH` trỏ vào `tmp_path / "test.db"`.
2. **Từ Quan sát 2 đến Chuẩn hóa Checkpoint Submit Schema**:
   - Tại `Section 2.3.2` và `Section 4.2 (Phase 1)`, xây dựng model Pydantic v2 `CheckpointSubmitRequest` với trường `selected_options: dict[str, str]` (mapping `question_id -> selected_option_id`). Bổ sung thuật toán tính điểm phần trăm server-side (`correct_count / total_questions * 100`) và model `QuestionRubricFeedback` tuân thủ nguyên tắc Zero-Leakage: câu sai chỉ trả về gợi ý `socratic_hint`, tuyệt đối không lộ đáp án đúng.
3. **Từ Quan sát 3 đến Kiến trúc `<SocraticStreamProvider />` Root Wrapper**:
   - Tại `Section 3.1` và `Section 3.2.6`, đưa `<SocraticStreamProvider />` lên vị trí root bao bọc toàn bộ `<LearnHubDualPaneLayout />`. Toàn bộ dòng stream SSE, buffer tích lũy tin nhắn và `AbortController` được lưu trữ bền vững tại cấp Context của React. Do đó, component Drawer trên thiết bị di động có thể đóng, mở hoặc unmount tùy ý mà không làm teardown luồng SSE ngầm.
4. **Từ Quan sát 4 đến Hàng đợi `seekQueueRef` trong `YouTubePlayerBridge.jsx`**:
   - Tại `Section 3.2.3` và `Section 3.3.1`, thiết kế cơ chế hàng đợi `const seekQueueRef = useRef(null)` trong `YouTubePlayerBridge.jsx`. Khi có lệnh seek: nếu player đã `onReady`, thực thi ngay; nếu chưa ready, lưu mốc thời gian vào `seekQueueRef.current`. Khi callback `onPlayerReady` kích hoạt, player tự động xả hàng đợi và seek đến đúng giây yêu cầu.
5. **Từ Quan sát 5 đến Ma trận Cache-Control `private, no-cache, must-revalidate`**:
   - Tại `Section 2.1`, `Section 2.2.2` và `Section 2.2.3`, bổ sung ma trận Cache-Control chuẩn hóa. Mọi endpoint trả về dữ liệu tiến độ cá nhân hóa gắn với `X-Session-ID` (`GET /learning/courses/{id}`, `GET /learning/lessons/{id}`) đều áp dụng nghiêm ngặt `Cache-Control: private, no-cache, must-revalidate`. Trình duyệt buộc phải revalidate với máy chủ ở mỗi lần tải trang, loại bỏ 100% tình trạng hiển thị trạng thái cũ chưa cập nhật.

---

## 3. Caveats
- No caveats. Toàn bộ 5 nội dung chỉ đạo từ Dispatch đã được bổ sung trực tiếp, ăn khớp chặt chẽ và nhất quán với các phần hiện hữu của `docs/LEARN_HUB_BLUEPRINT.md`.

---

## 4. Conclusion
Tài liệu `docs/LEARN_HUB_BLUEPRINT.md` (phiên bản v2.0.0-PROD) đã được hoàn thiện và nâng cấp toàn diện:
- Bổ sung quy trình phục hồi CSDL tự động 4 bước và chuẩn test isolation cho Phase 0.
- Chuẩn hóa Pydantic v2 schema cho `CheckpointSubmitRequest` hỗ trợ `selected_options: dict[str, str]`.
- Thiết lập kiến trúc `<SocraticStreamProvider />` chống ngắt kết nối stream trên mobile drawer.
- Bổ sung cơ chế `seekQueueRef` triệt tiêu dứt điểm race condition khi phát video YouTube.
- Thiết lập ma trận `Cache-Control: private, no-cache, must-revalidate` cho tiến độ học tập và chi tiết khóa học.
- Bổ sung 5 mã truy vết tương ứng (`DB-CORRUPT-01`, `FE-STREAM-01`, `FE-SEEK-01`, `API-CHECKPOINT-01`, `API-CACHE-01`) vào Phụ lục C (Traceability Matrix).

---

## 5. Verification Method
1. **Kiểm tra cú pháp và sự hiện diện của các mục bổ sung**:
   ```bash
   # Kiểm tra DB Recovery trong Phase 0
   grep -n "PRAGMA integrity_check" docs/LEARN_HUB_BLUEPRINT.md

   # Kiểm tra Checkpoint Multi-Question Schema
   grep -n "selected_options: dict\[str, str\]" docs/LEARN_HUB_BLUEPRINT.md

   # Kiểm tra SocraticStreamProvider Context Wrapper
   grep -n "SocraticStreamProvider" docs/LEARN_HUB_BLUEPRINT.md

   # Kiểm tra seekQueueRef
   grep -n "seekQueueRef" docs/LEARN_HUB_BLUEPRINT.md

   # Kiểm tra Cache-Control
   grep -n "private, no-cache, must-revalidate" docs/LEARN_HUB_BLUEPRINT.md
   ```
2. **Kiểm tra tính nhất quán trong Ma trận Truy xuất (Appendix C)**:
   ```bash
   grep -E "(DB-CORRUPT-01|FE-STREAM-01|FE-SEEK-01|API-CHECKPOINT-01|API-CACHE-01)" docs/LEARN_HUB_BLUEPRINT.md
   ```
3. **Điều kiện vô hiệu hóa (Invalidation Conditions)**:
   - Nếu bất kỳ endpoint nào liên quan đến tiến độ người dùng (`courses/{id}`, `lessons/{id}`) cho phép client cache mà không revalidate (`max-age > 0` mà thiếu `no-cache` / `must-revalidate`).
   - Nếu checkpoint request không chấp nhận kiểu dictionary `dict[str, str]`.
   - Nếu drawer unmount làm rớt kết nối SSE streaming.
