# ĐÁNH GIÁ CHUYÊN SÂU & PHẢN BIỆN ĐỐI KHÁNG: AUDIT REPORT (M1) & ARCHITECTURE (M2)

**Mã tài liệu**: `REV-CRITIC-LEARN-HUB-M1-M2`  
**Reviewer & Adversarial Critic**: reviewer_1  
**Ngày đánh giá**: 2026-10-10  
**Tài liệu được đánh giá**:
1. `docs/LEARN_HUB_AUDIT_REPORT.md` (M1 / Requirement R1)
2. `docs/LEARN_HUB_ARCHITECTURE.md` (M2 / Requirement R2)
**Hợp đồng đối chiếu**: `ORIGINAL_REQUEST.md`, `PROJECT.md`

---

## 1. TỔNG QUAN ĐIỀU HÀNH & KẾT LUẬN (EXECUTIVE SUMMARY & VERDICT)

### Phán Quyết Chính Thức (Explicit Verdict):
# ⚠️ REQUEST_CHANGES (Yêu Cầu Chỉnh Sửa Kỹ Thuật Trước Khi Phê Duyệt)

### Tóm tắt lý do phán quyết:
- **Tài liệu Audit (`LEARN_HUB_AUDIT_REPORT.md`)**: Đạt chất lượng xuất sắc. Các phát hiện về hiệu năng (re-render cascade, canvas GPU leak), bảo mật (zero-leakage breach trong `mockExamData.js`), kiến trúc backend (blocking I/O event loop, connection leak, seeding storm) đều có trích dẫn mã nguồn chính xác 100%, có bằng chứng thực chứng rõ ràng và phân tích nguyên nhân gốc rễ sâu sắc.
- **Tài liệu Kiến Trúc (`LEARN_HUB_ARCHITECTURE.md`)**: Cực kỳ toàn diện, thiết kế bài bản mô hình 4 trụ cột học liệu, tích hợp BCTC VN30 thực chiến và Pydantic v2 schemas rất chuẩn mực. **TUY NHIÊN**, quá trình thẩm định động và chạy thử nghiệm code thực tế đã phát hiện **2 LỖI NGHIÊM TRỌNG TRONG ĐẶC TẢ DDL VÀ TRIGGER**:
  1. **Lỗi DDL gãy câu lệnh SQL (`OperationalError: no such column: fetched_at`)**: Composite index `idx_courses_v2_active_fetched` (dòng 680-681) trỏ tới cột `fetched_at`, nhưng bảng `learning_courses_v2` hoàn toàn không có cột này. Khi chạy script DDL trên SQLite, lệnh tạo index bị crash ngay lập tức.
  2. **Lỗi đệ quy vô tận trong Database Trigger (`OperationalError: too many levels of trigger recursion`)**: Trigger `trg_courses_v2_updated_at` (dòng 701-709) tự kích hoạt cập nhật lại bảng `learning_courses_v2` sau mỗi câu lệnh update mà không có điều kiện dừng `WHEN`, dẫn đến sập cơ sở dữ liệu do vượt quá giới hạn đệ quy.
  3. **Lỗ hổng bảo vệ Zero-Leakage qua Regex**: Cơ chế `AntiCheatingGuardian` chỉ sử dụng 3 regex tiếng Việt tĩnh, dễ dàng bị vượt qua bởi các câu hỏi tiếng Anh hoặc cấu trúc câu đảo.

---

## 2. ĐÁNH GIÁ CHẤT LƯỢNG BÁO CÁO KIỂM TOÁN (`LEARN_HUB_AUDIT_REPORT.md` - R1)

### 2.1. Độ chính xác trích dẫn & Khảo sát thực chứng (100% Verified)
Đã độc lập kiểm tra từng trích dẫn tệp và dòng code trong báo cáo kiểm toán:
- `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx:41,122`: Xác nhận chính xác dòng 41 khởi tạo `useState(0)` và dòng 122 gắn `onTimeUpdate` gây Re-render Cascade 4-5 lần/giây.
- `frontend/src/features/learn-hub/pages/NotePaper.jsx:125-135`: Xác nhận chính xác việc khởi tạo thẻ `<canvas width={960} height={1400} />` chiếm ~5.38MB bộ nhớ đồ họa bitmap/trang và `toDataURL` đồng bộ gây lag.
- `frontend/src/features/learn-hub/content/mockExamData.js:1-417`: Xác nhận chính xác 417 dòng chứa 90 câu hỏi đóng gói lộ toàn bộ `correctOptionId` và chấm điểm 100% tại client.
- `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py:146-150` & `video_agent_service.py:121`: Xác nhận chính xác gọi `urllib.request.urlopen` đồng bộ với timeout 8s bên trong hàm `async def` của FastAPI loop.
- `src/risk_dashboard/modules/learning/infrastructure/catalog_reader.py:127-128, 286-326`: Xác nhận chính xác khởi tạo `ensure_learning_catalog_seeded` lặp đi lặp lại trên mỗi request.
- `src/risk_dashboard/platform/database/schema/baseline.sql:106-172`: Xác nhận chính xác các bảng catalog cũ thiếu index trên `fetched_at` hoặc `(is_active, fetched_at)`.

