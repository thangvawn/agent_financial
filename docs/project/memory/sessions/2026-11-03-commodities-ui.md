# Chart và UI Hàng hoá — 03/11/2026

**Verified.** User yêu cầu chỉnh chart/UI/UX subtab Hàng hoá theo screenshot.

- Thay sine sparkline bằng history thật; bảng compact/master-detail, chart lớn OHLC/volume/nến/đường và 1/3/6 tháng/1 năm. Mobile chọn bảng/chart; hai theme chung, giữ zoom.
- Giữ đơn vị provider (cents không thêm `$`), 0 khác thiếu; cao/thấp tính từ history kỳ xem. Không dùng high/low5m snapshot như phạm vi cả ngày. Mini màu theo tháng, % bảng theo tham chiếu.
- Selection thuộc kết quả lọc; request canceled không ghi đè, quote refresh lỗi giữ bảng; history thiếu/error/stale công khai, thiếu OHLC chỉ dùng đường.
- 180 frontend tests, lint0 lỗi/1 warning Social cũ, CSS57/build, 14nhóm Chromium đạt; public history23×251bars tải vào QA riêng, không ghi DB thật. Desktop1600/1280, tablet850/768, mobile390/320; đã xem ảnh.
- Localhost8000 HTTP200 cùng asset QA `index-Df2NeQSu.js`; watcher tự cập nhật, không deploy/restart/push. Staged116 giữ nguyên hash cũ.

[Báo cáo/source/commands/giới hạn](../../qa/results/COMMODITIES_UI_2026_11_03.md), [acceptance](../../engineering/COMMODITIES_UI_2026_11_03.md). Không cam kết nguồn realtime hay kiểm chứng Safari/iOS. Header app hiện có chật ở850px; subtab không tràn ngang. Sự cố DB lịch sử vẫn unresolved.
