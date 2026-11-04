# Đồng bộ sáng/tối toàn ứng dụng — 2026-11-02

**Verified trên local QA.** Theo yêu cầu tiếp theo của người dùng, phạm vi Market-only được mở rộng cho toàn bộ workspace. Một lựa chọn dùng chung cho Market và các tab con, Learn Hub/reader, BCTC, News/Social/calendar, Simulation/Backtest, homepage và auth.

## Thay đổi

- `frontend/src/shared/theme/appTheme.js`: provider và preference `public-beta.theme`, chuyển tiếp lựa chọn `public-beta.market-theme`, đồng bộ browser tabs; storage bị chặn vẫn đổi được trong phiên.
- `ThemeToggle.jsx`: control chung trên navigation, reader và auth; có nhãn switch, keyboard và trạng thái truy cập được trên mobile.
- `frontend/src/styles/app-theme.css`: palette tối/sáng chung, token neutral/accent và màu tăng/giảm; portal theo root theme. Bỏ các palette cố định trong Learn Hub, BCTC, Simulation, homepage và auth.
- Chart Simulation đổi appearance trên instance hiện tại; giữ vùng zoom và nội dung editor. Reader giữ màu tài liệu/PDF, giấy A4, chữ/vẽ và vị trí đang đọc; chỉ giao diện bao quanh đổi theme.
- Hộp thoại Simulation có backdrop, bề mặt và chữ theo theme. Chuyển theme không remount workspace hay xóa nội dung đang nhập.

## Kiểm chứng

| Kiểm tra | Kết quả |
| --- | --- |
| Frontend unit | 176/176 pass |
| ESLint | 0 errors; 1 warning có sẵn ở `useSocialFeed.js:61` |
| CSS syntax | 56 files, 0 failed |
| Production build | Pass |
| `git diff --check` | Pass |
| Browser main surfaces | 9 nhóm, 0 pageerror |
| Browser subtabs/state | 14 nhóm, 0 pageerror |
| Browser preference/navigation | 16 nhóm, 0 pageerror |

Chromium desktop 1440×1000 và mobile 390×844. Các nhóm kiểm tra gồm chuyển theme qua mọi workspace chính, 9 tab Market còn lại, Learn library/shelf/docs/tutor/exam/reader, BCTC notes/ratio/reports, Simulation chart/editor/builder/tearsheet/modal. Preference được giữ khi SPA navigation/reload, migrate từ Market, đồng bộ browser tabs và sử dụng bằng bàn phím; trường hợp localStorage từ chối ghi cũng đạt.

Chart Simulation vẫn giữ vùng 40–90 sau đổi theme: cho phép lệch dưới 1 nến do độ rộng trục giá tự điều chỉnh, không chấp nhận reset về toàn bộ dữ liệu. Reader giữ chuỗi ghi chú, màu ink và iframe URL. BCTC notes và code editor giữ nội dung nhập.

Đã xem ảnh thực tế của các workspace và tab con tiêu biểu ở hai chế độ; sửa thêm auth bị ép `dark`, màu chữ nút auth và hộp thoại Simulation sau kiểm tra. HTTP GET localhost:8000 trả 200 và dùng cùng entry `index-BtKvc1pc.js` như QA build. Watcher hiện có phục vụ bản mới; không restart hay deploy.

## Bằng chứng và chạy lại

- Scripts: `scripts/qa/global-theme-server.py`, `global-theme-browser.mjs`, `global-theme-subtabs.mjs`, `global-theme-behavior.mjs`.
- Kết quả/ảnh: `output/global-theme/checks.json`, `subtabs.json`, `behavior.json` và các PNG cùng thư mục.
- Build: `npm --prefix frontend run build -- --outDir ../output/global-theme/dist`.
- Static checks: `npm --prefix frontend run lint`, `npm --prefix frontend run lint:css`, `npm --prefix frontend run test:unit`.
- Server QA: `PYTHONPATH=src python3 scripts/qa/global-theme-server.py` (cần Python env có dependencies). Server tự tạo DB/auth tạm và đọc bản sao snapshot `output/market-heatmap/live-snapshot.json`.
- Chạy ba browser script bằng Node có package Playwright sau khi server 5190 sẵn sàng; dừng server và xóa `output/global-theme/session.json` khi xong.

## Giới hạn và cách ly

QA chỉ ghi DB/auth tạm, không reset hay ghi DB người dùng. Giá VN là bản sao snapshot công khai; lịch sử chart/BCTC dùng fixture; các API ngoài phạm vi trả trạng thái thiếu kết nối, requests provider bên ngoài bị chặn. Đây là kiểm chứng theme/UI và giữ trạng thái, không chứng nhận feed trực tiếp, Google sign-in, AI, native PDF renderer hay nghiệp vụ toàn bộ backend. PDF được kiểm tra giữ URL và màu giấy/ink; Safari/iOS thật chưa được kiểm tra.

116 mục staged giữ nguyên, SHA-256 của `git diff --cached --binary`: `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`. Không stage/commit/push/deploy. Sự cố DB lịch sử không được khôi phục bởi thay đổi này.
