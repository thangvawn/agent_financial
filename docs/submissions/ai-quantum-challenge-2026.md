# HỒ SƠ Ý TƯỞNG THAM DỰ AI–QUANTUM CHALLENGE 2026

## Thông tin đề xuất

- **Tên sản phẩm:** Northstar Finance Lab
- **Tên đề tài:** Nền tảng AI giải thích được hỗ trợ phân tích rủi ro và kiểm thử chiến lược đầu tư trên thị trường chứng khoán Việt Nam
- **Chủ đề đăng ký chính:** AI cho Dịch vụ Tài chính thông minh
- **Hướng tác động bổ trợ:** AI cho Giáo dục Tài chính
- **Đội thi:** [Tên đội]
- **Thành viên:** [Họ tên – trường/lớp – vai trò]
- **Người liên hệ:** [Họ tên – email – số điện thoại]

> Ghi chú: Bản mô tả phân biệt rõ ba mức độ: **đã triển khai**, **đang hoàn thiện** và **định hướng phát triển**. Các chỉ số định lượng chỉ được điền sau khi chạy benchmark trên tập dữ liệu và cấu hình cố định.

---

## 1. Bản tóm tắt dùng cho biểu mẫu đăng ký

Nhà đầu tư cá nhân tại Việt Nam hiện phải sử dụng nhiều nguồn rời rạc để theo dõi giá, báo cáo tài chính, dữ liệu vĩ mô và kiểm thử chiến lược. Phần lớn công cụ phổ thông mới dừng ở việc hiển thị thông tin hoặc đưa ra chỉ báo kỹ thuật; người dùng khó trả lời đồng thời bốn câu hỏi: thị trường đang ở trạng thái nào, rủi ro giảm giá trong từng kỳ hạn là bao nhiêu, yếu tố nào tạo ra rủi ro đó, và một chiến lược cụ thể sẽ tác động thế nào đến tài sản của mình. Việc thiếu khả năng giải thích và kiểm chứng dễ dẫn đến quyết định cảm tính, quá tin vào tín hiệu hoặc đánh giá thấp rủi ro đuôi.

Northstar Finance Lab được xây dựng như một nền tảng AI hỗ trợ ra quyết định và giáo dục rủi ro dành cho thị trường chứng khoán Việt Nam. Hệ thống hợp nhất dữ liệu giá–khối lượng, độ rộng thị trường, chỉ báo kỹ thuật, vĩ mô, báo cáo tài chính và dữ liệu danh mục. Trên lớp dữ liệu này, mô hình gradient boosting ước lượng xác suất rủi ro theo ba kỳ hạn 1 tuần, 2 tuần và 1 tháng; kết quả được hiệu chỉnh xác suất và giải thích bằng SHAP. Các mô hình bổ trợ gồm HMM để nhận diện trạng thái Bull/Sideways/Bear, GARCH(1,1) để dự báo biến động ngắn hạn, cùng VaR/CVaR và mô phỏng Monte Carlo để đo lường rủi ro danh mục.

Khác với một hệ thống chỉ phát tín hiệu mua–bán, Northstar Finance Lab cho phép người dùng kiểm chứng giả thuyết trong Simulation Lab. Biểu đồ nến của từng mã hiển thị trực tiếp điểm vào/ra lệnh, đường vốn, mức sụt giảm và trạng thái danh mục qua thời gian. Mỗi nhận định bằng ngôn ngữ tự nhiên đều được sinh từ kết quả định lượng và có cơ chế đối chiếu lại với số liệu nhằm hạn chế diễn giải sai.

Sản phẩm dự kiến được đánh giá bằng quy trình rolling-origin để tránh nhìn trước dữ liệu, sử dụng ROC-AUC, Brier Score, độ chính xác tại ngưỡng cảnh báo, mức sụt giảm tối đa, Sharpe/Sortino và độ nhạy với chi phí giao dịch. Mục tiêu của dự án không phải dự đoán chắc chắn giá cổ phiếu hay thay thế chuyên gia, mà giúp nhà đầu tư hiểu rủi ro, kiểm chứng chiến lược và ra quyết định có kỷ luật hơn.

---

## 2. Bối cảnh và bài toán

### 2.1. Bối cảnh

