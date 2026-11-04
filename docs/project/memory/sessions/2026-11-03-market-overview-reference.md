# Tổng quan theo tham khảo FireAnt /thi-truong

- Date:2026-11-03. Status:**verified**; source:user URL + browser đọc trang thật + code hiện hành.
- Đã áp dụng thứ tự chỉ số gọn → nhịp thị trường → bản đồ → ngành/movers → quốc tế. Mobile chỉ số vuốt ngang. Bỏ footer kỹ thuật trên Tổng quan; giữ controls và cơ chế cập nhật map của lượt trước.
- Dùng chung hook/feed heatmap cho độ rộng/GTGD/ngành/movers. Độ rộng chỉ đếm mã đã giao dịch có giá/% hợp lệ; thiếu dữ liệu hiển thị `—`. Ngành tính tỷ trọng GTGD thật; movers lọc trước giới hạn6, có ngưỡng1tỷ tùy chọn.
- Source:frontend/src/features/market-portfolio/components/MarketOverviewTab.jsx và services/marketOverviewModel.js; chi tiết đầy đủ trong [QA report](../../qa/results/MARKET_OVERVIEW_REFERENCE_2026_11_03.md).
- Verification:192 frontend tests đạt;4 model tests chạy lại sau tinh chỉnh; lint0errors/1warning Social cũ, CSS57/build đạt; browser desktop/mobile sáng tối, tab/filter, tổng594 mã và tick riêngVCI giữ camera đạt. Local build được đối chiếu với8000. QA dùng DB tạm và public snapshotcopy.
- Giới hạn:giá chỉ số từ global feed hiện có, sparkline daily1tháng; không thêm intraday/index impact/foreign flow. Chi tiết hình học/cập nhật độc lập vẫn theo [session trước](2026-11-03-market-overview-live-updates.md). FullPage screenshot của môi trường này có thể tạm thay viewport; dùng đo cố định và viewport screenshot.