### 2.2. Kiểm chứng kết quả kiểm thử tự động (Test Execution Verification)
- **Frontend test runner**: Lệnh `npm run test:unit` (`node ./scripts/test-runner.mjs`) chạy thực tế đạt **20 passed, 6 suites**, hoàn toàn khớp với báo cáo.
- **Frontend npm test**: Lệnh `npm test` thất bại với mã lỗi 1 (`Missing script: "test"`), hoàn toàn khớp với báo cáo.
- **Backend test suite (`pytest`)**:
  - Khi chạy độc lập từng file với database sạch (`RISK_DASHBOARD_DB_PATH=/tmp/test.db`), toàn bộ các file test đều đạt **100% pass (147 passed, 1 skipped)**.
  - **Phát hiện quan trọng của Reviewer**: Khi chạy toàn bộ 18 file test cùng lúc vào tệp database mặc định `data/db/northstar.db`, tệp này bị **lỗi phân mảnh đĩa (`sqlite3.DatabaseError: database disk image is malformed`)** do tranh chấp ghi SQLite (Write Contention). Đây là bằng chứng ngoại cảnh củng cố thêm tính xác thực của các lỗ hổng BE-04 (Connection Leak), BE-06 (Seeding Storm) và BE-09 (SQLite Deadlock) mà báo cáo đã cảnh báo!

---

## 3. ĐÁNH GIÁ CHUYÊN SÂU TÀI LIỆU KIẾN TRÚC (`LEARN_HUB_ARCHITECTURE.md` - R2)

### 3.1. Đánh giá Mô hình 4 Trụ Cột Học Liệu (4-Pillar Multi-Format Model)
- **Ebook / PDF Reader**: Đặc tả đầy đủ PDF.js vector rendering, hệ thống neo tọa độ `BoundingBoxRect ({x, y, width, height})`, bảng highlight `learning_book_annotations` và `learning_book_bookmarks`.
- **Video Player**: Đặc tả tích hợp YouTube IFrame Player API hai chiều, giải quyết dứt điểm lỗi kẹt 0s (FE-PERF-02). Bảng phân đoạn chương `learning_video_chapters` kèm `key_takeaways` và ghi chú mốc thời gian `learning_video_notes`.
- **Khóa học phân cấp 4 tầng**: Cấu trúc chặt chẽ `Course -> Module -> Lesson -> Checkpoint`. Xóa bỏ hoàn toàn mô hình phẳng V1.
- **BCTC Case-Studies**: Tích hợp 120+ file JSON BCTC thực tế từ `data/financials/cache/`. Đóng gói 3 case study mẫu xuất sắc:
  1. HPG: Chu kỳ Capex Dung Quất 2 (85.000 tỷ VND) & Dòng tiền tự do FCF âm.
  2. VNM: Phân rã DuPont 3 nhân tố & Đánh giá dòng tiền cổ tức an toàn.
  3. FPT: Chất lượng doanh thu phần mềm toàn cầu & Chu kỳ chuyển hóa tiền mặt CCC.

### 3.2. Đánh giá Toàn vẹn DDL & Schema Database (DDL Integrity)
- **Ưu điểm**:
  - Đã chuẩn hóa khóa ngoại có `ON DELETE CASCADE`.
  - Có các ràng buộc `CHECK (tier IN (...))`, `CHECK (lesson_type IN (...))`, `CHECK (progress_percentage BETWEEN 0 AND 100)`.
  - Có bảng chứng thực 2 pha: `learning_checkpoints` (không gửi đáp án ra ngoài), `learning_verified_events` và `learning_progress_receipts` có `idempotency_key` và `confirmation_hash`.
  - Bảng tìm kiếm toàn văn FTS5 đa định dạng `learning_fts5_unified_index` có cấu hình tokenizer `unicode61 remove_diacritics 2`.
- **Lỗi Nghiêm Trọng Cần Fix**:
  1. **Lỗi Cột Không Tồn Tại**: `idx_courses_v2_active_fetched ON learning_courses_v2(is_active, fetched_at DESC)` bị crash vì bảng không có `fetched_at`.
  2. **Lỗi Đệ Quy Trigger**: `trg_courses_v2_updated_at` thiếu điều kiện dừng `WHEN NEW.updated_at = OLD.updated_at`.

### 3.3. Đánh giá Mô hình Miền Pydantic v2 (Pydantic Integrity)
- **Kết quả chạy thử nghiệm**: Đã viết script kiểm tra toàn bộ 22 model Pydantic trong Mục 3. Kết quả: **Khởi tạo và validate 100% thành công**.
- **Điểm sáng kỹ thuật**:
  - Sử dụng triệt để `model_config = ConfigDict(frozen=True, extra="forbid")`.
  - Custom validator `validate_page_bounds` kiểm tra `current_page <= total_pages`.
  - Custom validator `validate_time_range` kiểm tra `start_seconds < end_seconds`.
  - Validator `ContextGroundingPayload` kiểm tra định dạng `ticker` 3 ký tự và `playback_seconds >= 0`.

