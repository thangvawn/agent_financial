# Review logic Northstar Finance

Ngày rà soát: 30/10/2026. Mốc Git: `459f038`, bao gồm thay đổi chưa commit đang có trong workspace.

Kết quả: 13 phát hiện đáng xử lý, gồm 8 mức P1 và 5 mức P2. P1 là lỗi cần ưu tiên vì làm sai đầu ra chính hoặc ảnh hưởng dữ liệu và phiên người dùng; P2 là lỗi chức năng và kiểm chứng cần sửa tiếp theo. Đây là review có trọng tâm, không phải chứng nhận toàn bộ repository không còn lỗi.

## Phạm vi và phương pháp

Đối chiếu route đang được sử dụng, frontend và backend của Market, Simulation Lab, BCTC, xác thực và trình đọc Learn Hub. Kiểm tra cả code đang chạy trong nhánh chính lẫn thay đổi chưa commit. Simulation Lab hiện dùng `quantaBacktestSimulator.js` ở frontend; test backend Pro Lab không đủ xác nhận hành vi trang này.

CodeGraph đã được thử trước khi tìm kiếm mã nguồn, nhưng executable hiện tại không hỗ trợ lệnh `explore`; không có MCP CodeGraph trong phiên. Phần còn lại được kiểm tra trực tiếp qua mã nguồn và các phép tái hiện cục bộ.

Không sửa source ứng dụng. Không gọi dịch vụ giao dịch, không gửi lệnh thật, không publish hoặc push. Dữ liệu thử nghiệm và database kiểm chứng được tách vào thư mục tạm.

## Các lỗi mức P1

### R01 Trình đọc chèn URL chưa escape vào HTML cùng origin

**Vị trí:** `src/risk_dashboard/modules/learning/api/reader_proxy.py:121`.

Khi nguồn tài liệu trả lỗi HTTP, `target` được nội suy trực tiếp vào thuộc tính `href` có dấu nháy đơn rồi trả về `text/html`. URL qua kiểm tra hostname vẫn có thể chứa dấu nháy và markup trong query. Vì vậy kiểm tra whitelist không ngăn việc thoát khỏi thuộc tính và chèn phần tử HTML; đây là điểm có thể dẫn đến reflected XSS trên origin ứng dụng.

**Kiểm chứng:** gọi hàm thật với upstream giả lập trả 503 và URL thuộc `www.gutenberg.org`, chỉ chèn một `span` vô hại. Response trả 200 và HTML parser nhận được phần tử được chèn. Không thực thi mã đánh cắp phiên hoặc gửi dữ liệu ra ngoài.

**Hướng sửa:** escape thuộc tính bằng `html.escape(target, quote=True)` hoặc trả lỗi có cấu trúc để frontend render text an toàn. Bổ sung kiểm tra URL chứa dấu nháy và markup. CSP có thể bổ sung phòng vệ nhưng không thay cho escape.

### R02 Phiên hết hạn vẫn được chấp nhận qua query session_id

**Vị trí:** `src/risk_dashboard/modules/auth/application/dependencies.py:88`.

Nhánh `resolve_surface_principal` chỉ kiểm tra `session.status == "active"`, không kiểm tra `expires_at` như `ResolveSession`. Các route dùng resolver này, gồm watchlist và portfolio, có thể nhận principal xác thực từ phiên đã hết hạn nếu phiên chưa bị thu hồi bởi một request khác.

**Kiểm chứng:** tạo tài khoản trong database tạm, đặt hạn phiên về ngày trước. Query session vẫn trả `is_anonymous=False` với đúng account; cùng phiên qua Bearer trả 401.

**Hướng sửa:** dùng chung `ResolveSession` cho mọi phương thức truyền phiên; không chuyển một token tài khoản hết hạn thành phiên anonymous hợp lệ. Thêm test hết hạn cho query và header.

### R03 Backtest không thực thi chiến lược người dùng viết

**Vị trí:** `frontend/src/features/simulation-lab/utils/quantaBacktestSimulator.js:180`; điều kiện giao dịch cố định ở dòng 63.

`runDeterministicBacktest(code, params, bars)` bỏ hoàn toàn `code`. Engine luôn chạy giao cắt EMA, sử dụng 95% tiền mặt; các khối `detect`, `act`, quy tắc RSI, Donchian, Bollinger và sizing trong preset không được thực thi. Tên tham số `fast_period` và `slow_period` cũng không được engine đọc như `fast_len` và `slow_len`.

