# Sửa lỗi sau đợt dùng thử — 31/10/2026

Trạng thái: **verified** trên workspace local. Đối chiếu [11 finding U01–U11](USAGE_LOGIC_REVIEW_2026_10_31.md). Không push/deploy. Backend QA dùng SQLite tạm, không dùng tài khoản thật.

## Kết quả sửa

| Finding | Hành vi sau sửa | Bằng chứng |
| --- | --- | --- |
| U01 | GET/POST/DELETE dùng cùng account ID đã xác minh. Bearer ưu tiên; session từ body/query cũng phải hợp lệ. Phiên revoke và owner tùy ý bị từ chối. | API probe; `tests/test_usage_fixes.py`; browser thêm/xóa watchlist, lệnh giấy/danh mục |
| U02 | Thiếu giá: đánh dấu `incomplete`, liệt kê mã thiếu; tổng equity/PnL không được tính giả thành số âm. | Test mất quote và API probe |
| U03 | Blueprint, bookmark và bài thi lưu theo account ID ổn định; đổi tài khoản reset state; đăng nhập lại vẫn đọc được bản lưu của chính account. | Browser hai tài khoản và đăng nhập lại; test import/delete blueprint |
| U04 | Warmup tính từ AST gồm `[n]`, indicator lồng và crossover; `not null` giữ trạng thái chưa xác định. | Unit + math probe: 50 nến không chạy điều kiện cần 101 nến |
| U05 | Online reload khôi phục draft; lệch revision hiển thị lựa chọn, khóa lưu đến khi quyết định; 409 giữ draft. | Browser offline/online, cập nhật server cạnh tranh, giữ nháp và lưu/reload |
| U06 | Boolean equality/inequality hợp lệ; so sánh khác kiểu báo lỗi. | Unit + math probe so sánh ngày vào lệnh |
| U07 | RSI đợi đủ cặp giá hợp lệ liên tiếp và reset sau gap. | Unit + math probe: RSI(SMA) trên giá phẳng bằng 50 |
| U08 | Copilot mở/đóng/áp dụng được; dùng code, dữ liệu và kết quả đang chạy. Bỏ phản hồi AI cố định. | Browser mở → đổi tham số → biên dịch/backtest lại |
| U09 | Bỏ CSS import Google Fonts gây lỗi preload, dùng font fallback. | Browser chặn font: trang vẫn chạy backtest |
| U10 | Xác minh session lúc khởi động, phản ứng với 401 từ API riêng, reset state riêng và giữ trang đích. 503 có retry, không tự xóa session. | Browser revoke/reload và 503/retry; unit session client |
| U11 | CSS script parse file thật. A11y script kiểm DOM thật và exit khác 0 khi không có target/lỗi. | 49 file CSS; browser trang register; lệnh thiếu target exit 1 |

Bổ sung: sửa Hook gọi có điều kiện trong BookDocumentPane, đồng bộ state với ticker, export context để fast refresh hoạt động, và các lỗi biến không dùng. Biểu đồ ForeignFlowButterfly lọc đúng bán ròng trước khi lấy trị tuyệt đối, bỏ dữ liệu mẫu, thêm trạng thái thiếu dữ liệu và thao tác bàn phím; test hồi quy kiểm cả hai chiều mua/bán.

## Dữ liệu cũ và giới hạn có chủ đích

- Watchlist cũ chỉ chuyển từ session thực sự thuộc account đã xác minh. Lặp lại migration không nhân đôi dữ liệu.
- Chỉ nhận danh mục cũ làm danh mục chính khi account chưa giao dịch và có đúng một danh mục cũ có dữ liệu. Nếu có nhiều danh mục với vốn độc lập, hiển thị từng danh mục cũ ở chế độ chỉ đọc; không tự cộng vốn hoặc ghi đè danh mục chính. Test xác nhận account khác không xem được.
- Cache local cũ không có bằng chứng owner được giữ nguyên, không tự gán cho tài khoản đang đăng nhập. Draft BCTC gắn với session hiện tại đã xác minh có thể chuyển sang khóa account.
- Copilot hiện là **kiểm tra quy tắc và thử tham số cục bộ**, có nhãn rõ chưa kết nối AI, chưa xác nhận tối ưu. Không triển khai dịch vụ AI mới trong lượt sửa lỗi này.
- CSS chỉ kiểm cú pháp; a11y smoke chỉ kiểm metadata, tên điều khiển và sự hiện diện của alt. Chưa chứng nhận WCAG, contrast hay toàn bộ thao tác bàn phím.
- Fixture được dùng cho nến, BCTC nguồn và tin tức; auth, workbook, watchlist, paper trade dùng backend thật. Chưa xác nhận chất lượng provider live. Các widget thị trường prototype khác còn dữ liệu mẫu như báo cáo gốc, chưa nằm trong route chính.

## Kiểm chứng

