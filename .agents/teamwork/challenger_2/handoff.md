# HANDOFF REPORT — CHALLENGER 2
## Adversarial Stress & Feasibility Verification of Architecture (M2) & Blueprint (M3)

- **Agent**: `challenger_2` (EMPIRICAL CHALLENGER / Critic & Domain Specialist)
- **Target Recipient**: Orchestrator (`97a90bba-b298-4ab1-be4b-07eacc3cdf32`)
- **Working Directory**: `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/challenger_2`
- **Verdict**: **REQUEST_CHANGES (YÊU CẦU ĐIỀU CHỈNH THIẾT KẾ BẮT BUỘC)**

---

### 1. OBSERVATION
Qua việc kiểm tra tài liệu và chạy mã kiểm thử thực chứng độc lập trên terminal, chúng tôi trực tiếp ghi nhận các phát hiện sau:

1. **Lỗi cú pháp DDL index không tồn tại cột**:
   - Vị trí: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 680–682:
     ```sql
     CREATE INDEX IF NOT EXISTS idx_courses_v2_active_fetched 
     ON learning_courses_v2(is_active, fetched_at DESC);
     ```
   - Trong bảng `learning_courses_v2` (dòng 259–276), các cột chỉ có: `course_id, title, slug, description, instructor, tier, category, total_duration_minutes, thumbnail_url, prerequisites_json, target_competencies_json, is_active, published_at, created_at, updated_at`.
   - Kết quả lệnh thực thi:
     `sqlite3.OperationalError: no such column: fetched_at`

2. **Lỗi đệ quy vô hạn trigger SQLite**:
   - Vị trí: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 701–708:
     ```sql
     CREATE TRIGGER IF NOT EXISTS trg_courses_v2_updated_at
     AFTER UPDATE ON learning_courses_v2
     FOR EACH ROW
     BEGIN
         UPDATE learning_courses_v2 
         SET updated_at = CURRENT_TIMESTAMP 
         WHERE course_id = OLD.course_id;
     END;
     ```
   - Kết quả lệnh thực thi khi bật `PRAGMA recursive_triggers = ON`:
     `sqlite3.OperationalError: too many levels of trigger recursion`

3. **Lỗi khóa ngoại chặn ghi nhận tiến độ bài học video/sách**:
   - Vị trí: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 630–642 (`learning_progress_receipts` có `verified_event_id VARCHAR(64) NOT NULL UNIQUE REFERENCES learning_verified_events`).
   - `learning_verified_events` (dòng 616–625) bắt buộc có `checkpoint_id REFERENCES learning_checkpoints`.
   - Kết quả lệnh insert khi bài học không có checkpoint:
     `sqlite3.IntegrityError: NOT NULL constraint failed: learning_progress_receipts.verified_event_id` (hoặc `FOREIGN KEY constraint failed`).

4. **Lỗi runtime sập adapter BCTC cache**:
   - Vị trí: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 1249–1257:
     `"available_periods": list(data.get("periods", {}).keys())`
   - File thực tế `data/financials/cache/HPG.json` có `type(data["periods"]) == list`, và báo cáo nằm trong `data["raw_statements"]["balance"]`.
   - Kết quả lệnh thực thi:
     `AttributeError: 'list' object has no attribute 'keys'`

5. **Lỗi bảo mật bypass rào chắn Socratic 90%**:
   - Vị trí: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 1434–1456 (`AntiCheatingGuardian` regex).
   - Thử nghiệm với 10 câu trả lời tự nhiên của LLM (markdown `**A**`, ngoặc `(A)`, tiếng Anh, số `-5.500 tỷ`): 9/10 câu lọt qua bộ lọc (tỷ lệ thất bại 90%).

6. **Thiếu trigger FTS5 UPDATE & các bảng khác**:
   - Vị trí: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 711–740 chỉ có trigger INSERT/DELETE cho BCTC. Không có trigger UPDATE và không có trigger cho sách/video/khóa học.

7. **Thiếu định nghĩa DDL cho `learning_resource_topics`**:
   - Vị trí: ERD dòng 200 có bảng `learning_resource_topics`, nhưng mục 2.2 đến 2.8 không có lệnh `CREATE TABLE` tương ứng.

