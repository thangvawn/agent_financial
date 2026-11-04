# Đề xuất bộ lọc cổ phiếu định lượng

Ngày: 01/11/2026 (Asia/Ho_Chi_Minh). Trạng thái: **accepted — engine/API/UI implemented, verified on controlled data** (yêu cầu ngày 01/11/2026). Dữ liệu thật và hiệu quả chiến lược chưa được xác minh đầy đủ.
Phạm vi được yêu cầu: áp dụng bộ lọc theo đặc tả. Triển khai engine/backend/UI và kiểm chứng tính đúng; backtest hiệu quả cần dữ liệu đủ chất lượng và không được suy ra từ unit test.

## 1. Thiết kế đề xuất

Chọn mặc định **tín hiệu cuối ngày (EOD), khung nắm giữ nghiên cứu 5–20–60 phiên**, phục vụ sàng lọc cổ phiếu Việt Nam. Cổ tức/giá trị được kiểm chứng riêng trên 63–126–252 phiên. Đây là giả định thiết kế có thể điều chỉnh, không phải yêu cầu đã chốt về chiến lược giao dịch.

Luồng: toàn bộ cổ phiếu trong phạm vi → kiểm tra chất lượng và thanh khoản → tính chỉ báo → kiểm tra điều kiện → xếp hạng → lọc/sắp xếp → phân trang. Không lấy 50 mã trước rồi mới tính tín hiệu. Giá trong phiên có thể cập nhật trên bảng, nhưng tín hiệu EOD giữ nguyên ngày chốt và không trộn khối lượng giữa phiên với trung bình cả ngày.

Mỗi tín hiệu có: điều kiện kích hoạt, điểm xếp hạng 0–100, các số liệu giải thích, ngày phiên, thời điểm dữ liệu sẵn có, trạng thái chất lượng, phiên bản công thức. Điểm là mức độ đáp ứng tiêu chí, không phải xác suất tăng giá. Mỗi nhóm có điểm riêng; không cộng điểm cổ tức với điểm breakout thành một điểm “nên mua”. Cảnh báo rủi ro hiển thị độc lập, có thể cùng xuất hiện với tín hiệu xu hướng.

## 2. Hiện trạng được kiểm tra

- [stockFilters.js](../../../../frontend/src/features/market-portfolio/services/stockFilters.js): sáu preset đã có điều kiện, sáu preset trả `null`; thiếu đầu vào bị loại và đếm `unavailable`.
- [GlobalTerminalPage.jsx](../../../../frontend/src/features/market-portfolio/pages/GlobalTerminalPage.jsx): lọc trực tiếp `vnSnapshot.items`; server đã giới hạn số mã.
- [API snapshot](../../../../src/risk_dashboard/modules/data_hub/api/public.py): trả `items[:limit]` sau sắp xếp; chưa có engine quét tín hiệu toàn thị trường.
- [global_market_feed.py](../../../../src/risk_dashboard/modules/data_hub/application/global_market_feed.py): có đường lấy lịch sử OHLCV cho mã Việt Nam, nhưng nhánh VN không trả metadata về điều chỉnh giá; có fallback dùng close thay open/high/low và 0 thay volume thiếu. Dữ liệu thuận tiện để vẽ chart chưa mặc nhiên đủ chất lượng để tính tín hiệu.
- [vn_market_feed.py](../../../../src/risk_dashboard/modules/data_hub/application/vn_market_feed.py): có phép ước lượng giá trị mua ròng bằng `(khối lượng mua − bán) × giá hiện tại`; không xem đó là tổng giá trị khớp mua/bán thực tế hay chuỗi lịch sử mua ròng.

Kiểm tra cache chỉ đọc: 1.521 mã snapshot; 0 mã có các trường MA/RSI/đỉnh 20 phiên/khối lượng trung bình/cổ tức/chuỗi mua ròng mà bộ lọc cần. Lịch sử ngày lưu cục bộ bao phủ 31 mã cổ phiếu: 26 mã ≥21 phiên, 7 mã ≥200 phiên, 3 mã ≥274 phiên; không có metadata điều chỉnh giá theo các khóa đã kiểm tra. Số lượng phiên không chứng minh dữ liệu mới, đầy đủ hoặc đã điều chỉnh đúng. Một số file dài kết thúc từ đầu tháng 10 trong khi file ngắn mới hơn.

