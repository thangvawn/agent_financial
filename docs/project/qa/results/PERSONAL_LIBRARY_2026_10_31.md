# Kệ sách cá nhân và upload PDF — 31/10/2026

**Status: verified trên workspace.** Người dùng yêu cầu thêm sách, paper, tài liệu từ máy và quản lý các sách từng đọc theo user. Chưa push/deploy.

## Chức năng đã có

- Learn Hub → **Sách & Tài liệu → Thêm tài liệu**, hoặc tab **Kệ sách của tôi**. Chọn một PDF, nhập tên/tác giả, phân loại Sách / Paper / Tài liệu.
- Upload tối đa **40 MiB/file**, **500 MiB/tài khoản**, **1.000 tài liệu/kệ**. File phải là PDF đầy đủ, đọc được, không khóa mật khẩu. PDFium xác định số trang; không nhận file chỉ đổi đuôi thành PDF. Nhận diện trùng nội dung trong cùng tài khoản và giữ nguyên trạng thái/metadata bản đã có.
- Tài liệu tải lên là riêng tư. UUID làm tên file, không dùng đường dẫn do client gửi; file nằm trong `learning_library_files/` cạnh DB đang cấu hình, ngoài mọi static mount. Folder/file dùng quyền 0700/0600. Thư mục này được Git ignore; data cũng đã nằm trong Docker ignore.
- Từ thư viện, **Thêm vào kệ** lưu tham chiếu sách/paper. Không sao chép tài liệu công khai vào kho upload.
- Kệ có tìm kiếm, lọc loại tài liệu, trạng thái **Muốn đọc / Đang đọc / Đã đọc**, sửa tên/tác giả/loại, xóa có xác nhận.
- **Lịch sử đọc** liệt kê tài liệu từng mở thành công, thời điểm gần nhất và số lượt mở. Nội dung mở lỗi không tạo lượt đọc; tải lại request cùng event ID không đếm đôi. Mỗi lần mở reader là một lượt, đổi chế độ tài liệu/ghi chú trong cùng reader không tăng thêm.
- Reader có trạng thái đọc và ô **Trang đang đọc → Lưu vị trí**. **Đọc tiếp** mở PDF ở trang đã lưu. Đây là vị trí người dùng nhập/lưu, không tự theo dõi thao tác cuộn của trình xem PDF native.
- Kệ, lịch sử và vị trí đọc lưu theo **account_id**, tồn tại qua reload/phiên đăng nhập mới. Tính năng bắt đầu ghi nhận từ các lần mở sau cập nhật; không suy đoán hoặc khôi phục lịch sử cũ.
- Bản upload được đọc/tải qua Bearer auth, giữ nguyên byte. Không đặt token trong URL. Paper arXiv dạng `/pdf/ID` không cần đuôi `.pdf` cũng đi vào luồng reader.

## API và lưu trữ

Prefix: `/api/v1/public/learning/library`. Toàn bộ endpoint dùng `resolve_principal`, không nhận anonymous/query-session làm chủ sở hữu.

| Endpoint | Hành vi |
|---|---|
| GET `/` | Danh sách riêng, quota, no-store |
| POST `/uploads` | Multipart file/title/author/kind; 201 mới, 200 trùng |
| POST `/items` | Lưu tham chiếu catalog, idempotent theo nguồn |
| GET/PATCH/DELETE `/items/{id}` | Đọc/sửa/xóa tài liệu thuộc account |
| POST `/items/{id}/open` | Event idempotent, cập nhật trạng thái/lịch sử |
| GET `/items/{id}/file.pdf` | Chỉ chủ sở hữu; hỗ trợ HTTP Range, no-store |

SQLite thêm hai bảng `learning_library_items`, `learning_library_events` bằng `CREATE TABLE IF NOT EXISTS`, không reset bảng cũ. Quota và dedupe chạy trong transaction `BEGIN IMMEDIATE`. Request upload được xác thực trước khi parse, chặn Content-Length và tổng byte stream; giới hạn số multipart file/field. File tạm được dọn khi lỗi. Muốn sao lưu đầy đủ cần sao lưu **DB và thư mục `learning_library_files/` đi cùng**.

