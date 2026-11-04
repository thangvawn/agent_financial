# Review logic và dọn file — 31/10/2026

Status: **verified** cho việc dọn file và các tình huống tái hiện dưới đây. Bảy nhóm lỗi logic được ghi nhận, **chưa sửa** trong lượt review này.

## Kết quả chính

- Đã xóa 43 file frontend không được entrypoint hoặc test sử dụng: 30 file tracked và 13 file chưa tracked, tổng 152.666 byte. Đã sao lưu toàn bộ nội dung, kiểm tra CRC/SHA-256 trước khi xóa.
- Đồ thị trước dọn: 322 file JS/JSX/TS/TSX/CSS; 248 nằm trong luồng app, 279 khi tính cả test. Sau dọn còn 279 file, tất cả đều có đường sử dụng từ app/test; không có lỗi parse hay dynamic import tính toán trong phạm vi quét.
- 148 frontend unit + 86 backend tests theo phạm vi đạt; ESLint, 50 CSS files và build đạt. Sáu route đã mở được trên Chromium với fixture API unavailable. Sáu tình huống lỗi UI và ba tình huống backend đã tái hiện riêng.
- Không sửa nghiệp vụ, dữ liệu người dùng, PDF hay package dependencies. Không stage, commit, push hoặc deploy. Hash nội dung staging vẫn như trước lượt review.

## Findings theo mức ưu tiên

### R01 · P1 — Ghi chú gắn với session thay vì tài khoản

Nguồn: [bookReaderModel.js](../../../../frontend/src/features/learn-hub/pages/bookReaderModel.js), dòng 5–6; [useBookReaderState.js](../../../../frontend/src/features/learn-hub/pages/useBookReaderState.js), dòng 56 và 246.

`learn-reader:${sessionId}:${assetId}` đổi sau lần đăng nhập mới. Chromium đã lưu ghi chú bằng phiên A, đăng nhập lại cùng `account_id` bằng phiên B và mở lại cùng sách: editor trống, trong khi bản ghi phiên A vẫn còn trong localStorage. Đây là mất khả năng truy cập từ giao diện, không phải bằng chứng dữ liệu đã bị xóa.

Đề xuất: dùng account ID đã xác minh làm owner; tách credential khỏi khóa dữ liệu. Chỉ di chuyển dữ liệu legacy khi chứng minh được chủ sở hữu, không quét và nhận toàn bộ khóa của phiên cũ. [CoursePlayerPage.jsx](../../../../frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx), dòng 14–21 và [LearningHomePage.jsx](../../../../frontend/src/features/learn-hub/pages/LearningHomePage.jsx), dòng 25–30 cũng dùng session cho tiến độ học; phần này xác nhận bằng đọc source, chưa chạy browser flow hoàn thành bài học.

Bằng chứng: `newSession` trong [browser-evidence.json](../../../../output/playwright/code-review-2026-10-31/browser-evidence.json), [ảnh phiên mới](../../../../output/playwright/code-review-2026-10-31/same-account-new-session.png).

### R02 · P1 — Kết quả scenario cũ có thể gắn vào doanh nghiệp mới

Nguồn: [BctcLabPage.jsx](../../../../frontend/src/features/bctc/pages/BctcLabPage.jsx), dòng 401–407, đặc biệt `setScenarioResult(result)` sau await không kiểm tra scope/request hiện hành.

Đã giữ response scenario FPT, chuyển sang HPG và đợi workbook HPG tải xong, sau đó trả response FPT. Giao diện HPG hiển thị doanh thu dự phóng 987 tỷ từ fixture FPT, cả trong bảng và khối kết quả. Reset state khi đổi mã không ngăn response cũ về sau đó ghi đè.

Đề xuất: khóa kết quả theo ticker, kỳ và request hiện hành; hủy hoặc bỏ qua request lỗi thời, bao gồm các lần chạy scenario nối tiếp.