Bằng chứng: [data-audit.json](../../../../output/qa/quant-screener-proposal/data-audit.json). Đây là ảnh chụp cache tại lúc nghiên cứu, không phải cam kết về khả năng hay độ phủ của nhà cung cấp. Chưa có cơ sở chạy backtest toàn thị trường đáng tin từ tập cache này.

## 3. Cơ sở nghiên cứu và giới hạn áp dụng

MSCI dùng động lượng nhiều kỳ, điều chỉnh biến động và chuẩn hóa trước xếp hạng. Đề xuất dưới học cách chuẩn hóa rủi ro, nhưng dùng cửa sổ và benchmark riêng; không phải bản sao chỉ số MSCI. [MSCI Momentum, bản tháng 4/2025](https://www.msci.com/indexes/documents/methodology/2_MSCI_Momentum_Indexes_Methodology_20250417.pdf).

Chất lượng doanh nghiệp nên gồm khả năng sinh lời, tăng trưởng và an toàn tài chính, thay vì chỉ một ngưỡng P/E. [Asness, Frazzini, Pedersen — Quality Minus Junk](https://www.aqr.com/insights/research/working-paper/quality-minus-junk).

Cổ tức cao cần kiểm tra khả năng duy trì và chất lượng doanh nghiệp; chỉ yield cao có thể chọn doanh nghiệp đang khó khăn. [MSCI High Dividend Yield, bản tháng 8/2025](https://www.msci.com/indexes/documents/methodology/3_MSCI_High_Dividend_Yield_Indexes_Methodology_20250829.pdf).

ATR đo biến động, CMF là đại diện áp lực giá–khối lượng, RSI có thể ở vùng cao/thấp lâu trong xu hướng mạnh. Công thức tham khảo: [ATR](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/atr), [CMF](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/cmf), [RSI](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/rsi).

Các nghiên cứu trên không xác nhận hiệu quả của bộ ngưỡng cụ thể tại Việt Nam. **Toàn bộ ngưỡng, cửa sổ, trọng số và tiêu chí đưa vào sử dụng dưới đây là giả thuyết khởi đầu cần kiểm chứng**, không phải tham số đã được tối ưu hay lợi nhuận đã chứng minh.

## 4. Hợp đồng dữ liệu và điều kiện được đánh giá

| Nội dung | Quy ước đề xuất |
| --- | --- |
| Phạm vi | Cổ phiếu phổ thông HOSE/HNX/UPCoM, phân biệt loại tài sản, mã đổi tên, niêm yết/hủy niêm yết và đình chỉ theo ngày |
| Giá kỹ thuật | OHLC cùng cơ sở điều chỉnh đã xác minh cho chia tách/quyền/cổ tức; lưu raw và hệ số, không trộn close đã điều chỉnh với high/low thô |
| Khối lượng | Cổ phiếu, cùng cơ sở số lượng sau chia tách khi so sánh qua ngày quyền; không áp hệ số cổ tức tiền mặt lên volume |
| Giá trị giao dịch | VND thực tế, phân biệt khớp lệnh/thỏa thuận; không lấy giá đã điều chỉnh nhân volume thô để tính thanh khoản |
| Thời điểm | `session_date`, `available_at`, `source`, `fetched_at`, `is_final`, `adjustment_basis`, `quality_flags`; ngày lấy dữ liệu không thay thế ngày phiên |
| Thiếu dữ liệu | `unknown`, kèm lý do; không thay bằng 0 hoặc nội suy OHLC. OHLC được fallback để vẽ chart phải được đánh dấu và không đi vào CMF/ATR/pattern |
| Tính mới | Đúng phiên hoàn tất gần nhất theo lịch giao dịch; cuối tuần không tự coi dữ liệu thứ Sáu là cũ. Thiếu phiên kỳ vọng phải được giải thích, không âm thầm nén cửa sổ |
| Thanh khoản mặc định | Trung vị giá trị khớp 20 phiên trước ≥5 tỷ VND/phiên; ≥18/20 phiên có giao dịch; phiên hiện tại có giao dịch và không bị đình chỉ |
| Lịch sử | Tín hiệu ngắn: ≥80 phiên hợp lệ để có vùng khởi tạo ATR/RSI; xu hướng MA200 + độ dốc: ≥210 phiên; điểm momentum dài: ≥274 phiên |
| Thông tin công bố | BCTC/cổ tức chỉ được dùng từ lúc công bố và có thể truy cập; lưu bản sửa đổi riêng. Không sử dụng BCTC được công bố sau ngày ra tín hiệu |

5 tỷ/phiên là ngưỡng khởi đầu cho thanh khoản, không phải luật thị trường. UI có bộ lọc thanh khoản riêng; thay ngưỡng phải hiện rõ. Điểm xếp hạng sử dụng phạm vi chuẩn cố định theo ngày, không đổi vì người dùng chuyển từ 50 sang 100 hàng.

Phân biệt `not_eligible` (không đạt phạm vi/thanh khoản), `unknown` (không tính được), `stale` (đánh giá ở phiên cũ), `evaluated` (đã tính: đạt hoặc không đạt). Không gộp tất cả thành “Không có mã phù hợp”. Nguồn điều chỉnh chưa xác minh thì chặn nhóm tín hiệu phụ thuộc, không suy đoán từ đồ thị.

## 5. Công thức dùng chung

`t` là phiên đã hoàn tất. `C,H,L,O,V` là OHLCV chuẩn hóa; `B` là benchmark giá cùng cơ sở với cổ phiếu; `A_t = ATR14[t−1]`. Mọi mẫu số phải hữu hạn và dương. Thiếu trường cần thiết → `unknown`.

```text
SMA_n[t] = mean(C[t−n+1 : t])
HH_n[t]  = max(H[t−n : t−1])          # đỉnh trước hôm nay
LL_n[t]  = min(L[t−n : t−1])
RVOL20[t] = V[t] / mean(V[t−20 : t−1])
TR[t] = max(H[t]−L[t], abs(H[t]−C[t−1]), abs(L[t]−C[t−1]))
ATR14[t] = (13 × ATR14[t−1] + TR[t]) / 14
CLV[t] = (C[t]−L[t]) / (H[t]−L[t])
CMF20[t] = sum((2×CLV[j]−1)×V[j], j=t−19..t) / sum(V[j], j=t−19..t)
RS63[t] = ln(C[t]/C[t−63]) − ln(B[t]/B[t−63])
Slope50[t] = (SMA50[t]−SMA50[t−10]) / (10 × A_t)
Extension[t] = (C[t]−SMA20[t]) / A_t
RSI14[t] = 100 − 100/(1 + WilderAvg(gain,14)/WilderAvg(loss,14))
```

Seed Wilder bằng trung bình 14 quan sát hợp lệ đầu tiên, sau đó dùng truy hồi; không khởi tạo từ dữ liệu tương lai. RSI: loss=0/gain>0 →100; gain=0/loss>0 →0; cả hai bằng 0 →50 theo quy ước phiên bản. Với bar thật H=L, CLV cho điều kiện nến là `null`; CMF cho đóng góp bar đó bằng 0 và ghi số bar không biên độ. Nếu >2/20 bar không biên độ thì CMF không đủ chất lượng cho preset. Không dùng quy ước này để che dữ liệu OHLC bị thiếu.

Benchmark giá mặc định: HOSE→VNINDEX, HNX→HNXINDEX, UPCoM→UPCOMINDEX. Chỉ dùng cùng loại lợi suất/điều chỉnh; nếu cổ phiếu được tính total return thì benchmark cũng phải total return. Nếu không cung cấp được benchmark tương thích, RS là `unknown`; không âm thầm thay bằng 0. Kết quả kinh tế của backtest phải tính cổ tức/quyền và so với benchmark total return hoặc báo rõ giới hạn dữ liệu.

## 6. Thay thế 12 preset hiện có

Các dấu `AND` trong cùng hàng là điều kiện bắt buộc. Bộ lọc cảnh báo không phải chỉ thị bán khống. Tín hiệu kiểu sự kiện được lưu `triggered_on`; UI có thể xem 5 phiên gần nhất nhưng không đổi ngày kích hoạt thành hôm nay.

| ID / tên đề xuất | Điều kiện kích hoạt ban đầu | Mục tiêu và dữ liệu |
| --- | --- | --- |
| Q01 — Breakout 60 phiên có xác nhận | `C > HH60 + 0,25×A`; `RVOL20 ≥1,5`; `CLV ≥0,70`; `C>SMA50`; `Extension≤3` | Giá vượt nền với biên an toàn theo biến động, đóng gần đỉnh ngày; tránh xếp cú tăng quá xa vào cùng tập. OHLCV ≥80 phiên |
| Q02 — Xu hướng tăng bền | `C>SMA20>SMA50>SMA200`; `Slope50>0`; `SMA200[t]>SMA200[t−10]`; `RS63>0` và percentile RS63≥70 | Xu hướng, độ dốc và sức mạnh tương đối. ≥210 phiên + benchmark; chưa có momentum dài vẫn có thể đánh giá điều kiện, điểm nâng cao để trống |
| Q03 — Áp lực mua theo giá–khối lượng | `RVOL20≥1,5`; `C>C[t−1]`; `CLV≥0,70`; `CMF20≥0,10` | Thay “Dòng tiền vào mạnh”. Đây là proxy OHLCV, không phải giá trị tiền mua chủ động thực tế |
| Q04 — Hồi phục từ vùng quá bán | `min(RSI[t−5:t−1])<30`; `RSI[t−1]≤35<RSI[t]`; `C>H[t−1]`; `RVOL20≥1,2` | Thay “Dò đáy”: ghi nhận hồi phục đã xảy ra, không tuyên bố bắt được đáy. ≥80 phiên |
| Q05 — Nền giá co hẹp, thử nghiệm | `C>SMA50`; `NATR10/NATR60≤0,65`; percentile BBWidth20 trong 126 phiên trước≤20; `mean(V[t−4:t])/mean(V[t−24:t−5])≤0,75`; `0≤(HH60−C)/C≤0,08` | Thay tên VCP bằng proxy co hẹp có công thức; không nhận diện VCP đầy đủ. `NATR_n=ATR_n/C`; `BBWidth20=4×stdev_population(C,20)/SMA20`; ≥200 phiên |
| Q06 — Giá tăng quá xa nền | `Extension≥2,5`; `RSI14≥75` | Thay “Cảnh báo đu đỉnh”. Đo trạng thái kéo xa nền, không khẳng định sắp giảm; RSI cao một mình không đủ kết luận đảo chiều |
| Q07 — Suy yếu xu hướng | `C[t−1]≥SMA20[t−1]`; `C[t]<SMA20[t]−0,25×A`; `RVOL20≥1,3`; `CLV≤0,30` | Thay “Đảo chiều giảm”. Cú cắt xuống có xác nhận; trạng thái dài hơn hiển thị số phiên dưới MA20, không lặp sự kiện mỗi ngày |
| Q08 — Áp lực bán bất thường | `(C[t]−C[t−1])/A≤−1`; `RVOL20≥2`; `CLV≤0,25`; `CMF20<0` | Thay “Dấu hiệu bị xả”. Đo giảm mạnh với khối lượng; không suy diễn ai đang bán |
| Q09 — Mua ròng ngoại có trọng số | `F5≥0,02`; ít nhất 3/5 phiên net buy>0; tổng net buy 20 phiên>0 | `F5=sum(net_foreign_value,5)/sum(matched_turnover,5)` cùng VND và cùng phạm vi giao dịch. Cần lịch sử mua/bán thực tế, không dùng ước lượng snapshot |
| Q10 — Cổ tức cao và có khả năng duy trì | `DY_TTM≥5%`; percentile DY≥75 trong các doanh nghiệp trả cổ tức thường xuyên; lợi nhuận kỳ so sánh>0; `0<payout≤0,8`; độ phủ tiền mặt≥1 | Thay ngưỡng 8% đơn độc; mặc định profile phi tài chính, loại khoản đặc biệt khỏi yield thường xuyên. Bổ sung điều kiện thanh khoản |
| Q11 — Cổ tức tiền mặt đều | Có cổ tức thường xuyên đã thực trả trong 3 năm lịch hoàn tất liên tiếp; DPS năm gần nhất≥80% DPS năm trước; `0<payout≤0,8`; độ phủ tiền mặt≥1 | Không đếm cổ tức bằng cổ phiếu hoặc nghị quyết chưa trả như tiền mặt đã nhận; dữ liệu từng sự kiện và lịch trả |
| Q12 — Chất lượng với định giá hợp lý | EPS TTM>0; vốn chủ>0; percentile Quality≥70 và percentile Value≥70 trong ngành | Thay “P/E rẻ” bằng so sánh cùng ngành; cần dữ liệu có thời điểm công bố. Ngân hàng/bảo hiểm/chứng khoán có profile riêng, không dùng debt/EBITDA của công nghiệp |

Q01 mặc định 60 phiên; 20 phiên là cấu hình nghiên cứu riêng có version riêng, không dùng “20–60” mơ hồ hoặc chọn cửa sổ nào cho kết quả đẹp hơn sau khi xem test.

Q05 chỉ báo nền co hẹp, có thể giải phóng theo cả hai hướng. Nếu muốn VCP thực sự: bổ sung detector swing với số nhịp/độ sâu/khối lượng từng nhịp và dữ liệu gán nhãn; pivot có xác nhận phải ghi thời điểm xác nhận, không gán ngược tín hiệu về ngày đáy bằng dữ liệu tương lai. Không đưa vào đợt đầu.

Q09 nếu chỉ có lượng mua/bán: có thể xây một biến thể **tỷ trọng khối lượng ngoại ròng** `sum(buy_vol−sell_vol,5)/sum(total_matched_vol,5)`, có nhãn/unit riêng; không tráo thành giá trị tiền. Thiếu lịch sử 20 phiên → unknown.

Q10–Q11: `DY_TTM = cash_DPS_regular(last365d, ex_date≤t, announced_at≤cutoff) / raw_C[t]`. Các DPS cũ phải quy về cùng cơ sở cổ phần hiện tại. Lưu riêng kỳ vọng tương lai và yield gồm khoản đặc biệt. Payout dùng cổ tức thường xuyên quy thuộc năm tài chính chia EPS cùng năm, chỉ tính khi thông tin kỳ đó đủ và công bố; không lấy dividend tương lai chia EPS quá khứ tùy tiện. Độ phủ tiền mặt phi tài chính = tổng CFO 3 năm hoàn tất / tổng cổ tức tiền mặt thực trả cùng 3 năm, đồng thời CFO năm gần nhất>0; mẫu số phải>0. Đây là sàng lọc sơ bộ, có thể thay CFO bằng FCF ở phiên bản đã kiểm chứng sau.

Q12 phi tài chính: `Quality=mean(pct(ROE_TTM), pct(CFO_TTM/NI_TTM), pct(−NetDebt/EBITDA_TTM))`; chỉ xếp hạng khi NI, vốn chủ và EBITDA dương. `Value=mean(pct(E/P_TTM), pct(EBIT_TTM/EV))`, yêu cầu EV>0. Xếp trong nhóm ngành có ít nhất 20 mã đủ dữ liệu; thiếu thì dùng nhóm ngành mẹ đã khai báo và hiện rõ, nếu vẫn thiếu thì không xếp hạng. Không áp ROE≥15% hoặc P/E≤10 cho mọi ngành. Đây là proxy triển khai tối giản có tham khảo tư duy chất lượng, không phải tái tạo QMJ.

Profile ngân hàng dự kiến dùng ROE, nợ xấu, dự phòng bao phủ, CAR và P/B theo ROE; cần bộ chỉ tiêu thống nhất và đặc tả riêng trước khi bật. Không tự suy ra “an toàn” từ tổng nợ/vốn chủ của ngân hàng.

## 7. Điểm xếp hạng có thể giải thích

Tách **đạt điều kiện** khỏi **mức độ nổi bật**. Một mã đủ điều kiện vẫn xuất hiện khi điểm thấp; điểm phục vụ sắp xếp. `pct(x)` tính ở cùng ngày trên universe chuẩn đủ dữ liệu cho feature, trước bộ lọc UI và phân trang. Dùng average rank cho đồng hạng: `100×(rank−1)/(N−1)`; nếu mọi giá trị bằng nhau →50; N<20 →unknown. Không tính percentile trên 50 mã đang hiển thị.

Điểm ban đầu dùng trung bình đều theo nhóm thông tin độc lập. Không tối ưu hàng chục trọng số, không thưởng cùng một hiện tượng nhiều lần bằng RSI, MACD và MA tương quan cao. Chỉ áp direction đã định; thông số nhạy cảm phải ghi version.

| Preset | Điểm xếp hạng thô 0–100 đề xuất |
| --- | --- |
| Q01 | mean(pct(RS63), pct(log RVOL20), pct(CLV)); điều kiện breakout/Extension là gate |
| Q02 | mean(MomentumRiskAdjustedScore, pct(Slope50)); thiếu lịch sử dài thì score=null, vẫn ghi rõ các gate đã đánh giá |
| Q03 | mean(pct(CMF20), pct(log RVOL20), pct(CLV)) |
| Q04 | mean(pct(RSI[t]−RSI[t−1]), pct(log RVOL20)); chỉ so sánh mã đã qua gate hồi phục, giá trị pct vẫn lấy trên universe chuẩn |
| Q05 | mean(pct(−NATR10/NATR60), pct(−BBWidth20), pct(−volume_ratio)); xếp hạng mức co hẹp, không phải khả năng breakout tăng |
| Q06 | mean(pct(Extension), pct(RSI14)); cao hơn nghĩa là kéo xa nền hơn |
| Q07 | mean(pct((SMA20−C)/A), pct(log RVOL20), pct(1−CLV)) |
| Q08 | mean(pct((C[t−1]−C)/A), pct(log RVOL20), pct(−CMF20)) |
| Q09 | mean(pct(F5), pct(F20)); `F20` cùng định nghĩa 20 phiên |
| Q10 | pct(DY_TTM) sau khi có đủ các trường sàng lọc bền vững |
| Q11 | mean(pct(số năm trả liên tiếp), pct(−CV(DPS 3 năm))); cùng cơ sở cổ phần |
| Q12 | mean(Quality, Value), sau các gate chất lượng/định giá |

`MomentumRiskAdjustedScore`: hai cửa sổ đầy đủ 126 và 252 phiên kết thúc tại t−21 (bỏ tháng gần nhất), lấy lợi suất log cổ phiếu trừ log benchmark cùng cửa sổ, chia biến động năm hóa 252 phiên của cổ phiếu (`stdev_sample(log returns[t−251:t])×sqrt(252)`). Lợi suất 6 tháng dùng `ln(C[t−21]/C[t−147])`; 12 tháng dùng `ln(C[t−21]/C[t−273])`; benchmark có cùng các mốc. Điểm là trung bình percentile của hai tỷ số; cần ≥274 giá đóng cửa. Đây là biến thể đề xuất, khác MSCI ở benchmark, tần suất/độ dài ước lượng biến động và cách chuẩn hóa. Vol=0 hoặc thiếu benchmark →unknown, không cho điểm cực đại.

Không tự đổi mẫu số hoặc phân bổ lại trọng số khi thiếu feature. Lưu `score_components` và `universe_id` để tái hiện. Dùng nhóm “top 20% theo tiêu chí” sau khi xếp hạng điểm, không gắn “rất tin cậy” hoặc “80% thắng”. Nếu sau này cần xác suất, phải có nhãn kỳ hạn, calibration ngoài mẫu, reliability curve/Brier score và khoảng bất định riêng.

Ví dụ **giả lập để giải thích công thức**, không phải khuyến nghị một mã: C=51.200, HH60=50.000, ATR hôm trước=1.000, volume=1,8 triệu, trung bình trước=1 triệu, H=51.500, L=50.300, SMA50=48.000, SMA20=49.000. Mức vượt đỉnh=1,2 ATR, RVOL=1,8, CLV=0,75, Extension=2,2 → qua các gate Q01. Nếu percentile RS/RVOL/CLV là 85/75/80 thì điểm=80/100; không có phép suy ra xác suất lời 80%.

## 8. Kiểm chứng trước khi gắn nhãn hiệu quả

**Đơn vị nghiên cứu:** mỗi preset là một giả thuyết đã ghi trước, có universe, dữ liệu, signal time, entry/exit, kỳ hạn và chi phí riêng. Giữ baseline đơn giản (chỉ vượt đỉnh; chỉ MA; chỉ volume) để đo điều kiện bổ sung có ích thật không.

**Tập lịch sử:** ưu tiên ≥5–7 năm, nhiều trạng thái thị trường, gồm mã đã hủy niêm yết và các thành viên đúng tại từng thời điểm. Nếu chỉ có mã còn sống thì báo survivorship bias và không công bố kết quả như toàn thị trường. BCTC/cổ tức dùng timestamp công bố, không thay mọi bản lịch sử bằng bản sửa mới nhất. Các điều chỉnh quyền phải nhất quán, không cộng cổ tức hai lần.

**Chia thời gian:** walk-forward: 3 năm hình thành/chọn cấu hình, 6 tháng validation, 6 tháng test; dịch 6 tháng. Giữ 12 tháng cuối làm holdout đóng kín. Loại các nhãn train/validation có cửa sổ lợi suất chồng lên test; gap tối thiểu bằng kỳ hạn nhãn đang đánh giá (60 phiên cho kỹ thuật, tối đa252 cho nhóm dài), không coi các cửa sổ lợi suất chồng nhau là mẫu độc lập. Khoảng tin cậy dùng block bootstrap theo thời gian và lưu phụ thuộc chéo giữa mã trong ngày, không bootstrap từng giao dịch như độc lập.

**Thời điểm khớp giả định:** tín hiệu dùng close t chỉ có thể giao dịch từ phiên kế tiếp đủ điều kiện; không khớp ở chính close t. Giá trần/sàn, không có bên đối ứng, đình chỉ, ngày nghỉ, bước giá và chu kỳ thanh toán theo quy định tại ngày giao dịch phải được mô phỏng/đối chiếu khi triển khai. Mua bán giả định chỉ ở mức tham gia nhỏ, ví dụ ≤1% thanh khoản ngày; quy mô vốn phải khai báo. Không suy ra tất cả lệnh đều khớp từ OHLCV ngày.

**Chi phí:** phí, thuế bên bán và spread/slippage theo thị trường/tài khoản/thời điểm; thông số có nguồn và ngày hiệu lực. Có stress-test 1×/2× chi phí và trễ thêm 1 phiên. Chưa chốt con số pháp lý/chi phí hiện hành trong đề xuất này. Cảnh báo được kiểm chứng bằng rủi ro phía trước, không tự biến thành chiến lược short cổ phiếu.

**Thước đo:**

- Giá trị tín hiệu: median/mean lợi suất vượt benchmark 5/20/60 phiên; hit rate với định nghĩa rõ là vượt benchmark sau chi phí; rank IC (Spearman score với forward excess return) và mức chênh top/bottom quintile. Chỉ dùng IC khi đủ mã/không điểm đồng nhất.
- Rủi ro: MAE/MFE, xác suất giảm >1 ATR trong kỳ, drawdown và phân phối đuôi; cảnh báo Q06–Q08 ưu tiên khả năng phân biệt downside so với nhóm đối chứng cùng ngành/thanh khoản/xu hướng.
- Khả năng giao dịch: số mã, số sự kiện không trùng, turnover, tỷ lệ lệnh khớp, capacity, chi phí, mức tập trung ngành. Tín hiệu kéo dài chỉ tính là sự kiện mới khi chuyển false→true; rule tái kích hoạt tối thiểu 5 phiên được cố định trước và đối chiếu sensitivity.
- Danh mục kiểm chứng long-only: đối với Q01–Q04, danh mục equal-weight số vị thế/cap ngành/giữ 20 phiên cố định trước; đánh giá CAGR, Sharpe, max drawdown từ chuỗi P&L theo ngày có xử lý overlap. Không tính Sharpe bằng cách ghép lợi suất 20 ngày chồng nhau như daily return. Nhóm cổ tức/giá trị dùng lịch rebalance chậm hơn và benchmark phù hợp.
- Ghi toàn bộ cấu hình đã thử; dùng điều chỉnh multiple testing/Deflated Sharpe cho kết quả danh mục. DSR xử lý thiên lệch chọn mô hình và phân phối không chuẩn, không sửa dữ liệu bị nhìn trước. [Bailey & López de Prado — Deflated Sharpe Ratio](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf).

**Ngưỡng quyết định nghiên cứu đề xuất:** triển khai trước như “bộ lọc điều kiện” sau khi tính đúng, không tự gắn “đã có lợi thế đầu tư”. Muốn gắn nhãn hiệu quả cần ≥200 sự kiện phân bố qua ít nhất 3 năm và đủ mẫu hiệu dụng; kết quả ngoài mẫu tích cực ở đa số fold, CI95% của excess return trung bình có cận dưới>0, ổn định khi thay ngưỡng ±20%, không chỉ thắng nhờ một ngành/năm, và giữ hướng kết quả sau stress chi phí. Với cảnh báo, kiểm định mức tăng rủi ro giảm giá so với nhóm đối chứng thay cho tiêu chí lợi suất dương. Nếu đã chọn mô hình qua nhiều thử nghiệm, kiểm tra DSR≥0,95 đối với danh mục với số thử có điều chỉnh phụ thuộc và công bố giả định; điều chỉnh kiểm định nhiều giả thuyết cho các thống kê tín hiệu. Các ngưỡng này là cổng quản trị nghiên cứu đề xuất, không đảm bảo hiệu quả tương lai. Thiếu mẫu hoặc không vượt kiểm chứng → nhãn “chưa đủ bằng chứng”, không chọn lại tham số bằng holdout.

## 9. Áp dụng vào kiến trúc và UI

**Backend đề xuất:** đặt indicator functions thuần, registry điều kiện/phiên bản, service quét universe trong module `data_hub` trước; không khởi tạo thêm microservice. Lưu OHLCV chuẩn và chất lượng; batch tăng dần sau khi nhà cung cấp xác nhận EOD, giới hạn đồng thời/rate theo nhà cung cấp, retry/backoff, checkpoint. Không gọi lịch sử 1.500 mã đồng bộ khi user bấm chip. Lưu snapshot tín hiệu bất biến theo ngày/version; đổi ngưỡng tạo version mới và job tính lại.

**API đề xuất:** `/api/v1/public/data-hub/vn-market/screener?signals=breakout&as_of=...&sort=score_desc&limit=50&cursor=...`; phân trang gắn cùng `as_of + formula_version + universe_id`. Nhóm bộ lọc tín hiệu mặc định chọn một để điểm sort có nghĩa; advanced nhiều tín hiệu có `combine=all|any` rõ ràng và người dùng chọn score theo preset nào. Trả `universe_total`, `eligible`, `evaluated`, `unknown`, `stale`, `matched`, `returned`; các tập/count phải có định nghĩa không chồng nhau. Mỗi mã có `matched`, `score`, `triggered_on`, `reason_codes`, `metrics`, `missing_fields`, `data_as_of`, `quality_status`.

**Frontend đề xuất:** [stockFilters.js](../../../../frontend/src/features/market-portfolio/services/stockFilters.js) không còn tính lại ngưỡng tài chính riêng với server; UI chỉ gửi tiêu chí và hiển thị kết quả có giải thích. Giữ biểu đồ và giá hiện tại tách ngày với signal EOD. Khi không có dữ liệu, cho thấy độ phủ và lý do. Không hiển thị “Tìm thấy 0 mã” một mình khi cả thị trường chưa được đánh giá.

Ví dụ câu giải thích với số giả lập: “Breakout 60 phiên · Điểm 80/100 · Vượt đỉnh 1,2 ATR · KL 1,8× · Đóng ở 75% biên ngày · Chốt phiên dd/mm”. Giao diện chi tiết cho xem từng điều kiện đạt/không đạt, phiên bản và nguồn; phần người dùng không cần nhìn tên hàm hay tham số kỹ thuật nội bộ.

## 10. Thứ tự triển khai đề xuất và nghiệm thu

| Đợt | Kết quả quan sát được | Điều kiện nghiệm thu |
| --- | --- | --- |
| P1 | Chuẩn hóa và xem được độ phủ OHLCV/benchmark theo phiên | Đủ provenance/đơn vị/adjustment, kiểm tra ngày quyền, giữ missing; job không ghi vào DB thật khi test |
| P2 | Q01/Q02/Q03/Q06/Q07/Q08 chạy toàn universe đã đủ dữ liệu | Bấm chip thấy kết quả + công thức; đổi 20/50/100 hàng không đổi tổng match/điểm; missing/stale đúng; EOD không đổi theo quote giữa phiên |
| P3 | Walk-forward và báo cáo baseline/chi phí/độ ổn định | Có snapshot/version/split tái hiện được; không leakage, kiểm chứng khớp lệnh; công bố cả ca thất bại và số cấu hình thử |
| P4 | Q04 và Q05 ở nhóm thử nghiệm | Kiểm chứng riêng hồi phục/co hẹp; không gọi là dự báo đáy/VCP đã xác nhận |
| P5 | Q09 khi có lịch sử foreign, Q10–Q12 khi có event/BCTC | Unit giá trị/lượng rõ, dữ liệu point-in-time; ngành tài chính có đặc tả riêng; thiếu dữ liệu không cho match |

Lộ trình trên được viết ở lượt nghiên cứu; yêu cầu tiếp theo “oke thực hiện áp dụng cho bộ lọc” đã cho phép triển khai. Engine 12 preset, API scan/rank trước phân trang, UI giải thích/coverage và đường import đã áp dụng. Collector có checkpoint nhưng feed đang cài thiếu capability; P0 về bao phủ dữ liệu thật và P3 về backtest chưa hoàn tất. Q04/Q05 giữ trạng thái thử nghiệm; Q09–Q12 cần bundle bổ sung, profile ngành tài chính chưa có. Chưa có UI xem lịch sử tín hiệu 5 phiên. Trạng thái thực tế, schema và lệnh vận hành: [hướng dẫn bộ lọc](quant-screener-operations.md); bằng chứng: [session triển khai](../../memory/sessions/2026-11-01-quant-screener-implementation.md).
