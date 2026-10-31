# Dùng thử và rà soát logic — 31/10/2026

**Trạng thái: báo cáo phát hiện ban đầu; U01–U11 đã được xử lý trong [báo cáo sửa lỗi](USAGE_FIXES_2026_10_31.md).** Kiểm tra trên workspace hiện tại, gồm các thay đổi local của người dùng và checkpoint `f3286d7`. Lượt này bổ sung kịch bản tái hiện và báo cáo; không thay đổi logic sản phẩm, không push/deploy.

Có **11 vấn đề cần xử lý**, trong đó 4 nhóm ưu tiên P1. Build và các test có sẵn đạt nhưng chưa bao phủ đủ luồng giữa frontend và backend với tài khoản đăng ký thật, đổi tài khoản và dữ liệu thiếu.

## Phạm vi và phương pháp

- Chromium desktop 1440×1000; kiểm tra thêm Learn Hub ở 390×844.
- Backend FastAPI thật chạy localhost, database SQLite tạm riêng, không dùng dữ liệu tài khoản thật. Đăng ký, đăng xuất, watchlist, lệnh giấy và workbook model đi qua endpoint thật.
- Quote backend lấy từ bản cache local; nến mô phỏng, BCTC nguồn và tin tức UI dùng fixture kiểm soát. Không xác nhận độ đúng/độ mới của provider live, thanh toán sở giao dịch hay đầu ra AI thực.
- Tắt lifecycle/background jobs trong server QA. Font ngoài trả CSS rỗng trong luồng chức năng; có phép thử riêng chặn font để tái hiện lỗi tải trang.
- Playwright CLI không tải được do registry DNS `ENOTFOUND`; dùng thư viện Playwright đã cài trong repository.
- Có thử CodeGraph theo AGENTS.md; CLI đang cài không hỗ trợ `explore`, nên đối chiếu trực tiếp source và đường gọi.

## Kết quả kiểm chứng

| Kiểm tra | Kết quả và giới hạn |
| --- | --- |
| Vite build | Đạt |
| Frontend unit hiện có | 87 đạt, 0 lỗi |
| Backend theo phạm vi mở rộng | 111 đạt, 0 lỗi; không phải toàn bộ suite repository |
| ESLint toàn frontend | **18 lỗi, 2 cảnh báo** |
| Browser chức năng chính | 5 nhóm đạt, 6 assertions không đạt; hai lỗi watchlist/lệnh giấy cùng nguyên nhân U01 |
| Browser Learn Hub/News | 6 nhóm đạt, 2 assertions cách ly tài khoản không đạt |
| Browser mất dịch vụ font | Tái hiện error boundary thay toàn bộ trang Simulation Lab |
| API probes riêng | 4 kỳ vọng không đạt; dùng Bearer đúng làm đối chứng đọc/ghi thành công |
| Math/DSL probes riêng | 3 sai lệch tái hiện được |
| `git diff --check`, syntax check QA scripts | Đạt |

Các browser assertions không đạt là bằng chứng lỗi hiện tại, không phải test đã sửa. Abort của request khi chuyển trang được ghi riêng, không tính thành lỗi sản phẩm. Sau khi sửa selector để bỏ nút tab ẩn trên desktop và tính biểu tượng trong tên AI Copilot, đã chạy lại các bước liên quan; báo cáo chỉ dùng kết quả đã xác nhận.

Các luồng đạt: đăng ký và đăng xuất server; workbook lưu online và tải lại; chạy preset mô phỏng khi nguồn fixture đủ dữ liệu; lưu blueprint; tìm/lưu khóa học; ghi chú sách lưu rồi mở lại trong cùng phiên; tiếp tục CFA Mock trong cùng tài khoản; News chọn tin/tìm không có kết quả/nguồn 503; Learn Hub mobile không tràn ngang. File PDF mẫu trả HTTP 200 với MIME PDF; không dùng kết quả này để khẳng định mọi viewer PDF/nguồn sách ngoài đều hoạt động.

