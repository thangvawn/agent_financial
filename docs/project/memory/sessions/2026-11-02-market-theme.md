# Đồng bộ Global Terminal và sáng/tối

2026-11-02 · **verified**.

- Yêu cầu: đồng bộ màu với Global Terminal, thêm sáng/tối. Thang màu ô heatmap theo mẫu trước được giữ nguyên.
- Nguồn: `frontend/src/styles/market-theme.css`, `frontend/src/shared/theme/marketTheme.js`, AppShell, MarketPortfolioPage, LightweightChartPanel/TradingViewRealtimeWidget và CSS market.
- Theme chỉ cho workspace thị trường: tối mặc định, lưu theo trình duyệt, đồng bộ tab, fallback in-memory; các workspace khác giữ mặc định. Chuyển màu giữ mã và zoom.
- 176 unit tests +8 nhóm Chromium, lint0error/1warning cũ, CSS56, build đạt. Đã xem ảnh desktop/mobile. Localhost8000 HTTP200; entry index-HYit13em.js trùng QA.
- [Báo cáo, ảnh và giới hạn](../../qa/results/MARKET_THEME_2026_11_02.md). QA dùng DB tạm/public snapshot, history/TradingView stub. Không ghi DB người dùng, push hoặc deploy.
