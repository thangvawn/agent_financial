# Review trang Tin tức — 01/11/2026

> **02/11/2026 — superseded về trạng thái chưa sửa:** NR-01–NR-07 đã có [bản sửa và kiểm chứng](NEWS_FIXES_2026_11_02.md). Nội dung dưới đây giữ lại bằng chứng tại thời điểm review.

**Trạng thái: verified về các phát hiện bên dưới; chưa sửa code sản phẩm.** Phạm vi: `/dashboard-static/news`, API feed/highlights/detail và phân loại tin. Các hướng sửa là **proposed**, chưa triển khai.

## Các lỗi cần sửa

### NR-01 · P1 · Phân loại tiếng Việt nhầm “đầu tư” thành “dầu”

- Vị trí: `src/risk_dashboard/modules/news_intelligence/domain/text.py:37–38`; được dùng trong `application/enrichment.py:_refine_category`, `domain/impact.py` và scoring.
- `contains_keyword` bỏ toàn bộ dấu và đổi đ→d cho cả nội dung lẫn từ khóa. Do đó “đầu” và “dầu” cùng thành `dau`; ranh giới từ không giải quyết được trường hợp này.
- Tái hiện trên dữ liệu thật: bài **“Hải Phòng dự kiến chi hơn 38.760 tỉ đồng đầu tư công năm 2027”** có `category=commodities`, `affected_markets=["Oil"]`. Gọi trực tiếp classifier với nguyên tiêu đề cũng cho kết quả này.
- Ảnh hưởng: sai danh mục, nhãn thị trường, điểm quan trọng và khái niệm học tập đi kèm.
- Hướng sửa: tách chuẩn hóa phục vụ tìm kiếm khỏi đối sánh ngữ nghĩa; giữ dấu cho từ khóa tiếng Việt, dùng alias/cụm từ được kiểm soát. Cần phân loại lại cache sau khi sửa.

### NR-02 · P2 · Bộ lọc sắc thái không xử lý được tin tiếng Việt

- Vị trí: `src/risk_dashboard/modules/news_intelligence/application/enrichment.py:17–44,124–131`.
- Từ điển tích cực/tiêu cực chỉ có tiếng Anh. Hai câu “Cổ phiếu tăng trưởng mạnh, lợi nhuận doanh nghiệp tăng kỷ lục” và “Cổ phiếu giảm mạnh, doanh nghiệp thua lỗ và phá sản” đều trả `neutral`.
- Trong bản sao dữ liệu 710 tin, **370/370 tin vùng VN đều neutral**. Việc chọn tích cực/tiêu cực loại bỏ các tin VN dù nội dung có sắc thái rõ ràng.
- UI ghi “Sắc thái (AI)” nhưng đường phân loại đang chạy là quy tắc từ khóa, không gọi mô hình AI.
- Hướng sửa: classifier hỗ trợ tiếng Việt, xử lý phủ định và ngữ cảnh; biểu diễn thiếu độ tin cậy thay vì mặc định coi là trung tính. Đổi nhãn UI cho đúng cơ chế thực tế và phân loại lại dữ liệu cũ.

### NR-03 · P2 · Cắt danh sách trước khi lọc độ quan trọng làm mất tin

- Vị trí: `application/services.py:99–123`; `_list_articles` trả `_deduplicate_articles(articles)[:limit]` tại dòng 567.
- `get_feed` lấy tối đa 80 tin khi UI yêu cầu limit=80, bỏ điều kiện importance ở SQL, rồi mới lọc nhãn. Các tin phù hợp ngoài tập 80 đầu không được xét.
- Tái hiện trên cùng DB tạm: `region=VN,time_range_hours=168,importance=low,limit=80` trả **56 tin**; tăng limit=100 trả **77 tin**. Bài “Làng nghề lược sừng Thụy Ứng chuyển mình trong thời đại số” không xuất hiện ở truy vấn đầu, nhưng tìm đúng tiêu đề với cùng importance/limit=80 trả được 1 tin.
- Scoring còn phụ thuộc tập kết quả đang truy vấn: cùng bài Binance có thể là low/49 khi nằm trong tập 100 tin, nhưng medium/50 khi tìm riêng. Cần giữ điểm canonical ổn định theo snapshot, rồi lọc và phân trang trên cùng tập đã chấm điểm.