## Phát hiện cần sửa

### U01 · P1 · Đọc và ghi Market & Portfolio dùng hai định danh khác nhau; body session chưa được xác thực

**Nguồn:** [market_portfolio/api/public.py](../../../../src/risk_dashboard/modules/market_portfolio/api/public.py), dòng 387, 413, 433, 455; [marketPortfolioApi.js](../../../../frontend/src/features/market-portfolio/services/marketPortfolioApi.js), dòng 21–28 và các POST khác.

Frontend POST gửi `session_id` trong JSON, không có Bearer/query. Dependency chỉ đọc header/query nên tạo principal anonymous; handler dùng nguyên `req.session_id` làm owner. GET lại xác thực query session và đổi sang `account_id`.

**Tái hiện:** đăng ký tài khoản thật → thêm FPT trả 200 nhưng GET watchlist có `items: []`; mua 100 FPT trả `FILLED` nhưng Danh mục không có vị thế. Gửi cùng lệnh với Bearer đúng thì GET thấy vị thế. Sau logout, GET bằng session đã revoke trả 401, nhưng POST body session đó vẫn thêm VCB và trả 200.

**Hướng sửa:** mọi thao tác tài khoản dùng một principal đã xác thực; frontend thống nhất Bearer, backend không lấy owner trực tiếp từ body. Nếu giữ anonymous demo, dùng namespace/quy tắc riêng không cho giả làm định danh tài khoản. Cần xử lý dữ liệu từng ghi dưới session ID bằng migration có kiểm chứng owner, tránh bỏ lại watchlist/lệnh cũ.

### U02 · P1 · Mất quote làm tổng danh mục bị báo lỗ giả

**Nguồn:** [services.py](../../../../src/risk_dashboard/modules/market_portfolio/application/services.py), dòng 143–175.

Position thiếu giá trả `market_value: null`, nhưng tổng chỉ cộng các position có quote rồi vẫn công bố equity/PnL như đầy đủ.

**Tái hiện:** 100 triệu vốn, mua 100 FPT giá 100.000; khi quote bị thiếu, hệ thống trả cash 90 triệu, equity 90 triệu và `total_pnl: -10.000.000`, dù không có bằng chứng giá cổ phiếu giảm về 0.

**Hướng sửa:** trả trạng thái định giá chưa đầy đủ và không công bố tổng PnL chính xác trong tình huống này. Nếu dùng giá gần nhất, lưu timestamp/nguồn và gắn nhãn stale; không mặc định giá trị vị thế bằng 0.

### U03 · P1 · Chiến lược, bookmark và bài thi dùng chung giữa các tài khoản trên cùng trình duyệt

**Nguồn:** [quantaBlueprintStorage.js](../../../../frontend/src/features/simulation-lab/services/quantaBlueprintStorage.js):6; [useCourseBookmarks.js](../../../../frontend/src/features/learn-hub/hooks/useCourseBookmarks.js):3; [MockExamRoomPage.jsx](../../../../frontend/src/features/learn-hub/pages/MockExamRoomPage.jsx):23.

**Tái hiện:** A lưu `QA private strategy A`, bookmark một khóa và trả lời câu 1 CFA Mock. Đăng xuất rồi đăng ký B trong cùng browser context: B thấy blueprint của A, có bookmark của A, và tiếp tục đúng bài thi đang dở với đáp án đã chọn/timer cũ.

**Hướng sửa:** cache riêng theo account ID ổn định + loại dữ liệu + resource ID; reset state trong bộ nhớ khi đổi tài khoản. Không chỉ thêm session ID vì đăng nhập lại/rotate session sẽ làm người dùng mất khả năng truy cập dữ liệu của chính mình. Cache legacy chưa có owner cần cơ chế nhận/migrate rõ ràng.