Thị trường chứng khoán Việt Nam có lượng lớn nhà đầu tư cá nhân, trong khi hành vi ra quyết định thường chịu ảnh hưởng mạnh bởi tin tức, biến động ngắn hạn và các tín hiệu thiếu kiểm chứng. Dữ liệu phục vụ phân tích tồn tại ở nhiều dạng và nhiều nguồn: dữ liệu giao dịch, vĩ mô, báo cáo tài chính, tin tức và dữ liệu danh mục cá nhân. Sự phân mảnh này tạo ra ba khoảng trống:

1. **Khoảng trống dữ liệu:** khó đồng bộ tần suất, mã chứng khoán, ngày giao dịch, đơn vị và nguồn gốc dữ liệu.
2. **Khoảng trống mô hình:** một chỉ báo đơn lẻ không phản ánh đầy đủ xác suất giảm giá, chế độ thị trường, biến động và rủi ro danh mục.
3. **Khoảng trống diễn giải:** người dùng nhận được con số hoặc tín hiệu nhưng không hiểu nguyên nhân, độ tin cậy và điều kiện khiến kết quả thất bại.

### 2.2. Phát biểu bài toán

Với dữ liệu được quan sát đến thời điểm \(t\), hệ thống cần:

- Ước lượng xác suất xảy ra rủi ro giảm giá trong các kỳ hạn 5, 10 và 21 phiên;
- Nhận diện trạng thái thị trường và dự báo mức biến động kế tiếp;
- Giải thích các biến đóng góp làm tăng hoặc giảm rủi ro;
- Đo lường rủi ro của danh mục hiện tại;
- Cho phép kiểm thử chiến lược trên dữ liệu lịch sử mà không sử dụng thông tin tương lai;
- Trình bày kết quả bằng giao diện và ngôn ngữ dễ hiểu, có cảnh báo về giới hạn mô hình.

Đây là bài toán hỗ trợ quyết định dưới bất định, không phải bài toán khẳng định giá tương lai hoặc tự động đưa ra lời khuyên đầu tư.

### 2.3. Người dùng mục tiêu

- Nhà đầu tư cá nhân cần một quy trình phân tích có kỷ luật;
- Sinh viên tài chính, kinh tế và dữ liệu muốn học qua mô phỏng;
- Giảng viên hoặc câu lạc bộ học thuật cần công cụ minh họa mô hình rủi ro;
- Nhóm phân tích nhỏ cần một nền tảng thử nghiệm trước khi mua nguồn dữ liệu thương mại.

---

## 3. Mục tiêu của dự án

### 3.1. Mục tiêu tổng quát

Xây dựng nền tảng AI giải thích được, tích hợp từ dữ liệu đến mô hình và giao diện, giúp người dùng đánh giá rủi ro và kiểm chứng chiến lược đầu tư trên thị trường chứng khoán Việt Nam.

### 3.2. Mục tiêu cụ thể

- Chuẩn hóa một lớp dữ liệu có truy vết nguồn và thời điểm cập nhật;
- Xây dựng điểm rủi ro đa kỳ hạn có hiệu chỉnh xác suất;
- Kết hợp rủi ro thị trường, biến động, trạng thái và rủi ro danh mục;
- Giải thích kết quả ở cấp biến số và chuyển thành nhận định tiếng Việt;
- Xây dựng backtest trực quan với biểu đồ nến, điểm mua/bán, đường vốn và drawdown;
- Đánh giá mô hình theo chuỗi thời gian và công bố cả trường hợp mô hình thất bại;
- Thiết kế hệ thống có khả năng thay thế nguồn miễn phí bằng nguồn dữ liệu thương mại khi mở rộng.

---

## 4. Dữ liệu

### 4.1. Nhóm dữ liệu sử dụng

