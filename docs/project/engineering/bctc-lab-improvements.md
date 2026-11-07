# BCTC Lab — điều hướng và tính chỉ số

Ngày: 05/11/2026 · Trạng thái: in_progress

## Kết quả và tiêu chí
- Điều hướng cho biết trang hoặc tab hiện tại, các nút đưa tới đúng nội dung và dùng được trên desktop/mobile.
- Bộ tính cho phép chọn kỳ, tự lấy khoản mục đã công bố hoặc nhập tay; hiển thị công thức, kết quả và thiếu dữ liệu, không sửa báo cáo gốc.
- Lọc kỳ và tìm chỉ tiêu trong bảng; chọn năm/quý và đơn vị vẫn dùng được trên màn hình nhỏ.
- Biểu đồ nằm trong vùng, không biến dữ liệu thiếu thành 0 hoặc nối qua kỳ thiếu; tỷ lệ đường cùng thang.
- Kiểm tra bằng test hành vi, lint, CSS, build và giao diện nếu trình duyệt khả dụng.

## Đầu việc
1. in_progress — Điều hướng, tìm kiếm và lọc.
2. in_progress — Bộ tính chỉ số từ dữ liệu hoặc nhập tay theo kỳ.
3. in_progress — Sửa biểu đồ và responsive.
4. ready — Kiểm chứng và bàn giao phạm vi, giới hạn.

Giả định: giá trị nhập tay chỉ phục vụ tính thử trong phiên; báo cáo gốc và dữ liệu máy chủ không thay đổi. Chỉ số dùng số cuối kỳ khi công thức ghi rõ điều đó.

## Kiểm chứng và giới hạn

- `npm run lint` và `npm run lint:css`: đạt; test `FinancialCalculator`: 2/2 đạt, kiểm tra công thức, số thiếu và mẫu số 0.
- `docker compose exec -T frontend npm run build -- --emptyOutDir false`: đạt. Build trên host thất bại vì `node_modules` thiếu `d3-hierarchy`, dù dependency được khai báo; container có dependency và build được.
- Chưa thử trực quan: browser access host không khả dụng trong phiên. Chưa kiểm chứng thao tác autofill với provider thật hoặc responsive bằng trình duyệt; giữ task kiểm chứng mở.
- Bộ tính hiện có 8 chỉ số, nhập tạm trong phiên; đổi kỳ hoặc đơn vị xóa đầu vào. Biểu đồ cột hiện không vẽ số âm và có chú thích; chưa có biểu đồ số âm. Bộ lọc kỳ áp dụng cho bảng và bộ tính, chưa lọc chuỗi biểu đồ. Chưa triển khai thư viện toàn bộ công thức hoặc lưu các giá trị nhập.

## Mở rộng danh mục chỉ số — 05/11/2026

Yêu cầu: nghiên cứu, phân nhóm chỉ số và vẽ theo kỳ. Đã xây dựng 35 chỉ số phổ biến cho doanh nghiệp phi tài chính: 7 sinh lời, 4 thanh khoản, 6 đòn bẩy/khả năng trả lãi, 9 hiệu quả hoạt động, 4 dòng tiền, 2 tăng trưởng và 3 định giá. Công thức, phụ thuộc và chú thích cụ thể đặt tại `frontend/src/features/bctc/utils/financialMetrics.js`; UI cho chọn nhóm, tìm, nhập/lấy dữ liệu và xem biểu đồ có số âm, bảng dữ liệu và kỳ thiếu.

