# Chart và UI Hàng hoá — 03/11/2026

**Verified trên local QA.** Yêu cầu chỉnh chart/UI/UX subtab Hàng hoá. Bản cũ sinh đường từ `Math.sin` + giá/% hiện tại, không có lịch sử; giá cents cũng bị thêm ký hiệu USD. Tab mới dùng dữ liệu history hiện có và bố cục theo dõi/chi tiết.

## Kết quả

- Bảng theo dõi bên trái, chart lớn bên phải; header và độ rộng danh sách thu gọn. Bỏ avatar chữ cái, kicker, thông tin bảng DB và KPI “mixed” không giúp người xem.
- Chart ngày thật: nến/đường, 1/3/6 tháng/1 năm, crosshair OHLC, volume khi có dữ liệu, pan/zoom/reset/retry. Cao/thấp và % theo kỳ lấy từ history, không dùng high/low của nến 5 phút làm cao/thấp cả phiên.
- Mini chart dùng lịch sử đóng cửa 1 tháng với queue/cache chung, không sinh sóng giả. Màu mini theo thay đổi trong tháng; % ở bảng theo tham chiếu và được giải thích riêng.
- Giá số + đơn vị gốc: không biến `447.25 US cents/bu` thành `$447.25`. Mã có giá nhỏ giữ bốn chữ số thập phân. Khối lượng 0 khác thiếu dữ liệu.
- Lọc nhóm/tìm/sort và lựa chọn nhất quán; lựa chọn chi tiết luôn thuộc kết quả đang hiển thị. Native button thao tác bằng bàn phím. Mobile chuyển Bảng giá ↔ Biểu đồ, chọn mã tự mở chart.
- Shared light/dark, giữ zoom khi đổi theme. Refresh lỗi giữ quotes trước đó, không ghi đè từ request đã hủy. History lỗi/thiếu có recovery; thiếu OHLC chỉ dùng đường, không dựng nến giả.

## Bằng chứng

| Kiểm chứng | Kết quả |
| --- | --- |
| Frontend unit | 180/180 pass; gồm 4 test model hàng hoá |
| ESLint | 0 errors; 1 warning Social có sẵn ở `useSocialFeed.js:61` |
| CSS | 57 files, 0 syntax failures |
| Vite production build | Pass |
| `git diff --check` | Pass |
| Impeccable layout scan phạm vi | Không finding; vẫn kiểm tra ảnh thực tế |
| Chromium UI | 14 nhóm đạt, 0 pageerrors |

Browser: desktop1600,1280; tablet850,768; mobile390,320. Đã xem ảnh dark/light, candle/line, responsive; sửa button kế thừa flex/shadow làm mã dài bị vỡ chữ. Mobile tách bảng/chart để chart không bị đẩy xuống sau toàn bảng. Test gồm số hợp đồng/đơn vị, lọc nhóm, search/reset, sort, keyboard, khoảng xem/mode/reset, zoom qua theme, responsive overflow, mobile chọn mã, quote error/retry, history lỗi/empty/close-only/stale và chọn A→B→A nhanh.

Lịch sử công khai tải trực tiếp bằng yfinance vào QA: **23 hợp đồng × 251 daily bars**, không dùng đường minh hoạ. Quotes là bản sao `data/global_market_prices/global_market_snapshot.json`, mốc `as_of` được giữ. Browser giới hạn số nến theo từng khoảng để kiểm tra UI; không dùng server QA làm provider sản phẩm.

Ảnh/JSON: `output/playwright/commodities/desktop-dark.png`, `desktop-light.png`, `width-390.png`, `width-320.png`, `final-dark.png`, `checks.json`. Localhost8000 trả HTTP200 và cùng entry `index-Df2NeQSu.js` với QA. Watcher có sẵn cập nhật bản local; không restart/deploy.

## Source và chạy lại

- `frontend/src/features/market-portfolio/pages/CommoditiesPanel.jsx`, `commodities.css`.
- `services/commodityModel.js`, `hooks/useCommodityHistory.js`, `services/marketPortfolioApi.js` (AbortSignal snapshot).
- `LightweightChartPanel.jsx`: precision tuỳ chọn và chart resize được dưới280px; consumer cũ giữ behavior mặc định.
- Test `frontend/src/__tests__/logic-fixes/commodity-model.test.js`.

```sh
.venv/bin/python scripts/qa/collect-commodity-reference.py
npm --prefix frontend run build -- --outDir ../output/playwright/commodities/dist
PYTHONPATH=src .venv/bin/python scripts/qa/commodities-server.py
# Trong terminal khác, khi server5191 sẵn sàng:
node scripts/qa/commodities-browser.mjs
npm --prefix frontend run test:unit
npm --prefix frontend run lint
npm --prefix frontend run lint:css
```

Server chỉ dùng DB/auth tạm, không reset/ghi DB người dùng; browser chỉ request QA, provider ngoài bị chặn. Xóa `output/playwright/commodities/session.json` và dừng server QA sau kiểm tra. Dữ liệu tải thật chứng minh chart hoạt động với history provider, không bảo đảm availability/timing provider liên tục, giá realtime hay quy cách rollover/điều chỉnh hợp đồng. Không thêm backend tests vì không thay backend. Chưa kiểm chứng Safari/iOS thật. Navigation app dùng bố cục hiện có; ảnh850 cho thấy header app chật, nằm ngoài thay đổi subtab này.

116 staged files giữ nguyên; SHA-256 của `git diff --cached --binary`: `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`. Không stage/commit/push/deploy. Sự cố DB lịch sử không liên quan và chưa khôi phục.