Bằng chứng: `staleScenario` trong [bctc-evidence.json](../../../../output/playwright/code-review-2026-10-31/bctc-evidence.json), [ảnh HPG với kết quả FPT](../../../../output/playwright/code-review-2026-10-31/bctc-stale-scenario.png).

### R03 · P1 — Công cụ danh mục của agent báo lỗ khi thiếu giá

Nguồn: [agent_tools.py](../../../../src/risk_dashboard/modules/market_portfolio/application/agent_tools.py), dòng 198–216, 240–245 và 270–274; [schema snapshot](../../../../src/risk_dashboard/modules/market_portfolio/schemas/agent_tools.py), dòng 67–80.

Vị thế thiếu quote có `market_value=None` nhưng tổng vẫn khởi tạo từ 0, rồi tính equity/PnL như đủ dữ liệu. Probe với tiền mặt 90 triệu và 100 FPT giá vốn 100.000, không có quote, trả `market_value=0`, `equity=90 triệu`, `total_pnl=-10 triệu`, `total_pnl_pct=-10`. Cờ freshness `partial` không làm các con số này trở nên xác định. Luồng API danh mục thường đã có xử lý missing quote, nhưng công cụ agent còn logic riêng và không đồng nhất.

Đề xuất: thống nhất logic định giá giữa service và agent; tổng chưa xác định phải có trạng thái/giá trị phù hợp trong contract, và exposure/scenario downstream phải xử lý cùng quy tắc.

Bằng chứng: [portfolio-probe.json](../../../../output/qa/code-review-2026-10-31/portfolio-probe.json). Repository và quote provider được thay bằng fixture trong probe; không đặt lệnh thật.

### R04 · P2 — Lưu ghi chú lỗi nhưng không có thông báo; trạng thái đã lưu không phản ánh sửa đổi

Nguồn: [useBookReaderState.js](../../../../frontend/src/features/learn-hub/pages/useBookReaderState.js), dòng 237–256; [ReaderChrome.jsx](../../../../frontend/src/features/learn-hub/pages/ReaderChrome.jsx), dòng 20–22.

Sau khi lưu A rồi sửa thành B, header vẫn hiển thị trạng thái đã lưu cũ. Khi giả lập `QuotaExceededError` tại `localStorage.setItem`, bấm Lưu tạo page error nhưng không có alert; nội dung B vẫn ở editor, trạng thái vẫn là đã lưu. Người dùng có thể đóng/reload tab với niềm tin bản sửa đã được lưu. Không kết luận thao tác Xong tự đóng và xóa ghi chú: exception hiện ngăn callback đóng tiếp tục chạy.

Đề xuất: theo dõi dirty state, catch lỗi đọc/ghi storage, thông báo lưu thất bại và giữ bản nháp; chỉ đánh dấu đã lưu sau thành công. Ảnh base64 và canvas làm quota là tình huống có thể xảy ra trong sử dụng thực tế.

Bằng chứng: `dirtyStatus`, `quota` trong [browser-evidence.json](../../../../output/playwright/code-review-2026-10-31/browser-evidence.json), [ảnh trạng thái sai](../../../../output/playwright/code-review-2026-10-31/dirty-note-status.png).

### R05 · P2 — Tải lại BCTC không kích hoạt request; tra cứu lại cùng mã bị kẹt loading

Nguồn: [BctcLabPage.jsx](../../../../frontend/src/features/bctc/pages/BctcLabPage.jsx), dòng 357–363, 384–388 và 463.

Nút ↻ gọi `setTicker(value => value)`, không thay dependency nên không tải lại. Form tra cứu gọi `setStatus('loading')` rồi set ticker bằng giá trị hiện tại; khi người dùng nhấn Enter lại cùng mã, effect không chạy, bảng biến mất và loading giữ nguyên. Browser xác nhận cả hai thao tác không tạo thêm request workspace. Khi sửa cần xem cả cache `fetchCompanyFinancialWorkspace`: load nonce riêng chưa đủ nếu không truyền `refresh` để bỏ cache.

