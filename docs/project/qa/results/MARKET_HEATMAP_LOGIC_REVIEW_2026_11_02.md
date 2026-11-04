# Review logic bản đồ thị trường — 02/11/2026

Status: **review lịch sử; HM-01–HM-06 đã được sửa và kiểm chứng ở lượt tiếp theo**. Xem [bản sửa và bằng chứng](MARKET_HEATMAP_LOGIC_FIXES_2026_11_02.md). Nội dung dưới đây mô tả lỗi trước khi sửa; phạm vi là heatmap và nguồn snapshot, không phải toàn bộ dự án.

## Kết quả theo mức ưu tiên

### HM-01 · P1 · Bản thiếu sàn ghi đè snapshot đầy đủ và vẫn báo fresh

- Nguồn: [`vn_market_feed.py`](../../../../src/risk_dashboard/modules/data_hub/application/vn_market_feed.py), `_fetch_ssi_price_board` dòng640–649, `_fetch_snapshot_live` dòng307–310, `_finish_live_items` dòng373–378.
- Tái hiện: tạo cache tạm gồm AAA/HOSE, BBB/HNX, CCC/UPCOM; mock request HNX timeout, hai sàn còn lại trả dữ liệu. Gọi `snapshot(force_refresh=True)`.
- Kết quả: trả và ghi cache chỉ AAA/CCC, `freshness='fresh'`, không có `stale_reason`. Snapshot đầy đủ bị thay bằng tập thiếu cả sàn; fallback không chạy vì danh sách còn lại khác rỗng. Heatmap tính tỷ trọng trên thị trường thiếu dữ liệu mà người dùng không nhận cảnh báo nguồn.
- Hướng sửa: lưu kết quả thành công/lỗi theo từng sàn; kiểm tra completeness trước khi chấp nhận snapshot. Giữ bản đầy đủ gần nhất hoặc dùng fallback cho phần thiếu; phản ánh rõ trạng thái degraded/coverage, không âm thầm trộn phiên khác nhau.
- [Probe hoàn toàn mock, cache tạm](../../../../output/market-heatmap/review/feed-probe.py), [kết quả](../../../../output/market-heatmap/review/feed-findings.json). Đây là tình huống lỗi được mô phỏng, không phải khẳng định nguồn live đang mất HNX.

### HM-02 · P2 · Giao dịch khác 0 hiển thị thành 0

- Nguồn: [`marketHeatmapModel.js`](../../../../frontend/src/features/market-portfolio/services/marketHeatmapModel.js), `formatNumber`/`formatMetric` dòng7–9.
- Chia mọi GTGD cho 1e9 và KL cho 1e6 rồi giới hạn hai số thập phân. Trong snapshot sao chép, **123 mã có GTGD >0 thành “0 tỷ”** và **341 mã có KL >0 thành “0 triệu CP”**. PFL có 150.000 đồng nhưng hộp thông tin hiển thị 0 tỷ; ACE có 100 CP thành 0 triệu CP.
- Diện tích vẫn dùng số gốc nên không sai trọng số, nhưng thông tin đọc được mâu thuẫn với ô đang tồn tại.
- Hướng sửa: đơn vị linh hoạt (đồng/triệu/tỷ, CP/nghìn/triệu CP) hoặc hiển thị `<0,01` thay vì làm tròn thành 0; số chính xác vẫn truy cập được.
- [Probe dữ liệu](../../../../output/market-heatmap/review/model-probe.json), [tái hiện hộp thông tin trên trình duyệt](../../../../output/market-heatmap/review/browser-findings.json).

### HM-03 · P2 · Refresh làm mất mã đang phóng tới

- Nguồn: [`MarketHeatmap.jsx`](../../../../frontend/src/features/market-portfolio/components/MarketHeatmap.jsx) dòng41–50 và [`useHeatmapCamera.js`](../../../../frontend/src/features/market-portfolio/hooks/useHeatmapCamera.js) dòng7–9.
- Focus PFL; mô phỏng GTGD VCB tăng 1%, giữ PFL nguyên vẹn; refresh và chờ worker hoàn tất. Camera vẫn giữ nguyên tọa độ/scale cũ, nhưng treemap đã bố trí lại theo trọng số mới. PFL ra khỏi viewport, hộp thông tin biến mất; vùng nhìn chuyển sang ILC/SVG.
- Nguyên nhân: camera chỉ gắn với kích thước/metric/sàn/ngành, không neo lại mã đang chọn sau đổi layout. Trước đây đây là giới hạn chưa kiểm chứng; nay đã tái hiện cụ thể với thay đổi dữ liệu nhỏ.
- Hướng sửa: neo viewport theo ticker/vị trí tương đối đang xem khi nhận layout mới; giữ quote được ghim khi ticker vẫn còn trong tập dữ liệu. Cân nhắc treemap ổn định giữa lần cập nhật.
- [Kết quả sau khi worker hoàn tất](../../../../output/market-heatmap/review/browser-findings.json), [ảnh](../../../../output/market-heatmap/review/refresh-zoom.png).

### HM-04 · P2 · Thả chuột ngoài khung khiến bản đồ tiếp tục kéo

