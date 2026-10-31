# Learn Hub: kiểm tra nguồn và đọc sách

**2026-10-31 · verified trên workspace hiện tại.** Phạm vi: tab Sách & Tài liệu, nguồn sách, PDF/HTML/text và ghi chú khi đọc. Không bao gồm kiểm chứng nội dung học thuật hoặc mọi paper/video trong catalog.

## Những thay đổi

- Thư viện kiểm tra nguồn trên trang đang xem, hiển thị trạng thái và giờ kiểm tra; có lọc nguồn, kiểm tra lại toàn bộ danh sách đã tải, phân trang 12 mục và loại trùng URL nguồn. Mỗi batch chạy ba worker, hủy batch khi chuyển trang; cache thành công 5 phút, trạng thái khác 1 phút.
- Reader kiểm tra HTTP, định dạng và kích thước trước khi tạo iframe; kiểm tra dấu kết thúc PDF sau tải. Lỗi 404/403/503, MIME sai và file thiếu không còn bị biến thành HTTP 200/trang thành công. Lỗi tải toàn bộ cập nhật lại cache thư viện; vẫn dùng được tóm lược và ghi chú.
- Archive: đọc metadata để tìm file thật; phân biệt mất mục, hạn chế mượn sách, lỗi kết nối, nhiều file không rõ cuốn cần đọc và không có bản công khai phù hợp. Bỏ file private/encrypted, trang PDF rời trong thư mục và file trên 40 MiB. Trường hợp nhiều file phù hợp dẫn đến trang nguồn để người dùng tự chọn.
- Bỏ ghép đoán `<identifier>.pdf` trong crawler; Gutenberg ưu tiên HTML trước EPUB. Không tự biến HTML/EPUB hoặc `file_name` thành PDF, không gán file local bằng cách đoán từ tiêu đề.
- Sửa ba liên kết bài ghi chú `.pdf` thành `.html` thực sự có trong repo. Nhãn bài ghi chú/tài liệu mẫu tách rõ khỏi sách đầy đủ; không dùng số trang của sách đầy đủ cho bài ghi chú.
- The Wealth of Nations đã chuyển từ mục Archive bị hạn chế sang [bản HTML Project Gutenberg](https://www.gutenberg.org/cache/epub/3300/pg3300-images.html); probe API và luồng đọc HTML thật qua backend QA đều đạt.
- Proxy chỉ cho các host được cho phép, kiểm tra DNS public và từng redirect trước khi gửi request; giới hạn file 40 MiB, metadata 4 MiB và ngân sách đọc metadata 10 giây. HTML đọc trong iframe sandbox, CSP chặn script/tài nguyên chủ động.

## Bằng chứng

- Frontend: **116/116 test đạt**, ESLint, production build và kiểm tra cú pháp **49 file CSS đạt**.
- Backend: **65/65 test trong nhóm liên quan đạt**; coverage dòng của `reader_proxy.py`: **88%**. Nhóm này gồm nguồn sách, crawler, learning, remediation, usage fixes và hồi quy reader.
- Coverage logic nguồn frontend: `bookSource.js` **100% dòng**, `bookAvailability.js` **99.16% dòng**; nhánh tương ứng **90.74% / 85.71%**. Không suy diễn đây là coverage toàn bộ ứng dụng.
- Browser: **10 luồng đạt**, không có page error: loại trùng/phân trang, kiểm tra hàng loạt/lọc trạng thái, mất nguồn/lưu ghi chú/thử lại phục hồi, hạn chế truy cập, 404 khi tải, HTML giả PDF, PDF local, HTML note sandbox, Gutenberg live, desktop/mobile.
- PDF được thử thêm qua một lượt smoke riêng không mock network (`reader-pdf-native-no-fixtures.png`, `reader-pdf-native.log`) bằng Chromium đầy đủ (`channel: chromium`), có render trang PDF và thanh công cụ native; headless shell mặc định không có PDF viewer. Đã xem ảnh thư viện và reader ở 1440×1000 và 390×844.
- Test lỗi ngoài có fixture để tái hiện ổn định. Đợt audit nguồn thật riêng kiểm tra metadata và prefix, không tải toàn bộ mọi sách. Trạng thái live phản ánh thời điểm chạy, không bảo đảm nguồn luôn còn.

Audit live 124 URL duy nhất trong 120 dòng catalog đã tải cộng 8 sách featured (loại trùng URL), ngày 31/10/2026: **59 nguồn có nội dung đọc**, **36 hạn chế truy cập**, **12 không còn tại nguồn**, **8 chưa kết nối được**, **9 phải chọn/xem tại nguồn**. 59 bao gồm 4 file local và 55 nguồn remote; chỉ xác nhận metadata/prefix. Đây là tập URL **trước sửa**, nên vẫn gồm link Archive cũ của Wealth of Nations; nguồn Gutenberg thay thế được kiểm tra riêng. Không cộng kết quả trước/sau thành số sách đã khôi phục.

Evidence local: `output/playwright/book-reader-audit/`: `sources-before.json`, `sources-after.json`, `gutenberg-replacement.json`, `browser-evidence.json`, các ảnh `library-*.png`, `reader-*.png` và log RED/GREEN.

## Sự cố trong lần chạy test mở rộng đầu

Lần chạy đầu thiếu biến DB tạm; các test cũ trong `test_learning.py` và `test_learning_remediation.py` gọi `reset_app_state_tables()` trên DB mặc định. Các bảng trạng thái được reset bởi helper này (onboarding/learning/news/goals/legacy portfolio/community/pro-lab/CMS/analytics...) có thể mất trạng thái đã có. Không có snapshot trước chạy để xác định chính xác số bản ghi bị ảnh hưởng. Một lần chạy còn gặp `sqlite3.OperationalError: disk I/O error`; không tính lần đó là đạt.

Đã thêm fixture DB riêng theo `tmp_path` vào hai module test này và chạy lại toàn bộ nhóm thành công trên DB tạm. Script audit cũng cô lập DB của bootstrap. Đã đối chiếu **200 bản ghi sách lưu trước lượt làm việc: không bản ghi nào thay đổi**. Ghi chú reader nằm trong localStorage; các lệnh SQL reset không xóa localStorage.

Bản `data/db/northstar.db.bak` ngày 10/10 thiếu các bảng trạng thái liên quan, không đủ để khôi phục chính xác. Snapshot bảo toàn hiện trạng sau khi phát hiện được lưu tại `.local-dev/qa-backups/2026-10-31-post-test-reset.db`; đây **không phải** bản trước sự cố. Người dùng xác nhận **không có bản sao lưu mới hơn**. Việc khôi phục vẫn **chưa giải quyết**; chưa tự ghi đè DB bằng bản cũ. Thử SQLite `.recover` trên bản sao riêng tạo `.local-dev/qa-backups/2026-10-31-offline-recovery.db`: không tìm thêm bản ghi trong các bảng có tên, chỉ thêm 28.159 dòng `lost_and_found_1` chưa xác định bảng/niên đại. Không nhập các dòng này vào DB đang dùng; chưa thể coi là khôi phục trạng thái. Chi tiết số lượng theo bảng: `output/playwright/book-reader-audit/db-test-impact.json`.

## Chạy lại

Từ repo root:

```bash
PYTHON_DOTENV_DISABLED=1 MPLCONFIGDIR=/tmp/ns-books-mpl RISK_DASHBOARD_APP_STATE_DB=/tmp/ns-books-tests.db .venv/bin/python -m pytest tests/test_book_source_availability.py tests/test_reader_proxy.py tests/test_logic_review_regressions.py tests/test_usage_fixes.py tests/test_learning.py tests/test_learning_crawlers.py tests/test_learning_remediation.py --cov=risk_dashboard.modules.learning.api.reader_proxy --cov-report=term-missing -o addopts='' -q
npm --prefix frontend run test:unit
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend run lint:css
```

Browser dùng DB tạm do script server tự tạo, không khởi động scheduler:

```bash
PYTHON_DOTENV_DISABLED=1 MPLCONFIGDIR=/tmp/ns-books-mpl .venv/bin/python scripts/qa/usage-review-server.py
# Terminal khác, sau khi server lắng nghe 5186:
REVIEW_LIVE_SOURCE=1 node scripts/qa/book-reader-review.mjs
```

Audit chỉ đọc các URL từ JSON; input có thể là list book hoặc `{books:[...]}`:

```bash
PYTHON_DOTENV_DISABLED=1 .venv/bin/python scripts/qa/audit-book-sources.py output/playwright/book-reader-audit/sources-before.json output/playwright/book-reader-audit/sources-after.json
```

## Giới hạn và phạm vi Git

Catalog UI vẫn lấy tối đa 120 sách từ API cộng sách featured. Nút kiểm tra toàn bộ áp dụng cho danh sách này. Không xoá item chết khỏi DB; nguồn có thể phục hồi và ghi chú cũ cần giữ định danh. PDF viewer phụ thuộc hỗ trợ PDF của trình duyệt; luôn có nút mở tại nguồn. Probe prefix xác nhận khả năng truy cập/định dạng sơ bộ, không chứng minh đúng nội dung học thuật hoặc tính toàn vẹn mọi trang.

Các checkpoint RED nằm trên nhánh đang làm (`7c9de32`, `390331f`, `286d29e`, `0cba157`). Checkpoint GREEN chỉ chọn file của tác vụ. Các file reader/content/proxy đã có thay đổi hoặc untracked trước lượt này được giữ trong working tree; không đưa toàn bộ thay đổi trước đó vào checkpoint. 116 mục staged sẵn có được bảo toàn (hash index đã đối chiếu). Kết quả áp dụng **workspace hiện tại**, không coi checkout riêng checkpoint là bản phát hành hoàn chỉnh. Chưa push/deploy.
