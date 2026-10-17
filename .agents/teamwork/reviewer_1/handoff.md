# BÁO CÁO BÀN GIAO THẨM ĐỊNH (HANDOFF REPORT) - REVIEWER 1

**Người thực hiện**: reviewer_1  
**Mục tiêu**: Báo cáo kết quả thẩm định độc lập & phản biện đối kháng cho Milestone M1 (`docs/LEARN_HUB_AUDIT_REPORT.md`) và Milestone M2 (`docs/LEARN_HUB_ARCHITECTURE.md`) theo các yêu cầu R1 và R2.  
**Phán quyết chính thức**: **REQUEST_CHANGES** (Yêu cầu chỉnh sửa kỹ thuật trước khi phê duyệt).

---

## 1. OBSERVATION (QUAN SÁT THỰC CHỨNG TRỰC TIẾP)

1. **Về Báo cáo Kiểm toán (`docs/LEARN_HUB_AUDIT_REPORT.md`)**:
   - Khảo sát mã nguồn frontend: `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx:41,122` chứa `useState(0)` cho `currentTimeSeconds` và `onTimeUpdate` gây Re-render 4-5 lần/s.
   - Khảo sát canvas ghi chú: `frontend/src/features/learn-hub/pages/NotePaper.jsx:125-135` tạo thẻ `<canvas width={960} height={1400} />` và xuất `toDataURL('image/png')` đồng bộ gây giật lag.
   - Khảo sát rò rỉ đáp án: `frontend/src/features/learn-hub/content/mockExamData.js:9-21` chứa 90 câu hỏi đóng gói kèm `correctOptionId` trực tiếp ở client.
   - Khảo sát backend blocking I/O: `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py:146-150` gọi đồng bộ `video_agent.ask()`, bên trong gọi `urllib.request.urlopen` (timeout 8s) trong hàm `async def`.
   - Khảo sát kiểm thử tự động:
     - Lệnh `npm test` trong `frontend/` trả về lỗi: `npm error Missing script: "test"` (Exit Code 1).
     - Lệnh `node ./scripts/test-runner.mjs` trả về: `ℹ tests 20, ℹ suites 6, ℹ pass 20, ℹ fail 0`.
     - Lệnh `RISK_DASHBOARD_DB_PATH=/tmp/test.db .venv/bin/pytest tests/test_learning.py` trả về: `5 passed in 11.28s`.
     - Lệnh chạy toàn bộ 18 test suite trên database mặc định `data/db/northstar.db` trả về: `sqlite3.DatabaseError: database disk image is malformed`.

2. **Về Tài liệu Kiến trúc (`docs/LEARN_HUB_ARCHITECTURE.md`)**:
   - Khảo sát DDL: Dòng 680-681 định nghĩa:
     ```sql
     CREATE INDEX IF NOT EXISTS idx_courses_v2_active_fetched 
     ON learning_courses_v2(is_active, fetched_at DESC);
     ```
     Trong khi đó, bảng `learning_courses_v2` (dòng 259-276) chỉ có các cột: `course_id`, `title`, `slug`, `description`, `instructor`, `tier`, `category`, `total_duration_minutes`, `thumbnail_url`, `prerequisites_json`, `target_competencies_json`, `is_active`, `published_at`, `created_at`, `updated_at`. Bảng hoàn toàn không có cột `fetched_at`.
     Khi thực thi lệnh DDL trên SQLite, hệ thống trả về lỗi nghiêm trọng:
     `sqlite3.OperationalError: no such column: fetched_at`.
   - Khảo sát Trigger: Dòng 701-709 định nghĩa:
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
     Khi thực hiện `UPDATE learning_courses_v2` trên SQLite với `PRAGMA recursive_triggers = ON`, lệnh update kích hoạt trigger đệ quy vô tận và ném ngoại lệ:
     `sqlite3.OperationalError: too many levels of trigger recursion`.
   - Khảo sát Pydantic Schemas: Toàn bộ 22 model Pydantic v2 trong Mục 3 chạy độc lập qua script Python đều hợp lệ về mặt cú pháp và validation logic.

---

## 2. LOGIC CHAIN (CHUỖI LẬP LUẬN TỪ QUAN SÁT ĐẾN KẾT LUẬN)

1. Từ **Quan sát 1**: Báo cáo kiểm toán `LEARN_HUB_AUDIT_REPORT.md` đáp ứng đầy đủ và vượt trội các tiêu chí của Requirement R1. Mọi lỗi logic, hiệu năng, bảo mật và kiểm thử đều được trích dẫn chính xác từng file và phạm vi dòng, có số liệu đo lường cụ thể và phân tích nguyên nhân gốc rễ thuyết phục. Không phát hiện bất kỳ dấu hiệu ngụy tạo hay gian lận (Zero integrity violations).
2. Từ **Quan sát 2**: Tài liệu kiến trúc `LEARN_HUB_ARCHITECTURE.md` giải quyết triệt để các bài toán nghiệp vụ của Requirement R2 (4 trụ cột học liệu, BCTC VN30 HPG/VNM/FPT thực chiến, Pydantic v2, Socratic AI Tutor).
3. Tuy nhiên, việc tồn tại lỗi cú pháp DDL (`idx_courses_v2_active_fetched` tham chiếu cột không tồn tại `fetched_at`) và lỗi đệ quy vô hạn trong trigger (`trg_courses_v2_updated_at`) có nghĩa là bất kỳ mã nguồn triển khai nào (ở Milestone M3) cố gắng chạy file schema này trên môi trường thật hoặc migration script đều sẽ gặp lỗi `OperationalError` và dừng tiến trình.
4. Ngoài ra, việc cơ chế chống gian lận `AntiCheatingGuardian` chỉ dựa vào 3 regex tĩnh tạo ra rủi ro bị vượt qua dễ dàng qua prompt jailbreak đơn giản (bằng tiếng Anh hoặc đổi cấu trúc câu).
5. Do đó, theo nguyên tắc chất lượng nghiêm ngặt của vai trò Reviewer & Adversarial Critic, bản thiết kế kiến trúc chưa thể được `APPROVE` chừng nào 2 lỗi thực thi DDL/Trigger cốt lõi này chưa được chỉnh sửa.