---

## 4. KẾT QUẢ KIỂM THỬ ĐỐI KHÁNG & CÁC KỊCH BẢN TẤN CÔNG (ADVERSARIAL STRESS-TESTS)

| Kịch Bản Thử Nghiệm Đối Kháng | Mục Tiêu Thử Nghiệm | Dự Đoán Kiến Trúc | Kết Quả Thực Tế Độc Lập | Đánh Giá Rủi Ro |
|---|---|---|---|---|
| **Thực thi DDL Section 2 trên SQLite** | Áp dụng toàn bộ DDL vào SQLite engine | Thành công | **CRASH: `OperationalError: no such column: fetched_at`** | **CRITICAL** |
| **Cập nhật dòng dữ liệu bảng `learning_courses_v2`** | Kiểm tra Trigger `trg_courses_v2_updated_at` | Cập nhật `updated_at` | **CRASH: `OperationalError: too many levels of trigger recursion`** | **CRITICAL** |
| **Tấn công Bypass Regex Socratic Zero-Leakage** | Gửi prompt tiếng Anh hoặc câu đảo: `"Select option B"`, `"Câu trả lời là B"` | Bị chặn bởi `AntiCheatingGuardian` | **LỌT HOÀN TOÀN (Bypass thành công)** | **HIGH** |
| **Thử nghiệm sai số làm tròn số học BCTC** | Nộp số liệu hàng nghìn tỷ VND với float 64-bit | Sai số < 1% | Số liệu quá lớn có thể sai lệch phần thập phân khi chuyển đổi đơn vị | **MEDIUM** |
| **Đồng bộ dữ liệu FTS5 từ Video và Sách** | Truy vấn phụ đề video và sách qua FTS5 | Tìm kiếm được | FTS5 chỉ có trigger cho BCTC, thiếu cơ chế index cho video/sách | **MEDIUM** |

---

## 5. DANH SÁCH YÊU CẦU CHỈNH SỬA CHI TIẾT (REQUIRED CHANGES)

Để tài liệu kiến trúc `docs/LEARN_HUB_ARCHITECTURE.md` đạt chuẩn phê duyệt (APPROVE), tác giả cần thực hiện các chỉnh sửa kỹ thuật sau:

### Yêu Cầu 1 (BẮT BUỘC - Khắc phục DDL gãy cột `fetched_at`):
- **Vị trí**: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 259-276 và dòng 680-681.
- **Giải pháp**:
  - *Cách 1*: Bổ sung cột `fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP` vào định nghĩa bảng `learning_courses_v2`.
  - *Cách 2*: Sửa index thành `CREATE INDEX IF NOT EXISTS idx_courses_v2_active_published ON learning_courses_v2(is_active, published_at DESC);`.

### Yêu Cầu 2 (BẮT BUỘC - Khắc phục đệ quy vô tận trong Trigger):
- **Vị trí**: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 701-709.
- **Giải pháp**:
  Bổ sung mệnh đề `WHEN` để triệt tiêu đệ quy:
  ```sql
  CREATE TRIGGER IF NOT EXISTS trg_courses_v2_updated_at
  AFTER UPDATE ON learning_courses_v2
  FOR EACH ROW
  WHEN NEW.updated_at = OLD.updated_at
  BEGIN
      UPDATE learning_courses_v2 
      SET updated_at = CURRENT_TIMESTAMP 
      WHERE course_id = OLD.course_id;
  END;
  ```

### Yêu Cầu 3 (KHUYẾN NGHỊ CAO - Nâng cấp Kiến trúc Zero-Leakage thành Zero-Knowledge Context):
- **Vị trí**: `docs/LEARN_HUB_ARCHITECTURE.md`, dòng 1434-1456 (Mục 5.5).
- **Giải pháp**:
  Không dựa vào regex hậu kiểm. Thiết lập quy tắc kiến trúc bất biến: **Trong prompt gửi cho AI Tutor khi giải đáp học viên, trường `correct_answer` và `rubric_evidence` TUYỆT ĐỐI KHÔNG ĐƯỢC ĐƯA VÀO Context Window**. Khi LLM không biết đáp án đúng, nó không thể tiết lộ đáp án dưới bất kỳ thủ thuật prompt injection nào.

### Yêu Cầu 4 (KHUYẾN NGHỊ - Bổ sung đặc tả cơ chế nạp FTS5 cho Video & Sách):
- **Vị trí**: `docs/LEARN_HUB_ARCHITECTURE.md`, Mục 2.8 và Mục 5.4.
- **Giải pháp**:
  Bổ sung định nghĩa Trigger hoặc Background Indexer Worker để trích xuất phụ đề từ `learning_video_transcripts` và các chương sách từ `learning_book_metadata` nạp vào `learning_fts5_unified_index`.
