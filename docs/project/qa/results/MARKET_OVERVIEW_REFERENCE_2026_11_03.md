# Tổng quan theo tham khảo FireAnt /thi-truong

Ngày: 03/11/2026. Trạng thái: **verified** trên build local và bản QA cô lập.

## Tham khảo và quyết định

Đã mở trực tiếp https://fireant.vn/thi-truong lúc khoảng 09:44–09:45: quan sát dải chỉ số, biểu đồ chỉ số/điểm nhấn phiên, độ rộng/thanh khoản/khối ngoại/ngành, heatmap và bảng cổ phiếu nổi bật có ngưỡng GTGD. Đã thấy heatmap có dữ liệu. Đây là bằng chứng về UI hiển thị; không chứng minh thuật toán cập nhật nội bộ của FireAnt.

Áp dụng cho Northstar: dải chỉ số gọn → nhịp toàn thị trường → bản đồ → thanh khoản ngành và cổ phiếu nổi bật → quốc tế. Giữ màu và typography của Global Terminal, bản đồ đầy đủ có zoom/kéo với diện tích thật. Mobile dùng dải chỉ số vuốt ngang để dành chiều cao cho bản đồ. Thống kê theo sàn mở bằng details. Bỏ status bar kỹ thuật khỏi riêng Tổng quan; thông tin nguồn/lỗi của bản đồ vẫn có.

## Dữ liệu và logic

- Nâng hook `useMarketHeatmap` lên `MarketOverviewTab`, truyền feed xuống bản đồ. Độ rộng, GTGD, ngành và movers tính từ cùng snapshot đầy đủ, cùng lượt cập nhật.
- Trước đây độ rộng dùng request snapshot riêng và mặc định cộng thành 0 khi chưa có phản hồi; movers gọi thêm hai request xếp hạng. Nay khi chưa có feed hiển thị dấu `—`, không suy ra thị trường đứng giá.
- Đếm mã đã giao dịch khi KL hoặc GTGD >0; độ rộng cần giá dương và % hữu hạn. Thiếu %/giá và mã chưa giao dịch không bị tính là tham chiếu. Tổng GTGD cộng giá trị hợp lệ không âm; thiếu toàn bộ giữ null, không đổi thành0.
- Thanh khoản ngành = tổng GTGD các mã thuộc ngành / tổng GTGD có dữ liệu. Đây là tỷ trọng thanh khoản, không phải % hiệu suất ngành hoặc mua ròng.
- Movers lọc dấu biến động và ngưỡng `GTGD ≥ 1 tỷ` (mặc định bật, có thể tắt) trên toàn bộ tập mã trước khi lấy6. Tab Thanh khoản xếp GTGD giảm dần. Giá cổ phiếu hiển thị đồng theo đúng contract của heatmap.
- Sparkline chỉ số giữ nhãn `1 tháng · Đóng cửa`. Giá chỉ số là nguồn global terminal hiện có, có thể khác thời điểm cập nhật cổ phiếu; không gắn nhãn intraday cho lịch sử daily.

## Kiểm chứng

- Suite frontend: **192/192 đạt**, gồm4 test mới cho thiếu dữ liệu, phân loại độ rộng, tỷ trọng GTGD, lọc trước giới hạn và tick đồng bộ. Sau tinh chỉnh xử lý giá trị âm,4 test model chạy lại đạt.
- ESLint:0 errors,1 warning Social cũ. CSS57 files đạt; build QA và build local đạt; `git diff --check` sạch. Impeccable layout detector không có findings trong2file overview.
- Browser trên QA cổng5194, DB auth tạm, bản sao quote công khai từ localhost:1.521 mã,594 mã có giao dịch,201 tăng/150 tham chiếu/243 giảm, GTGD1.679,77tỷ ở snapshot đã chụp.
- Đã thử3 chế độ movers, bật/tắt ngưỡng, mở11ngành, mở độ rộng3sàn, refresh, zoom, đổi theme. Một tick giá VCI chỉ thay outerHTML của VCI trong các ô đang thấy; camera giữ `(scale=2,x=-186,y=-270)`. Đổi theme giữ camera đó.
- Desktop1600, tablet768, mobile390/320 không tràn ngang trang. Ảnh viewport được xem trực tiếp. API snapshot/history/global trong QA dùng bản sao thật; cập nhật VCB/VCI kiểm thử chỉ sửa fixture, sau đó phục hồi.
- Build localhost8000 đã đối chiếu entry với QA; xem `output/market-overview-reference/assets.json`. Không publish/push/restart backend.

## Bằng chứng và giới hạn

`output/market-overview-reference/`: unit.log, lint.log, css.log, build.log, local-build.log, assets.json, live-update.json và ảnh kiểm chứng. Source: MarketOverviewTab.jsx, marketOverviewModel.js, IndexCardsBar.jsx, IndexSparklineCard.jsx, sonar-cards.css, market-overview-tab.css, GlobalTerminalPage.jsx.

Ảnh fullPage ở browser thử nghiệm có thể làm đổi kích thước viewport tạm thời và reset camera; phép đo tick cuối được thực hiện với viewport cố định, không chụp fullPage giữa hai mốc. Dùng ảnh viewport cuối để đánh giá mobile. Không khẳng định kiểm chứng DOM identity/frame-by-frame ở lượt này; kiểm chứng chống nháy sâu của lượt trước được ghi riêng tại MARKET_OVERVIEW_LIVE_UPDATES_2026_11_03.md.

Chưa thêm dòng tiền khối ngoại, tác động điểm VN-Index hay chart chỉ số trong phiên vào Tổng quan: các khối mới chỉ dùng trường dữ liệu đã có và công thức được mô tả ở trên. Không thay feed backend. Các component mock/ước lượng ở nơi khác không được sử dụng cho màn hình này.

QA cổng5194 đã dừng; DB tạm của lượt chạy đã xóa theo đường dẫn do chính server tạo. Ảnh bàn giao: `overview-final.jpg`, `mobile-320-dark.jpg`; ảnh320 cuối có rail304px/scroll1064px và đã thử vuốt (scrollLeft268). Không dùng ảnh fullPage trung gian để chứng nhận giao diện.