| Nhóm dữ liệu | Trường dữ liệu chính | Tần suất dự kiến | Vai trò |
|---|---|---:|---|
| Giá và khối lượng | OHLCV, giá điều chỉnh, thanh khoản | Ngày/intraday tùy nguồn | Lợi suất, biến động, xu hướng, backtest |
| Độ rộng thị trường | Tỷ lệ tăng giá, tỷ lệ trên MA20/MA50, phân tán lợi suất, áp lực khối lượng | Ngày | Đánh giá sức khỏe chung của thị trường |
| Chỉ số/vĩ mô | VN-Index, USD/VND, lãi suất, CPI, FDI | Ngày/tháng/quý/năm | Giải thích điều kiện kinh tế và rủi ro hệ thống |
| Báo cáo tài chính | Doanh thu, lợi nhuận, tài sản, nợ, dòng tiền và các tỷ số | Quý/năm | Phân tích sức khỏe doanh nghiệp |
| Danh mục | Mã, số lượng, giá vốn, giao dịch, tiền mặt | Theo sự kiện | VaR/CVaR, lãi/lỗ, phân bổ và stress test |
| Tin tức | Tiêu đề, nội dung tóm tắt, thời gian, nguồn | Gần thời gian thực | Bối cảnh và nghiên cứu mở rộng về sự kiện |

### 4.2. Nguồn dữ liệu dự kiến

- Dữ liệu thị trường Việt Nam: thư viện kết nối các nhà cung cấp trong nước, tệp CSV do người dùng cung cấp và nguồn thương mại khi có giấy phép;
- Dữ liệu đối chiếu và tài sản liên thị trường: Yahoo Finance hoặc nguồn tương đương;
- Dữ liệu vĩ mô chính thức: Tổng cục Thống kê, Ngân hàng Nhà nước và các tệp dữ liệu chính thức do nhóm thu thập;
- Dữ liệu quốc tế bổ trợ: World Bank;
- Báo cáo tài chính: dữ liệu tải lên, nguồn công khai hợp pháp hoặc nhà cung cấp được cấp phép;
- Tin tức: RSS và nguồn được phép khai thác.

Nguồn miễn phí chỉ phục vụ prototype và nghiên cứu. Khi thương mại hóa, nhóm sẽ ưu tiên hợp đồng dữ liệu có SLA, quyền sử dụng rõ ràng và lịch sử điều chỉnh đầy đủ.

### 4.3. Quy trình xử lý dữ liệu

1. Chuẩn hóa mã chứng khoán, múi giờ, lịch giao dịch và đơn vị;
2. Loại bỏ bản ghi trùng lặp, kiểm tra OHLC bất hợp lệ và khối lượng âm;
3. Tách dữ liệu theo thời gian, tuyệt đối không xáo trộn ngẫu nhiên chuỗi;
4. Chỉ dùng dữ liệu đã khả dụng tại thời điểm dự báo để hạn chế look-ahead bias;
5. Lưu nguồn, thời điểm lấy dữ liệu và trạng thái fallback;
6. Gắn cờ dữ liệu thiếu thay vì âm thầm nội suy trong mọi trường hợp;
7. Theo dõi độ đầy đủ, độ trễ và mức sai khác giữa các nhà cung cấp.

### 4.4. Các hạn chế dữ liệu cần công bố

- Nguồn miễn phí có thể chậm, ngắt kết nối hoặc thay đổi giao diện;
- Một số chuỗi vĩ mô chỉ có tần suất năm; việc quy đổi sang tháng chỉ là phép xấp xỉ và phải được gắn nhãn;
- Dữ liệu cổ phiếu hủy niêm yết có thể thiếu, dẫn đến survivorship bias;
- Giá điều chỉnh, sự kiện doanh nghiệp và báo cáo tài chính có thể được sửa đổi sau công bố;
- Dữ liệu tin tức có rủi ro trùng lặp và sai lệch lựa chọn nguồn.

---

## 5. Phương pháp

### 5.1. Tạo đặc trưng

Hệ thống xây dựng bốn nhóm đặc trưng:

- **Kỹ thuật:** lợi suất 1/3/5/7/10/20 phiên, biến động thực tế 5/10/20 phiên, downside volatility, drawdown, khoảng cách và độ dốc đường trung bình;
- **Thanh khoản:** z-score khối lượng, gia tốc khối lượng và áp lực khối lượng;
- **Độ rộng:** tỷ lệ mã tăng, tỷ lệ mã nằm trên MA20/MA50, lợi suất trung bình 5 phiên và độ phân tán;
- **Vĩ mô:** biến động USD/VND, lãi suất, CPI, FDI cùng cờ dữ liệu thiếu.