### U04 · P1 · Backtest có thể mua khi không đủ lịch sử cho biểu thức

**Nguồn:** [quantaStrategy.js](../../../../frontend/src/features/simulation-lab/utils/quantaStrategy.js), dòng 75–81.

Warm-up chỉ lấy chu kỳ indicator lớn nhất, bỏ qua dịch lịch sử `[n]` và phụ thuộc lồng nhau. `not` đổi `null` thành `true`.

**Tái hiện:** chỉ có 50 nến, điều kiện `not (market.close > market.close[100])` vẫn được chấp nhận, báo warm-up 2 và mở vị thế ở nến thứ 4. Không có 100 nến trước đó để đánh giá điều kiện.

**Hướng sửa:** tính số nến cần thiết trên cây biểu thức, gồm shift, indicator lồng nhau và nến trước cho crossover. Dữ liệu chưa sẵn sàng phải được truyền xuyên toán tử; không cho `not unavailable` thành tín hiệu mua. Báo thiếu lịch sử khi toàn bộ tập không đủ.

### U05 · P2 · Workbook bỏ qua bản nháp offline mới khi online trở lại

**Nguồn:** [workbookState.js](../../../../frontend/src/features/bctc/services/workbookState.js), dòng 6–15, 24–25.

**Tái hiện:** lưu `server version A` online → API 503 → lưu `offline newer version B` và nhận thông báo đã lưu bản nháp → khôi phục mạng, reload → editor hiển thị A. Cache B vẫn còn nhưng không có đường khôi phục trên UI; lần lưu online sau sẽ xóa cache đó.

**Hướng sửa:** đọc cả draft và bản server, lưu trạng thái dirty/base revision/thời điểm; khôi phục draft hoặc hiển thị lựa chọn so sánh, đồng bộ. Giữ draft khi xung đột 409; chỉ xóa sau khi đúng nội dung draft đã đồng bộ hoặc người dùng chủ động bỏ.

### U06 · P2 · So sánh boolean hợp lệ làm chiến lược im lặng mất tín hiệu

**Nguồn:** [quantaExpression.js](../../../../frontend/src/features/simulation-lab/utils/quantaExpression.js), dòng 49–61.

`==`/`!=` đi qua guard `Number.isFinite` nên boolean bị loại. Parser lại chấp nhận `true`/`false`.

**Tái hiện:** cùng dữ liệu và khai báo `bullish = market.close > 9000`, `when bullish` mở vị thế; `when bullish == true` không mở vị thế, cũng không báo lỗi.

**Hướng sửa:** kiểm tra kiểu theo từng toán tử, hỗ trợ equality boolean hoặc từ chối rõ khi compile. Bổ sung test tính tương đương biểu thức.

### U07 · P2 · RSI trên chuỗi có giá trị trống tính ra tín hiệu sai

**Nguồn:** [quantaIndicators.js](../../../../frontend/src/features/simulation-lab/utils/quantaIndicators.js), dòng 18–26.

Phép trừ không chặn `null`, khiến giá trị đầu tiên sau vùng trống bị so với 0. Với RSI của SMA, đoạn khởi tạo SMA chính là vùng trống hợp lệ.

**Tái hiện:** giá đóng cửa luôn 10.000; `rsi(sma(close, 5), 5)` ở nến đã qua warm-up vẫn bằng 100, trong khi theo chính quy ước engine với chuỗi phẳng phải là 50.

**Hướng sửa:** chỉ khởi tạo Wilder smoothing sau đủ các cặp giá hữu hạn liên tiếp; quy định cách reset/bỏ qua gap, dùng cùng quy ước cho mọi indicator.

### U08 · P2 · Nút AI Copilot không mở; phần phân tích bên trong vẫn là mẫu cố định

**Nguồn:** [SimulationLabWorkspace.jsx](../../../../frontend/src/features/simulation-lab/pages/SimulationLabWorkspace.jsx), dòng 153–162; [SimLabAiCopilotModal.jsx](../../../../frontend/src/features/simulation-lab/pages/components/SimLabAiCopilotModal.jsx), dòng 28–55.

