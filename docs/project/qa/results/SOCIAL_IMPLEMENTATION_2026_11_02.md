# Social Intelligence — nghiệm thu 02/11/2026

Status: **verified trên workspace/QA** cho bản Social công khai đầu tiên. Chưa deploy, chưa rebuild/restart localhost:8000. [Hướng dẫn vận hành và giới hạn](../../engineering/SOCIAL.md).

## Kết quả

- Tab News → Social, route `/dashboard-static/news/social`, layout hai cột desktop và chuyển danh sách/chi tiết trên mobile.
- YouTube/Reddit, Việt Nam/quốc tế, tìm chủ đề/mã, 24 giờ/7 ngày, watchlist, lưu bài theo tài khoản, thêm URL, quản lý nguồn. Import thành công tự bookmark, bài cũ vẫn đọc được trong Saved.
- Adapter Agent-Reach 1.6.1 khóa commit `7a38047acf26a729cbb27851e3cb81639da86b29`, environment riêng; public-only. Hàng đợi bền, lease/fencing, hạn mức/retry/backoff; HTTP không gọi provider.
- Trích đoạn có tác giả/link gốc/loại nội dung, phân biệt mô tả/phụ đề; phiên bản nội dung và đối chiếu News đã cache. Không có AI dịch/tóm tắt, sentiment hay chỉ số attention giả.
- Sửa phát hiện qua dữ liệu/browser thật: nhận diện acronym trùng mã; alias BTC-USD; job trùng khác nguồn/phạm vi; bài từ nguồn đã bỏ; stale detail; công tắc nguồn bật lại trong lúc chờ; overflow grid trên 390/320px; scroll chi tiết sau nav; Reddit trả trang bị chặn với HTTP200.

## Kiểm chứng

| Phạm vi | Kết quả / bằng chứng |
| --- | --- |
| Backend Social + News regression | **71 passed**, `output/qa/isolated-tests/20261102T130026Z-4c554ae3/report.json`; cả ba đường DB trỏ temp, dotenv/scheduler tắt |
| Frontend unit toàn bộ | **165 passed**; sau thay đổi cuối chạy lại 3 test Social, đạt |
| ESLint | `npm run lint -- --quiet` đạt |
| CSS | 54 file, 0 lỗi cú pháp; không phải chứng nhận accessibility |
| Vite production build | Đạt, output riêng `output/social-qa/dist` |
| Ruff phạm vi Social | Đạt cho runtime và test Social |
| Browser các luồng chính | 10 nhóm đạt; `output/social-qa/browser-report.json`, không có pageerror |
| Browser khi nguồn lỗi thật | 4 nhóm đạt; `output/social-qa/imported-browser-report.json` |
| Viewport | Chromium 1440×1000, 768×844, 390×844, 320×844; kiểm tra cả document và controls không tràn; chọn bài bằng Enter, nút quay lại, lưu sau reload |
| Detector Impeccable | Chạy một lần trên UI mới, không có findings: `output/social-qa/design-detector.json` |
| Diff whitespace | `git diff --check` đạt |

Browser chạy **auth/API/SQLite thật nhưng DB và tài khoản QA riêng**, không mock feed thành công. Dữ liệu là mẫu công khai đã thu, không phải bài giả. Ca lỗi feed dùng route 503 có nhãn QA để thử retry. Backend unit dùng fixture cho pagination, quyền hai tài khoản, job chết/lease hết hạn, duplicate/revision, URL và trang bị chặn. Không chạy reset DB thật.

## Kết quả nguồn live và giới hạn

Hai lượt probe đều nhận **18 kết quả**: 6 YouTube Việt Nam, 6 YouTube quốc tế và 6 Reddit quốc tế. Mẫu cuối ở `output/social-qa/live-posts.json`, thời gian/câu truy vấn ở `live-probe.json`. Ở mẫu cuối, 12 video nằm trong 7 ngày; 6 bài Reddit cũ hơn cửa sổ này. Query có `after:` không buộc public search tuân thủ ngày; server lọc bằng ngày gốc nên Reddit có thể rỗng.

