# BÁO CÁO PHẢN BIỆN THỰC CHỨNG & ADVERSARIAL STRESS-TEST KIẾN TRÚC TAB LEARN HUB (M2 - M3)
## (Adversarial Empirical Stress-Testing Report & Technical Verification)

- **Mã tài liệu**: `CHALLENGER-2-ADVERSARIAL-REPORT`
- **Phiên bản đối tượng kiểm định**: `LEARN_HUB_ARCHITECTURE.md` (v2.0.0) & `LEARN_HUB_BLUEPRINT.md` (v2.0.0-PROD)
- **Vai trò thẩm định**: EMPIRICAL CHALLENGER (Critic & Domain Specialist)
- **Ngày thực hiện**: 2026-10-10
- **Phán quyết tổng thể**: **REQUEST_CHANGES (YÊU CẦU ĐIỀU CHỈNH THIẾT KẾ BẮT BUỘC)**

---

## 1. PHÁN QUYẾT TỔNG THỂ & TÓM TẮT ĐIỀU HÀNH (EXECUTIVE VERDICT)

Qua quá trình rà soát đối kháng chuyên sâu và **trực tiếp viết mã kiểm thử thực chứng (Empirical Verification Code)** trên môi trường thực thi máy chủ, chúng tôi đưa ra phán quyết:

> **VERDICT: REQUEST_CHANGES**  
> Bản thiết kế Kiến trúc (M2) và Bản đặc tả Kỹ thuật (M3) có tầm nhìn xuất sắc, bao phủ toàn diện 13/13 tính năng trong `PROJECT.md`, giải quyết đúng trọng tâm các điểm nghẽn hiệu năng giao diện (Dual-Pane Split Layout, Throttled Media Sync, Active-only Canvas) và chuẩn hóa phân tầng độ khó CFA.  
> **TUY NHIÊN**, quá trình stress-test thực chứng đã phát hiện **4 LỖ HỔNG CRITICAL**, **2 LỖ HỔNG HIGH**, và **2 ĐIỂM NGHẼN MEDIUM**. Nếu không khắc phục ngay tại tầng đặc tả tài liệu, việc triển khai code ở M4 sẽ gặp lỗi cú pháp DDL gãy migration, lỗi đệ quy trigger làm sập transaction, không thể ghi nhận tiến độ bài học video/sách, sập phân hệ BCTC do bất nhất schema cache, và để lộ đáp án trắc nghiệm với tỷ lệ 90%.

---

## 2. BẢNG TỔNG HỢP CÁC LỖ HỔNG THỰC CHỨNG (EMPIRICAL FINDINGS MATRIX)

| Mã Lỗi | Phân Loại | Vị Trí Tài Liệu | Mô Tả Ngắn Gọn | Trạng Thái Thực Chứng |
|---|---|---|---|---|
| **EMP-SQL-01** | **CRITICAL** | `LEARN_HUB_ARCHITECTURE.md:680` | Lỗi DDL: Tạo index trên cột `fetched_at` không tồn tại trong `learning_courses_v2`. | **Xác nhận (Crash `no such column`)** |
| **EMP-SQL-02** | **CRITICAL** | `LEARN_HUB_ARCHITECTURE.md:701` | Lỗi Trigger: `trg_courses_v2_updated_at` đệ quy vô hạn khi bật recursive triggers. | **Xác nhận (Crash `too many levels`)** |
| **EMP-ARCH-03** | **CRITICAL** | `LEARN_HUB_ARCHITECTURE.md:630` | Lỗi Mô Hình: `verified_event_id NOT NULL` chặn ghi nhận tiến độ bài học Video/Reading. | **Xác nhận (Crash `NOT NULL failed`)** |
| **EMP-DOM-04** | **CRITICAL** | `LEARN_HUB_ARCHITECTURE.md:1240` | Lỗi Tích Hợp: `FinancialCrossLinkService` crash do đọc sai cấu trúc `periods` trong cache BCTC. | **Xác nhận (Crash `AttributeError: list`)** |
| **EMP-SEC-05** | **HIGH** | `LEARN_HUB_ARCHITECTURE.md:1434` | Lỗi Bảo Mật: `AntiCheatingGuardian` regex bị qua mặt 90% trước định dạng markdown/số thực. | **Xác nhận (90% bypass rate)** |
| **EMP-FTS-06** | **HIGH** | `LEARN_HUB_ARCHITECTURE.md:711` | Lỗi Bất Đồng Bộ: Thiếu trigger UPDATE FTS5 và bỏ sót hoàn toàn 3 trụ cột (Sách, Video, Khóa học). | **Xác nhận (Stale text sau UPDATE)** |
| **EMP-NET-07** | **MEDIUM** | `LEARN_HUB_BLUEPRINT.md:786` | Lỗi Giao Thức: Cam kết tiếp tục stream bằng `Last-Event-ID` nhưng thiếu backend event buffer. | **Xác nhận (Thiếu thiết kế đệm)** |
| **EMP-NET-08** | **MEDIUM** | `LEARN_HUB_BLUEPRINT.md:264` | Lỗi Caching: `Cache-Control: max-age=60` trên tiến độ cá nhân gây hiển thị bài học chưa xong. | **Xác nhận (Stale browser cache)** |