**Kiểm chứng:** chạy hai preset Turtle Donchian và Bollinger trên cùng chuỗi giá; toàn bộ output bằng nhau qua `assert.deepEqual`. Việc thay chiến lược trên giao diện không chứng minh chiến lược đó đã được backtest.

**Hướng sửa:** nối editor với parser và engine hỗ trợ tập quy tắc công bố; từ chối rõ cú pháp chưa hỗ trợ. Nếu chỉ cung cấp EMA, giới hạn editor và preset đúng phạm vi này. Test phải kiểm tra các chiến lược khác nhau cho giao dịch đúng khác nhau trên fixture có chủ đích.

### R04 CAGR Sharpe và Sortino không được tính từ chuỗi lợi nhuận

**Vị trí:** `frontend/src/features/simulation-lab/utils/quantaBacktestSimulator.js:148`.

CAGR bằng tổng lợi nhuận nhân 1,35; Sharpe và Sortino là các hằng số được điều chỉnh theo tỷ lệ thắng hoặc dấu lợi nhuận. Thời lượng backtest, biến động, downside deviation và lãi suất phi rủi ro không tham gia tính, dù Tearsheet hiển thị các giá trị như chỉ số định lượng.

**Kiểm chứng:** 100 nến giá đứng yên cho 0 giao dịch, lợi nhuận 0%, nhưng Sharpe 1,15 và Sortino 1,35.

**Hướng sửa:** tính từ equity returns và thời gian thực tế; quy định kết quả không xác định khi mẫu thiếu hoặc mẫu số bằng 0. Kiểm tra chuỗi hằng, chuỗi có mức giảm biết trước và cùng hiệu suất trên khoảng thời gian khác nhau.

### R05 Bộ lọc cổ phiếu không dùng tiêu chí đã công bố

**Vị trí:** `frontend/src/features/market-portfolio/pages/GlobalTerminalPage.jsx:514`; mô tả tiêu chí tại `frontend/src/features/market-portfolio/services/filterPresetData.js`.

MA20, MA50 và MA200 đều được thay bằng điều kiện tăng giá trong phiên; RSI dùng phần trăm tăng giảm; khối lượng dùng biên độ thay đổi giá. Cổ tức cao, cổ tức đều và P/E rẻ dùng chung điều kiện giá và mức giảm. Khối ngoại gom dùng danh sách ticker cố định. `money_inflow` và `vcp_pattern` có nút chọn nhưng không có nhánh xử lý.

**Kiểm chứng:** chạy nguyên phần lọc trích từ component với một mã có cổ tức 0, P/E 100, ROE 1, giá 50 thấp hơn MA20 100, RSI 20 và volume 1. Mã vẫn lọt các bộ lọc cổ tức cao, P/E rẻ, giá trên MA20, RSI quá mua và khối lượng tăng mạnh.

**Hướng sửa:** dùng dữ liệu đúng chỉ tiêu và đúng khoảng lịch sử; thiếu dữ liệu thì hiển thị chưa đánh giá được. Các preset chưa có logic cần được vô hiệu hóa hoặc ghi rõ chưa hỗ trợ.

### R06 Tín hiệu EMA cắt lên được suy ra sai từ hai giá đóng cửa

**Vị trí:** `frontend/src/features/simulation-lab/utils/quantaTodaySignalEngine.js:26`.

Hai EMA được ước tính lại bằng giá đóng cửa phiên trước thay cho EMA tích lũy. Với kỳ nhanh nhỏ hơn kỳ chậm, một phiên tăng nhẹ có thể bị gắn nhãn giao cắt lên dù xu hướng dài vẫn giảm. Banner hiện mô tả đây là tín hiệu BUY từ EMA.

**Kiểm chứng:** tạo chuỗi giảm rồi tăng nhẹ 100 đồng ở nến cuối. EMA21 thực tính là 111.099, EMA55 là 127.302, nhưng engine trả BUY với lý do EMA21 vừa cắt lên EMA55.

**Hướng sửa:** dùng cùng chuỗi EMA với engine backtest, so sánh EMA nhanh và chậm ở cả hai nến liên tiếp. Chuyển trạng thái vị thế thực từ engine thay vì suy luận chỉ từ danh sách giao dịch đã đóng.

### R07 Dữ liệu thật bị thay bằng giá giả nhưng giao diện vẫn báo dữ liệu thật