Mọi phép biến đổi rolling được tính chỉ từ quá khứ đến thời điểm \(t\).

### 5.2. Xây dựng nhãn rủi ro đa kỳ hạn

Prototype sử dụng ba nhãn nhằm phản ánh các dạng rủi ro khác nhau:

- **1 tuần (5 phiên):** xuất hiện drawdown nhỏ nhất dưới \(-1\%\);
- **2 tuần (10 phiên):** lợi suất cuối kỳ dưới \(-1\%\);
- **1 tháng (21 phiên):** lợi suất cuối kỳ dưới \(-2,5\%\).

Các ngưỡng trên là cấu hình nghiên cứu ban đầu, không phải quy luật cố định. Chúng sẽ được kiểm tra độ nhạy theo từng chế độ thị trường và có thể thay đổi dựa trên kết quả thực nghiệm.

### 5.3. Mô hình xác suất rủi ro

Mỗi kỳ hạn sử dụng mô hình **Histogram-based Gradient Boosting Classifier**. Lựa chọn này phù hợp với dữ liệu dạng bảng, mô hình hóa được quan hệ phi tuyến và có chi phí huấn luyện vừa phải. Xác suất đầu ra được hiệu chỉnh bằng **isotonic calibration** để con số ước lượng có ý nghĩa tốt hơn trong quản trị rủi ro.

Điểm tổng hợp hiện dùng trọng số:

\[
RiskScore = 0{,}45P_{1w} + 0{,}35P_{2w} + 0{,}20P_{1m}
\]

Trọng số ưu tiên cảnh báo ngắn hạn nhưng vẫn duy trì góc nhìn trung hạn. Trong thử nghiệm, nhóm sẽ so sánh cấu hình cố định này với trọng số học từ dữ liệu.

### 5.4. Khả năng giải thích

SHAP được sử dụng để xác định các đặc trưng đóng góp lớn nhất vào từng dự báo. Giao diện không chỉ hiển thị “rủi ro cao/thấp” mà còn nêu:

- Năm yếu tố tác động mạnh nhất;
- Yếu tố nào làm tăng hoặc làm giảm rủi ro;
- Giá trị hiện tại của yếu tố;
- Cảnh báo khi dữ liệu thiếu hoặc dự báo ngoài vùng dữ liệu huấn luyện.

### 5.5. Trạng thái và biến động thị trường

- **HMM ba trạng thái** phân loại thị trường thành Bull, Sideways và Bear dựa trên lợi suất và biến động;
- **GARCH(1,1)** ước lượng biến động kỳ vọng một ngày và khoảng biến động 95%;
- Kết quả trạng thái và biến động là lớp bối cảnh, không tự động được coi là tín hiệu mua/bán.

### 5.6. Rủi ro danh mục

Hệ thống tính toán:

- Value at Risk (VaR) và Conditional Value at Risk (CVaR);
- Mô phỏng Monte Carlo cho phân phối lãi/lỗ;
- Drawdown và đóng góp rủi ro theo tài sản;
- Kịch bản stress theo biến động thị trường;
- Backtest VaR và phương pháp conformal thích nghi trong mô-đun nghiên cứu.

### 5.7. Backtest chiến lược

Simulation Lab mô phỏng chiến lược trên dữ liệu OHLCV của từng mã. Giao diện gồm:

- Biểu đồ nến và chỉ báo kỹ thuật;
- Điểm vào lệnh bằng tam giác hướng lên, điểm thoát bằng tam giác hướng xuống;
- Đường vốn, benchmark và drawdown;
- Lịch sử giao dịch, trạng thái vị thế, tiền mặt và lãi/lỗ danh mục;
- Các chỉ số: lợi suất, Sharpe, Sortino, max drawdown, win rate và turnover.

Chi phí giao dịch, trượt giá, lô giao dịch và quy tắc thanh toán phải được đưa vào toàn bộ nhánh tính toán trước vòng đánh giá chính thức. Ở prototype hiện tại, một số tham số đã được lưu phục vụ kiểm toán nhưng chưa được khấu trừ nhất quán trong mọi chiến lược.

### 5.8. Sinh nhận định bằng ngôn ngữ tự nhiên