| Phép kiểm | Kết quả |
| --- | --- |
| Frontend unit toàn workspace | **96 passed**, 0 failed |
| Backend phạm vi auth/ownership/market/financial/learning | **78 passed**, 0 failed; 5 cảnh báo thư viện vnstock cũ |
| Facade sau cô lập nguồn terminal bên ngoài | **2 passed** (nằm trong nhóm backend ở trên) |
| Browser chức năng chính | **15 passed**, 0 finding, 0 page error |
| Browser Learn Hub/News/mobile | **8 passed**, 0 finding, 0 page error |
| Browser chặn Google Fonts | **2 passed**, 0 finding, 0 page error |
| API / math probes | Đạt tất cả kỳ vọng |
| Build / ESLint | Đạt; lint 0 lỗi, 0 cảnh báo |
| CSS syntax | **49 file**, 0 lỗi |
| A11y DOM smoke | Trang đăng ký đạt; thiếu target bị từ chối với exit 1 |
| Coverage nhóm test logic frontend | **86,93% line**, **87,62% branch** trên các module được import; không phải coverage toàn frontend |
| Coverage backend owner resolver/migration | **96%**, 55 statements, 2 nhánh dòng xử lý JSON lỗi chưa chạy |

`sessionClient` và `workbookState` đạt 100% line; blueprint storage 93,10%; expression/indicator 100%; strategy compiler 98,13% trong nhóm test logic. Các route/UI được kiểm thêm bằng browser, không tính vào số coverage này.

Bằng chứng local (gitignored): [logs kiểm chứng](../../../../output/playwright/review-2026-10-31/fixes/), [browser chính](../../../../output/playwright/review-2026-10-31/functional/browser-evidence.json), [Learn Hub](../../../../output/playwright/review-2026-10-31/learning/evidence.json), [font](../../../../output/playwright/review-2026-10-31/font-offline/browser-evidence.json), [API](../../../../output/playwright/review-2026-10-31/api-evidence.json), [math](../../../../output/playwright/review-2026-10-31/math-evidence.json).

## Chạy lại

Frontend, từ `frontend/`:

```bash
npm run test:unit
npm run lint
npm run lint:css
npm run build
npm run test:a11y -- http://127.0.0.1:5186/dashboard-static/register
node --experimental-test-coverage --test src/__tests__/logic-fixes/usage.test.js src/__tests__/logic-fixes/math.test.js src/__tests__/logic-fixes/state.test.js
```

Backend, từ root:

```bash
PYTHON_DOTENV_DISABLED=1 MPLCONFIGDIR=/tmp/ns-fixes-mpl RISK_DASHBOARD_APP_STATE_DB=/tmp/ns-fixes-tests.db .venv/bin/python -m pytest tests/test_usage_fixes.py tests/test_auth_google.py tests/test_auth_principal.py tests/test_idor_matrix.py tests/test_logic_review_regressions.py tests/test_financial_workbook_model.py tests/test_market_portfolio_facade.py tests/test_market_portfolio_fills.py tests/test_market_portfolio_agent_security.py tests/test_market_portfolio_agent_integration.py tests/test_market_portfolio_agent_contracts.py tests/test_market_portfolio_agent_tools.py tests/test_financial_upload_validation.py tests/test_company_financial_workspace.py tests/test_financial_scenario.py tests/test_learning.py --cov=risk_dashboard.modules.market_portfolio.application.identity --cov-report=term-missing
```

Không đặt thêm `RISK_DASHBOARD_DB_PATH` khi chạy nhóm này: biến canonical đó sẽ ưu tiên hơn DB tạm mà một số test cũ đặt qua `RISK_DASHBOARD_APP_STATE_DB`.

Browser, root, terminal thứ nhất:

```bash
MPLCONFIGDIR=/tmp/ns-fixes-mpl .venv/bin/python scripts/qa/usage-review-server.py
```

Terminal thứ hai:

```bash
node scripts/qa/usage-review-browser.mjs
node scripts/qa/usage-review-learning.mjs
REVIEW_BLOCK_FONTS=1 REVIEW_STEPS=registration-real-backend,simulation-default node scripts/qa/usage-review-browser.mjs
.venv/bin/python scripts/qa/usage-review-api.py
node scripts/qa/usage-review-math.mjs
```

## Phạm vi Git

RED checkpoint `fad05c0` chứa test tái hiện U01–U11; log RED được giữ trong thư mục evidence. GREEN checkpoint chỉ chọn file của lượt sửa này. 116 mục đã stage từ trước được giữ nguyên. Các chỉnh sửa nhỏ chồng lên BookDocumentPane/GlobalTerminalPage và component prototype đang untracked được giữ trong working tree cùng thay đổi sẵn có, không đưa toàn bộ công việc trước đó của người dùng vào checkpoint. Kết quả kiểm thử ở trên áp dụng cho **workspace hiện tại**.
