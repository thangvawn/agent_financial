# Review logic và pipeline Hàng hoá — 03/11/2026

> **Cập nhật:** CP-01–CP-09 đã được sửa và kiểm chứng trong [bản sửa mã nguồn](COMMODITIES_PIPELINE_FIXES_2026_11_03.md). Các kết quả bên dưới là bằng chứng trước sửa, được giữ để đối chiếu.

**Trạng thái: review hoàn tất; 9 finding chưa sửa.** Phạm vi là tab Hàng hoá vừa thiết kế và đường dữ liệu dùng chung: Yahoo/yfinance → global snapshot/history cache → API/SQLite commodity_quotes → client cache/hooks → bảng giá/chart. Đã đọc scheduler và consumer Global Terminal/Watchlist để đánh giá ảnh hưởng. Không phải chứng nhận toàn dự án hoặc độ chính xác của dữ liệu giao dịch thời gian thực.

## Kết luận

Luồng bình thường tải được dữ liệu và render chart, nhưng chưa đủ tin cậy ở các tình huống đồng thời, qua ngày UTC, nguồn trả thiếu và refresh. Có **4 lỗi P1**, **4 lỗi P2**, **1 lỗi P3**. Không thay đổi code ứng dụng trong lượt review này; chỉ thêm script tái hiện và hồ sơ review.

## Findings theo mức ưu tiên

### CP-01 · P1 · Giá tham chiếu bị chọn sai khi ngày UTC khác ngày sàn

**Source:** `src/risk_dashboard/modules/data_hub/application/global_market_feed.py:699` (`_previous_close`), nhánh fallback ở dòng 696 và consumer dòng 364.

Daily download của yfinance bỏ timezone, giữ ngày sàn; intraday trả UTC. Hàm so trực tiếp `.date()` của hai chuỗi, nên quote 01:05 UTC ngày 03/11, vẫn là 02/11 ở New York, bị coi là phiên mới so với daily bar 02/11. Nó chọn close của daily bar đang chạy thay vì daily close trước đó. Fixture qua API cho daily `[90, 100]`, quote `101`: API trả **+1%**, trong khi so với daily bar hoàn tất trước đó phải là **+12,222%**. Khi daily hoàn toàn thiếu, code còn dùng nến intraday đầu tiên làm tham chiếu mà không đánh dấu mất tham chiếu.

**Đối chiếu nguồn thật:** raw daily index `None`, intraday `UTC`, metadata cả XAU/WTI/CORN là `America/New_York`. Mẫu XAU daily cuối 02/11 = 3966,3999, quote UTC 03/11 01:20 cũng = 3966,3999; daily trước = 3898,8999. Pipeline trả gần/đúng 0% do chọn sai mốc. Đây là đối chiếu quy tắc previous daily close hiện có; chưa xác nhận quy ước settlement chính thức của từng hợp đồng/sàn.

**Hướng sửa:** lưu timezone/trading-session cùng instrument, chuẩn hoá về cùng phiên trước khi chọn mốc; nếu dùng settlement thì truyền trường tham chiếu có nguồn riêng. Thiếu tham chiếu phải trả unknown; không thay bằng giá đầu chuỗi.

### CP-02 · P1 · Lịch sử hai request đồng thời bị lẫn trong yfinance

**Source:** `src/risk_dashboard/modules/data_hub/application/global_market_feed.py:522`, cùng hai đường snapshot gọi `yf.download` ở dòng 331/344.

Installed yfinance **1.2.0** dùng `shared._DFS` chung trong `multi.download`; `threads=False` chỉ tắt tải song song bên trong một lời gọi, không cách ly hai HTTP request. Chart chi tiết và sparkline tải cùng XAU với `3mo`/`1mo`, và scheduler cũng có thể gọi snapshot đồng thời.

**Tái hiện:** dùng nguyên `producer.history` và implementation `yf.download` đã cài, chỉ thay leaf tải network bằng hai frame xác định. Cho request 1mo dừng sau download, request 3mo chạy xong rồi tiếp tục 1mo. Kết quả 1mo nhận **3 điểm của 3mo**, bao gồm **01/09** ngoài khoảng, thay vì 2 điểm tháng 11. Payload bị gắn nhãn/cache dưới key 1mo. Đây là lịch chạy điều khiển để chứng minh race; chưa đo tần suất trong vận hành thật.

**Hướng sửa:** cách ly state provider hoặc khoá chung mọi đường gọi download dùng state này, thêm single-flight theo symbol/period/interval; giới hạn đồng thời và kiểm tra series trả về trước khi cache. Khoá chỉ từng mã hoặc chỉ nhánh refresh snapshot không đủ.

### CP-03 · P1 · Snapshot thiếu mã ghi đè snapshot đầy đủ

**Source:** `global_market_feed.py:190`; `src/risk_dashboard/modules/market_portfolio/application/commodity_feed.py:73`.

Chỉ cần `live.items` không rỗng, toàn bộ cache cũ bị thay. Khi một phần Yahoo lỗi hoặc chỉ crypto thành công, các mã không trả về bị mất. SQLite fallback chỉ hoạt động khi **toàn bộ** nhóm commodities rỗng; thiếu riêng một mã không được bù.