## Bằng chứng

- RED đầu: 25 API và 3 UI thất bại đúng vì chưa có tính năng (checkpoint `438a457`). RED bổ sung: HTTP 413 cho multipart stream quá lớn và arXiv PDF không đuôi (checkpoint `4209009`).
- **130 frontend unit**, **69 backend** trong phạm vi (32 case kệ cá nhân + 37 regression nguồn/asset PDF), tất cả đạt.
- Coverage backend mới **99% statement**; `personalLibraryApi.js` **100% line / 98.11% branch**. Đây không phải tuyên bố coverage toàn bộ giao diện/backend.
- ESLint, CSS syntax **50 file**, build frontend và Ruff ba module Python mới đều đạt. Hai warning NumPy reload xuất hiện trong pytest; không có test lỗi/bỏ qua.
- **12 browser flows** đạt với API upload/library/file/auth thật và SQLite riêng: upload paper, file trùng, nguồn mở lỗi không thêm lịch sử, đọc/lưu trang/đã đọc, đọc tiếp/tải nguyên bản SHA-256, bộ lọc, thêm catalog/sửa metadata, reload/đăng nhập mới, cách ly account, upload/đọc tài liệu trên mobile, file hỏng/thử lại, xác nhận xóa file.
- Đã xem ảnh desktop 1440×1000 và mobile 390×844; native PDF hiển thị nội dung. Không có page error hoặc overflow ngang trong các luồng đã kiểm tra. Không chứng nhận mọi trình duyệt/a11y.
- Kiểm tra hồi quy thêm **8 luồng PDF công khai/ghi chú hiện có** đều đạt; tổng **20 luồng trình duyệt**. Log `pdf-regression.log` trong thư mục evidence.
- [Script dùng thử](../../../../scripts/qa/personal-library-review.mjs) tự tạo PDF fixture, không dùng file cá nhân. Browser evidence/screenshot/log: `output/playwright/personal-library/` (gitignored). Catalog và nguồn ngoài được fixture để kiểm tra tập trung; quyền truy cập/upload/lưu/đọc file cá nhân không mock.

## Chạy lại an toàn

Chỉ dùng DB thử riêng, bật `PYTHON_DOTENV_DISABLED=1` trước import backend. Không chạy test legacy reset state vào DB mặc định.

```sh
PYTHON_DOTENV_DISABLED=1 RISK_DASHBOARD_DB_PATH=/tmp/northstar-shelf-tests.db RISK_DASHBOARD_APP_STATE_DB=/tmp/northstar-shelf-tests.db MPLCONFIGDIR=/tmp/northstar-shelf-mpl .venv/bin/python -m pytest tests/test_personal_library.py tests/test_learning_asset_files.py tests/test_book_source_availability.py -o addopts='' -q
npm --prefix frontend run test:unit
npm --prefix frontend run lint
npm --prefix frontend run lint:css
npm --prefix frontend run build
```

Browser: khởi động `scripts/qa/usage-review-server.py` (tự tạo DB riêng, port 5186, tắt startup jobs), rồi `node scripts/qa/personal-library-review.mjs`; dừng server sau dùng thử. Playwright Chromium phải sẵn có. `pypdfium2` đã có trong dependency dự án; lượt này cài vào `.venv` để chạy validator.

## Phạm vi giữ nguyên

- Định dạng upload hiện tại là PDF; không tự chuyển DOCX/EPUB hoặc tạo bản tóm tắt thay sách.
- Ghi chú notebook hiện có vẫn giữ cơ chế lưu của reader; kệ/lịch sử không tuyên bố đồng bộ notebook.
- Kiểm chứng chỉ chạy trên DB/thư mục upload tạm. Không reset DB mặc định, không thực hiện khôi phục dữ liệu. Sự cố reset trạng thái được ghi trong đợt trước vẫn unresolved.
- Giữ nguyên 116 mục staged trước tác vụ. Các file reader/source đã dirty hoặc untracked từ trước tiếp tục được giữ trong workspace; không gom toàn bộ thay đổi sẵn có vào commit mới.
