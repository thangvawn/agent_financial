# 2026-10-31 · Kệ sách cá nhân và upload PDF

**Status: verified trên workspace.** Yêu cầu: tải sách/paper/tài liệu từ local và quản lý sách từng đọc theo tài khoản.

- Tab `shelf` trong LearningHomePage, upload từ thư viện hoặc kệ; PersonalLibrary lọc, sửa, xóa có xác nhận, trạng thái muốn đọc/đang đọc/đã đọc và lịch sử mở thành công. Reader lưu trang nhập thủ công để đọc tiếp; không suy đoán lịch sử cũ.
- API `learning/library` dùng principal bắt buộc; `account_id` là owner. SQLite thêm bảng độc lập, không reset bảng cũ. PDF lưu ở `get_db_path().parent / learning_library_files`, không dưới static assets. Sao lưu cả DB lẫn folder này.
- Upload PDF 40 MiB, quota 500 MiB/1.000 tài liệu mỗi user. Kiểm tra loại/header/EOF/PDFium/số trang, giới hạn multipart stream, dedupe SHA-256 theo owner, path UUID và transaction quota. File chỉ phục vụ qua endpoint auth hỗ trợ Range; tải về giữ nguyên byte.
- Nguồn code: `modules/learning/{api,infrastructure,schemas}/personal_library.py`; frontend `usePersonalLibrary`, `personalLibraryApi`, `PersonalLibrary`, `UploadDocumentDialog`, `ReaderLibraryTools`, `AddToShelfButton` và tích hợp reader/catalog.
- Verified 130 frontend, 69 backend, 20 browser flows (12 kệ cá nhân + 8 PDF regression); lint/build/CSS/Ruff đạt. Backend mới 99% statement; API frontend mới 100% line. [Báo cáo và lệnh chạy lại](../../qa/results/PERSONAL_LIBRARY_2026_10_31.md); evidence `output/playwright/personal-library/`.
- Chỉ QA DB/files tạm, không reset/khôi phục DB mặc định. Sự cố cũ vẫn unresolved, xem [record cũ](2026-10-31-book-source-audit.md).
- Không push/deploy. Giữ nguyên staged entries của người dùng; các reader/source đã dirty hoặc untracked từ trước còn trong workspace, không gom vào checkpoint mới.