- Nguồn: [`useHeatmapCamera.js`](../../../../frontend/src/features/market-portfolio/hooks/useHeatmapCamera.js) dòng23–33,45–50.
- Zoom2×, nhấn ở cách mép phải1px, di chuyển ra ngoài khung rồi thả. Pointer đầu tiên chưa được capture; `pointerup` không đến SVG nên pointer vẫn nằm trong Map. Khi đưa chuột vào lại, camera dịch từ x=-765 sang x=-854 dù không giữ nút chuột.
- Hướng sửa: bắt và kết thúc đầy đủ vòng đời pointer (capture/release/lostcapture hoặc listener ngoài SVG), xử lý mất focus và tránh pan khi mouse buttons=0.
- [Tái hiện bằng thao tác chuột thật trong Chromium](../../../../output/market-heatmap/review/browser-probe.mjs), [kết quả](../../../../output/market-heatmap/review/browser-findings.json).

### HM-05 · P2 · Nút tải lại không phục hồi lỗi worker khi dữ liệu không đổi

- Nguồn: [`useHeatmapLayout.js`](../../../../frontend/src/features/market-portfolio/hooks/useHeatmapLayout.js) dòng5–21.
- Cho worker đầu tiên lỗi, sau đó cho phép worker mới hoạt động bình thường. Bấm Tải lại; API trả cùng snapshot. Worker count vẫn1 và lỗi vẫn hiện vì effect phụ thuộc duy nhất vào key dữ liệu/kích thước/options; refresh chỉ chạy fetch, không đổi key hoặc trạng thái lỗi.
- Hướng sửa: có cơ chế retry layout riêng hoặc đưa refresh/retry generation vào dependency. Thêm ca worker lỗi tạm thời rồi hồi phục với dữ liệu không đổi.
- [Bằng chứng worker count và lỗi còn hiển thị](../../../../output/market-heatmap/review/browser-findings.json).

### HM-06 · P3 · Sau pan, Enter trên tên ngành bị chặn

- Nguồn: [`useHeatmapCamera.js`](../../../../frontend/src/features/market-portfolio/hooks/useHeatmapCamera.js) dòng25–27,49–51.
- Kéo bản đồ, về Toàn cảnh, focus tên Bất động sản bằng bàn phím và Enter: scale vẫn1. Click chuột cùng nút thì scale thành1,5784.
- `suppressClick` chỉ reset ở pointerdown; click tạo từ bàn phím không có pointerdown nên tiếp tục bị chặn bởi `onClickCapture`.
- Hướng sửa: chỉ bỏ synthetic pointer click ngay sau drag, không chặn click từ bàn phím; reset trạng thái đúng lúc kết thúc gesture.
- [Kết quả bàn phím so với click chuột](../../../../output/market-heatmap/review/browser-findings.json).

## Phần kiểm tra đạt và giới hạn

- Chạy lại **8 test frontend heatmap**: pass. Chạy **4 test API/domain heatmap +6 test nguồn VN** qua runner DB/cache tạm: pass. Những test này chưa bao phủ các lỗi trên, nên pass không đồng nghĩa không còn lỗi logic.
- [Frontend log](../../../../output/market-heatmap/review/frontend-tests.log), [4 backend tests](../../../../output/qa/isolated-tests/20261102T154856Z-d2963f48/report.json), [6 feed tests](../../../../output/qa/isolated-tests/20261102T155058Z-fa4c4cf1/report.json).
- Snapshot sao chép có1.521 mã, 874 mã GTGD/KL dương và14 mã vốn hóa dương. Không phát hiện sai lệch giữa % nguồn và `(giá/tham chiếu−1)×100` lớn hơn0,02 điểm phần trăm ở các dòng có giao dịch. Trọng số và tỷ lệ đơn vị VND→tỷ là đúng; lỗi HM-02 nằm ở cách làm tròn khi trình bày.
- Thang màu cam/đỏ–vàng–xanh, điểm bão hòa −7%/+3%, mã trần/sàn theo % là thiết kế đã thống nhất, không coi là bug. Số liệu vốn hóa thiếu vẫn là giới hạn nguồn đã công khai.
- Probe thuần phát hiện ±0,001% có thể được format thành ±0%; không có trường hợp này trong snapshot hiện tại, nên ghi chú biên này không được xếp thành lỗi ưu tiên riêng.
- Browser không có page error; các lỗi đã tái hiện là sai trạng thái/hành vi. Browser build được rà là `index-Ca71-u7t.js`; không rebuild hay sửa source sản phẩm trong lượt review. [Source fingerprint](../../../../output/market-heatmap/review/source-fingerprints.json).
- QA dùng DB tạm và quote công khai sao chép. Feed probe dùng requests mock hoàn toàn và thư mục cache tạm. Không ghi DB/cache thật, không restart main app, không push/deploy. Chưa kiểm tra trên thiết bị Safari/iOS thật.

Thứ tự ưu tiên lúc review là HM-01, HM-02–05 rồi HM-06. Cả sáu đã được khép lại bằng bản sửa và kiểm chứng liên kết ở đầu báo cáo; các bằng chứng trong báo cáo này vẫn mô tả phiên bản cũ.