**Vị trí:** `frontend/src/features/simulation-lab/utils/quantaBacktestSimulator.js:45`; ngưỡng nhận feed tại `frontend/src/features/simulation-lab/services/quantaMarketDataService.js:45`.

Adapter chấp nhận từ 10 nến và đặt `isReal=true`, nhưng simulator chỉ dùng đầu vào nếu có trên 30 nến. Với 10–30 nến, simulator tự sinh dữ liệu mẫu. Wrapper không truyền ticker nên dữ liệu thay thế còn mặc định là FPT. Metadata hiển thị vẫn lấy từ feed ban đầu.

**Kiểm chứng:** feed HPG 20 nến, giá 26.000, được ghi nhận `isReal=true`; đầu ra mô phỏng trở thành 143 nến mẫu với giá đầu 136.614.

**Hướng sửa:** để tầng nạp dữ liệu quyết định nguồn duy nhất. Engine báo thiếu lịch sử thay vì âm thầm đổi nguồn; metadata phải mô tả chính bộ dữ liệu dùng để tính.

### R08 Ghi chú workbook có thể bị dùng chéo tài khoản trên cùng thiết bị

**Vị trí:** `frontend/src/features/bctc/pages/BctcLabPage.jsx:386`; ghi cache tại dòng 430.

Cache dự phòng dùng khóa chỉ có ticker. Payload có `owner` nhưng khi đọc không kiểm tra chủ sở hữu. Khi A đã lưu cục bộ, A đăng xuất và B đăng nhập trên cùng trình duyệt, một lỗi tải workbook có thể đưa ghi chú của A vào màn hình B. B lưu lại sẽ đưa nội dung này vào workbook của mình.

**Kiểm chứng:** thực thi nguyên phần effect với cache thuộc `user-a` và phiên `user-b`, giả lập lỗi tải API. Setter ghi chú nhận `private user-a note`. Điều kiện là lỗi tải API; response 404 bình thường được adapter chuyển thành `null`, không đi qua catch này.

**Hướng sửa:** namespace cache bằng owner và ticker, xác nhận `owner` khi đọc, xóa trạng thái màn hình khi đổi tài khoản. Có test chuyển người dùng và offline fallback.

## Các lỗi mức P2

### R09 Adapter nến giờ làm mất giờ và tạo timestamp trùng

**Vị trí:** `frontend/src/features/simulation-lab/services/quantaMarketDataService.js:11`.

`split('T')[0]` biến mọi nến cùng ngày thành cùng timestamp. Giao diện có lựa chọn 1H, nhưng chart nhận trực tiếp các timestamp này tại `SimLabMultiChart.jsx:56`; dữ liệu không còn thứ tự thời gian phân biệt mà chart yêu cầu. Backtest cũng mất thông tin thời điểm trong ngày.

**Kiểm chứng:** nến 09:00 và 10:00 cùng ngày đều trở thành `2025-01-01`.

**Hướng sửa:** giữ timestamp đầy đủ hoặc UTC epoch cho intraday, chuẩn hóa và kiểm tra tăng nghiêm ngặt trước khi truyền chart; không âm thầm gộp nến giờ thành ngày.

### R10 Đổi sang mã chưa có workbook giữ nguyên revision và ghi chú mã trước

**Vị trí:** `frontend/src/features/bctc/pages/BctcLabPage.jsx:370`.

Khi API tải mã mới trả 404, adapter trả `null`; effect thoát mà không reset `modelRevision`, ghi chú hay giả định. Ví dụ HPG đã lưu revision 1 rồi chuyển VCB chưa có model: VCB giữ revision 1, trong khi backend chờ 0. Save nhận 409 nhưng catch báo chung máy chủ chưa sẵn sàng và lưu cục bộ, khiến workbook mới không được lưu lên server.

**Kiểm chứng:** chạy effect với phản hồi `null`, trạng thái vẫn giữ revision 1 và ghi chú HPG. Backend kiểm tra `expected_revision` tại `src/risk_dashboard/modules/financials_product/api/public.py:455`.

**Hướng sửa:** reset state theo owner và ticker trước khi tải; xử lý riêng chưa có model, xung đột revision và mất mạng. Không diễn giải 409 là server offline.

### R11 PnL từng giao dịch bỏ phí mua đã khấu trừ khỏi tiền mặt

**Vị trí:** `frontend/src/features/simulation-lab/utils/quantaBacktestSimulator.js:83`.