Lớp diễn giải chuyển kết quả định lượng thành bản tóm tắt tiếng Việt và kiểm tra lại nội dung với đầu ra mô hình. Quy tắc thiết kế là:

- Không tạo ra con số không tồn tại trong dữ liệu;
- Phân biệt dữ kiện, suy luận và khuyến nghị hành động;
- Luôn nêu giới hạn và trạng thái dữ liệu;
- Không sử dụng ngôn ngữ cam kết lợi nhuận.

---

## 6. Kiến trúc hệ thống và sản phẩm

### 6.1. Kiến trúc tổng thể

```text
Nguồn dữ liệu
    ↓
Thu thập – chuẩn hóa – kiểm tra chất lượng – truy vết nguồn
    ↓
Kho dữ liệu SQLite/Redis cache
    ↓
Feature pipeline
    ↓
Risk model ─ HMM ─ GARCH ─ VaR/CVaR ─ Backtest
    ↓
Lớp giải thích và kiểm tra nhận định
    ↓
FastAPI
    ↓
Web app React: Terminal – BCTC – Portfolio – Simulation Lab
```

Backend Python/FastAPI chịu trách nhiệm thu thập dữ liệu, tính toán mô hình, lưu kết quả và cung cấp API. Frontend React/Vite hiển thị terminal thị trường, phân tích báo cáo tài chính, danh mục và phòng thí nghiệm mô phỏng. Redis được dùng cho cache và SQLite cho prototype; kiến trúc cho phép chuyển sang PostgreSQL/TimescaleDB khi khối lượng dữ liệu tăng.

### 6.2. Các màn hình chính

1. **Global Terminal:** cổ phiếu, chỉ số, phái sinh, tài sản số, hàng hóa, watchlist và sự kiện;
2. **BCTC doanh nghiệp:** biểu đồ doanh thu, lợi nhuận, biên lợi nhuận, cấu trúc vốn, dòng tiền và chỉ số định giá;
3. **Portfolio:** vị thế, lãi/lỗ, phân bổ và chỉ số rủi ro;
4. **Simulation Lab:** cấu hình chiến lược, biểu đồ nến, điểm vào/ra, đường vốn, drawdown và nhật ký giao dịch;
5. **Risk Dashboard:** xác suất đa kỳ hạn, trạng thái thị trường, biến động và giải thích SHAP.

---

## 7. Thiết kế thực nghiệm và đánh giá

### 7.1. Chia tập dữ liệu

Nhóm sử dụng **rolling-origin evaluation**: mô hình chỉ huấn luyện trên dữ liệu quá khứ, dự báo một cửa sổ tương lai, sau đó mới mở rộng cửa sổ huấn luyện. Cấu hình prototype dành khoảng 25% cuối chuỗi cho kiểm thử, bước dịch chuyển tối thiểu 5 phiên và yêu cầu ít nhất 60 quan sát huấn luyện. Cấu hình chính thức sẽ được khóa trước khi chạy benchmark.

### 7.2. Chỉ số đánh giá

| Thành phần | Chỉ số |
|---|---|
| Chất lượng dữ liệu | Completeness, freshness, tỷ lệ lỗi, sai khác giữa nguồn |
| Mô hình phân loại | ROC-AUC, Brier Score, precision tại ngưỡng cảnh báo 0,60, calibration curve |
| Backtest | Lợi suất sau chi phí, max drawdown, Sharpe, Sortino, turnover, win rate |
| Rủi ro danh mục | Số lần vi phạm VaR, CVaR, kết quả stress test |
| Hệ thống | Độ trễ API, tỷ lệ cache hit, tỷ lệ fallback thành công |
| Người dùng | Thời gian hiểu báo cáo, mức cải thiện kiến thức, khả năng nhận biết rủi ro |

### 7.3. Baseline so sánh

- Dự báo xác suất không đổi theo tỷ lệ nhãn lịch sử;
- Logistic Regression;
- Tín hiệu kỹ thuật đơn giản như giao cắt MA;
- Buy-and-hold đối với backtest;
- Historical VaR đối với mô hình rủi ro nâng cao.

### 7.4. Kết quả cần điền sau benchmark

