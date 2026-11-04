# Hàng hoá: sửa logic và data pipeline · 03/11/2026

**Trạng thái: verified trên source và môi trường QA cô lập.** Người dùng đã yêu cầu sửa mã nguồn sau [review CP-01–CP-09](COMMODITIES_PIPELINE_REVIEW_2026_11_03.md). Cả 9 finding đã được xử lý trong phạm vi bảng giá, chart, cache, API và lưu trữ hàng hoá. Không suy ra toàn dự án hoặc nguồn dữ liệu luôn ổn định từ kết quả này.

## Thay đổi và bằng chứng

| Finding | Hành vi sau sửa | Kiểm chứng |
| --- | --- | --- |
| CP-01 · Giá tham chiếu | Chọn daily close có ngày nhỏ hơn ngày của quote theo timezone nguồn. Không có daily/reference thì trả null thay vì dùng nến intraday hoặc giả 0%. | API với quote sau nửa đêm UTC/trước nửa đêm New York; thiếu daily; đối chiếu XAU/WTI/CORN thật. |
| CP-02 · Download đồng thời | Mọi `yfinance.download` trong feed và backtest đi qua cùng khoá; khởi tạo cache Yahoo trước worker. Request cùng history key dùng chung một lượt tải. | Hai kỳ tải đồng thời qua implementation yfinance thật, chỉ thay leaf network; single-flight; probe nguồn thật không còn cảnh báo SQLite cache lock. |
| CP-03 · Snapshot thiếu mã | Merge theo mã, giữ quote tốt trước đó và đánh dấu stale. Endpoint trả danh mục 23 hợp đồng, placeholder unavailable khi chưa có giá; công khai coverage. | API partial/missing; Chromium vẫn giữ XAU đang chọn khi nguồn bỏ XAU. |
| CP-04 · Timestamp/freshness | Tách quote_at/updated_at với fetched_at. Refresh crypto không gia hạn commodity. SQLite lưu thời điểm quote thật, upsert cùng symbol/time; fallback đọc lại timestamp gốc kể cả row legacy. | Quote cũ 7 ngày + crypto refresh + fallback DB; số row không tăng do đọc lại/refresh nhóm khác. |
| CP-05 · Chart đứng yên | Quote kiểm tra mỗi phút; main chart và mini chart đang hiển thị kiểm tra mỗi 5 phút, thêm focus/online/visibility. Refresh bảng áp dụng cho cả chart. Giữ vùng zoom khi cập nhật điểm. | Chromium tiến 11 phút, quote/main/mini thay đổi và zoom giữ nguyên. Backend history thường vẫn có TTL 10 phút. |
| CP-06 · Refresh không tới nguồn | `refresh=true` đi xuyên client → API → producer, bỏ cache history khi yêu cầu; gom request trùng và giới hạn refresh cùng key cách nhau 5 giây. UI báo khi bị giới hạn. | API đếm số provider calls; Chromium request main/mini có flag, dữ liệu thay đổi, lần bấm liên tiếp có thông báo. |
| CP-07 · Lỗi xoá chart | Giữ history tốt của đúng mã/kỳ trong lúc tải và khi timeout/503/provider rỗng. Hiển thị cảnh báo; retry thành công xoá cảnh báo. Consumer huỷ request không huỷ các consumer khác. | API fallback; unit client/mini; Chromium provider failure, 503, recovery, đổi kỳ chưa có dữ liệu. |
| CP-08 · Thống kê sai cửa sổ | Max/min/sum intraday trong ngày lịch của quote theo timezone nguồn. Payload có `statistics_window=exchange_day`; UI dùng nhãn phù hợp, không gọi là rolling 24h. | Nến ngày trước có extrema rất lớn bị loại; extrema trong ngày được giữ thay vì nến 5m cuối. |
| CP-09 · RAM cache lẫn môi trường | Key chứa đường dẫn cache đã resolve + symbol/period/interval. Cache history chuyển namespace v2 để không dùng payload có thể đã bị trộn bởi lỗi concurrent cũ; ghi JSON qua file tạm duy nhất. | Hai producer dùng thư mục khác nhau nhận history khác nhau; các kiểm tra cache permission/atomic write đạt. |

Source chính: `src/risk_dashboard/modules/data_hub/application/global_market_feed.py`, `quote_quality.py`, `src/risk_dashboard/data/yahoo_client.py`, `src/risk_dashboard/modules/market_portfolio/application/commodity_feed.py`, các route/service history; frontend `CommoditiesPanel`, `useCommodityHistory`, `useSparklineHistory`, history clients và `LightweightChartPanel`.

