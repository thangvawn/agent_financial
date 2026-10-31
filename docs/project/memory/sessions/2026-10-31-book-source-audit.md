# 2026-10-31 · Nguồn sách Learn Hub

**Status: verified cho bản sửa trên workspace; sự cố reset trạng thái DB chưa khôi phục.**

Yêu cầu: kiểm tra/thiết kế lại phần đọc sách có nhiều tài liệu không tồn tại. Chi tiết, lệnh chạy lại và giới hạn: [báo cáo](../../qa/results/BOOK_READER_AUDIT_2026_10_31.md).

- Tab đang dùng là `DocumentLibrary.jsx`, đi qua `bookSource.js` → `BookDocumentPane.jsx`/`PdfBookPane.jsx`. Có lọc và kiểm tra nguồn, phân trang, dedupe URL, cache, cảnh báo lỗi và giữ ghi chú.
- `/reader/check`: lấy metadata Archive, kiểm tra file thật bằng prefix; không đoán identifier.pdf. Hạn chế mượn sách không phải 404. Nhiều file phù hợp yêu cầu chọn tại nguồn. `/reader/stream` trả lỗi HTTP thật, kiểm tra redirect/DNS public, định dạng và giới hạn kích thước.
- HTML ghi chú không được quảng cáo là sách đầy đủ; sửa 3 URL note `.pdf` sai. Wealth of Nations chuyển sang Gutenberg HTML đã kiểm chứng. Không sửa/xóa các dòng catalog DB bằng audit.
- Frontend 116 test, backend 65 test, coverage proxy 88%, source resolver 100%/availability 99.16% dòng; lint/build/CSS đạt. Browser có fixture lỗi và nguồn Gutenberg thật; ảnh PDF cần Chromium đầy đủ, không dùng headless shell mặc định.
- Audit 124 URL gốc: 59 ready, 36 restricted, 12 missing, 8 unavailable, 9 external. Đây là kết quả tại thời điểm audit/prefix, không chứng minh toàn vẹn hay nội dung học thuật của mọi file. Nguồn thay thế Gutenberg kiểm tra riêng.

## Sự cố test và việc còn lại

Lần test mở rộng đầu thiếu biến DB tạm; hai module test cũ reset các bảng trạng thái DB mặc định. Sau đó đã thêm fixture `tmp_path` cho `tests/test_learning.py` và `tests/test_learning_remediation.py`, đồng thời cô lập DB bootstrap của script audit. Lần chạy lại 65 test trên DB tạm đạt.

Đã đối chiếu 200 dòng sách gốc: không thay đổi. Không có snapshot trước chạy để xác định/khôi phục chính xác trạng thái trong các bảng bị reset. `.bak` 10/10 thiếu những bảng đó; người dùng xác nhận không có backup mới hơn. Snapshot **sau** sự cố: `.local-dev/qa-backups/2026-10-31-post-test-reset.db`. Không tự coi snapshot này là bản trước sự cố hoặc tự ghi đè DB. SQLite `.recover` offline được lưu ở `.local-dev/qa-backups/2026-10-31-offline-recovery.db`: chỉ thêm 28.159 dòng orphan chưa xác định bảng/niên đại, không thêm dòng vào bảng có tên; chưa nhập vào DB đang dùng. Tình trạng khôi phục: **unresolved**. Báo cáo có chi tiết và bằng chứng, đã thông báo người dùng.

## Handoff

Giữ nguyên 116 mục staged có sẵn. Checkpoint chỉ chứa file của lượt làm; reader/content/proxy đã dirty hoặc untracked trước đó vẫn trong working tree. Bằng chứng áp dụng workspace, không phải checkout checkpoint độc lập. Chưa push/deploy/restart stack người dùng. Backend QA sử dụng DB riêng, cần dừng khi bàn giao.
