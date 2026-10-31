# 2026-10-31 · Sổ ghi chú tự nối trang

**Status: verified trên workspace.** Yêu cầu: tự thêm trang khi cuộn xuống hoặc khi hết chỗ ghi chú.

- `useBookReaderState`, `BookReaderWorkspace`: cuộn/vuốt xuống gần cuối sẽ thêm một trang phía sau, giữ focus/vị trí viết và bố cục PDF. Chỉ xử lý khi có thao tác người dùng; mount, resize, cuộn lập trình và event lặp không tự sinh chuỗi trang trống. Có thông báo ARIA và hướng dẫn ngắn ở cuối sổ.
- `NotePaper`, `notePaperLayout`, `bookReaderModel`: đo chữ theo khổ giấy/font/padding thực tế, chia phần tràn sang trang tiếp theo, ưu tiên ranh giới dòng/từ; giữ nguyên chuỗi Unicode và khoảng trắng. Dùng lại trang trống liền sau; chèn trước trang đã có chữ/ảnh/nét vẽ, không ghi đè. Con trỏ chuyển đúng vị trí và được đưa vào vùng nhìn thấy. Chờ kết thúc IME mới chia trang.
- Vẽ gần mép dưới tạo sẵn trang tiếp theo sau khi nhấc bút, giữ nét vẽ. Sửa thêm lỗi nút thêm trang thủ công phụ thuộc thời điểm chạy state updater. Dãy số trang cuộn ngang, tự hiện số trang đang chọn, không làm sổ nhiều trang chiếm hết mobile.
- Lưu/đọc lại dùng cơ chế localStorage hiện có; không thay backend/schema hay tự thay dữ liệu notebook cũ khi mở. Không reset DB mặc định, không push/deploy.

## Kiểm chứng

- RED: 5 case model thiếu hành vi, checkpoint `a46956a` trên branch hiện hành. GREEN: 139/139 frontend unit; ESLint và 51 CSS files đạt; build đạt với `--emptyOutDir false` (dist cũ vẫn giữ hash asset trước).
- `scripts/qa/notebook-continuation-review.mjs`: **8/8 browser flows đạt**, không page error. Bao gồm cuộn giữ focus/layout; dán 58 dòng tiếng Việt/emoji và tiếp tục gõ; sửa trang trước không ghi đè trang sau; lưu/mở lại; IME; vẽ cuối giấy; mobile phân trang/active-tab; vuốt qua Chromium CDP thêm đúng một trang trống.
- Chạy lại **9/9 reader studio flows đạt** sau tích hợp nối trang (trước lần tinh chỉnh ưu tiên ngắt dòng và dãy số trang); bản cuối đã chạy lại đủ 8 continuation flows và toàn bộ unit/lint/build/CSS.
- Đã xem ảnh desktop và mobile. Evidence local gitignored: `output/playwright/notebook-continuation/{browser-evidence.json,continued-desktop.png,continued-mobile.png}` và log cùng folder. QA server dùng SQLite/file tạm; không startup jobs, nguồn ngoài có fixture.
- Giới hạn: Chromium headless + viewport mobile/touch qua CDP, chưa kiểm chứng bàn phím/iOS thiết bị thật. IME dùng composition events trong browser. Chưa đo coverage instrumentation; không tuyên bố coverage 80%.

## Chạy lại

Từ `frontend/`: `npm run test:unit`, `npm run lint`, `npm run lint:css`, `npm run build -- --emptyOutDir false`.

Từ repo root, terminal A:
```sh
PYTHON_DOTENV_DISABLED=1 REVIEW_LIVE_SOURCE=1 MPLCONFIGDIR=/tmp/ns-books-mpl .venv/bin/python scripts/qa/usage-review-server.py
```

Terminal B: `node scripts/qa/notebook-continuation-review.mjs`. Server QA tự tạo DB tạm trước import; dừng server khi xong. Nếu cần regression đầy đủ reader: `node scripts/qa/reader-studio-review.mjs`.