`tests/test_data_hub.py` có fixture GTGD cũ theo triệu VND; đã đổi sang raw VND đúng contract hiện hành của snapshot (không đổi logic thị trường Việt Nam). Market pulse bỏ giá trị change_pct thiếu khỏi phép tính để contract reference=null không gây lỗi 500.

## Kết quả kiểm chứng

- **40/40 backend tests** trong một lần chạy cuối: 9 commodity regressions, 3 cache resilience, 12 watchlist đa tài sản, 6 data hub, 10 backtest. DB/env tạm được thiết lập trước import.
- **183/183 frontend unit**, CSS **57/57**, ESLint **0 lỗi**; còn 1 warning cũ ở Social `useSocialFeed.js`. Production build QA đạt, entry `index-jTmrauO8.js`.
- **11 nhóm Chromium**, **0 pageerrors**, qua route/auth/SQLite/cache thật trên QA5192, provider leaf fixture có kiểm soát. Bao gồm polling, giữ zoom, forced refresh, lỗi nguồn/HTTP, retry, throttle, partial snapshot, đổi mã/kỳ, theme và viewport 768/390/320. Đã xem ảnh desktop dark và mobile light, không tràn ngang trang.
- **Nguồn Yahoo thật:** 3/3 quotes; 65 daily bars mỗi mã XAU/WTI/CORN; OHLC hợp lệ và ngày tăng dần. Probe dùng cache riêng, chạy 2,59 giây; không có cảnh báo cache lock trong lần này. Đây là một lần quan sát, không phải chứng nhận uptime hay realtime.
- Ruff đạt trên 4 file mới/viết lại (Yahoo wrapper, quote quality, commodity feed, commodity regressions). Các file legacy còn lint có sẵn; không phát sinh diagnostic trên dòng code mới của feed/service/backtest sau chỉnh format. `git diff --check` sạch.

Bằng chứng:

- `output/qa/isolated-tests/20261103T020339Z-3522cdf3/report.json` và `pytest.log`.
- `output/qa/commodities-pipeline-fixed/frontend-tests.log`, `css.log`, `public-provider.json`, `provider-run.log`.
- `output/playwright/commodities-fixed/checks.json`, `browser-run.log`, `desktop-updated.png`, `stale-contract.png`, `desktop-light.png`, `width-768.png`, `width-390.png`, `width-320.png`.

## Chạy lại

```sh
.venv/bin/python scripts/qa/run_isolated_tests.py -- tests/modules/data_hub/test_commodity_pipeline.py tests/modules/data_hub/test_cache_resilience.py tests/test_watchlist_multi_asset.py tests/test_data_hub.py tests/test_backtest.py
npm --prefix frontend run test:unit
npm --prefix frontend run lint
npm --prefix frontend run lint:css
npm --prefix frontend run build -- --outDir ../output/playwright/commodities/dist
.venv/bin/python scripts/qa/probe-commodities-provider.py --output output/qa/commodities-pipeline-fixed/public-provider.json
# Browser cần public fixtures quotes.json/histories.json từ QA UI Hàng hoá trước đó.
# Mở server dưới đây, sau đó chạy browser ở terminal khác và dừng server khi xong.
.venv/bin/python scripts/qa/commodities-pipeline-server.py
node scripts/qa/commodities-pipeline-browser.mjs
```

Server chỉ bind localhost5192, dùng temp DB/cache và session QA. Nếu dừng bằng signal khiến cleanup không chạy, xoá `output/playwright/commodities-fixed/session.json` và thư mục temp `northstar-commodity-fixed-*` của lượt đó. Lượt bàn giao này đã dừng server, xoá session và temp directory. Script review cũ lưu trạng thái lỗi lịch sử; dùng regression mới để kiểm chứng bản sửa.

## Giới hạn và vận hành

- Giá tham chiếu là **daily close của Yahoo**, chưa phải settlement chính thức hoặc lịch phiên futures/rollover. Thống kê exchange_day là ngày lịch theo timezone nguồn; giữ tên API legacy `high_24h/low_24h/volume_24h` để tương thích, có metadata giải thích phạm vi.
- Freshness thận trọng theo tuổi quote/fetch. Chưa thêm lịch nghỉ từng sàn để phân biệt đầy đủ thị trường đóng cửa với nguồn ngừng cập nhật; giá cũ luôn được ghi rõ thay vì gắn thời điểm mới.
- Khoá download và single-flight nằm trong một process. Chưa soak/load test nhiều worker; chưa có rate limit phân tán. Cache history v2 cần tải lại lần đầu.
- Kiểm chứng trên QA cô lập; không reset DB người dùng, không restart localhost8000, không push/deploy. Giữ nguyên 116 file đã staged, SHA256 staged diff `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`.
