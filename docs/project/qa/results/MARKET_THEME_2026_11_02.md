# Global Terminal — đồng bộ màu và sáng/tối

2026-11-02 · **verified** trên build production và Chromium QA.

## Thay đổi

- Bộ màu chung trong `frontend/src/styles/market-theme.css`; gỡ màu tối gán cố định ở desk/terminal. Nền, chữ, viền, accent, quote states, logo, tooltip và panel theo cùng chế độ.
- Switch cạnh thanh tab, hiển thị trên mobile, có nhãn và dùng được bằng bàn phím. Tối mặc định; lưu `public-beta.market-theme`, đồng bộ tab, vẫn đổi được khi storage bị chặn.
- Theme chỉ áp dụng Market & Portfolio. Các workspace khác giữ mặc định. Giữ thang màu ô heatmap cam–đỏ/vàng/xanh theo yêu cầu trước.
- Theme context cập nhật chart. Lightweight giữ instance/series và visible range, không đặt lại barSpacing/rightOffset khi đổi màu. TradingView embed nhận cấu hình theme mới.

## Kiểm chứng

- 176 frontend unit tests đạt. ESLint 0 lỗi, 1 warning có sẵn ở `useSocialFeed.js:61` ngoài phạm vi. CSS56, Vite build và git diff --check đạt.
- `node scripts/qa/market-theme.mjs`: 8 nhóm kiểm tra, 0 pageerror. Palette shell/map/tooltip, giữ mã/zoom/toàn bộ ô; lưu sau reload; bảng giá và tooltip sparkline portalled; mobile/Space/no overflow; chart giữ zoom và instance; TradingView config; đồng bộ tab; storage lỗi.
- Ảnh desktop1600×1100 và mobile390×844 đã xem: `output/market-heatmap/theme/{light,dark}-overview.png`, `light-focus.png`, `{light,dark}-stocks.png`, `{light,dark}-detail.png`, `mobile-{light,dark}.png`. Kết quả máy đọc: `output/market-heatmap/theme/checks.json`.
- Localhost8000 HTTP200, entry `index-HYit13em.js` trùng QA build. Watcher hiện có phục vụ bản mới; không restart/push/deploy.

## Giới hạn

Server QA5188 dùng auth/DB tạm và bản sao snapshot công khai1.521 mã,874 ô đủ GTGD; không ghi/reset DB người dùng. History là fixture và script TradingView được stub: kiểm chứng giao diện/cấu hình, không xác nhận giá hay render từ provider trực tiếp. Không chạy backend tests vì backend không đổi. Staged diff người dùng được giữ nguyên. Ca resize chờ worker layout hoàn tất trước tìm mã; screenshot tắt animation để chụp màu đã ổn định.
