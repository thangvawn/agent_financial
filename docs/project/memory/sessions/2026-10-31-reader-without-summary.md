# Reader bỏ tóm lược và nguyên tắc

- Date: 2026-10-31. Status: **verified**.
- Request: bỏ mục “Tóm lược & Nguyên tắc” trong khung đọc tài liệu.
- Change: BookDocumentPane chỉ hiển thị tài liệu với nhãn loại nội dung; bỏ tab, CTA và fallback sang summary trong PDF/loading/error states. Xóa BookStudyNotes, bookDetailReaderData và CSS riêng; gỡ ba test của chức năng đã bỏ, cập nhật QA script cũ. Sổ ghi chú cá nhân vẫn hoạt động.
- Sources: `frontend/src/features/learn-hub/pages/BookDocumentPane.jsx`, `PdfBookPane.jsx`, `book-reader.css`, `reader-studio.css`, `services/bookAvailability.js`.
- Verification: 145 frontend unit, ESLint, CSS 50 file và build đạt. Chromium: PDF đúng signature, nhãn không còn tab summary, ghi chú lưu được; mobile không tràn; lỗi tải có retry, ghi chú còn nguyên, retry phục hồi. [Browser evidence](../../../../output/playwright/reader-without-summary/evidence.json), [ảnh header](../../../../output/playwright/reader-without-summary/heading.png), [logs](../../../../output/qa/reader-without-summary/).
- QA dùng DB tạm, build riêng `/private/tmp/northstar-review-20261031-dist`; không deploy. [Bản sao source summary đã bỏ](../../../../output/qa/reader-without-summary/removed-summary-source.zip). Không sửa 7 nhóm lỗi của review trước.