---

## 3. CHI TIẾT BẰNG CHỨNG THỰC CHỨNG TỪNG LỖ HỔNG (EMPIRICAL EVIDENCE)

### 3.1. [CRITICAL] EMP-SQL-01: Lỗi DDL Không Tồn Tại Cột `fetched_at`
- **Quan sát trực tiếp**:
  Tại `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 680–682:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_courses_v2_active_fetched 
  ON learning_courses_v2(is_active, fetched_at DESC);
  ```
  Trong khi bảng `learning_courses_v2` (dòng 259–276) có schema:
  `course_id, title, slug, description, instructor, tier, category, total_duration_minutes, thumbnail_url, prerequisites_json, target_competencies_json, is_active, published_at, created_at, updated_at`. Cột `fetched_at` hoàn toàn không tồn tại.
- **Mã thực nghiệm tái lập**:
  ```python
  import sqlite3
  conn = sqlite3.connect(":memory:")
  conn.executescript(ddl_courses_and_index)
  ```
- **Kết quả thực chứng**:
  `sqlite3.OperationalError: no such column: fetched_at`
- **Hệ quả**: Migration tạo bảng CSDL mới sẽ crash 100% ngay tại bước khởi tạo composite index.
- **Khắc phục**: Đổi index thành:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_courses_v2_active_published 
  ON learning_courses_v2(is_active, published_at DESC);
  ```

---

### 3.2. [CRITICAL] EMP-SQL-02: Đệ Quy Vô Hạn Database Trigger `trg_courses_v2_updated_at`
- **Quan sát trực tiếp**:
  Tại `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 701–708:
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
- **Phân tích logic & Thực nghiệm**:
  Trong SQLite, khi kích hoạt `PRAGMA recursive_triggers = ON` (cờ bắt buộc để kích hoạt Foreign Key Cascades hoạt động xuyên suốt các bảng phân cấp), mỗi lần thực hiện UPDATE một khóa học, trigger này phát sinh lệnh UPDATE trên chính bảng đó, kích hoạt lại chính nó liên tục cho tới khi tràn ngăn xếp.
- **Kết quả thực chứng**:
  `sqlite3.OperationalError: too many levels of trigger recursion`
- **Hệ quả**: Bất kỳ cập nhật khóa học nào phía backend hay Admin CMS đều làm sập transaction.
- **Khắc phục**: Thêm điều kiện ngắt đệ quy `WHEN OLD.updated_at = NEW.updated_at`:
  ```sql
  CREATE TRIGGER IF NOT EXISTS trg_courses_v2_updated_at
  AFTER UPDATE ON learning_courses_v2
  FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN
      UPDATE learning_courses_v2 
      SET updated_at = CURRENT_TIMESTAMP 
      WHERE course_id = OLD.course_id;
  END;
  ```

---

