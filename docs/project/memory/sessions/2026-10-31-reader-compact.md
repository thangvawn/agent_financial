# 2026-10-31 · Thu gọn phần đầu reader

**Status: verified trên workspace.** Người dùng phản hồi các thanh phía trên chiếm quá nhiều diện tích trong ảnh reader.

- `ReaderChrome` và `reader-studio.css`: bỏ breadcrumb, thu nhỏ mô hình sách 3D và header, giảm padding/thanh vị trí đọc/tab tài liệu; giữ tên sách/tác giả và các hành động chính. Footer/gutter gọn hơn.
- `BookReaderWorkspace`: ghép tiêu đề ghi chú với công cụ thành một hàng; chuyển số trang/khổ A4 sang hàng điều hướng trang. Nút chèn ảnh/thêm trang dùng icon có accessible name và tooltip. Các tùy chọn bút/tẩy hiện khi cần.
- `ReaderLibraryTools`: mobile/tablet có nút “Trang x/y” để mở phần trạng thái/lưu vị trí/tải PDF. Có `aria-expanded`, `aria-controls`, Enter mở và Escape đóng/trả focus. Lỗi đọc vẫn ở ngoài vùng thu gọn. Desktop giữ các trường trực tiếp.

## Số đo thực tế

Chromium desktop 1600 × 1000, cùng sách và trạng thái đầu:

| Vùng | Trước | Sau |
| --- | ---: | ---: |
| Header | 104 px | 54 px |
| Thanh vị trí đọc | 64 px | 45 px |
| Mép trên giấy ghi chú | 422,5 px | 270 px |
| Chiều cao vùng ghi chú cuộn | 561,5 px | 723,5 px |
| Mép trên iframe PDF | 297 px | 207 px |
| Chiều cao iframe PDF | 665 px | 770,5 px |

Vùng ghi chú cao hơn khoảng 29%. Mobile 390 × 844: header 52 px, thanh vị trí/chế độ 53 px, giấy bắt đầu ở y=329, vùng ghi chú cuộn cao 509,5 px. Đã kiểm tra thêm 360 × 800 và split hẹp ở 1280 × 800; không tràn ngang.

## Bằng chứng và chạy lại

- RED `dc8ecec`: browser thất bại đúng header 104px vượt mục tiêu ≤60px. GREEN: 139 frontend unit, ESLint, 51 CSS files, Vite build đều đạt.
- Browser **13/13 luồng đạt**, không page error: 4 compact-reader (kích thước, PDF/notes/3D, lưu vị trí/keyboard mobile, split hẹp) + 9 notebook continuation/A4 regression.
- Đã xem ảnh desktop có PDF render thật, mobile đọc và ghi chú. Evidence gitignored `output/playwright/reader-compact/{desktop.png,mobile-notes.png,mobile-pdf.png,browser-evidence.json}` và log cùng thư mục; regression evidence `output/playwright/notebook-continuation/browser-evidence.json`.
- Chạy frontend: `npm run test:unit`, `npm run lint`, `npm run lint:css`, `npm run build -- --emptyOutDir false`. Server QA/DB tạm theo [hướng dẫn notebook](2026-10-31-notebook-continuation.md), rồi chạy tuần tự `node scripts/qa/reader-compact-review.mjs` và `node scripts/qa/notebook-continuation-review.mjs`.
- Không thay backend, không reset DB mặc định, không push/deploy. 116 staged entries sẵn có giữ nguyên. Kiểm chứng Chromium headless/viewport mobile; chưa thử Safari hoặc thiết bị thật. Native PDF toolbar vẫn do trình duyệt quản lý.
