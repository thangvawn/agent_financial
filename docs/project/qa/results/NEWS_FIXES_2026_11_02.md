# Sửa trang Tin tức — 02/11/2026

**Trạng thái: verified trên source, DB tạm và Chromium.** Thực hiện theo yêu cầu “thực hiện fix”, khép lại NR-01–NR-07 trong [review trước](NEWS_REVIEW_2026_11_01.md). Chưa rebuild/restart dịch vụ đang phục vụ localhost:8000; chưa deploy/push.

## Kết quả

| ID | Bản sửa | Kiểm chứng |
| --- | --- | --- |
| NR-01 | Giữ dấu khi đối sánh từ khóa; chuẩn hóa bỏ dấu chỉ phục vụ tìm kiếm/gom nhóm. Tự phân loại lại cache một lần, có marker phiên bản. | Bài Hải Phòng đầu tư công không còn thuộc Hàng hóa/Oil; kiểm tra cả “dầu” thật. |
| NR-02 | Hỗ trợ từ khóa tiếng Việt, phủ định, một số ngữ cảnh tăng/giảm không thể suy ra sắc thái. Thêm `unknown`, phân biệt với trung tính; UI bỏ nhãn AI; adapter agent giữ nguyên `unknown`. | Trong 370 tin VN sao chép: 57 tích cực, 20 tiêu cực, 5 trung tính, 288 chưa xác định. Test phủ định, lạm phát/chi phí và schema agent. |
| NR-03 | Chấm điểm canonical khi cập nhật dữ liệu; lọc importance trước phân trang. Điểm không thay đổi chỉ vì tìm kiếm một tập tin khác. | API fixture có 70 tin low ngoài 90 tin ưu tiên: trả đúng 70. Dữ liệu thật trả 316 tin low; tìm riêng/detail giữ cùng điểm. |
| NR-04 | API cursor theo snapshot cố định; 24 tin/trang ở UI; tổng tin, has_more, tải thêm thật. Snapshot tồn tại 15 phút, tối đa 256; hết hạn trả 410 và UI tải lại. | Backend đọc đủ 160 tin không trùng dù đổi thứ hạng DB giữa chừng. Browser đọc 96 tin qua 3 request cursor. |
| NR-05 | Ánh xạ 9 concept tới bài học hiện có, dùng tên bài thật. Learn Hub hiểu `course`/`lesson` và tương thích `concept` cũ. | Nhấn từ bài tin và mở URL `concept=oil_inflation` đều vào bài CPI, không dừng tại danh mục/khởi đầu khóa. |
| NR-06 | Hiển thị thời điểm dữ liệu thực, số nguồn và trạng thái cũ/thiếu nguồn. Lỗi toàn bộ nguồn không thay thời điểm lần cập nhật thành công. | Browser mô phỏng stale/503; giữ dữ liệu cũ có thông báo. Đổi bộ lọc lỗi không giữ nhầm kết quả bộ lọc trước. |
| NR-07 | Tự cập nhật 60 giây khi tab hiển thị, khi quay lại tab, và nút thủ công. Hủy/chặn phản hồi cũ. Khi đã tải nhiều trang, báo có thay đổi thay vì xáo danh sách đang đọc. | Poll/focus/visibility, tab ẩn, phản hồi đến chậm, cập nhật không thay đổi, cập nhật có tin mới, retry trang đầu/trang sau. |

UI bổ sung: nổi bật ghi rõ phạm vi toàn cầu, độc lập với bộ lọc; thu gọn còn 3 tin desktop/1 tin mobile và mở rộng đủ 8 tin. Panel nâng cao đóng được khi đang lọc. Việt hóa nhãn thị trường/sắc thái/ưu tiên; đổi phần giải thích chung thành “Thông tin phân loại”. Mobile chọn bài tự đưa phần đầu bài đọc vào màn hình.

## Mã nguồn chính

- Backend: `modules/news_intelligence/{domain/text.py,application/enrichment.py,application/services.py,application/feed_pagination.py,api/public.py,schemas/models.py,agent_tools/enrichment_tool.py}` trong `src/risk_dashboard/`.
- Migration bổ sung: `platform/database/migrate.py`, `020_news_feed_snapshots`. Không xóa bảng/bản ghi sách hay trạng thái người dùng.
- Frontend: `features/news/pages/NewsPage.jsx`, hooks `useNewsFeed/useNewsAutoRefresh/useNewsHighlights`, các component tin, `newsLabels.js`, service `newsApi.js`.
- Deep link: `features/learn-hub/content/newsLessonLinks.js`, `LearningHomePage.jsx`, `CoursePlayerPage.jsx`.

