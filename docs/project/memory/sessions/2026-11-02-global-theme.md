# Sáng/tối dùng chung mọi workspace — 2026-11-02

**Verified.** User yêu cầu “đồng bộ sáng tối cho tất cả các tab luôn”, mở rộng quyết định Market-only ở session trước. Không khôi phục các workspace bị ép light/dark riêng.

- Một provider `shared/theme/appTheme.js` và key `public-beta.theme`; migrate key Market cũ. Root/portal cùng theme; storage lỗi vẫn hoạt động trong phiên.
- Switch trên navigation, reader và auth. Tất cả workspace chính và tab con dùng token chung, bao gồm Learn Hub, BCTC, News/Social/calendar, Simulation/Backtest, homepage/auth.
- Chuyển theme giữ active tab, code/notes đang nhập và chart zoom. Không đảo màu PDF/ảnh/giấy A4/ink. Không remount chart Simulation chỉ để đổi màu.
- 176 unit tests, 39 nhóm Chromium (9 main +14 subtabs +16 behavior), CSS56 và build đạt; ESLint 0 errors/1 warning Social cũ. Đã xem screenshot desktop/mobile và sửa các vùng auth/modal còn ép dark.
- Localhost8000 HTTP200, cùng entry `index-BtKvc1pc.js` như QA; watcher hiện có tự cập nhật. Không restart/deploy/push.
- QA DB/auth tạm, snapshot VN copy, history/BCTC fixture và provider ngoài bị chặn. Không chứng nhận live provider, native PDF rendering hoặc Safari/iOS thật; không chạy backend tests vì thay đổi frontend.
- 116 staged files cùng hash `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`; không reset DB người dùng.

[Báo cáo, commands và bằng chứng](../../qa/results/GLOBAL_THEME_2026_11_02.md). [Acceptance](../../engineering/GLOBAL_THEME_2026_11_02.md). `PRODUCT.md` đã phản ánh scope toàn app. Session Market-only trước là lịch sử, kết quả kiểm chứng ở thời điểm đó vẫn giữ nguyên.
