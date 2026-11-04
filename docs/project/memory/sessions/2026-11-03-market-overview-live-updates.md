# 03/11/2026 — Tổng quan gọn, heatmap cập nhật độc lập

Status: **verified** trên source, Chromium QA và đối chiếu asset localhost8000.

- Yêu cầu: bỏ header dư như ảnh, đơn giản hóa UI và sửa nháy toàn bản đồ mỗi lần cập nhật; giữ tỷ trọng GTGD và zoom/kéo.
- Bỏ hero lớn; toolbar desktop 98px, thông tin nguồn/cách xem chuyển vào details; giữ cảnh báo stale/lỗi. Hai theme và 320/390/768/1600px đã xem.
- Worker dùng lại theo scope; giá/% không kích hoạt layout. React memo theo mã; các cây resquarify riêng ngành và mã giữ topology. Mã mới chỉ dựng lại hàng của ngành liên quan; resize khung tính lại hình dạng để dùng tốt trên mobile.
- Giữ layout tốt khi chờ/lỗi; chặn phản hồi cũ; ghép quote/bố cục khi thêm-bớt mã để không tạo ô trống trước khi worker xong. Giữ camera qua tick, chỉ reanchor khi mã ghim không còn đọc được/mất khỏi bản đồ.
- Cập nhật màu 180ms/diện tích 220ms, reduced motion; tổng bản đồ loại giá trị của mã không được vẽ. Backend/feed không thay đổi.
- 188 frontend tests (trước chỉnh cuối về chuyển quote), 16 heatmap tests, 12 nhóm live browser + 9 hồi quy, CSS 57/build đạt, ESLint0 errors/1 warning Social cũ. Browser cuối kiểm chứng thay đổi React cuối. VCB-only tick/poll: chỉ VCB đổi; delayed weights:0 blank frames/60 sampled; DOM/worker/camera giữ lại.
- Local frontend build dùng `--emptyOutDir false`; localhost:8000 cùng asset QA; không restart/deploy/push/reset DB. Staging nguyên trạng.

[Report/source/evidence và giới hạn](../../qa/results/MARKET_OVERVIEW_LIVE_UPDATES_2026_11_03.md).

Quyết định camera thay thế hành vi reanchor mọi lần relayout của HM-03 ngày 02/11. Diện tích vẫn là tỷ trọng thực nên các biên liên quan co giãn khi tổng GTGD đổi; không đóng băng sai tỷ trọng các ngành khác. Chưa thử Safari/iOS vật lý hoặc load nhiều tab dài hạn. FireAnt chỉ đối chiếu cấu trúc UI; bản đồ của họ trống ở phiên quan sát, không suy đoán cơ chế cập nhật nội bộ.