## Kiểm chứng và cách chạy lại

- 42 backend tests news/regression đạt với DB tạm tự dọn:
  `.venv/bin/python scripts/qa/run_isolated_tests.py -- tests/test_news_review_fixes.py tests/test_news_intelligence.py tests/test_news_optimization.py -q`.
  [Report](../../../../output/qa/isolated-tests/20261101T170352Z-9551094a/report.json).
- Thêm **19 tests** contract/adapter agent đạt (phase1 + phase2), gồm giữ `unknown` và phiên bản classifier mới. [Report](../../../../output/qa/isolated-tests/20261101T170608Z-d32a3ed2/report.json). Tổng backend trong phạm vi: **61 tests**.
- Frontend: **159 tests**, ESLint, CSS syntax **52 file**, build temp đạt. [Log unit](../../../../output/qa/news-fix/frontend-unit.log), [log build](../../../../output/qa/news-fix/build.log).
- Ruff I/F/UP phạm vi các file tích hợp; Ruff đầy đủ cho module phân trang và regression test mới đạt. Không tuyên bố lint toàn bộ repository.
- Chromium: **12 luồng chính + 7 luồng phục hồi + 2 viewport kiểm tra hình ảnh**. [Luồng chính](../../../../output/playwright/news-fix/evidence.json), [phục hồi](../../../../output/playwright/news-fix/resilience.json), [hình học UI](../../../../output/playwright/news-fix/visual.json). Không có uncaught page error trong các luồng chức năng hoàn tất.
- Đã xem ảnh cuối bằng phiên browser mới: [desktop](../../../../output/playwright/news-fix/desktop-final.png), [mobile](../../../../output/playwright/news-fix/mobile-final.png), [mobile đọc bài](../../../../output/playwright/news-fix/mobile-reader-final.png). Dòng tin ở y≈630 desktop /768 mobile khi chọn kỳ tháng; so với ≈1241/1689 trong review cũ. Không tràn ngang tại 320/390/768/1440.
- QA server port 5191 chỉ sao chép 4 bảng public news/source health vào DB tạm; source mở `mode=ro`. Giữ nguyên 711 tiêu đề, tóm tắt, URL, thời điểm xuất bản/thu thập và sort timestamp: [đối chiếu](../../../../output/qa/news-fix/classification.json). Phiên browser giả lập auth/analytics; không kiểm thử xác thực.
- Refresh nguồn theo lịch bị tắt trong harness. Nút refresh dùng producer kiểm soát không gọi RSS bên ngoài. Kiểm thử này xác nhận luồng cập nhật và phản hồi lỗi, không xác nhận mọi nhà cung cấp live đang hoạt động.
- Test highlights cũ phụ thuộc 15 phút đầu ngày VN đã được sửa fixture: mọi bài test nằm trong ngày hiện tại kể cả sát 00:00. Các timeout do script chờ tham số rỗng, chờ DOM trước response, và server chưa khởi động đã được sửa ở harness; kết quả cuối bên trên đã hoàn tất. Ảnh UI cuối không dùng đồng hồ giả lập.

## Giới hạn và vận hành

- Sắc thái vẫn là quy tắc từ khóa, không phải mô hình ngôn ngữ hay tín hiệu giao dịch; có thể thiếu ngữ cảnh. `unknown` là kết quả hợp lệ, không ép mọi tin thành tích cực/tiêu cực.
- Việc phân loại lại sẽ chạy trên cache hiện hữu ở lần gọi news đầu tiên sau khi dịch vụ dùng source mới. Đã kiểm chứng trên bản sao dữ liệu; chưa chạy migration/backfill trên DB đang phục vụ.
- Chưa kiểm tra Safari/iOS thật. Không sửa cơ chế auth/saved-news trong đợt này.
- Working tree có nhiều thay đổi trước đó. Staging giữ nguyên SHA-256 `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`; không stage/commit/push hoặc triển khai.
