# Learn Hub — ưu tiên PDF toàn văn

**2026-10-31 · verified trên workspace.** Yêu cầu: người dùng muốn sách PDF đầy đủ, không muốn thư viện hiển thị chủ yếu các bản ghi chú.

## Kết quả

- Tab Sách & Tài liệu mặc định chọn Sách & Giáo trình và **PDF toàn văn**. File ghi chú và PDF mẫu nằm ở lựa chọn **Ghi chú & tài liệu mẫu**; HTML/text vẫn có trong **Tất cả định dạng**.
- Sách PDF thực được xếp trước bản ghi chú. Archive chỉ vào danh sách PDF sau khi xác định định dạng thật; HTML/text không được đếm là PDF.
- Nút chính là **Đọc PDF**; có **Tải PDF** lấy file thật và tab reader **PDF toàn văn**. Ghi chú cá nhân vẫn nằm ở khung bên cạnh.
- Bổ sung ba PDF đầy đủ, nguyên byte từ OpenStax (tiếng Anh): Principles of Finance 2e **629 trang**, Principles of Macroeconomics 3e **635 trang**, Principles of Microeconomics 3e **595 trang**.
- Khi catalog API rỗng, thư viện vẫn có bốn PDF toàn văn sẵn có: ba giáo trình trên và file The Intelligent Investor đã có trong workspace. Không chuyển ghi chú thành PDF để thay cho sách gốc.
- Sửa lỗi 404 của file đi kèm bản build: backend tìm trong data/learning_assets trước, sau đó frontend/dist/learning-assets và frontend/public/learning-assets. Giữ kiểm tra đường dẫn/symlink và HTTP Range của Starlette.
- Những sách chưa có PDF truy cập được không được gán nhãn PDF hoặc thay bằng nội dung tóm tắt trong chế độ PDF.

## Nguồn và file

Các bản tải là ©2026 Rice University / OpenStax, giấy phép **CC BY-NC-SA 4.0** theo trang license của chính bản PDF. Giữ nguyên mọi trang, tác giả, nội dung và attribution. Nguồn, hash, dung lượng và ngày tải nằm trong:

- frontend/public/learning-assets/books/OPENSTAX-SOURCES.md
- frontend/public/learning-assets/books/openstax-pdf-sources.json
- frontend/src/features/learn-hub/content/fullPdfBooks.js

Nguồn chính thức: [Tài chính](https://openstax.org/details/books/principles-finance-2e), [Vĩ mô](https://openstax.org/details/books/principles-macroeconomics-3e), [Vi mô](https://openstax.org/details/books/principles-microeconomics-3e).

## Kiểm chứng

- **120 frontend test đạt**, ESLint, production build và cú pháp 49 file CSS đạt.
- **37 backend test đạt**: bộ reader source và static asset mới. Test mới tái hiện hai lỗi 404 trước sửa, sau sửa kiểm tra được fallback bundle/public, HTTP Range, ưu tiên file người dùng và chặn traversal/symlink ra ngoài.
- **8 luồng browser đạt**, không page error: mặc định chỉ PDF, tải file đúng SHA-256 của nhà xuất bản, mở cả ba sách, bộ lọc ghi chú riêng, lưu/khôi phục ghi chú cá nhân, viewport mobile không tràn ngang.
- Đã đọc PDF bằng parser, xác nhận không mã hóa, số trang và nội dung đầu/giữa/cuối; render ảnh để kiểm tra. Browser hiển thị PDF tài chính với bộ đếm 629 trang. Hash toàn bộ nội dung blob khi mở mỗi cuốn khớp file gốc.
- Coverage logic bookAvailability.js: 99.26% dòng / 87.85% nhánh; bookSource.js: 100% dòng / 92.73% nhánh. Không coi đây là coverage toàn ứng dụng.
- Backend QA tự tạo DB riêng; các lệnh pytest đặt cả RISK_DASHBOARD_DB_PATH và RISK_DASHBOARD_APP_STATE_DB vào /tmp. Không chạy nhóm test reset DB cũ trong lượt này. Đối chiếu 200 dòng catalog đã lưu trước đó vẫn không đổi.
- Evidence: output/playwright/pdf-library/ gồm browser-evidence.json, pdf-source-verification.json, ảnh reader/library/PDF và các log RED/GREEN.

## Chạy lại

Từ repo root:

```bash
npm --prefix frontend run test:unit
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend run lint:css
PYTHON_DOTENV_DISABLED=1 RISK_DASHBOARD_DB_PATH=/tmp/ns-pdf-assets-tests.db RISK_DASHBOARD_APP_STATE_DB=/tmp/ns-pdf-assets-tests.db MPLCONFIGDIR=/tmp/ns-pdf-mpl .venv/bin/python -m pytest tests/test_learning_asset_files.py tests/test_book_source_availability.py -o addopts='' -q
```

Browser: khởi động scripts/qa/usage-review-server.py (DB tạm) và đợi port 5186 sẵn sàng, sau đó chạy node scripts/qa/pdf-library-review.mjs. Dừng server QA sau khi browser kết thúc.

RED checkpoints: e6d018c (4 frontend cases), 1bbcbe1 (2 lỗi asset 404). GREEN checkpoint chỉ chọn file của tác vụ; BookDocumentPane đang có thay đổi từ trước được giữ trong working tree. Không stage công việc sẵn có khác; 116 mục staged được giữ nguyên. Không push/deploy.