---

## 3. CAVEATS (GIỚI HẠN & GIẢ ĐỊNH)

1. Chưa tiến hành đo đạc benchmark I/O trên cụm cơ sở dữ liệu phân tán quy mô triệu bản ghi đối với FTS5 unified search (hiện mới kiểm chứng trên tập dữ liệu cục bộ).
2. Giả định rằng hệ thống sẽ chạy SQLite trong giai đoạn phát triển và hỗ trợ chuyển đổi sang PostgreSQL trong tương lai; một số kiểu dữ liệu như `TIMESTAMP WITH TIME ZONE` trong SQLite được ánh xạ thành `NUMERIC/TEXT` và cần bộ xử lý thời gian chuẩn ISO-8601 tại lớp ứng dụng.

---

## 4. CONCLUSION (KẾT LUẬN & ĐỀ XUẤT HÀNH ĐỘNG)

**Phán quyết**: **REQUEST_CHANGES**  
Tác giả tài liệu kiến trúc (`docs/LEARN_HUB_ARCHITECTURE.md`) cần cập nhật 2 điểm bắt buộc sau:
1. **Sửa lỗi DDL**: Bổ sung cột `fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP` vào `learning_courses_v2`, HOẶC sửa composite index thành:
   `CREATE INDEX IF NOT EXISTS idx_courses_v2_active_published ON learning_courses_v2(is_active, published_at DESC);`.
2. **Sửa lỗi Trigger đệ quy**: Bổ sung điều kiện `WHEN NEW.updated_at = OLD.updated_at` vào trigger `trg_courses_v2_updated_at`.
3. *(Khuyến nghị nâng cấp)*: Định nghĩa nguyên tắc Zero-Knowledge Context cho AI Tutor (không đưa `correct_answer` vào LLM prompt context) để đảm bảo Zero-Leakage bất biến mà không phụ thuộc vào regex lọc chuỗi.

---

## 5. VERIFICATION METHOD (PHƯƠNG PHÁP ĐỐI SOÁT ĐỘC LẬP)

Để kiểm chứng độc lập các phát hiện trong báo cáo này, người thẩm tra có thể chạy các lệnh sau trong terminal:

1. **Kiểm chứng lỗi DDL cột `fetched_at`**:
   ```bash
   .venv/bin/python3 -c '
   import sqlite3
   conn = sqlite3.connect(":memory:")
   conn.execute("CREATE TABLE learning_courses_v2 (course_id VARCHAR(64) PRIMARY KEY, is_active BOOLEAN, published_at TIMESTAMP);")
   conn.execute("CREATE INDEX idx_courses_v2_active_fetched ON learning_courses_v2(is_active, fetched_at DESC);")
   '
   # Kỳ vọng: Ném ra sqlite3.OperationalError: no such column: fetched_at
   ```

2. **Kiểm chứng lỗi Trigger đệ quy**:
   ```bash
   .venv/bin/python3 -c '
   import sqlite3
   conn = sqlite3.connect(":memory:")
   conn.execute("PRAGMA recursive_triggers = ON;")
   conn.execute("CREATE TABLE learning_courses_v2 (course_id VARCHAR(64) PRIMARY KEY, updated_at TIMESTAMP);")
   conn.execute("CREATE TRIGGER trg_courses_v2_updated_at AFTER UPDATE ON learning_courses_v2 FOR EACH ROW BEGIN UPDATE learning_courses_v2 SET updated_at = CURRENT_TIMESTAMP WHERE course_id = OLD.course_id; END;")
   conn.execute("INSERT INTO learning_courses_v2 VALUES (\"c1\", CURRENT_TIMESTAMP);")
   conn.execute("UPDATE learning_courses_v2 SET course_id = \"c1\";")
   '
   # Kỳ vọng: Ném ra sqlite3.OperationalError: too many levels of trigger recursion
   ```

3. **Kiểm chứng các bộ test hiện tại**:
   - Frontend unit test: `node frontend/scripts/test-runner.mjs` (20 passed).
   - Frontend npm test: `cd frontend && npm test` (Lỗi Missing script "test").
   - Backend pytest độc lập: `RISK_DASHBOARD_DB_PATH=/tmp/verify.db .venv/bin/pytest tests/test_learning.py` (5 passed).
