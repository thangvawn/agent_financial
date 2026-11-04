# Hàng hoá: chart và trải nghiệm theo dõi

2026-11-03 · implemented / verified on local QA. Người dùng yêu cầu chỉnh chart và UI/UX tab Hàng hoá.

Tiêu chí: bảng hợp đồng gọn đi cùng chart lịch sử lớn; bỏ đường sine giả, dùng history hiện có; nến/đường/khoảng thời gian/reset dùng được. Giữ đơn vị giá gốc (cents không hiển thị USD), nguồn và thời gian quote, tách % tham chiếu với % khoảng xem. Lọc/tìm/sort/chọn bàn phím nhất quán; trạng thái lỗi/thiếu lịch sử rõ ràng; cả theme và mobile không tràn trang.

Nguồn source: CommoditiesPanel, LightweightChartPanel, dataHub history API và GlobalMarketFeedProducer. Chỉ thay frontend, không chỉnh feed/DB hay deploy. QA dùng DB tạm, public quotes sao chép và lịch sử Yahoo tải vào output riêng; kịch bản lỗi có kiểm soát. Kiểm chứng bằng browser screenshots/interaction, unit model, lint/CSS/build.

Kết quả: 180 frontend tests, 14 nhóm Chromium, lint (0 lỗi/1 warning cũ), CSS57/build đạt. [Báo cáo nghiệm thu](../qa/results/COMMODITIES_UI_2026_11_03.md).