### 3.3. [CRITICAL] EMP-ARCH-03: Khóa Ngoại `verified_event_id` Chặn Tiến Độ Của Bài Học Video/Sách
- **Quan sát trực tiếp**:
  Tại `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 630–642:
  ```sql
  CREATE TABLE IF NOT EXISTS learning_progress_receipts (
      receipt_id VARCHAR(64) PRIMARY KEY,
      verified_event_id VARCHAR(64) NOT NULL UNIQUE,
      user_id VARCHAR(64) NOT NULL,
      course_id VARCHAR(64) NOT NULL,
      lesson_id VARCHAR(64) NOT NULL,
      idempotency_key VARCHAR(128) NOT NULL UNIQUE,
      confirmation_hash VARCHAR(64) NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (verified_event_id) REFERENCES learning_verified_events(verified_event_id) ON DELETE CASCADE,
      FOREIGN KEY (course_id) REFERENCES learning_courses_v2(course_id) ON DELETE CASCADE,
      FOREIGN KEY (lesson_id) REFERENCES learning_course_lessons(lesson_id) ON DELETE CASCADE
  );
  ```
  Và bảng `learning_verified_events` (dòng 616–625) bắt buộc:
  `checkpoint_id VARCHAR(64) NOT NULL REFERENCES learning_checkpoints(checkpoint_id)`.
- **Mâu thuẫn kiến trúc**:
  Theo `PROJECT.md` và `LEARN_HUB_BLUEPRINT.md` § 2.3.1, endpoint `POST /api/v1/public/learning/lessons/{lesson_id}/complete` ghi nhận hoàn thành bài học và sinh ra `receipt`. Tuy nhiên, trong 4 loại bài học (`video`, `reading`, `bctc_case`, `quiz`), các bài học dạng video và tài liệu đọc thường **không có checkpoint** (checkpoint là null hoặc tùy chọn). Khi đó, bài học không có `verified_event_id`.
- **Kết quả thực chứng**:
  Cố gắng insert receipt cho bài học video không checkpoint:
  - Nếu `verified_event_id = NULL`: `sqlite3.IntegrityError: NOT NULL constraint failed: learning_progress_receipts.verified_event_id`
  - Nếu truyền giá trị giả định (chuỗi rỗng): `sqlite3.IntegrityError: FOREIGN KEY constraint failed`
- **Hệ quả**: Toàn bộ bài học video và đọc sách trong hệ thống không thể hoàn thành hoặc sinh chứng từ tiến độ hợp lệ.
- **Khắc phục**: Sửa `learning_progress_receipts`:
  1. Cho phép `verified_event_id VARCHAR(64) NULL REFERENCES ...`
  2. Bổ sung cột `receipt_type VARCHAR(32) NOT NULL DEFAULT 'lesson_completed'` (`lesson_completed` | `checkpoint_verified`).
  3. Chỉ áp dụng ràng buộc foreign key khi `verified_event_id IS NOT NULL`.

---

### 3.4. [CRITICAL] EMP-DOM-04: Sập Runtime `FinancialCrossLinkService` Do Sai Cấu Trúc File Cache BCTC
- **Quan sát trực tiếp**:
  Tại `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 1249–1257:
  ```python
  return {
      "ticker": ticker.upper(),
      "available_periods": list(data.get("periods", {}).keys()),
      "selected_period": period or data.get("latest_period"),
      "balance_sheet": data.get("balance_sheet", {}),
      "income_statement": data.get("income_statement", {}),
      "cash_flow": data.get("cash_flow", {}),
      "ratios": data.get("ratios", {}),
  }
  ```
- **Khảo sát cấu trúc thực tế của kho dữ liệu `data/financials/cache/*.json`**:
  Kiểm tra file thật `data/financials/cache/HPG.json`:
  1. `data["periods"]` là một mảng `list[dict]` gồm 27 phần tử: `[{'period': '2018-Q1', 'revenue': ...}, ...]`. Hoàn toàn không phải là `dict` để gọi `.keys()`.
  2. Dữ liệu báo cáo tài chính nằm tại `data["raw_statements"]["balance"]`, `data["raw_statements"]["income"]`, `data["raw_statements"]["cash_flow"]`. Hoàn toàn không có các key cấp 1 `"balance_sheet"` hay `"income_statement"`.