8. **Rủi ro Stale Cache tiến độ học tập**:
   - Vị trí: `docs/LEARN_HUB_BLUEPRINT.md`, dòng 264 đặt `Cache-Control: private, max-age=60` trên `GET /courses/{course_id}` khi có `X-Session-ID`, khiến bài học vừa hoàn thành bị cache trình duyệt hiển thị là chưa hoàn thành trong 60 giây.

---

### 2. LOGIC CHAIN
1. **Từ Observation 1**: Khi chạy kịch bản DDL migration từ bản thiết kế M2, lệnh `CREATE INDEX idx_courses_v2_active_fetched` tham chiếu cột `fetched_at` không tồn tại, khiến migration thất bại ngay lập tức (`OperationalError`). Do đó, schema CSDL hiện tại không thể triển khai được nếu không sửa tên cột.
2. **Từ Observation 2**: Ứng dụng production bắt buộc phải bật `PRAGMA recursive_triggers = ON` để Foreign Key Cascades hoạt động chính xác xuyên suốt mô hình 4 tầng. Trigger `trg_courses_v2_updated_at` thiếu điều kiện ngắt đệ quy `WHEN OLD.updated_at = NEW.updated_at`, dẫn đến mọi lệnh cập nhật khóa học bị sập do tràn ngăn xếp đệ quy trigger.
3. **Từ Observation 3**: Bảng `learning_progress_receipts` áp đặt `verified_event_id NOT NULL REFERENCES learning_verified_events`, trong khi chỉ bài học kiểm tra (quiz) mới sinh ra `verified_event_id`. Các bài học dạng video và tài liệu đọc PDF không thể lưu chứng từ tiến độ hoàn thành, phá vỡ cam kết lưu vết tiến độ máy chủ bất biến.
4. **Từ Observation 4**: Code mẫu `FinancialCrossLinkService` trong tài liệu M2 giả định `periods` là một `dict` và có các trường cấp 1 `balance_sheet`, `income_statement`. Trong khi đó, 120+ file JSON thật trong `data/financials/cache/` lưu `periods` dưới dạng `list` và báo cáo trong `raw_statements`. Sự không tương thích này làm sập ngay lập tức toàn bộ phân hệ BCTC Case-Study Sandbox ở runtime.
5. **Từ Observation 5**: Rào chắn Zero-Leakage chỉ dựa vào 3 regex cố định không chuẩn hóa markdown hoặc cú pháp số liệu tài chính. Khi LLM phản hồi bằng markdown in đậm hoặc định dạng số thông thường, đáp án trắc nghiệm bị rò rỉ tới 90%, vô hiệu hóa nguyên tắc bảo vệ đề thi.
6. **Từ Observation 6 & 7**: FTS5 không thể tìm kiếm chính xác sau các lệnh UPDATE do thiếu trigger, và DDL thiếu bảng liên kết chủ đề `learning_resource_topics`.
7. **Từ Observation 8**: Caching tiến độ người dùng theo thời gian cố định 60 giây gây ra trải nghiệm người dùng sai lệch (UI hiển thị tiến độ cũ sau khi submit).

**Kết luận logic**: Hệ thống tài liệu kiến trúc và đặc tả có 4 điểm nghẽn nghiêm trọng (DDL syntax, trigger recursion, receipt schema block, BCTC cache crash) cần phải được sửa đổi trực tiếp trong tài liệu trước khi tiến hành viết code.

---