**Tái hiện qua API:** cache và DB có XAU+WTI; provider tiếp theo trả WTI. API trả 1 mã WTI và `freshness=fresh`, dù DB vẫn giữ XAU. Bảng, số lượng nhóm và lựa chọn đang xem có thể đổi đột ngột theo lỗi nguồn.

**Hướng sửa:** merge theo mã với bản thành công gần nhất, giữ danh mục instrument cố định; gắn stale/unavailable từng mã, báo coverage và không coi thành công một phần là toàn bộ feed fresh.

### CP-04 · P1 · Refresh crypto có thể làm hàng hoá cũ được báo mới

**Source:** `global_market_feed.py:262`, `:205`; `commodity_feed.py:23`, `:60`, `:76`, `:95`.

Refresh riêng crypto thay `as_of` của snapshot chung, giữ nguyên commodity items. `freshness` chỉ dựa vào `as_of` đó. Endpoint commodities tiếp tục lưu `q.as_of` theo thời điểm snapshot chung và gắn freshness chung. Nhánh fallback DB không lấy lại `raw_json.updated_at`, nên giao diện lấy `row.as_of` thay timestamp giá thật.

**Tái hiện:** XAU/WTI cũ 7 ngày → refresh BTC → endpoint hàng hoá trả `fresh`. Sau đó global snapshot chỉ có BTC, fallback trả commodity rows từ DB vẫn `fresh` và mất `updated_at`; giá cũ có timestamp snapshot mới.

**Hướng sửa:** tách `fetched_at`, `quote_at`, `last_success_at` theo nhóm/mã; freshness tính từ nguồn giá và lịch phiên, có trạng thái thị trường đóng cửa. Giữ timestamp provider qua storage/fallback và tránh ghi thêm quote chỉ vì nhóm tài sản khác được refresh.

### CP-05 · P2 · Bảng giá tự cập nhật nhưng chart và sparkline đứng yên

**Source:** `frontend/src/features/market-portfolio/hooks/useCommodityHistory.js:9`, `hooks/useSparklineHistory.js:7`; polling quote ở `pages/CommoditiesPanel.jsx:67`.

History chỉ tải khi symbol/period/revision đổi; sparkline tải một lần lúc vào viewport. TTL hết hạn không tự gọi lại hook. Revision làm mới bảng giá không truyền xuống history/sparkline.

**Browser:** tiến 11 phút bằng Playwright clock, quote requests tăng 1→2 nhưng XAU history requests giữ 2 (một main, một mini), legend chart không đổi. Bấm làm mới bảng giá tiếp tục không phát sinh history request.

**Hướng sửa:** lịch revalidate phù hợp nến ngày đang chạy, refresh khi focus/online và thao tác làm mới chung; chỉ cập nhật khi cần, giữ zoom và dữ liệu trước trong lúc tải.

### CP-06 · P2 · Làm mới lịch sử chỉ bỏ cache frontend

**Source:** `frontend/src/features/market-portfolio/services/dataHubApi.js:82`; `src/risk_dashboard/modules/data_hub/api/public.py:95`; `global_market_feed.py:289`.

`forceRefresh` không được gửi tới server; API không nhận option này. Backend vẫn dùng cache ngày 600 giây. Người dùng bấm “Tải lại lịch sử giá” có thể nhận nguyên payload cũ dù thao tác thành công.

**Tái hiện:** browser request không có refresh flag. API history hai lần, lần sau thử `refresh=true`, vẫn chỉ một provider call và payload bằng nhau.

**Hướng sửa:** bổ sung refresh contract xuyên client/API/producer, vẫn collapse requests và giới hạn tần suất; UI thể hiện refresh đang được yêu cầu/kết quả thành công gần nhất.

### CP-07 · P2 · Lỗi refresh lịch sử xoá chart đã tải thành công

**Source:** `useCommodityHistory.js:20` và `:23`.

Revision đổi khiến result cũ không khớp key và UI chuyển về loading trống. Khi timeout/503, hook ghi `points: []`, làm mất chart, high/low và thống kê kỳ, dù history trước của đúng mã/kỳ vẫn có thể dùng.

**Browser:** tải chart thành công, cho request refresh trả 503 → canvas về **0**, bảng giá vẫn có 1 mã. Không có stale chart để tiếp tục xem.

**Hướng sửa:** giữ last-good history theo symbol/period, tách loading/error khỏi points, hiển thị thời gian/lỗi refresh bên cạnh chart. Chỉ xoá khi thật sự đổi mã/kỳ không có dữ liệu tương ứng.

### CP-08 · P2 · Trường cao/thấp phiên chứa cao/thấp nến 5 phút cuối

**Source:** `global_market_feed.py:383`.

`high_24h` và `low_24h` lấy `.iloc[-1]`; volume lại cộng cả chuỗi intraday. API/DB dùng cùng tên thống kê phiên nhưng phạm vi tính không nhất quán. Chart detail mới tính “Cao/Thấp trong kỳ” từ history nên **không bị lỗi này trực tiếp**; finding thuộc contract snapshot/storage và consumer khác.