- Giai đoạn dữ liệu: **[dd/mm/yyyy – dd/mm/yyyy]**;
- Số mã và số quan sát: **[bổ sung]**;
- ROC-AUC 1w/2w/1m: **[bổ sung]**;
- Brier Score 1w/2w/1m: **[bổ sung]**;
- Precision tại ngưỡng 0,60: **[bổ sung]**;
- Kết quả chiến lược sau phí so với buy-and-hold: **[bổ sung]**;
- Kết quả khảo sát người dùng: **[bổ sung]**.

Không đưa số liệu minh họa vào bản nộp như thể đó là kết quả thực nghiệm.

---

## 8. Tính mới và giá trị của giải pháp

### 8.1. Tính mới trong phạm vi sản phẩm

- Kết hợp dữ liệu thị trường Việt Nam, vĩ mô, doanh nghiệp và danh mục trong một luồng thống nhất;
- Dự báo **xác suất rủi ro đa kỳ hạn** thay vì đưa ra một tín hiệu nhị phân;
- Gắn khả năng giải thích SHAP với trạng thái HMM, biến động GARCH và rủi ro đuôi;
- Cho phép người dùng kiểm chứng nhận định trên biểu đồ nến và đường vốn;
- Chuyển kết quả định lượng thành nội dung tiếng Việt nhưng vẫn có lớp kiểm tra số liệu;
- Thiết kế theo hướng giáo dục: người dùng nhìn thấy cả nguyên nhân, hậu quả và giới hạn của mô hình.

### 8.2. Giá trị kinh tế – xã hội

- Nâng cao hiểu biết về rủi ro cho nhà đầu tư cá nhân;
- Hỗ trợ sinh viên tiếp cận mô hình tài chính bằng dữ liệu Việt Nam;
- Giảm xu hướng ra quyết định dựa trên cảm xúc hoặc tín hiệu không kiểm chứng;
- Tạo nền tảng thử nghiệm cho nghiên cứu học thuật và đổi mới trong dịch vụ tài chính.

### 8.3. Khả năng phát triển

Sản phẩm có thể phát triển theo mô hình freemium cho giáo dục và nhà đầu tư cá nhân; gói dữ liệu nâng cao cho nhóm nghiên cứu; hoặc triển khai nội bộ tại trường đại học, câu lạc bộ đầu tư và doanh nghiệp tư vấn. Mọi phương án thương mại hóa đều phụ thuộc vào quyền sử dụng dữ liệu và yêu cầu pháp lý liên quan.

---

## 9. Rủi ro, đạo đức và tuân thủ

- Không mô tả sản phẩm là công cụ bảo đảm lợi nhuận;
- Không dùng kết quả mô hình thay thế tư vấn đầu tư được cấp phép;
- Công bố nguồn dữ liệu, độ trễ, thời điểm cập nhật và tình trạng fallback;
- Kiểm soát look-ahead bias, survivorship bias, overfitting và data leakage;
- Bảo vệ dữ liệu danh mục cá nhân bằng phân quyền và hạn chế thu thập thông tin không cần thiết;
- Lưu phiên bản mô hình, tham số, dữ liệu đầu vào và kết quả để có thể tái lập;
- Luôn cho phép người dùng xem kết quả định lượng gốc đứng sau phần diễn giải AI.

---

## 10. Kế hoạch phát triển

### Giai đoạn 1 – Hoàn thiện hồ sơ và benchmark

- Khóa phạm vi dữ liệu và tập mã nghiên cứu;
- Hoàn thiện kiểm tra chất lượng dữ liệu;
- Chạy baseline và rolling benchmark;
- Công bố bảng kết quả có thể tái lập.

### Giai đoạn 2 – Hoàn thiện prototype

- Tích hợp phí, trượt giá, lô và quy tắc giao dịch vào toàn bộ backtest;
- Bổ sung mô hình dữ liệu danh mục và nhật ký thí nghiệm;
- Hoàn thiện giao diện giải thích rủi ro và trạng thái dữ liệu;
- Tối ưu hiệu năng API và cơ chế fallback.

### Giai đoạn 3 – Đánh giá với người dùng

- Thử nghiệm với sinh viên và nhà đầu tư cá nhân;
- Đo mức độ hiểu rủi ro trước/sau khi sử dụng;
- Ghi nhận lỗi diễn giải và điều chỉnh UX;
- Hoàn thiện video demo và kịch bản thuyết trình.