### NR-04 · P2 · “Xem thêm” không tải được tin sau mốc 80

- Vị trí: `frontend/src/features/news/pages/NewsPage.jsx:88,150,241–242`; API `public.py:get_news_feed` không có offset/cursor.
- Browser thực tế: nhấn Xem thêm đến **80/80** thì nút biến mất; phát sinh **0 request feed bổ sung**. Đây chỉ là mở dần mảng 80 tin đã tải. API cùng bộ lọc trả được 100 tin, chứng minh dữ liệu chưa hết.
- Hướng sửa: phân trang API với cursor ổn định, `has_more`/tổng phù hợp; UI tải trang tiếp khi cuộn hoặc nhấn nút, reset cursor khi thay bộ lọc.

### NR-05 · P2 · Liên kết khái niệm không mở đúng nội dung

- Vị trí: `frontend/src/features/news/pages/components/NewsArticleReader.jsx:89`; nơi nhận `features/learn-hub/pages/LearningHomePage.jsx:41–46`.
- Nhấn “Giá dầu và lạm phát” tới `/learn?concept=oil_inflation`, nhưng chỉ hiện danh mục 10 khóa học chung, ô tìm kiếm rỗng. Route `/learn` tồn tại; lỗi là không có xử lý tham số `concept`, không phải HTTP 404.
- Hướng sửa: ánh xạ concept sang bài học/nội dung có thật và xử lý deep link; nếu chưa có nội dung thì không trình bày như một liên kết mở khái niệm cụ thể.

### NR-06 · P2 · Dữ liệu cũ vẫn được trình bày “Sẵn sàng”

- Vị trí: `frontend/src/features/news/pages/components/NewsFeedList.jsx:39`; NewsPage không chuyển `freshness`, `stale_reason`, `data_quality` sang component.
- Mô phỏng tại browser bằng phản hồi feed thật đã thay metadata thành `freshness=stale`, nguồn thành công=0: UI vẫn ghi “Sẵn sàng”, không có thông báo dữ liệu cũ, thời điểm cập nhật hoặc nút thử lại.
- Hướng sửa: hiển thị thời điểm dữ liệu, tình trạng nguồn và cache cũ; phân biệt tải xong với dữ liệu còn mới. Không dùng thời điểm `as_of` của response thay cho thời điểm cập nhật dữ liệu.

### NR-07 · P2 · Trang mở lâu không cập nhật tin mới

- Vị trí: `frontend/src/features/news/pages/NewsPage.jsx:111–113`; `hooks/useNewsHighlights.js:55–58`.
- Feed chỉ tải khi mount/thay bộ lọc; highlights chỉ tải khi đổi kỳ hoặc gọi retry. Component NewsHeader có nút cập nhật nhưng hiện không được render.
- Browser clock tiến 5 phút và phát sự kiện focus: **0 request news mới**; không có nút cập nhật trong trạng thái bình thường. TTL 60 giây ở backend không tự đẩy dữ liệu tới browser.
- Hướng sửa: cập nhật định kỳ khi tab đang hiển thị, revalidate khi quay lại tab và có nút cập nhật thủ công; hủy request cũ để giữ bộ lọc mới nhất.

## UI/UX đã quan sát