### 3. CAVEATS
1. **Môi trường cơ sở dữ liệu**: Kiểm thử thực chứng được chạy trên engine SQLite 3 của Python 3.10. Nếu trong tương lai hệ thống chuyển đổi sang PostgreSQL, một số hành vi (như recursive triggers hoặc FTS5) sẽ sử dụng cú pháp khác (`tsvector`, trigger function PL/pgSQL).
2. **Tình trạng file DB cục bộ**: File `data/db/northstar.db` trên ổ cứng hiện đang bị `malformed disk image` từ các phiên chạy trước. Khi chạy test với DB sạch (`RISK_DASHBOARD_DB_PATH=/tmp/test.db`), các test suite hiện hữu đều pass 100%. Đội ngũ triển khai cần lưu ý xóa file db hỏng này.
3. **Phạm vi thẩm định**: Đánh giá tập trung vào tính khả thi, tính toàn vẹn dữ liệu, hiệu năng và rủi ro bảo mật của hai tài liệu M2 và M3. Chúng tôi không can thiệp sửa trực tiếp tài liệu do tuân thủ nguyên tắc Review-Only của Challenger.

---

### 4. CONCLUSION
- **Phán quyết chính thức**: **REQUEST_CHANGES**.
- Đội ngũ thiết kế M2 (`worker_m2_arch`) và M3 (`worker_m3_blueprint`) cần cập nhật hai tài liệu `docs/LEARN_HUB_ARCHITECTURE.md` và `docs/LEARN_HUB_BLUEPRINT.md` theo danh sách chỉ dẫn sau:
  1. *Sửa DDL Index*: Đổi `fetched_at` thành `published_at` trong `idx_courses_v2_active_fetched`.
  2. *Sửa Trigger*: Bổ sung `WHEN OLD.updated_at = NEW.updated_at` vào trigger `trg_courses_v2_updated_at`.
  3. *Sửa Receipt Schema*: Cho phép `verified_event_id` nhận giá trị `NULL` trong `learning_progress_receipts` và thêm `receipt_type`.
  4. *Sửa Service BCTC*: Viết lại hàm `load_ticker_financial_snapshot` để đọc đúng cấu trúc `periods: list[dict]` và `raw_statements: dict` của file `data/financials/cache/*.json`.
  5. *Tái cấu trúc Zero-Leakage*: Áp dụng *Prompt Isolation Architecture* (không truyền đáp án đúng vào prompt của gia sư AI) thay vì chỉ trông cậy vào regex lọc output.
  6. *Sửa Cache Policy*: Đổi `Cache-Control` cho endpoint chi tiết khóa học cá nhân sang `private, no-cache, must-revalidate`.
  7. *Bổ sung DDL*: Thêm `CREATE TABLE learning_topics` và `CREATE TABLE learning_resource_topics`.

---

### 5. VERIFICATION METHOD
Cách thức độc lập kiểm chứng lại toàn bộ các phát hiện trên:

1. **Kiểm chứng DDL & Trigger**:
   ```bash
   .venv/bin/python -c "
   import sqlite3
   conn = sqlite3.connect(':memory:')
   conn.execute('PRAGMA foreign_keys = ON;')
   conn.execute('PRAGMA recursive_triggers = ON;')
   # Chạy DDL từ LEARN_HUB_ARCHITECTURE.md
   "
   ```
   *Điều kiện vô hiệu hóa*: Lệnh executescript chạy thành công không báo lỗi `no such column: fetched_at` và UPDATE khóa học không báo lỗi `too many levels of trigger recursion`.

2. **Kiểm chứng BCTC Cache Link**:
   ```bash
   .venv/bin/python -c "
   import json
   from pathlib import Path
   # Gọi hàm load_ticker_financial_snapshot với file data/financials/cache/HPG.json
   "
   ```
   *Điều kiện vô hiệu hóa*: Hàm trả về dict chứa danh sách kỳ và báo cáo tài chính không bị lỗi `AttributeError: 'list' object has no attribute 'keys'`.

3. **Kiểm chứng Zero-Leakage Bypass**:
   Chạy đoạn mã test harness trong `analysis.md` mục 3.5 với 10 câu trả lời markdown in đậm và số thực.
   *Điều kiện vô hiệu hóa*: Tỷ lệ chặn thành công đạt 100%.

4. **Kiểm chứng hồi quy toàn bộ hệ thống test suite**:
   ```bash
   RISK_DASHBOARD_DB_PATH=/tmp/clean_test.db .venv/bin/pytest tests/test_learning*.py tests/test_video_learning_agent.py tests/test_ai_tutor*.py
   ```