Parent truyền `code`, `onApplyOptimizedCode` và không truyền `isOpen`. Component đòi `isOpen`, `currentCode`, `onApplyCode`; vì vậy luôn return null. Browser bấm nút thật nhưng không xuất hiện dialog.

**Hướng sửa:** đồng nhất props và kiểm thử mở → áp dụng → biên dịch lại. Chỉ sửa props chưa hoàn tất chức năng: `handleAnalyze` hiện trả nhận xét/tham số cố định sau timeout, không dùng prompt hoặc kết quả chạy. Cần ghi rõ đây là gợi ý mẫu hoặc nối luồng phân tích thật; không gọi nó là tối ưu đã được kiểm chứng.

### U09 · P2 · Font ngoài không tải được làm sập cả Simulation Lab

**Nguồn:** [simlab-studio.css](../../../../frontend/src/features/simulation-lab/pages/styles/simlab-studio.css):2.

**Tái hiện:** Chromium abort request Google Fonts; stylesheet import thất bại khiến Vite preload reject và app hiện “Hệ thống gặp lỗi không mong muốn / Unable to preload CSS…”. Với cùng backend/build nhưng font trả CSS rỗng, trang chạy preset bình thường.

**Hướng sửa:** bỏ phụ thuộc `@import` font ngoài trong CSS chunk chức năng; self-host hoặc tải font như tài nguyên tùy chọn với system-font fallback. Kiểm thử route trong điều kiện offline/mạng chặn font.

### U10 · P2 · Phiên đã revoke vẫn ở giao diện đã đăng nhập

**Nguồn:** [AppShell.jsx](../../../../frontend/src/app/AppShell.jsx), dòng 46–71; [useAuth.js](../../../../frontend/src/features/auth/services/useAuth.js), hàm `verifyStoredSession` chưa được AppShell gọi.

**Tái hiện:** revoke session qua backend, giữ browser storage, mở lại Lệnh giấy. API GET trả 401 nhưng shell vẫn có “Đăng xuất”, không đưa người dùng về đăng nhập. Đây là lỗi đồng bộ trạng thái UI, không có nghĩa backend GET đã chấp nhận phiên đó.

**Hướng sửa:** kiểm tra phiên lúc bootstrap và xử lý 401 tập trung; xóa trạng thái account đã hết hiệu lực, giữ URL đích để đăng nhập lại. Phân biệt 401 với timeout/503 để tránh đăng xuất oan khi mạng lỗi.

### U11 · P2 · Hai lệnh QA báo “100% đạt” nhưng không chạy kiểm tra

**Nguồn:** [frontend/package.json](../../../../frontend/package.json), dòng 11–12.

`lint:css` và `test:a11y` chỉ chạy `console.log` rồi exit 0. Đã chạy cả hai để xác nhận output; chúng không đo CSS, ARIA, contrast hoặc WCAG.

**Hướng sửa:** thay bằng công cụ kiểm tra thật hoặc bỏ thông báo khẳng định đạt. Không dùng hai lệnh này làm release gate cho đến khi có assertions/thực thi tương ứng.

## Những phần nên nâng cấp sau khi xử lý lỗi

