# 2026-10-31 · PDF toàn văn

**Status: verified trên workspace.** Người dùng làm rõ rằng muốn bản PDF đầy đủ, không phải bản ghi chú. Quyết định này ưu tiên hơn hành vi hiển thị ghi chú local đầu danh sách trong đợt audit trước.

- DocumentLibrary mặc định Sách & Giáo trình / PDF toàn văn; notes/sample riêng. matchesBookFormat không coi HTML/text/Archive chưa kiểm chứng là PDF.
- fullPdfBooks.js cung cấp ba PDF OpenStax nguyên bản: Finance 2e 629 trang, Macro 3e 635 trang, Micro 3e 595 trang (tiếng Anh). File, hash, nguồn và giấy phép CC BY-NC-SA 4.0 nằm ở frontend/public/learning-assets/books/.
- BookCardItem có Đọc PDF/Tải PDF; reader mở tài liệu thật trước, ghi chú cá nhân vẫn dùng được.
- LearningAssetStaticFiles trong app_factory.py phục vụ data assets trước, rồi bundle dist và public; tránh file PDF có trong build nhưng HTTP 404 khi data volume chưa có.
- Verified: 120 frontend, 37 backend, 8 browser; lint/build/CSS đạt. Download và cả ba reader blob khớp SHA-256 nguồn. Xem [báo cáo](../../qa/results/PDF_LIBRARY_2026_10_31.md).
- Test backend dùng DB /tmp rõ ràng; QA server tự tạo DB riêng. Không chạy test reset DB cũ. Không thay đổi 200 dòng catalog đối chiếu.
- Giữ nguyên công việc sẵn có, 116 mục staged. Chưa push/deploy. Sự cố DB của lượt trước vẫn unresolved, xem [session trước](2026-10-31-book-source-audit.md); lượt này không tuyên bố đã khôi phục.