Đề xuất: một luồng reload rõ ràng cho nút refresh/tra cứu lại cùng mã; chỉ vào loading khi có request, đảm bảo mọi nhánh kết thúc cập nhật trạng thái.

Bằng chứng: `refreshNoOp`, `sameTickerLoading` trong [bctc-evidence.json](../../../../output/playwright/code-review-2026-10-31/bctc-evidence.json), [ảnh loading](../../../../output/playwright/code-review-2026-10-31/bctc-same-ticker-loading.png).

### R06 · P2 — AdaptiveConformalVaR.update lỗi ngay lần gọi đầu

Nguồn: [analytics.py](../../../../src/risk_dashboard/engines/quant/analytics.py), dòng 341–353.

Biểu thức tạo dictionary `record` lại đọc `self.history + [record]` trước khi biến được gán. Gọi `AdaptiveConformalVaR().update(actual_loss=2, predicted_var=1)` phát sinh `UnboundLocalError`; bộ đếm đã tăng lên 1, history vẫn rỗng. Chưa tìm thấy caller nội bộ dùng trực tiếp class này, nên không khẳng định mọi trang tính rủi ro đang hỏng.

Đề xuất: tính tỷ lệ vi phạm từ history và hit hiện tại trước khi tạo record; chỉ cập nhật state sau khi tính xong; thêm contract test cho lần gọi đầu và chuỗi cập nhật. Kiểm tra mô hình định lượng riêng trước khi khẳng định tính đúng thuật toán.

Bằng chứng: [quant-probe.json](../../../../output/qa/code-review-2026-10-31/quant-probe.json).

### R07 · P2 — Cache thị trường đặt nhầm trong cây source

Nguồn: [public.py](../../../../src/risk_dashboard/modules/market_portfolio/api/public.py), dòng 28–29 và [derivatives_feed.py](../../../../src/risk_dashboard/modules/market_portfolio/application/derivatives_feed.py), dòng 30.

Với độ sâu package hiện tại, `parents[4]` là `<repo>/src`, nên hai đường dẫn resolve về `src/data/vn_market`, khác cache chuẩn `data/vn_market` của data hub. Có thể đọc nhầm/mất cache dự kiến khi đóng gói hoặc khi chỉ mount thư mục data. Probe đã xác nhận đường dẫn thực; file derivatives cache hiện có dưới `src/data` được giữ vì vẫn đang được code sử dụng.

Đề xuất: dùng một hàm project root chung, xác định vị trí cache chuẩn và cách đọc dữ liệu legacy trước khi di chuyển/xóa.

Bằng chứng: [cache-path-probe.json](../../../../output/qa/code-review-2026-10-31/cache-path-probe.json).

## Đánh giá cấu trúc và phần giữ lại

Frontend đã chia theo product domain và có lazy route; backend có registry/API/application/domain/infrastructure. Vấn đề nổi bật là logic lặp ở nhiều đường dùng: định giá portfolio giữa service và agent, progress giữa LearningHome/CoursePlayer, và xử lý owner giữa notebook với các module đã chuyển sang account ID. Ưu tiên thống nhất các quy tắc này sau khi bổ sung test hành vi cho findings, chưa cần đổi toàn bộ kiến trúc.

Đã bỏ màn hình cũ, CSS cũ, các lớp chuyển tiếp không có nơi gọi, hook/service không còn dùng và các subdomain scaffold chưa gắn route. Kiểm tra AST import/export, literal dynamic import, chuỗi đường dẫn của test helper và CSS dependency; đối chiếu tham chiếu ngoài frontend trong scripts/tests/backend/docs/plans. Các tài liệu lịch sử vẫn có thể nhắc file đã bỏ; đó không phải runtime dependency.

Giữ compatibility export còn được test sử dụng, các backend package tắt route nhưng còn import/registry, PDF, DB, cache, node_modules và các thư mục skill. Không coi file không được frontend import là file thừa cho toàn dự án. Root node_modules còn tracked là vấn đề quản lý repository có thể xử lý riêng; không xóa dependency đang phục vụ QA.