Lúc mua, cash bị trừ cả phí 0,15%; lúc ghi PnL, giá vốn chỉ là số cổ phiếu nhân giá mua. Vì vậy PnL nhật ký cao hơn PnL thực, kéo theo win rate và profit factor có thể sai ở giao dịch sát hòa vốn. `retPct` còn là lợi nhuận giá trước phí.

**Kiểm chứng:** fixture 600 cổ phiếu, giá mua 153.915, giá bán 133.990: PnL báo -12.155.985 đồng; PnL sau đủ phí làm tròn khoảng -12.294.508 đồng. Chênh lệch trước làm tròn là phí mua 138.523,5 đồng.

**Hướng sửa:** giữ cost basis gồm phí mua, dùng thống nhất net PnL cho nhật ký và chỉ số tổng hợp. Nếu muốn hiển thị gross return thì đặt nhãn riêng.

### R12 Nút đăng xuất không thu hồi phiên server

**Vị trí:** `frontend/src/app/AppShell.jsx:149`.

`ConnectedWorkspaceNav` gọi `openLogout`, nhưng handler chỉ xóa localStorage và đổi trang. Hook `useAuth.logout` đã có request tới endpoint thu hồi phiên nhưng không được sử dụng ở luồng này. Phiên đã cấp còn hiệu lực tại server cho tới khi hết hạn hoặc bị thu hồi bằng đường khác.

**Kiểm chứng:** thực thi handler với storage và fetch giả lập: session cục bộ bị xóa, số request mạng là 0. Backend `/auth/logout` đã có cơ chế revoke và test riêng.

**Hướng sửa:** nối nút với thao tác logout server bằng token hiện tại, đồng thời dọn trạng thái cục bộ; xử lý rõ trường hợp request thu hồi thất bại.

### R13 Test runner trả thành công khi assertion thất bại

**Vị trí:** `frontend/scripts/test-runner.mjs:40`.

Runner chỉ đặt exit code khi stream phát sự kiện `error`. Assertion thất bại được báo qua test events; handler `end` hiện trống. Bởi vậy CI dựa vào exit code có thể cho qua một suite lỗi.

**Kiểm chứng:** sao chép chính runner sang thư mục tạm với một test `assert.equal(1, 2)`. Output có `fail 1` nhưng process trả exit code 0. Không thêm test cố tình lỗi vào repository.

**Hướng sửa:** xử lý `test:fail` để đặt `process.exitCode = 1`, hoặc dùng trực tiếp `node --test`. Kiểm tra chính runner bằng cả fixture đạt và fixture thất bại.

## Kiểm chứng đã chạy và giới hạn

| Kiểm chứng | Kết quả |
| --- | --- |
| `npm run test:unit` trong frontend | Báo 64 test đạt, 0 thất bại; có log Vite WebSocket EPERM do môi trường sandbox |
| Pytest cho auth principal, workbook model, reader proxy và financial scenario | 17 test đạt |
| Fixture bổ sung cho engine, signal, lọc cổ phiếu và timestamp | Tái hiện các sai lệch ghi trong báo cáo |
| Phiên hết hạn trong database tạm | Query được chấp nhận, Bearer trả 401 |
| HTML fallback với upstream mock | Xác nhận HTML không được escape; không chạy payload lấy dữ liệu |
| Workbook effects và logout handler | Chạy logic trích nguyên từ source với API/storage giả lập, không phải E2E trình duyệt |
| Runner với test cố tình thất bại trong thư mục tạm | Exit code 0 dù có `fail 1` |

Test hiện có chưa đủ để phủ nhận các phát hiện: một số test simulator chỉ kiểm tra kiểu dữ liệu và sự tồn tại của trường. Phép thử bổ sung mới kiểm tra tính đúng đắn của kết quả và biên phiên người dùng. Chưa chạy toàn bộ backend suite, kiểm thử trình duyệt E2E hoặc xác minh dữ liệu thị trường live trong đợt review này.

## Thứ tự xử lý đề xuất

1. Vá điểm HTML injection, thống nhất xác thực phiên, cách ly cache workbook và nối logout server.
2. Bảo đảm engine thực thi đúng chiến lược, nguồn dữ liệu và công thức; sửa bộ lọc và tín hiệu trước khi dùng chúng để diễn giải kết quả.
3. Sửa trạng thái workbook, timestamp intraday và PnL; bổ sung test kiểm tra kết quả số cụ thể.
4. Sửa exit code test runner trước khi dùng kết quả CI làm điều kiện thông qua thay đổi.
