# Reader studio · 31/10/2026

**Status: verified trên workspace.** Thiết kế lại màn đọc PDF và ghi chú theo yêu cầu ảnh tham chiếu; dùng Three.js thật để tạo chiều sâu.

## Thay đổi

- Giao diện graphite/sage, khung PDF nổi và giấy ghi chú màu ngà có lề, dòng kẻ, bóng nhiều lớp. Toolbar gom trạng thái đọc, lưu trang và chế độ xem.
- Desktop mở song song, có chế độ chỉ sách hoặc chỉ ghi chú. Mobile dùng từng khung, không cuộn ngang. Đổi bố cục giữ nguyên iframe PDF và nội dung ghi chú.
- Thanh chia hỗ trợ kéo, phím mũi tên, Home/End, nhấp đúp để về 56%; lưu tỷ lệ và công bố vị trí qua ARIA.
- Chồng sách 3D: geometry, ánh sáng, bóng đổ và phản hồi con trỏ. Engine tải khi bật 3D, DPR tối đa 1,5; chỉ render khi cần, tôn trọng reduced motion, giải phóng GPU khi tắt/đóng. Có biểu tượng thay thế khi thiếu WebGL/mất context. Preference lưu local.
- PDF mở vừa chiều ngang, ẩn mục lục native ban đầu; vị trí đọc vẫn là trang người dùng nhập và lưu thủ công, không tự suy đoán từ iframe.

## Bằng chứng

| Kiểm chứng | Kết quả |
| --- | --- |
| RED UI contract | 4 lỗi đúng tính năng còn thiếu; checkpoint `5147d93` |
| Frontend unit sau sửa | 134/134 đạt, gồm 4 case mới |
| ESLint / CSS | Đạt; 51 CSS files hợp lệ |
| Vite build | Đạt với `--emptyOutDir false` |
| Browser reader mới | 9/9 đạt; không có page error |
| Browser kệ sách regression | 12/12 đạt; không có page error |

9 luồng reader gồm: draw call WebGL thật và idle render budget; chuyển bố cục không mất state; splitter bằng chuột/phím; toggle giải phóng context và nhớ lựa chọn; bút/tẩy/thêm trang; lưu/đọc lại notes và trang PDF; reduced motion/context loss; mobile; browser không WebGL.

12 luồng kệ sách kiểm tra upload PDF, dedupe, tài liệu thiếu không tính đã đọc, trạng thái/lưu trang, resume/tải nguyên byte, lọc/lịch sử, catalog/sửa tên, đăng nhập lại, cách ly tài khoản, mobile upload/đọc/xóa, PDF lỗi và xác nhận xóa.

Đã xem trực tiếp ảnh desktop 1600×1000 và mobile 390×844. Evidence local (gitignored): `output/playwright/reader-studio/{browser-evidence.json,reader-desktop.png,reader-mobile.png,notes-mobile.png,fallback-desktop.png}` và `output/playwright/personal-library/browser-evidence.json`.

## Chạy lại

Tại `frontend/`:

```sh
npm run test:unit
npm run lint
npm run lint:css
npm run build -- --emptyOutDir false
```

Từ repo root, terminal A chạy server QA **tự tạo SQLite tạm trước import app**:

```sh
PYTHON_DOTENV_DISABLED=1 REVIEW_LIVE_SOURCE=1 MPLCONFIGDIR=/tmp/ns-books-mpl .venv/bin/python scripts/qa/usage-review-server.py
```

Terminal B chạy tuần tự:

```sh
node scripts/qa/reader-studio-review.mjs
node scripts/qa/personal-library-review.mjs
```

Dừng server QA sau kiểm tra. Không dùng/reset DB mặc định. Không gọi startup jobs; nguồn ngoài được chặn/fixture trong browser review. Reader dùng PDF OpenStax local thật; upload regression dùng PDF QA được sinh riêng.

## Giới hạn

- Kiểm chứng trên Chromium headless (WebGL2/SwiftShader) và viewport mobile; chưa kiểm chứng Safari/iOS thật hoặc GPU thiết bị thật. Không tuyên bố chứng nhận accessibility hay coverage 80%; chưa thu coverage instrumentation cho lượt UI này.
- Build mặc định gặp `ENOTEMPTY` khi dọn thư mục dist đang có asset. Build với `--emptyOutDir false` hoàn tất và toàn bộ browser QA chạy trên bundle mới; asset hash cũ vẫn còn trong dist.
- Không đổi backend/schema, không thêm dependency, không push/deploy. Tree đã có nhiều thay đổi trước lượt này; kết quả xác nhận workspace kết hợp hiện tại, không phải checkout sạch của checkpoint UI riêng.