CodeGraph được thử trước khi đọc code; CLI không hỗ trợ `explore`, fallback script/index không bao phủ frontend hiện tại. Vì vậy kết luận cleanup dựa vào source và đồ thị AST mới, không dựa riêng vào index cũ.

## Kiểm chứng và giới hạn

| Kiểm chứng | Kết quả | Bằng chứng |
| --- | --- | --- |
| Frontend unit | 148/148 đạt | [log](../../../../output/qa/code-review-2026-10-31/frontend-tests.log) |
| ESLint | Đạt | [log](../../../../output/qa/code-review-2026-10-31/frontend-lint.log) |
| CSS syntax | 50 file, 0 lỗi | [log](../../../../output/qa/code-review-2026-10-31/frontend-css.log) |
| Build | Đạt; outDir riêng trong `/private/tmp` | [log](../../../../output/qa/code-review-2026-10-31/frontend-build.log) |
| Backend regression theo phạm vi | 86/86 đạt | [log](../../../../output/qa/code-review-2026-10-31/backend-tests.log) |
| Backend probes | 3/3 tái hiện được vấn đề; không có nghĩa lỗi đã sửa | [script](../../../../output/qa/code-review-2026-10-31/test_review_probes.py), [log](../../../../output/qa/code-review-2026-10-31/backend-probes.log) |
| Chromium | 3 probe notebook + 3 probe BCTC; 6 route smoke đạt | [reader/routes](../../../../output/playwright/code-review-2026-10-31/browser-evidence.json), [BCTC](../../../../output/playwright/code-review-2026-10-31/bctc-evidence.json) |
| Đồ thị sau cleanup | 279/279 reachable, không lỗi parse | [JSON](../../../../output/qa/code-review-2026-10-31/frontend-graph-after.json), [script](../../../../output/qa/code-review-2026-10-31/frontend-graph.mjs) |
| Ruff F821/F811/F823 | Còn 6 diagnostics trong source hiện có | [log](../../../../output/qa/code-review-2026-10-31/backend-static.log) |

Ruff: `record` là runtime bug R06. Năm diagnostic còn lại thuộc annotation (`FreshnessState`, `Any`, `OpsInvestigationReport`); không kết luận các hàm crash chỉ vì các cảnh báo này. Các module dùng postponed annotations và biến local annotation không được đánh giá như biểu thức runtime.

Backend regression gồm personal library, book source, reader proxy, auth/ownership & valuation fixes, product registry và profile serialization. Test runner đặt DB tạm trước import; browser server dùng DB, thư mục upload và build riêng, tắt lifecycle scheduler. Không chạy bộ test đầy đủ hoặc gọi provider giá thật. Route smoke dùng fixture unavailable để kiểm tra route/chunk/error state, không chứng nhận dữ liệu live; `/home` khi đã đăng nhập chuyển sang Market theo thiết kế. Một page error quota là lỗi cố ý tái hiện; không gộp thành browser pass không lỗi.

Staging fingerprint trước/sau: `38f8fe1906f7dcd23ef9f97d84a7bab92051ebf08cc60ac7bc90a6bcd21d41ec`. Workspace đã có nhiều sửa đổi và dữ liệu live đang được Docker dùng; không coi thay đổi hash DB/cache đang chạy là kết quả kiểm chứng cleanup. Không giải quyết sự cố DB lịch sử trong lượt này.

## Phục hồi và danh sách file đã dọn

[ZIP phục hồi](../../../../output/qa/code-review-2026-10-31/unused-frontend-backup.zip) chứa đủ 43 file với đường dẫn gốc và `MANIFEST.json`; [manifest ngoài ZIP](../../../../output/qa/code-review-2026-10-31/cleanup-manifest.json) ghi SHA-256, kích thước và trạng thái tracked. Khi cần phục hồi, kiểm tra file đích chưa có sửa đổi mới rồi giải nén file được chọn vào repo root. Không giải nén ghi đè hàng loạt.