- **Phạm vi bộ lọc chưa rõ:** góc nhìn VN vẫn hiển thị Bloomberg/global trong Tin nổi bật. Tìm `zzreviewmissing` kết hợp negative làm Dòng tin rỗng nhưng giữ nguyên Tin nổi bật. `useNewsHighlights({limit:8})` không nhận các bộ lọc. Cần quyết định áp dụng bộ lọc cho cả trang hoặc ghi rõ khối nổi bật toàn cầu độc lập; đây là quyết định UX, chưa giả định yêu cầu sản phẩm.
- **P3 — không thu gọn được bộ lọc đang dùng:** `NewsFilters.jsx:99,109` dùng `showAdvanced || hasActiveSubFilters`. Chọn negative rồi bấm Bộ lọc để đóng vẫn thấy panel và `aria-expanded=true`. Nên tách trạng thái mở panel khỏi trạng thái có điều kiện lọc.
- **Danh sách chính nằm quá thấp:** ở desktop 1440×1000, Dòng tin bắt đầu tại y≈1241; mobile 390×844 bắt đầu tại y≈1689 vì 8 tin nổi bật chiếm phần trên. Nên rút gọn nổi bật còn 3 tin + mở rộng, hoặc dùng tab riêng. Mobile không tràn ngang trong viewport đã kiểm tra.
- Copy đang lẫn tiếng Anh: `medium`, `neutral`, `Oil`, `Rates`; phần “Vì sao đáng chú ý” chủ yếu là mô tả bộ phân loại. Nên Việt hóa nhãn và đưa giải thích tác động cụ thể có nguồn dẫn.

## Kiểm chứng và giới hạn

- Truy cập HTTP 200 tại URL người dùng gửi và dùng Chromium thực tế, viewport 1440×1000 và 390×844. Cần chạy ngoài sandbox vì sandbox chặn localhost/Chromium; không phải server ngừng chạy. Bundle NewsPage trên server và build từ source cùng tên hash `NewsPage-SS815RQN.js`.
- Browser dùng phiên QA mới, chỉ giả lập `/auth/me` và analytics; news API đọc từ server thật. Khi theo link Learn Hub, API kệ sách riêng được trả rỗng trong browser. Chưa review cơ chế xác thực trong lượt này.
- Probe API dùng FastAPI TestClient với bản sao **chỉ 4 bảng news/source health**, DB tạm đặt trước import; nguồn DB mở `mode=ro`, không reset dữ liệu thật. Refresh nguồn bị tắt cho probe để giữ nguyên tập dữ liệu. Metadata stale chỉ được thay trong response của browser QA.
- Existing backend suite: **28 passed**, chạy qua runner cô lập: `.venv/bin/python scripts/qa/run_isolated_tests.py -- tests/test_news_intelligence.py tests/test_news_optimization.py -q`. Các ca regression hiện có chưa bắt được những lỗi trên.
- Build source thành công: `npm run build -- --outDir /private/tmp/northstar-news-review-dist`; không thay dist đang phục vụ.
- Hai lượt script browser tổng hợp dừng vì timeout chờ response sau chọn dropdown. Đã tách ca và xác nhận request chọn negative/tìm kiếm thực sự chạy; không kết luận timeout của harness là lỗi app. Các bằng chứng hoàn tất nằm ở file riêng bên dưới. Không có uncaught page error trong các ca hoàn tất; chưa thử Safari/iOS thật.
- Không sửa code sản phẩm, không stage/commit/push/deploy. Thêm báo cáo và memory; output kiểm tra nằm trong thư mục ignored.

## Bằng chứng local

- `output/qa/news-review/filter-evidence.json`: kết quả API và bài bị bỏ sót.
- `output/qa/news-review/classification-evidence.json`, `data-distribution.json`: phân loại tiếng Việt và phân bố sắc thái.
- `output/playwright/news-review/partial-evidence.json`: phân trang và deep link đã hoàn tất trước timeout ở ca tiếp theo.
- `output/playwright/news-review/filter-scope-evidence.json`, `filters-debug.json`: request thực, kết quả rỗng và highlights không đổi.
- `output/playwright/news-review/freshness-evidence.json`: dữ liệu cũ, cập nhật, mobile và panel lọc.
- `output/playwright/news-review/{desktop.png,mobile.png,concept-destination.png}`: ảnh đã xem.
- `output/qa/isolated-tests/20261101T164116Z-f5fdc4a8/report.json`: 28 tests đã đạt.

Thứ tự đề xuất: NR-01/02 (độ đúng phân loại) → NR-03/04 (lọc và phân trang) → NR-06/07 (độ mới dữ liệu) → NR-05 và tinh gọn UI. Tất cả vẫn là việc chưa sửa.