Thử nhập video công khai lần đầu đọc được metadata trong 8,58 giây, nhưng phụ đề lỗi. Import Reddit từng bị upstream báo `ok` cho trang chặn truy cập; QA phát hiện và adapter đã sửa thành `PLATFORM_BLOCKED`, giữ nội dung cache trước đó. Lượt probe sau sửa ghi nhận **YouTube RATE_LIMITED** (0,22 giây) và **Reddit PLATFORM_BLOCKED** (2,50 giây), không có bài lỗi nào được lưu. Xem `output/social-qa/import-probe.json` và regression `test_reddit_http200_access_gate_is_not_stored_as_content`.

Do đó không tuyên bố Reddit read hoặc phụ đề YouTube hoạt động ổn định. Collector giữ cache, trạng thái lỗi và cooldown, không tự dùng cookie/login hay lách giới hạn nguồn. Import probe từng có assertion yêu cầu luôn thành công; đã sửa script QA để nghiệm thu theo trạng thái thật, và kiểm chứng JSON/bản hiển thị bằng browser thay vì gọi lại nguồn đang giới hạn.

## Review UI cuối

Review Impeccable chạy **trong cùng lượt** theo fallback của skill vì không có công cụ subagent; không phải review độc lập.

`disposition: ship` cho giao diện Social đã kiểm chứng, không phải phê duyệt deploy.

- **persistence:** PRODUCT.md lưu scope người dùng đã chốt; UI tiếp nối News hiện có, không dùng hệ marketing DESIGN.md cho màn đã đăng nhập.
- **fidelity:** tab và accent News giữ nguyên; dòng đọc/chi tiết đúng desktop; mobile chuyển vùng với nút quay lại; trường thiếu có nhãn thật. Không có approved raster comp cho phần mở rộng app này.
- **ceiling:** đủ cho workspace đọc: nội dung/link là trọng tâm, điều khiển nguồn mở theo nhu cầu, không có hero hoặc metrics giả. Mẫu mô tả video vẫn có thể chứa quảng cáo của tác giả; đây chưa phải pipeline trích luận điểm ngữ nghĩa.
- **material_fixes:** không còn lỗi UI chặn các luồng đã thử. Mobile đã sửa overflow và vị trí nút quay lại dưới nav. Safari/iOS thật và kiểm tra accessibility chuyên sâu chưa thực hiện.
- **keep:** giữ attribution, cache đọc được khi lỗi, account scope, source trạng thái thật và bố cục dòng đọc.

Captures: `output/social-qa/desktop.png`, `mobile-390.png`, `mobile-768.png`, `mobile-320.png`, `reader-320.png`, `import-status.png`. Mobile 390 cuối là fresh navigation; captures reader ghi trạng thái đã cuộn vào bài. Không coi full-page failure screenshot trong vòng sửa là ảnh nghiệm thu.

## Chạy lại

```sh
.venv/bin/python scripts/qa/run_isolated_tests.py -- tests/test_social_intelligence.py tests/test_news_intelligence.py tests/test_news_review_fixes.py tests/test_news_agent_phase2.py
```

Frontend: `npm run test:unit`, `npm run lint -- --quiet`, `npm run lint:css`, `npm run build -- --outDir ../output/social-qa/dist` trong `frontend/`.

QA live theo thứ tự: `social-live-probe.py` → `social-review-server.py` → `social-review-browser.mjs` → `social-import-probe.py` → `social-review-imported.mjs` trong `scripts/qa/`. Các script live cần mạng và collector đã cài; nguồn có thể từ chối hoặc trả mẫu khác. Script browser chính giả định seed Reddit cũ như mẫu nghiệm thu nên cần chỉnh assertion theo mẫu mới nếu nguồn đổi. Server QA luôn tạo temp DB trước import ứng dụng. `session.json` là credential của tài khoản QA, ignored và chmod600; không đưa vào commit/report.

Không thay đổi lịch sử DB của người dùng; sự cố DB cũ vẫn nằm trong memory riêng. Không stage/commit/push. Các thay đổi khác vốn có trong working tree được giữ nguyên.