| File | Trước cleanup |
| --- | --- |
| `frontend/src/components/market/MarketBreadth.tsx` | untracked — có trong ZIP |
| `frontend/src/components/market/index.ts` | untracked — có trong ZIP |
| `frontend/src/features/bctc/components/BctcActionBridge.jsx` | tracked |
| `frontend/src/features/bctc/content/ratioDefinitions.js` | tracked |
| `frontend/src/features/bctc/pages/FinancialRatioPage.jsx` | tracked |
| `frontend/src/features/bctc/services/index.js` | tracked |
| `frontend/src/features/financials/pages/FinancialRatioPage.jsx` | tracked |
| `frontend/src/features/home/analytics/events.js` | tracked |
| `frontend/src/features/home/index.js` | tracked |
| `frontend/src/features/home/schemas/homeOnboardingSchemas.js` | tracked |
| `frontend/src/features/index.js` | tracked |
| `frontend/src/features/learn-hub/hooks/useLearningHome.js` | tracked |
| `frontend/src/features/learn-hub/hooks/useLearningMutations.js` | tracked |
| `frontend/src/features/learn-hub/hooks/useLearningNextLessonBundle.js` | tracked |
| `frontend/src/features/learn-hub/pages/BookGrid.jsx` | tracked |
| `frontend/src/features/learn-hub/pages/LearnHubPage.jsx` | tracked |
| `frontend/src/features/learn-hub/pages/LibraryMedia.jsx` | tracked |
| `frontend/src/features/learn-hub/types/learningTypes.js` | tracked |
| `frontend/src/features/learn-hub/utils/mediaUtils.js` | tracked |
| `frontend/src/features/market-portfolio/components/market/index.ts` | untracked — có trong ZIP |
| `frontend/src/features/market-portfolio/pages/LeadersPanel.jsx` | tracked |
| `frontend/src/features/market-portfolio/subdomains/SubdomainNavBar.jsx` | untracked — có trong ZIP |
| `frontend/src/features/market-portfolio/subdomains/index.js` | untracked — có trong ZIP |
| `frontend/src/features/market-portfolio/subdomains/market-overview/MarketOverviewSubdomain.jsx` | untracked — có trong ZIP |
| `frontend/src/features/market-portfolio/subdomains/marketSubdomains.js` | untracked — có trong ZIP |
| `frontend/src/features/market-portfolio/subdomains/portfolio-tracker/PortfolioTrackerSubdomain.jsx` | untracked — có trong ZIP |
| `frontend/src/features/market-portfolio/subdomains/priceboard-screener/PriceboardScreenerSubdomain.jsx` | untracked — có trong ZIP |
| `frontend/src/features/market-portfolio/subdomains/ticker-deepdive/TickerDeepdiveSubdomain.jsx` | untracked — có trong ZIP |
| `frontend/src/features/news/pages/components/TodayBriefSection.jsx` | tracked |
| `frontend/src/features/news/pages/newsEconomicCalendarUrl.js` | tracked |
| `frontend/src/features/simulation/components/ActionProposalModal.jsx` | tracked |
| `frontend/src/features/simulation/index.js` | tracked |
| `frontend/src/features/simulation/services/simulationAgentApi.ts` | tracked |
| `frontend/src/features/simulation-lab/components/SimulationResearchPanel.jsx` | tracked |
| `frontend/src/features/simulation-lab/pages/simulation-lab-workspace.css` | tracked |
| `frontend/src/features/simulation-lab/services/index.js` | tracked |
| `frontend/src/features/simulation-lab/services/proLabApi.js` | tracked |
| `frontend/src/hooks/useMarketIndices.ts` | untracked — có trong ZIP |
| `frontend/src/pages/index.js` | tracked |
| `frontend/src/services/marketDataService.ts` | untracked — có trong ZIP |
| `frontend/src/shared/agentic/ActionProposalReview.jsx` | tracked |
| `frontend/src/shared/ui/ProductModuleShell.jsx` | tracked |
| `frontend/src/types/market.ts` | untracked — có trong ZIP |
