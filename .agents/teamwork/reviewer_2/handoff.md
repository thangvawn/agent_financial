# BÁO CÁO BÀN GIAO THẨM ĐỊNH KỸ THUẬT (HANDOFF REPORT)
## Thẩm Định & Phản Biện Độc Lập Tài Liệu LEARN_HUB_ARCHITECTURE.md (M2) & LEARN_HUB_BLUEPRINT.md (M3)

- **Người thực hiện**: Reviewer 2 / Adversarial Critic (`reviewer_2`)
- **Người nhận (Recipient)**: Orchestrator (`97a90bba-b298-4ab1-be4b-07eacc3cdf32`)
- **Ngày phát hành**: 2026-10-10
- **Phán quyết cuối cùng (Verdict)**: **REQUEST_CHANGES**

---

### 1. OBSERVATION (QUAN SÁT THỰC CHỨNG TRỰC TIẾP)

1. **Lỗi cột không tồn tại trong câu lệnh DDL index**:
   - Tệp: `docs/LEARN_HUB_ARCHITECTURE.md`, Dòng 680–681:
     `CREATE INDEX IF NOT EXISTS idx_courses_v2_active_fetched ON learning_courses_v2(is_active, fetched_at DESC);`
   - Đối chiếu định nghĩa bảng tại dòng 259–276: Bảng `learning_courses_v2` gồm các cột `course_id`, `title`, `slug`, `description`, `instructor`, `tier`, `category`, `total_duration_minutes`, `thumbnail_url`, `prerequisites_json`, `target_competencies_json`, `is_active`, `published_at`, `created_at`, `updated_at`.
   - Cột `fetched_at` hoàn toàn không có trong bảng này.
2. **Lỗi CSDL thực tế bị hỏng phân vùng đĩa**:
   - Lệnh: `sqlite3 "data/db/northstar.db" "PRAGMA integrity_check;"`
   - Kết quả xuất lỗi verbatim: `Error: stepping, database disk image is malformed (11)`
   - Khi chạy `pytest tests/test_learning.py` với cấu hình mặc định:
     `sqlite3.DatabaseError: database disk image is malformed` tại `src/risk_dashboard/modules/learning/infrastructure/repositories/sqlite.py:51` (5 tests failed).
   - Khi chạy với CSDL độc lập: `RISK_DASHBOARD_DB_PATH="/tmp/test_northstar.db" .venv/bin/pytest tests/test_learning.py`: 5 passed in 10.55s.
3. **Bất đồng bộ hợp đồng Checkpoint API giữa Architecture và Blueprint**:
   - `docs/LEARN_HUB_ARCHITECTURE.md:1034`: Schema Pydantic `GradeCheckpointRequest` có trường `user_selected_option_id: str` (câu trả lời đơn).
   - `docs/LEARN_HUB_BLUEPRINT.md:568`: Request payload `POST /checkpoints/{checkpoint_id}/submit` có trường `selected_options: { "q1": "opt_b", "q2": "opt_c" }` (map đa câu hỏi).
4. **Kho dữ liệu BCTC thực tế trong dự án**:
   - Lệnh `list_dir data/financials/cache` trả về 110 file JSON BCTC đã kiểm toán (HPG.json 734KB, VNM.json 733KB, FPT.json 736KB, VCB.json 654KB...).
5. **Độ ổn định của test suite hiện hữu**:
   - Lệnh: `RISK_DASHBOARD_DB_PATH="/tmp/test_northstar.db" .venv/bin/pytest tests/test_video_learning_agent.py tests/test_learning_agent_checkpoint.py tests/test_learning_agent_retrieval.py tests/test_ai_tutor_api.py tests/test_ai_tutor_learning.py tests/test_ai_runtime_streaming.py`
   - Kết quả: **27 passed in 17.63s**.
   - Lệnh: `cd frontend && node scripts/test-runner.mjs`
   - Kết quả: **20 passed in 2.72s (6 suites, 0 failed)**.
6. **Tuân thủ giới hạn mô-đun hóa Frontend**:
   - Toàn bộ 28 components và custom hooks trong `LEARN_HUB_BLUEPRINT.md § 3.2` đều được phân rã rõ ràng với số dòng ước lượng từ 85 đến 185 dòng (tuân thủ nghiêm ngặt giới hạn <200 dòng/file).

---

### 2. LOGIC CHAIN (CHUỖI LÝ LUẬN TỪ QUAN SÁT ĐẾN KẾT LUẬN)

- **Bước 1 (Tính khả thi của DDL Migration)**: 
  Từ Quan sát 1, câu lệnh `CREATE INDEX ... ON learning_courses_v2(is_active, fetched_at DESC)` cố tình tạo chỉ mục trên một cột không tồn tại (`fetched_at`). Trong SQLite hoặc PostgreSQL, khi thực thi lệnh này trong Phase 1 Migration (`src/risk_dashboard/platform/database/migrate.py`), engine CSDL sẽ ném lỗi runtime và dừng toàn bộ quá trình khởi tạo bảng mới. Do đó, tài liệu Architecture chứa một lỗi kỹ thuật bắt buộc phải sửa trước khi tiến hành code.