Nguồn tham khảo: [CFA Institute — Financial Analysis Techniques](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/financial-analysis-techniques) về phân loại, số dư bình quân và so sánh theo ngành; [IFRS IAS 33](https://www.ifrs.org/issued-standards/list-of-standards/ias-33-earnings-per-share.html/) về EPS. Không tự suy EPS từ số cổ phiếu cuối kỳ. Nợ vay tổng, EPS, giá và cổ tức cần nhập thủ công khi chưa có nguồn chuẩn hóa. ROE/ROA dùng bình quân đầu/cuối kỳ và không quy đổi năm; vòng quay sử dụng kỳ đang chọn; ngày mặc định theo quý/năm dương lịch và có thể chỉnh. Các xấp xỉ được ghi ngay cạnh công thức.

Kiểm chứng: 4 test `FinancialCalculator` đạt (bao gồm dữ liệu nhiều kỳ, số thiếu, mẫu số 0, ROE bình quân và số âm), frontend lint và CSS đạt, build Docker đạt. Đã nhìn thấy trang BCTC trên Chrome nhưng chưa xác nhận bản mới sau tải lại; browser automation không ổn định và người dùng đang tương tác. Chưa kiểm chứng mobile và provider thực tế. Không có danh sách chỉ số phổ quát cho mọi ngành: bộ này chưa bao gồm chỉ số chuyên ngành ngân hàng/bảo hiểm/chứng khoán, dữ liệu định giá lịch sử hoặc toàn bộ biến thể của các công thức. Lọc kỳ bảng vẫn chưa điều khiển biểu đồ cũ.

## Sửa tự điền khoản mục — 05/11/2026

Bộ tính đối chiếu từng kỳ qua dòng chuẩn và dòng tương đương thay vì dừng ở dòng đầu bị thiếu số; nhận `accounts_payable`, khoản trước thuế/lãi vay/thuế theo nhãn báo cáo, và tổng vay khi có đủ hai phần. Không đoán mã dòng tiền: `cfa20` và `cfa22` của FPT lần lượt là tiền thu thanh lý và thu hồi cho vay, không phải CFO/CAPEX. Ô đầu vào hiển thị kỳ nguồn hoặc tình trạng cần nhập thủ công.

Kiểm tra API FPT quý 2026-Q3: doanh thu, trước thuế, lãi vay, thuế, phải trả kỳ này/kỳ trước, tổng vay và CAPEX có số. Test `FinancialCalculator` 5/5, lint, CSS và build Docker đạt. Nguồn tổng hợp năm hiện không luôn cung cấp trước thuế/thuế/lãi vay và giá/EPS/cổ tức vẫn chưa có trong workspace; không suy số thiếu. Chưa dùng thử UI sau thay đổi vì phiên browser trước bị chặn khi đọc trạng thái rộng.

## Khôi phục vị trí bảng — 05/11/2026

Người dùng phản hồi bảng báo cáo ban đầu không còn thấy vì bộ tính đã bị đặt lên trước bảng. Đưa bảng về ngay dưới tab báo cáo, giữ bộ tính ở sau phần biểu đồ; nút BCTC gốc và Bảng chỉ số cuộn về bảng, nút Chỉ số & công thức cuộn tới bộ tính. Lint, kiểm tra CSS và build Docker đạt; chưa kiểm tra trực quan vì trình duyệt của phiên trước bị chặn đọc trạng thái rộng.

## Thư viện công thức thu gọn — 07/11/2026

Thêm thư viện mặc định thu gọn trong bộ tính, chia nhóm và trình bày các công thức, đầu vào của toàn bộ 35 chỉ số từ cùng registry. Công thức có một phép chia được trình bày dạng phân số; thao tác mở chỉ số đưa tới ô tính có sẵn. Bổ sung mục nền tảng, DuPont và đòn bẩy để tham khảo; nhóm đòn bẩy được ghi rõ chưa tính tự động.

Kiểm tra: 6 test FinancialCalculator, lint, CSS và build Docker đạt; app/Redis healthy, dashboard HTTP 200. Health vẫn degraded do panel model tham chiếu đường dẫn cũ đã mất; không suy ra các tính năng phụ thuộc panel đã sẵn sàng. Chưa kiểm tra trực quan trình duyệt trong phiên này.

## Bảng nổi công thức, công cụ đọc và biểu đồ biên — 07/11/2026

- Thay thư viện dạng mở rộng bằng dialog giữa màn hình, có chọn nhóm, nút đóng và thao tác chuyển sang bộ tính; dialog dùng cơ chế modal gốc và đóng bằng Escape.
- Thanh bên phải hiển thị ô đang chọn, kỳ/đơn vị, đối chiếu kỳ liền trước khi có số, công thức hoặc nguồn chỉ tiêu và ghi chú workbook. Không đánh giá công thức bằng kiểm tra giả; nếu đổi tab/chế độ phải chọn lại ô.
- Biểu đồ biên đọc `ratio_groups[].metrics[].series` và tính từ đầu vào khi chuỗi thiếu; không nối qua kỳ thiếu, có bảng số liệu. Đối chiếu API FPT theo năm: 9/9 kỳ có cả ba chuỗi biên.
- Kiểm chứng: 7 test frontend, ESLint, CSS và build Docker đạt. Dịch vụ đang chạy. Không thể kiểm tra giao diện bằng trình duyệt: browser access host không khả dụng; chưa xác nhận thao tác thực tế và bố cục mobile.

## Công cụ đọc BCTC bên phải — 07/11/2026

Tham khảo [Finbar](https://docs.finbar.com/web/extract-data) về chọn dữ liệu và chuỗi thời gian, [ChartExchange](https://chartexchange.com/docs/stocks/financials/) về theo dõi một chỉ tiêu theo kỳ. Thanh bên dùng chính chuỗi giá trị đang hiển thị của dòng bảng, kể cả khi bảng đang lọc một kỳ; thêm so sánh kỳ liền trước/cùng quý năm trước, lịch sử tám kỳ có thể chọn, sao chép ô và thêm ngữ cảnh vào ghi chú. Không giả lập liên kết tài liệu gốc; khi dữ liệu kỳ gốc không có hoặc không dương thì không tính tỷ lệ tăng trưởng. Đổi chế độ/kỳ hoặc tải lại dữ liệu yêu cầu chọn lại ô.

Kiểm chứng: 10 test FinancialCalculator, lint, CSS và build Docker đạt. Chưa kiểm tra trực quan bằng trình duyệt do browser access host không khả dụng; chưa kiểm tra thao tác clipboard hoặc ghi chú trong browser.