### Hướng nghiên cứu lượng tử – chưa phải chức năng hiện tại

Nhóm có thể xây dựng một thử nghiệm nhỏ về tối ưu danh mục bằng QAOA hoặc phương pháp quantum-inspired trên tập con VN30, sau đó so sánh với tối ưu mean–variance cổ điển về chất lượng nghiệm, thời gian tính và khả năng mở rộng. Nội dung này chỉ được đưa vào sản phẩm chính khi có triển khai và benchmark thực tế; hiện tại đây là hướng nghiên cứu mở rộng, không phải kết quả đã đạt được.

---

## 11. Phân công đội thi đề xuất

| Vai trò | Trách nhiệm | Thành viên |
|---|---|---|
| Product/Finance | Xác định bài toán, chỉ số tài chính, kịch bản demo | [Tên] |
| Data Engineering | Thu thập, chuẩn hóa, kiểm tra và lưu dữ liệu | [Tên] |
| AI/Quant | Feature engineering, mô hình, calibration, backtest | [Tên] |
| Backend | FastAPI, database, cache, monitoring | [Tên] |
| Frontend/UX | Dashboard, biểu đồ, trải nghiệm người dùng | [Tên] |

Với đội 3–4 người, một thành viên có thể đảm nhiệm nhiều vai trò.

---

## 12. Kịch bản thuyết trình 90 giây

“Nhà đầu tư cá nhân hiện có rất nhiều dữ liệu nhưng thiếu một quy trình để biến dữ liệu thành quyết định có thể kiểm chứng. Một ứng dụng cho biết giá đang tăng, ứng dụng khác hiển thị báo cáo tài chính, còn công cụ backtest thường tách rời danh mục thực tế. Vì vậy, người dùng vẫn khó biết rủi ro sắp tới là bao nhiêu, tại sao rủi ro tăng và nếu áp dụng một chiến lược thì tài sản sẽ biến động thế nào.

Northstar Finance Lab giải quyết khoảng trống đó bằng một nền tảng AI giải thích được dành cho thị trường chứng khoán Việt Nam. Hệ thống hợp nhất dữ liệu giá, độ rộng, vĩ mô, báo cáo tài chính và danh mục; sau đó ước lượng xác suất rủi ro theo ba kỳ hạn. SHAP giải thích yếu tố làm tăng hoặc giảm rủi ro, HMM nhận diện trạng thái thị trường, GARCH dự báo biến động và VaR/CVaR đo rủi ro danh mục.

Điểm khác biệt là mọi giả thuyết đều có thể kiểm chứng trong Simulation Lab. Người dùng nhìn thấy biểu đồ nến của từng mã, điểm vào–ra, đường vốn, drawdown và lãi/lỗ danh mục. AI chỉ diễn giải kết quả định lượng, không hứa hẹn lợi nhuận và không thay thế chuyên gia. Mục tiêu của chúng tôi là giúp nhà đầu tư Việt Nam hiểu rủi ro trước khi hành động, đồng thời tạo một phòng thí nghiệm tài chính trực quan cho sinh viên và nghiên cứu.”

---

## 13. Checklist trước khi nộp

- [ ] Điền tên đội, thành viên và người liên hệ;
- [ ] Chốt tên sản phẩm và chủ đề đăng ký chính;
- [ ] Chụp 4–6 màn hình thể hiện đúng luồng dữ liệu → rủi ro → giải thích → backtest;
- [ ] Chạy benchmark cố định và điền kết quả thật;
- [ ] Kiểm tra toàn bộ backtest đã trừ phí và trượt giá;
- [ ] Ghi rõ khoảng thời gian, số mã và nguồn dữ liệu;
- [ ] Chuẩn bị demo có phương án dự phòng khi nguồn realtime mất kết nối;
- [ ] Không đưa chức năng đang ở roadmap vào danh sách chức năng đã hoàn thành;
- [ ] Thêm tài liệu tham khảo học thuật theo chuẩn trích dẫn mà cuộc thi yêu cầu;
- [ ] Rút gọn bản tóm tắt theo giới hạn ký tự của biểu mẫu nếu có.
