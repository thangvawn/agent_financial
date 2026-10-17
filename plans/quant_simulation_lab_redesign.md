# Plan: Redesign & Rebuild Simulation Lab -> Quant Simulation Lab & Studio

## 1. Mục Tiêu & Bối Cảnh
- **Mục tiêu**: Tái thiết kế toàn diện phân hệ **Simulation Lab** (Pro Lab) của Northstar Finance Lab, tích hợp các tinh hoa bóc tách từ **AICIO Quant Hub** (`https://aicio.vn/quant` & `https://aicio.vn/quant/workshop`).
- **Phạm vi thay thế**: Dỡ bỏ giao diện form đơn điệu cũ của `SimulationLabWorkspace.jsx` (đang vượt quá 200 dòng), xây dựng lại kiến trúc module hóa theo tiêu chuẩn **Hard Limit < 200 dòng/file**, tích hợp Quanta Story DSL Editor, Dynamic Param Sliders, Multi-Panel Lightweight Charts, Tearsheet Metrics chuẩn quốc tế và AI Quant Copilot.

---

## 2. Kiến Trúc Phân Rã Module (Component Decomposition)

Mọi file đều dưới 200 dòng:

### A. Core Container & Header
1. `frontend/src/features/simulation-lab/pages/SimulationLabWorkspace.jsx` (< 170 dòng):
   - Root container điều phối state: mode (`workshop`, `visual_builder`, `results`), activeTicker, strategyCode, backtestResult.
2. `frontend/src/features/simulation-lab/pages/components/SimLabHeader.jsx` (< 160 dòng):
   - Topbar: Tên chiến lược, Ticker selector, Timeframe (`1D`, `1H`, `15m`), nút Chạy Backtest (F5), nút Tối ưu AI, nút Wiki tra cứu.

### B. Workshop IDE & Parameters
3. `frontend/src/features/simulation-lab/pages/components/QuantaWorkshopEditor.jsx` (< 180 dòng):
   - Trình soạn thảo mã Quanta DSL, menu chọn 6 mẫu chiến lược kinh điển, phím tắt F5/F9, syntax diagnostic.
4. `frontend/src/features/simulation-lab/pages/components/QuantaParamSliders.jsx` (< 160 dòng):
   - AST parser tự động quét `params:` trong code và sinh các thanh kéo trượt slider tương tác theo thời gian thực.
5. `frontend/src/features/simulation-lab/pages/components/SimLabVisualBuilder.jsx` (< 175 dòng):
   - Chế độ phụ trợ: Xây dựng chiến lược dạng thẻ điều kiện trực quan cho nhà đầu tư mới (F0).

### C. Visual Charts & Tearsheet Results
6. `frontend/src/features/simulation-lab/pages/components/SimLabMultiChart.jsx` (< 185 dòng):
   - Biểu đồ nến kỹ thuật số đa tầng (`lightweight-charts`): Panel nến + Overlays MA, dải BB/Keltner, đánh dấu Buy/Sell markers; Sub-panel Histogram/RSI.
7. `frontend/src/features/simulation-lab/pages/components/SimLabTearsheet.jsx` (< 180 dòng):
   - Tearsheet định lượng: Total Return, CAGR, Sharpe, Sortino, Max DD, Win Rate, Profit Factor, Trade Log T+2, Equity Curve so sánh VN-Index.

### D. AI Copilot & Presets
8. `frontend/src/features/simulation-lab/pages/components/SimLabAiCopilotModal.jsx` (< 165 dòng):
   - Trợ lý AI Quant: Phân tích rủi ro, kiểm tra Lookahead bias, gợi ý tham số tối ưu (kết nối `aiStrategyCopilot` backend).
9. `frontend/src/features/simulation-lab/content/quantaStrategyPresets.js` (< 150 dòng):
   - 6 bộ mã nguồn chiến lược mẫu: *Aurora Liquidity Pulse v2*, *Tide Reclaim Pulse*, *Turtle Donchian*, *Bollinger Squeeze*, *RSI Divergence*, *VN Trend Allocation*.
10. `frontend/src/features/simulation-lab/utils/quantaBacktestSimulator.js` (< 185 dòng):
    - Engine mô phỏng backtest client-side với dữ liệu OHLCV, tính toán Sharpe, MDD, Win rate, Equity curve tức thì cho người dùng khi thử nghiệm code.

### E. Stylesheets (< 180 dòng mỗi file)
11. `frontend/src/features/simulation-lab/pages/styles/simlab-studio.css` (< 170 dòng)
12. `frontend/src/features/simulation-lab/pages/styles/simlab-editor.css` (< 160 dòng)
13. `frontend/src/features/simulation-lab/pages/styles/simlab-chart.css` (< 160 dòng)

---

## 3. Quy Trình Thực Hiện Tuần Tự (Checklist)

- [ ] Task 1: Khởi tạo dữ liệu chiến lược mẫu `quantaStrategyPresets.js` & engine mô phỏng `quantaBacktestSimulator.js`.
- [ ] Task 2: Xây dựng các component Editor & Param Sliders: `QuantaWorkshopEditor.jsx` và `QuantaParamSliders.jsx`.
- [ ] Task 3: Xây dựng component biểu đồ đa tầng `SimLabMultiChart.jsx` & Tearsheet kết quả `SimLabTearsheet.jsx`.
- [ ] Task 4: Xây dựng Header `SimLabHeader.jsx`, Visual Builder `SimLabVisualBuilder.jsx` & AI Copilot `SimLabAiCopilotModal.jsx`.
- [ ] Task 5: Xây dựng các file CSS (`simlab-studio.css`, `simlab-editor.css`, `simlab-chart.css`) chuẩn Dark Fintech và font Inter.
- [ ] Task 6: Tái cấu trúc `SimulationLabWorkspace.jsx` thành container điều phối gọn nhẹ (< 170 dòng).
- [ ] Task 7: Viết unit tests kiểm thử toàn bộ tính năng và hợp đồng dữ liệu.
- [ ] Task 8: Chạy `npm run test:unit` và `npm run build`, kiểm tra giao diện bằng Playwright.