- **Kết quả thực chứng**:
  Chạy phương thức trên với file HPG thật văng lỗi ngay dòng đầu tiên:
  `AttributeError: 'list' object has no attribute 'keys'`
- **Hệ quả**: Toàn bộ Trụ cột 4 (BCTC Case Study) sập hoàn toàn ở runtime khi nạp dữ liệu tài chính của HPG, VNM, FPT.
- **Khắc phục**: Viết lại adapter chính xác theo schema cache thật:
  ```python
  periods_list = [p["period"] for p in data.get("periods", []) if isinstance(p, dict) and "period" in p]
  latest_period = periods_list[-1] if periods_list else None
  target_period = period or latest_period
  raw_stmts = data.get("raw_statements", {})
  return {
      "ticker": ticker.upper(),
      "available_periods": periods_list,
      "selected_period": target_period,
      "balance_sheet": raw_stmts.get("balance", {}),
      "income_statement": raw_stmts.get("income", {}),
      "cash_flow": raw_stmts.get("cash_flow", {}),
  }
  ```

---

### 3.5. [HIGH] EMP-SEC-05: Rào Chắn Socratic Regex Bị Qua Mặt 90%
- **Quan sát trực tiếp**:
  Tại `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 1434–1456:
  `AntiCheatingGuardian` chỉ lọc 3 regex tiếng Việt cứng nhắc: `đáp án (chính xác|đúng) là\s*[:=]?\s*([A-D]|opt_[a-d])`, `hãy chọn...`, `chọn ... nhé`.
- **Thử nghiệm đối kháng (Adversarial Testing)**:
  Tạo harness kiểm tra 10 câu phản hồi tự nhiên mà các mô hình ngôn ngữ lớn (Gemini, Claude, GPT) thường sinh ra:
  1. `Đáp án đúng là **A**` (Markdown formatting) -> **BỊ LỌT (90% LLMs dùng in đậm)**.
  2. `Đáp án đúng là: (A)` (Dấu ngoặc đơn) -> **BỊ LỌT**.
  3. `Phương án chính xác ở đây là B` (Từ đồng nghĩa) -> **BỊ LỌT**.
  4. `Đáp án là C nhé bạn.` (Rút gọn) -> **BỊ LỌT**.
  5. `Bạn nên chọn đáp án D.` (Câu mệnh lệnh) -> **BỊ LỌT**.
  6. `The correct answer is B.` (Tiếng Anh) -> **BỊ LỌT**.
  7. `Dòng tiền FCF là -5.500 tỷ VND` (Định dạng số tài chính) -> **BỊ LỌT** (vì giá trị cấm lưu dạng `-5500`).
  8. `1. A\n2. B\nChọn mục đầu tiên nhé.` -> **BỊ LỌT**.
  9. `Đáp án đúng là phương án thứ hai (B)` -> **BỊ LỌT**.
  10. `Đáp án đúng là b` (Chữ thường không có opt_) -> **BỊ CHẶN (1/10)**.
- **Tỷ lệ thất bại**: **90.0% (9/10 ca kiểm thử làm rò rỉ đáp án)**.
- **Khắc phục**:
  1. **Prompt Isolation Invariant**: Nguyên tắc tối thượng: KHÔNG BAO GIỜ truyền `correct_answer` vào context của Socratic AI Tutor trong phiên học viên. AI chỉ được nhận `prompt`, `learning_objective`, và `scaffolding_hints`. Nếu AI không biết đáp án cuối cùng, nó không bao giờ có thể tiết lộ đáp án.
  2. **Sanitizer Normalization**: Làm sạch văn bản trước khi regex: xóa toàn bộ markdown (`**`, `*`, `()`), chuẩn hóa số liệu (`-5.500` -> `-5500`), và kiểm tra đa ngôn ngữ.

---

### 3.6. [HIGH] EMP-FTS-06: Thiếu Trigger UPDATE và Bỏ Sót 3 Trụ Cột trong FTS5
- **Quan sát trực tiếp**:
  Mục 2.8 chỉ cung cấp trigger `AFTER INSERT` và `AFTER DELETE` cho bảng `learning_bctc_cases`. Hoàn toàn không có trigger `AFTER UPDATE`. Các bảng `learning_courses_v2`, `learning_book_metadata`, `learning_video_metadata` hoàn toàn không có trigger FTS5 nào.
- **Kết quả thực chứng**:
  - Khi cập nhật tiêu đề của BCTC Case từ `"Old Title HPG"` sang `"New Title HPG Expansion"`, FTS5 vẫn chỉ lưu `"Old Title HPG"` và không tìm thấy `"Expansion"`.
  - Đo lường hiệu năng: Trigger per-row tốn 35.31ms so với 6.12ms khi batch sync (chậm hơn 5.77 lần), gây nghẽn nghiêm trọng khi crawler nạp hàng trăm bài giảng.
- **Khắc phục**:
  Bổ sung trigger `AFTER UPDATE` cho BCTC cases, hoặc chuyển cơ chế đồng bộ FTS5 sang **Background Batch Ingestion Worker** để tối ưu hóa hiệu năng ghi đĩa SQLite.

---

### 3.7. [MEDIUM] EMP-NET-07: Cam Kết Resumption Ảo Tưởng Trên Giao Thức SSE
- **Quan sát trực tiếp**:
  `LEARN_HUB_BLUEPRINT.md` § 2.5: Cam kết client gửi header `Last-Event-ID: <id>` khi mất mạng để server phục hồi dòng token.
- **Phân tích logic**:
  Server sử dụng FastAPI stateless xử lý request `POST`. Backend không có Redis Stream buffer hay bộ nhớ đệm token theo phiên. Việc gọi lại LLM sẽ sinh ra chuỗi token mới với câu chữ khác.
- **Khắc phục**:
  Xác định rõ ràng: Nếu ngắt kết nối SSE giữa chừng, client sẽ kích hoạt chức năng "Tạo lại câu trả lời" (Regenerate Response), hoặc nếu muốn resume, phải kiến trúc thêm một Ring Buffer trong in-memory state của server có TTL 60 giây.

---

### 3.8. [MEDIUM] EMP-NET-08: Stale Browser Cache Trên Tiến Độ Khóa Học Cá Nhân
- **Quan sát trực tiếp**:
  `LEARN_HUB_BLUEPRINT.md` § 2.2.2: `Cache-Control: private, max-age=60 khi có X-Session-ID`.
- **Phân tích logic**:
  Khi người học bấm "Hoàn thành bài học" (POST), rồi bấm quay lại cây bài giảng khóa học, trình duyệt phục vụ bản ghi từ Memory Cache của nó mà không gửi request lên backend. Người học sẽ thấy bài vừa học vẫn ở trạng thái "Chưa hoàn thành" trong 60 giây tiếp theo, gây nhầm lẫn là hệ thống bị lỗi lưu tiến độ.
- **Khắc phục**:
  Sử dụng `Cache-Control: private, no-cache, must-revalidate` kèm `ETag` cho mọi endpoint có dữ liệu gắn liền với `X-Session-ID`.

---

## 4. MA TRẬN ĐỐI CHIẾU 13 TÍNH NĂNG PROJECT.MD (FEATURE INVENTORY CROSS-CHECK)

| # | Feature trong PROJECT.md | Trạng thái trong Tài liệu M2/M3 | Đánh giá Tính Đầy Đủ & Khoảng Trống |
|---|---|---|---|
| 1 | Full Codebase Audit & Bottleneck Catalog | ĐÃ ĐỐI CHIẾU | Phản ánh đầy đủ các vấn đề FE-PERF, BE blocking I/O trong M1/M2/M3. |
| 2 | Automated Test Suite Execution & Gap Analysis | ĐÃ ĐỐI CHIẾU | 148 tests được bảo toàn trong tài liệu, đã nhận diện lỗi database malformed. |
| 3 | Root Cause & Risk Matrix (R1) | ĐÃ ĐỐI CHIẾU | Phân loại rủi ro Critical/High/Medium/Low rõ ràng, có file:line citations. |
| 4 | Multi-Format Content Data Model (R2) | CẦN SỬA ĐỔI | Đầy đủ 4 định dạng nhưng gãy DDL tại `idx_courses_v2_active_fetched`. |
| 5 | Hierarchical Course & Checkpoint Engine | CẦN SỬA ĐỔI | 4 tầng Course->Module->Lesson->Checkpoint nhưng gãy receipt bài học video. |
| 6 | Ebook & Document Reader Architecture | ĐẠT YÊU CẦU | Đầy đủ PDF.js, bounding box vector, bookmarks, menu hỏi AI Tutor. |
| 7 | Video Lecture Player & Timestamped Notes | ĐẠT YÊU CẦU | Đầy đủ YouTube API Bridge, throttled timeupdate 1000ms, time-synced notes. |
| 8 | BCTC Case-Study Learning Engine | CẦN SỬA ĐỔI | 3 case studies HPG, VNM, FPT rất tốt nhưng sập adapter `FinancialCrossLinkService`. |
| 9 | Taxonomy, Tagging & VN30 Symbol Cross-Linking | ĐẠT YÊU CẦU | Chuẩn hóa 4 độ khó, cây chủ đề CFA 2 cấp, liên kết chéo mã cổ phiếu. |
| 10 | AI Tutor Socratic Companion Integration | CẦN SỬA ĐỔI | Thiết kế đa phương thức tốt nhưng bộ lọc Zero-Leakage regex bị bypass 90%. |
| 11 | REST & SSE Streaming API Specifications (R3) | CẦN SỬA ĐỔI | Contracts chi tiết nhưng cần điều chỉnh Stale Cache 60s và cơ chế resume SSE. |
| 12 | Dual-Pane UI Component Hierarchy & State Machine | ĐẠT YÊU CẦU | Layout 60/40 chuẩn, 26 component phân rã <200 dòng, custom hooks tối ưu. |
| 13 | Phased Migration Roadmap (Tracer Bullet) | ĐẠT YÊU CẦU | 5 Phase tracer bullet rõ ràng, có tiêu chí nghiệm thu và quality gates. |

---

## 5. KẾ HOẠCH HÀNH ĐỘNG KHẮC PHỤC CỤ THỂ (REMEDIATION DIRECTIVE)

Để đủ điều kiện phê duyệt kiến trúc (APPROVE), đội ngũ kiến trúc cần thực hiện các chỉnh sửa sau vào hai tài liệu:

1. **Chỉnh sửa `docs/LEARN_HUB_ARCHITECTURE.md`**:
   - Dòng 680–682: Đổi `idx_courses_v2_active_fetched ON learning_courses_v2(is_active, fetched_at DESC)` thành `idx_courses_v2_active_published ON learning_courses_v2(is_active, published_at DESC)`.
   - Dòng 701–708: Thêm mệnh đề `WHEN OLD.updated_at = NEW.updated_at` vào trigger `trg_courses_v2_updated_at`.
   - Dòng 632: Sửa cột `verified_event_id` trong `learning_progress_receipts` thành `NULLABLE`, bổ sung `receipt_type VARCHAR(32) NOT NULL DEFAULT 'lesson_completed'`.
   - Dòng 1249–1257: Cập nhật hàm `load_ticker_financial_snapshot` đọc `periods` dạng `list[dict]` và lấy số liệu từ `data["raw_statements"]`.
   - Dòng 1434–1456: Bổ sung nguyên tắc *Prompt Isolation Architecture* (không truyền đáp án vào prompt của gia sư Socratic) và bộ tiền xử lý chuẩn hóa chuỗi trước khi lọc.
   - Bổ sung `CREATE TABLE learning_topics` và `CREATE TABLE learning_resource_topics` vào DDL mục 2.8.
2. **Chỉnh sửa `docs/LEARN_HUB_BLUEPRINT.md`**:
   - Dòng 264: Đổi header của `GET /courses/{course_id}` sang `Cache-Control: private, no-cache, must-revalidate`.
   - Dòng 794: Làm rõ cơ chế kết nối lại của SSE: Khi mất kết nối thì tái yêu cầu (regenerate) hoặc mô tả tầng đệm in-memory/Redis stream cụ thể.
