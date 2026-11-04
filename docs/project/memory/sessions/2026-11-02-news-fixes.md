# News fixes — 2026-11-02

Status: **verified trên workspace/QA**, chưa triển khai localhost:8000. Theo yêu cầu “thực hiện fix”. Khép lại NR-01–NR-07 của [review 01/11](2026-11-01-news-review.md).

## Hiện trạng và quyết định đã áp dụng

- Đối sánh tiếng Việt giữ dấu; cache tự re-enrich một lần qua `app_kv.news_classification_v2`. Chuẩn hóa không dấu vẫn dùng cho search/gom nhóm.
- Sentiment hỗ trợ từ khóa VN, phủ định/ngữ cảnh hạn chế, trả `unknown` khi không đủ căn cứ. API/UI/agent chấp nhận unknown, method `keyword_rules_v2`. Không gọi AI; chưa có đánh giá độ chính xác trên tập dữ liệu gán nhãn.
- Điểm canonical được lưu khi cập nhật; filter trước page. Cursor dùng bảng `news_feed_snapshots` (migration020), snapshot cố định 15 phút, cap256. UI tải24 tin/trang; cursor410 tự tải lại. Không dùng offset trên bảng đang đổi thứ hạng.
- Poll60s khi visible, focus/visibility/manual refresh; chống stale response. Khi đã tải nhiều trang, giữ nguyên danh sách đang đọc, chỉ báo cập nhật nếu nội dung thay đổi. Retry phân biệt trang đầu/trang tiếp; dữ liệu nguồn lỗi có thời điểm cũ đúng.
- Nổi bật toàn cầu độc lập được ghi rõ, thu gọn3desktop/1mobile; nâng cao đóng được dù đang lọc. Learn Hub resolve9concept thành bài thật, hỗ trợ URLcũ; mở đúng lesson. Mobile chọn bài cuộn đến đầu phần đọc.

## Kiểm chứng

[Report chi tiết và giới hạn](../../qa/results/NEWS_FIXES_2026_11_02.md). **61 backend** (42 news +19 agent), **159 frontend**, lint/CSS52/build/Ruff phạm vi đạt. Chromium12luồng chính+7phục hồi+2viewport visual; ảnh cuối đã xem, không tràn320/390/768/1440. Hạ Dòng tin xuống y630desktop/y768mobile so với1241/1689.

QA dùng bản sao711 publicnews, chỉ4bảng; đối chiếu nguyên văn/thời điểm giữ nguyên. VN370tin sau phân loại: positive57/negative20/neutral5/unknown288. Nguồn live không được gọi khi test refresh: producer kiểm soát; auth browser giả lập. Không reset/ghi DB live. Fixture test ngày VN sửa để chạy được sát00:00.

## Còn lại/giới hạn

- Source đã sửa; dịch vụ localhost:8000 chưa rebuild/restart. Migration/backfill thật chưa chạy, sẽ chạy khi vận hành source mới.
- Rule-based sentiment có thể thiếu ngữ cảnh; chưa kiểm chứng Safari/iOS và provider live. Không mở rộng sửa auth/saved-news.
- Staging SHA-256 giữ nguyên `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`. Không stage/commit/push/deploy.