1. **Một lớp session/account chung cho mọi page.** Client API tự gắn Bearer, xử lý 401, cache theo account ID ổn định và reset khi đổi account. Bổ sung E2E với đăng ký/login thật; test legacy anonymous hiện không bắt được U01.
2. **Hợp đồng chất lượng dữ liệu chung.** Trả `as_of`, nguồn, độ đầy đủ, stale/missing theo từng tập dữ liệu; chỉ tính PnL/filter/indicator khi đầu vào thỏa điều kiện. Thống nhất trạng thái “chưa đánh giá” với “không đạt điều kiện”.
3. **DSL và mô phỏng có kiểm tra kiểu/lịch sử.** Hoàn thiện ba lỗi U04/U06/U07, thêm invariants đối chiếu tiền mặt + vị thế, không dùng nến tương lai, và kiểm thử các biểu thức tương đương. Sau đó mới mở rộng slippage, lô, lịch thanh toán và đối chiếu engine paper trading/backtest. Các giả định giao dịch vẫn cần cấu hình và hiển thị rõ, không tự thay đổi quy tắc nghiệp vụ.
4. **Draft có vòng đời khôi phục và xử lý xung đột.** Cùng cơ chế áp dụng cho BCTC, ghi chú và chiến lược; thông báo rõ đã lưu máy hay server. Dữ liệu local theo session hiện còn rủi ro khó truy cập sau lần đăng nhập mới.
5. **Khớp chỉ báo chart với chiến lược.** Chart hiện luôn vẽ EMA; nên hiển thị indicator thực dùng trong preset, vị thế mở và lệnh đang chờ, kèm nguồn dữ liệu và giả định. Đây là đề xuất cải thiện khả năng kiểm tra kết quả, chưa triển khai.

Các component thị trường mới `ForeignFlowButterfly`, `MarketMomentumWidgets`, `SectorHeatGrid`, `VnIndexImpactWidget` còn dữ liệu mẫu/fallback cứng. Đường gọi hiện chưa gắn nhóm `MarketOverviewSubdomain` vào route chính, nên không tính chúng là lỗi UI production đã tái hiện. Cần thay dữ liệu mẫu hoặc dán nhãn demo trước khi tích hợp. Riêng `ForeignFlowButterfly` lấy `Math.abs` trước khi chọn bên bán nên có thể đưa mã mua ròng sang cả bảng bán ròng.

Lint toàn frontend cần được dọn trước khi coi quality gate đạt. Có lỗi React Hook gọi sau early return ở `BookDocumentPane.jsx:19`; luồng sách đã thử không gây crash, vì vậy không nâng finding tĩnh này thành lỗi runtime đã xác nhận.

## Bằng chứng và chạy lại

- [API evidence](../../../../output/playwright/review-2026-10-31/api-evidence.json): định danh owner, revoke, định giá thiếu quote.
- [Math evidence](../../../../output/playwright/review-2026-10-31/math-evidence.json): boolean, lịch sử, RSI.
- [Browser chức năng](../../../../output/playwright/review-2026-10-31/functional/browser-evidence.json).
- [Learn Hub/News](../../../../output/playwright/review-2026-10-31/learning/evidence.json).
- [Font offline](../../../../output/playwright/review-2026-10-31/font-offline/browser-evidence.json).
- Logs build, frontend unit, backend tests và lint ở cùng thư mục `output/playwright/review-2026-10-31/`. Đây là artifacts local, có thể bị gitignore.

Tại root repository, terminal 1:

```bash
MPLCONFIGDIR=/tmp/ns-usage-mpl .venv/bin/python scripts/qa/usage-review-server.py
```

Terminal 2:

```bash
.venv/bin/python scripts/qa/usage-review-api.py
node scripts/qa/usage-review-math.mjs
node scripts/qa/usage-review-browser.mjs
node scripts/qa/usage-review-learning.mjs
REVIEW_BLOCK_FONTS=1 REVIEW_STEPS=registration-real-backend,simulation-default node scripts/qa/usage-review-browser.mjs
```

Các probe trả exit code 1 khi kỳ vọng không đạt. Số liệu phát hiện ở trên mô tả lượt review ban đầu; các script và artifact cùng đường dẫn đã được chạy lại sau sửa, xem báo cáo sửa lỗi để biết kết quả hiện tại. Server QA tạo database tạm mới mỗi lần khởi động, đọc cache market từ repository, không bật scheduler. Dừng server bằng Ctrl+C khi xong.
