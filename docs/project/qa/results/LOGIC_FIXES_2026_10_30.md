# Kết quả sửa logic Northstar Finance

Ngày 30/10/2026. Phạm vi: 13 phát hiện R01–R13 trong `LOGIC_CODE_REVIEW_2026_10_30.md`.

Đã xử lý cả 13 phát hiện. Thay đổi nằm trong workspace; không publish, deploy hoặc push. Các thay đổi có sẵn của người dùng được giữ nguyên.

## Đối chiếu từng phát hiện

| Mã | Thay đổi | Kiểm chứng |
| --- | --- | --- |
| R01 | Escape URL khi dựng HTML fallback của trình đọc | URL chứa markup không tạo thêm phần tử HTML |
| R02 | Query session dùng chung ResolveSession với Bearer; tài khoản hết hạn hoặc revoked nhận 401 | Database tạm và test auth, identity, IDOR |
| R03 | Parser biểu thức có danh sách toán tử và hàm hỗ trợ, thực thi detect/act, sizing và quy tắc từng preset; không dùng eval | Turtle và Bollinger cho giao dịch khác nhau; sửa điều kiện làm đổi giao dịch; từ chối cú pháp và biến không hỗ trợ |
| R04 | CAGR theo thời gian lịch, Sharpe và Sortino theo lợi nhuận đường vốn và giả định Rf; giá trị không xác định trả null | Fixture tính tay, chuỗi vốn phẳng và đường vốn có drawdown biết trước |
| R05 | Lọc theo dữ liệu đúng chỉ tiêu; trường thiếu được tính là chưa đánh giá; vô hiệu hóa preset chưa có quy tắc đầy đủ | Fixture sai điều kiện bị loại; fixture đúng điều kiện được nhận |
| R06 | Tín hiệu dùng quy tắc đã biên dịch hoặc EMA lịch sử đầy đủ; nhận vị thế còn mở từ simulator | Không báo BUY khi EMA nhanh vẫn dưới EMA chậm; vị thế mở nhận HOLD |
| R07 | Engine không sinh dữ liệu mẫu thay đầu vào; adapter báo lỗi nếu không có lịch sử | Feed 20 nến giữ nguyên và bị báo thiếu lịch sử; không hiển thị Tearsheet từ dữ liệu khác |
| R08 | Cache workbook v2 theo owner và ticker; kiểm tra owner trong payload | Unit test và trình duyệt đổi tài khoản khi API lỗi |
| R09 | Nến giờ giữ UTC timestamp riêng; metadata ngày được định dạng riêng cho UI | Hai nến cùng ngày có timestamp khác nhau; chart 1H chạy trong Chromium |
| R10 | Hook workbook reset state theo phạm vi owner/ticker; giữ revision đúng; không biến 409 thành offline save | Từ model FPT revision 2 sang VCB mới: ghi chú trống, lưu expected_revision 0 |
| R11 | Giá vốn gồm phí mua; PnL và return giao dịch dùng cùng giá vốn ròng | Tổng cash cuối kỳ khớp PnL giao dịch đóng; công thức phí hai chiều |
| R12 | Navigation gọi logout server bằng token hiện tại; thành công mới xóa phiên; lỗi có thông báo và cho retry | Chromium kiểm tra 503, retry thành công, token và localStorage |
| R13 | Runner nhận test:fail và đặt exit code 1 | Chạy runner sao chép trong thư mục tạm với assertion cố tình sai |

## Bằng chứng kiểm thử

- Frontend suite: **87 test đạt, 0 thất bại**.
- Bộ hồi quy mới: **23 test đạt**; coverage của các file được nạp bởi bộ này: **86,53% dòng, 87,48% nhánh, 89,21% hàm**. Đây không phải coverage toàn repository.
- Backend được chọn theo phạm vi ảnh hưởng: **51 test đạt, 2 test legacy skip theo gate hiện hành**.
- Chromium với API giả lập: **6 nhóm kiểm chứng đạt**, không có lỗi JavaScript chưa xử lý. Các nhóm gồm chiến lược/nến giờ, dữ liệu thiếu, workbook đổi ticker, workbook đổi tài khoản, logout và kiểm tra lỗi trình duyệt.
- Build Vite thành công. ESLint đạt đối với các module logic mới/thay thế và test hồi quy. `git diff --check` đạt.
- Test RED đã được chạy trước khi sửa: 7 lỗi mô phỏng/dữ liệu, runner exit code và 3 trường hợp backend thất bại đúng nguyên nhân. Các helper trạng thái mới được bổ sung sau khi xác nhận thiếu implementation và kiểm chứng lại hành vi tích hợp.