**Tái hiện:** nến đầu high/low=110/80, nến cuối=102/99 → API trả high/low=102/99, volume=300 của cả hai nến.

**Hướng sửa:** xác định session window, dùng max/min trong đúng cửa sổ; đổi tên nếu chỉ muốn thông tin nến cuối. Không gọi toàn bộ dữ liệu ngày lịch là 24h nếu nguồn không cung cấp cửa sổ đó.

### CP-09 · P3 · Cache RAM bỏ qua cache directory

**Source:** `global_market_feed.py:617` và `:641`.

Key RAM chỉ có symbol/period/interval; hai producer được cấu hình thư mục khác nhau vẫn dùng chung dữ liệu. Test/QA trong cùng process có thể trả history từ môi trường khác và bỏ qua provider dự kiến. Đây là ranh giới cache cấu hình, không phải bằng chứng lộ dữ liệu tài khoản.

**Tái hiện:** producer A ghi XAU3mo, producer B dùng thư mục mới trống → B trả 2 điểm của A, không gọi provider.

**Hướng sửa:** đưa namespace/cache_dir resolved vào key hoặc dùng cache thuộc instance có ownership rõ; thêm kiểm chứng isolation vào test provider.

## Kiểm chứng đã thực hiện

| Phạm vi | Kết quả |
| --- | --- |
| Commodity model unit | 4/4 pass |
| Sparkline model/queue unit | 6/6 pass |
| Backend cache resilience | 3/3 pass, runner DB tạm |
| Watchlist đa tài sản dùng cùng feed | 12/12 pass, runner DB/cache tạm |
| Vite production build | Pass, entry `index-Df2NeQSu.js`, output QA riêng |
| Backend review harness | 11 quan sát, gồm healthy API/NaN→null, các ca lỗi ở trên; network bị chặn |
| Chromium | 4 ca tái hiện lifecycle/refresh, 0 pageerrors; xem cả hai ảnh |
| Public provider thật | 3 quotes và 65 daily bars/mã XAU/WTI/CORN; OHLC hợp lệ, date tăng dần |

Các test hiện có pass **không** chứng minh các finding đã sửa. Test volume NaN không gây HTTP500 trên FastAPI hiện cài: response chuyển thành null; đã loại nghi vấn này khỏi finding.

Lần đối chiếu provider thứ hai ghi nhận lỗi `OperationalError('database is locked')` ở cache riêng của yfinance khi tải daily CORN song song; intraday và history 3mo vẫn thành công. Lỗi xảy ra trong thư mục QA mới, không phải bằng chứng SQLite DB ứng dụng bị lock. Báo cáo giữ log và không gọi lần lấy dữ liệu đó là hoàn toàn sạch. Chưa kiểm chứng độ trễ liên tục, settlement/rollover chính thức, soak/load test nhiều worker hoặc lịch nghỉ từng sàn.

## Bằng chứng và chạy lại

- `output/qa/commodities-pipeline-review/backend-observations.json`, `backend-run.log`.
- `output/qa/commodities-pipeline-review/public-provider.json`, `provider-run.log`.
- `output/playwright/commodities-review/observations.json`, `quote-chart-desync.png`, `history-retry-discards-chart.png`.
- Backend test reports: `output/qa/isolated-tests/20261103T012713Z-39cb25c4/`, `20261103T013235Z-44998d4e/`.

```sh
.venv/bin/python scripts/qa/review-commodities-pipeline.py
.venv/bin/python scripts/qa/probe-commodities-provider.py
npm --prefix frontend run test:unit -- --testPathPattern=commodity-model
npm --prefix frontend run test:unit -- --testPathPattern=market-sparklines
.venv/bin/python scripts/qa/run_isolated_tests.py -- tests/modules/data_hub/test_cache_resilience.py tests/test_watchlist_multi_asset.py
# Browser: build QA theo report UI trước, mở commodities-server.py trên 5191,
# rồi chạy node scripts/qa/review-commodities-browser.mjs; dừng QA và xoá session.json.
```

Đây là script **tái hiện trạng thái lỗi hiện tại**, không phải bộ regression đã kỳ vọng behavior sau fix. Hai Python harness tạo/xoá runtime riêng trước import; provider probe chỉ tải thông tin thị trường công khai. Browser dùng QA server/auth tạm và response điều khiển. Không gọi endpoint ghi/reset trên DB thật, không đổi app source, không restart8000/push/deploy. Server QA5191 đã dừng, credential QA đã xoá. 116 staged files giữ nguyên, SHA256 staged diff `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`.

## Thứ tự xử lý đề xuất

1. CP-01/02: đúng giá tham chiếu và không lẫn history khi tải đồng thời.
2. CP-03/04: giữ coverage, freshness và timestamp đúng xuyên cache/SQLite/API.
3. CP-05/06/07: đồng bộ vòng đời refresh chart, giữ last-good history.
4. CP-08/09: sửa contract thống kê phiên và cách ly cache.

Mỗi bản sửa cần regression qua API hoặc browser từ ca tái hiện, rồi kiểm tra nguồn thật có giới hạn. Các hướng sửa là đề xuất sau review, chưa được thực hiện.