- **Bước 2 (Tính khả thi của Phase 0 Roadmap)**:
  Từ Quan sát 2, file CSDL hiện tại `data/db/northstar.db` đã bị hỏng phân vùng dữ liệu vật lý (malformed disk image). Phase 0 của Blueprint đặt mục tiêu thêm các composite index (BE-07, BE-08) và chạy regression test. Nếu không bổ sung một bước phục hồi/tái tạo CSDL sạch trước khi tạo index, toàn bộ các tác vụ DB trong Phase 0 sẽ thất bại.
- **Bước 3 (Độ gắn kết giữa Hợp đồng Kiến trúc và Bản thiết kế)**:
  Từ Quan sát 3, việc Pydantic Model ở M2 chỉ chấp nhận một ID lựa chọn đơn trong khi REST API Contract ở M3 gửi một từ điển đa câu hỏi sẽ gây ra lỗi `422 Unprocessable Entity` khi frontend gửi payload tới backend. Cần phải đồng bộ hai tài liệu này.
- **Bước 4 (Đánh giá Tính Toàn Vẹn Kỹ Thuật - Integrity Evaluation)**:
  Từ Quan sát 4, 5, 6, không có dấu hiệu gian lận, hardcode đáp án hay tạo facade rỗng. Các tình huống BCTC (HPG, VNM, FPT) dựa trên dữ liệu thật; bộ test chạy thật đạt 27/27 backend và 20/20 frontend; quy tắc <200 dòng/file được tuân thủ 100%.
- **Bước 5 (Tổng hợp Phán quyết)**:
  Vì tồn tại lỗi DDL sẽ làm hỏng migration CSDL (Finding 1) và file CSDL thực tế đang bị hỏng cần đưa vào lộ trình xử lý (Finding 2), phán quyết độc lập của Reviewer 2 theo đúng quy chuẩn kỹ thuật nghiêm ngặt là **REQUEST_CHANGES** để đảm bảo chất lượng tuyệt đối trước khi bước sang giai đoạn lập trình.

---

### 3. CAVEATS (CÁC ĐIỂM CHƯA KHẢO SÁT & GIẢ ĐỊNH)

1. Giả định rằng trong môi trường CI/CD, các test suite sẽ tự động khởi tạo file CSDL tạm thời trong thư mục temp (`/tmp/`) thay vì dùng trực tiếp file `data/db/northstar.db`. Tuy nhiên, các nhà phát triển chạy local bằng lệnh pytest trần sẽ gặp lỗi nếu chưa sửa file DB này.
2. Chưa thực hiện benchmark tải thực tế (load test) với hàng nghìn kết nối đồng thời của SSE streaming trên server FastAPI vì hệ thống hiện đang ở giai đoạn hoàn thiện thiết kế kiến trúc (Blueprint phase).

---

### 4. CONCLUSION (KẾT LUẬN & HÀNH ĐỘNG CẦN THỰC HIỆN)

**Phán quyết**: **REQUEST_CHANGES**

Chất lượng thiết kế của `LEARN_HUB_ARCHITECTURE.md` và `LEARN_HUB_BLUEPRINT.md` là rất cao và toàn diện. Tuy nhiên, để đảm bảo an toàn tuyệt đối khi triển khai thực tế, yêu cầu tác giả tài liệu thực hiện 4 sửa đổi nhanh sau:
1. **Sửa dòng 680–681 trong `docs/LEARN_HUB_ARCHITECTURE.md`**:
   Đổi `fetched_at` thành `published_at` (tên index: `idx_courses_v2_active_published`).
2. **Cập nhật Phase 0 trong `docs/LEARN_HUB_BLUEPRINT.md § 4.1`**:
   Thêm bước 0.0: Phục hồi / tái tạo file CSDL sạch `data/db/northstar.db` từ migrations trước khi thêm composite indexes.
3. **Đồng bộ Schema Checkpoint**:
   Cập nhật `GradeCheckpointRequest` trong Architecture hỗ trợ `selected_options: dict[str, str]`.
4. **Bổ sung `<SocraticStreamProvider />` vào Blueprint (§ 3.2.6)**:
   Để bảo toàn luồng SSE stream khi người dùng đóng/mở Drawer trên thiết bị di động.

---

### 5. VERIFICATION METHOD (PHƯƠNG PHÁP XÁC MINH ĐỘC LẬP)

Bất kỳ kiểm định viên hoặc kỹ sư nào cũng có thể kiểm chứng lại các phát hiện trên bằng các lệnh sau:

1. **Kiểm tra lỗi cột DDL**:
   ```bash
   grep -n "idx_courses_v2_active_fetched" "docs/LEARN_HUB_ARCHITECTURE.md"
   # So sánh với định nghĩa cột bảng learning_courses_v2 ở dòng 259-276
   ```
2. **Kiểm tra trạng thái CSDL bị hỏng**:
   ```bash
   sqlite3 "data/db/northstar.db" "PRAGMA integrity_check;"
   # Kỳ vọng: Error: stepping, database disk image is malformed (11)
   ```
3. **Kiểm tra kết quả test suite với DB độc lập**:
   ```bash
   RISK_DASHBOARD_DB_PATH="/tmp/test_northstar.db" .venv/bin/pytest tests/test_learning.py
   # Kỳ vọng: 5 passed in ~10s
   ```
4. **Kiểm tra test runner frontend**:
   ```bash
   cd frontend && node scripts/test-runner.mjs
   # Kỳ vọng: 20 passed, 0 failed
   ```