Frontend SSR tests có thông báo Vite WebSocket EPERM trong sandbox; assertions vẫn đạt. Browser smoke chạy trên preview localhost riêng. Không dùng dữ liệu tài khoản thật hoặc gọi provider để xác nhận độ đúng của dữ liệu thị trường live.

## Hành vi và giới hạn cần biết

Bộ mô phỏng hỗ trợ biểu thức số, so sánh, logic, lịch sử `[n]`, EMA, SMA, RSI, ATR, Donchian, Bollinger và các hành động long đã khai báo. Các preset hiện có và code mới từ Visual Builder dùng cùng engine. Cú pháp khác, biến không khai báo, tham số sai hoặc thiếu lịch sử gây lỗi có thông báo; không tự chuyển sang chiến lược EMA. Khối render là mô tả hiển thị, score không được dùng như nguồn tín hiệu nếu chưa được khai báo bằng biểu thức hỗ trợ. Mô phỏng chạy trên ticker và khung thời gian được chọn ở thanh điều khiển.

Tín hiệu cuối nến thực hiện ở giá mở cửa nến kế tiếp. Mô hình dùng lô 100, phí mua 0,15%, phí và thuế bán 0,25%, chưa áp dụng trượt giá. Điều kiện chờ bán là hai phiên khác ngày quan sát được trong bộ dữ liệu; dữ liệu tuần vì vậy được xử lý thận trọng theo các phiên có dữ liệu, không phải mô phỏng lịch thanh toán sở giao dịch đầy đủ. Giá trị vị thế mở là mark-to-market, chưa trừ phí bán chưa phát sinh.

Rf 4,5%/năm là **giả định**, không phải lãi suất cập nhật. Sharpe/Sortino sử dụng tần suất giả định 252 phiên ngày, 52 phiên tuần hoặc 1260 nến giờ/năm. Chỉ số không xác định hiển thị dấu gạch; không gán số đẹp mặc định. Độ tin cậy tín hiệu không còn được gán phần trăm cố định.

Bộ lọc chỉ đánh giá tập mã đã tải và chỉ tiêu thực có trong dữ liệu. Các preset VCP, dò đáy, đu đỉnh, đảo chiều, dấu hiệu bị xả và bộ tổng hợp P/E–ROE–đòn bẩy được vô hiệu hóa có chú thích vì chưa có định nghĩa/dữ liệu đầy đủ. Những tiêu chí khác thiếu trường đầu vào trả số mã chưa đánh giá được. Không gọi API lịch sử hàng loạt để giả tạo độ đầy đủ của screener.

Cache workbook kiểu cũ không được tự động nhập sang tài khoản mới. Cache cũ được giữ trên thiết bị, nhưng không hiển thị khi chưa xác minh owner. Khi logout server lỗi, phiên cục bộ được giữ lại để người dùng có thể retry thu hồi; giao diện báo rõ thất bại.

## Chạy lại

```bash
cd frontend
npm run test:unit
node --test --experimental-test-coverage src/__tests__/logic-fixes/*.test.js
npm run build
npm run preview -- --host 127.0.0.1 --port 5185 --strictPort
```

Trong terminal khác, tại root repo:

```bash
node scripts/qa/logic-fixes-browser.mjs
MPLCONFIGDIR=/tmp/ns-fixes-mpl RISK_DASHBOARD_APP_STATE_DB=/tmp/ns-verify.db .venv/bin/python -m pytest tests/test_home_onboarding.py tests/test_identity_trust_remediation.py tests/test_idor_matrix.py tests/test_market_portfolio_agent_security.py tests/test_auth_google.py tests/test_auth_principal.py tests/test_logic_review_regressions.py tests/test_financial_workbook_model.py tests/test_reader_proxy.py tests/test_market_portfolio_fills.py tests/test_financial_scenario.py
```

Không đặt `RISK_DASHBOARD_DB_PATH` chung cho nhóm test dùng alias `RISK_DASHBOARD_APP_STATE_DB`: biến canonical có độ ưu tiên cao hơn có thể phá cách ly database giữa các test. Lần chạy cuối đã dùng đúng alias và các fixture tạo database riêng.
