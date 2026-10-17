# Nghiên cứu repository cho tab News

Ngày rà soát: 2026-09-28

## Mục tiêu

Tab News cần lấy dữ liệu từ nguồn thật, cập nhật gần thời gian thực, chống trùng bài, hiển thị đúng nguồn và không biến ảnh minh họa thành ảnh gốc của bài viết. Các repository dưới đây được dùng để đối chiếu kiến trúc và chọn các phần có thể đưa vào Northstar mà không làm mất provenance của tin.

## Các repository đã rà soát

| Repository | Mẫu thiết kế đáng dùng | Quyết định cho Northstar |
| --- | --- | --- |
| [`lanyasheng/ai-news-aggregator`](https://github.com/lanyasheng/ai-news-aggregator) | Nhiều RSS chạy song song; cache `ETag`/`Last-Modified`; lọc theo ngày; phân loại nguồn; chấm điểm quan tâm; giới hạn số bài mỗi nguồn; dedup URL qua nhiều ngày. | Đã áp dụng conditional request ở `NewsRssProducer`, thống kê nguồn trả `304`, và giữ logic phân loại/dedup hiện có của Northstar. |
| [`finaldie/auto-news`](https://github.com/finaldie/auto-news) | Hợp nhất RSS và các kênh khác; lọc nhiễu; recap định kỳ; pipeline pull → dedup → ranking → publish; có lịch chạy backend. | Dùng làm mẫu cho source catalogue, ranking và lịch backend. Không đưa LLM rewrite vào lớp lưu bài vì Northstar phải mở bài gốc và giữ văn bản/ảnh theo nguồn. |
| [`fabriziosalmi/UglyFeed`](https://github.com/fabriziosalmi/UglyFeed) | Nhóm bài tương đồng bằng TF-IDF/cosine similarity/DBSCAN; pipeline retrieve → aggregate → evaluate; có tùy chọn rewrite bằng LLM. | Northstar đã có clustering/dedup riêng; chỉ giữ ý tưởng nhóm các bài cùng sự kiện. Không rewrite headline hoặc thay ảnh gốc tự động trong feed chính. |
| [`nirholas/cryptocurrency.cv`](https://github.com/nirholas/cryptocurrency.cv) | API crypto nhiều nguồn, archive, category/search, RSS/Atom, SSE/WebSocket và widget. | Chỉ là nguồn tham khảo cho nhánh Crypto mở rộng. Chưa thêm dependency bên ngoài để kiểm soát license, độ ổn định và provenance nguồn. |

## Những gì đã áp dụng

### Conditional RSS fetch

`NewsRssProducer` giữ XML thành công gần nhất theo URL trong worker process. Nếu nguồn trả `ETag` hoặc `Last-Modified`, lần poll kế tiếp gửi `If-None-Match`/`If-Modified-Since`. Với `304 Not Modified`, producer parse lại XML đã cache và đi qua cùng pipeline enrichment, scoring, dedup và lưu SQLite như một lần fetch thành công.

Metadata của `news_fetch_runs` có thêm:

- `conditional_request_count`: số nguồn đã nhận validator;
- `not_modified_count`: số nguồn trả `304`.

API feed trả hai giá trị này trong `http_cache`. Tab News hiển thị trạng thái như `19/19 nguồn RSS · 9 nguồn không đổi`, giúp phân biệt kiểm tra nguồn thật với dữ liệu mock hoặc chỉ đổi timestamp.

### Nhịp cập nhật

- Backend cache bài đã lưu: mặc định 60 giây, cấu hình bằng `NEWS_CACHE_TTL_SECONDS` và không thấp hơn 15 giây.
- UI: poll mỗi 30 giây khi tab đang visible, dừng khi tab bị ẩn và đồng bộ lại khi quay lại.
- Nút `Làm mới`: buộc backend chạy refresh ngay.

RSS không phải giao thức push đồng nhất, nên đây là near-real-time. Nguồn nào có ETag/Last-Modified sẽ được kiểm tra liên tục mà không tải lại nguyên XML; nguồn nào không hỗ trợ vẫn được poll và parse bình thường.

### Provenance của bài và hình ảnh

Producer chỉ lấy ảnh từ các trường RSS/Atom hợp lệ: Media RSS, thumbnail, enclosure ảnh, `image/url`, HTML `img` và `og:image` trong nội dung feed. URL được kiểm tra scheme/http và canonical hóa trước khi lưu.

Frontend ưu tiên `article.image_url`. Chỉ khi RSS không có ảnh hoặc ảnh không tải được mới dùng ảnh fallback theo chủ đề; adapter gắn `image_origin: "source"` hoặc `"topic_fallback"`, còn detail hiển thị rõ `Ảnh: từ nguồn tin` hay `Ảnh: minh họa theo chủ đề`. Mọi bài vẫn có source và nút mở URL gốc.

## Giới hạn vận hành

HTTP validator hiện ở memory của từng worker, còn bài viết và trạng thái nguồn nằm trong SQLite. Sau khi process restart, lần fetch đầu tiên của mỗi worker có thể tải đầy đủ một lần. Nếu triển khai nhiều worker và muốn dùng validator chung, chuyển `_FEED_HTTP_CACHE` sang Redis hoặc thêm bảng cache HTTP có khóa theo source URL; không cần thay đổi contract API/UI.

Một số nguồn, như các feed Bloomberg hiện tại, không gửi ảnh trong RSS. Khi đó UI dùng ảnh chủ đề và đánh dấu đó là ảnh minh họa; không tự nhận đó là ảnh từ bài gốc.

## Kiểm tra

- `npm run lint` — pass.
- `npm run test:unit -- --testPathPattern=newsAdapter` — 3/3 pass.
- `npm run build` — pass; Vite chỉ còn cảnh báo chunk lớn hiện hữu.
- `PYTHONPATH=src pytest -q tests/test_news_optimization.py` — 9/9 pass, gồm test 200 → 304 → dùng XML cache.
- `PYTHONPATH=src python3 -m compileall -q src/risk_dashboard/modules/news_intelligence src/risk_dashboard/platform/database` — pass.
- API live: `19/19` nguồn thành công; lần refresh kiểm chứng trả `conditional_request_count=10`, `not_modified_count=9`.

