# Kế Hoạch Chi Tiết: Chuyển Đổi Northstar Finance Thành Nền Tảng Tài Chính Thế Hệ Mới (Next-Gen Fintech Platform)

## 1. Mục Tiêu & Bối Cảnh (Context & Objectives)
- **Vấn đề cốt lõi:** Hiện tại Northstar Finance sở hữu engine dữ liệu thật 15+ năm và Quanta Studio rất mạnh, nhưng các phân hệ (`Learn Hub`, `BCTC`, `Market & Portfolio`, `Simulation Lab`) đang hoạt động như các "ốc đảo" độc lập; thiếu tính kết nối luồng hành động thực tế (Actionable Execution Gap); và Quanta Engine mới dừng lại ở việc nhìn lại quá khứ (Past-looking Backtest) mà chưa cung cấp tín hiệu cho ngày hôm nay (Today's Forward Signal).
- **Mục tiêu chiến lược:** 
  1. **Hợp nhất luồng người dùng (Unified Workflow):** Kết nối 1-click liền mạch từ *Học lý thuyết (Learn Hub)* $\rightarrow$ *Soi cơ bản (BCTC)* $\rightarrow$ *Thử nghiệm định lượng (Simulation Lab)* $\rightarrow$ *Theo dõi danh mục (Portfolio)*.
  2. **Thước đo khắt khe chuẩn TTCK Việt Nam (Financial Rigor):** Tích hợp biên độ trần/sàn ($\pm7\%$, $\pm10\%$), bộ lọc thanh khoản tối thiểu, thuế, phí và trượt giá (slippage).
  3. **Chuyển hóa từ Quá khứ sang Hiện tại (Forward Signals Today):** Sinh tín hiệu hành động cụ thể cho phiên hôm nay (`BUY`, `SELL`, `HOLD` kèm mức dừng lỗ/chốt lời).
  4. **Lưu & Quản trị Chiến lược Cá nhân (Strategy Blueprint Manager):** Lưu trữ chiến lược vào bộ nhớ, so sánh hiệu suất giữa các phiên bản.

---

## 2. Kiến Trúc & Các File Bị Ảnh Hưởng (Architecture & File Impacts)

Tất cả các file đều tuân thủ **Hard Limit < 200 dòng/file**.

### A. Phân Hệ Cầu Nối Luồng Nghiệp Vụ (Cross-Module Workflow Bridge)
1. **`frontend/src/shared/context/financialWorkflowContext.js`** [NEW] (< 130 dòng):
   - Quản lý state điều hướng toàn cục: `activeTicker`, `preloadedStrategyCode`, `sourceModule`, `navigationTrigger`.
   - Cung cấp hook `useFinancialWorkflow()` cho phép mọi màn hình kích hoạt chuyển đổi ngữ cảnh tức thì.
2. **`frontend/src/features/learn-hub/pages/components/QuantaLessonLabCta.jsx`** [NEW] (< 90 dòng):
   - Nút CTA gắn trong các bài học của Learn Hub: "Mở chiến lược này trong Quanta Studio", tự động nạp code tương ứng.
3. **`frontend/src/features/bctc/components/BctcActionBridge.jsx`** [NEW] (< 110 dòng):
   - Thanh hành động gắn trong phân hệ BCTC: "Backtest mã này trong Lab", "Thêm vào Watchlist".

### B. Nâng Cấp Engine Định Lượng & Tín Hiệu Hôm Nay (Quanta Engine & Today Signals)
4. **`frontend/src/features/simulation-lab/utils/quantaVnMarketRules.js`** [NEW] (< 120 dòng):
   - Luật khớp lệnh TTCK Việt Nam: Giới hạn biên độ giá HOSE ($\pm7\%$), HNX ($\pm10\%$), UPCOM ($\pm15\%$), bộ lọc thanh khoản tối thiểu (vol > 50k cp/phiên), tính toán thuế bán 0.1%, phí mua/bán 0.15%, trượt giá slippage.
5. **`frontend/src/features/simulation-lab/utils/quantaTodaySignalEngine.js`** [NEW] (< 130 dòng):
   - Phân tích nến gần nhất (Latest Bar) để xác định trạng thái tín hiệu cho phiên giao dịch hiện tại: `ACTION: BUY | SELL | HOLD`, giá kích hoạt, mức cắt lỗ (Stop-Loss) và mục tiêu chốt lời (Take-Profit).
6. **`frontend/src/features/simulation-lab/utils/quantaBacktestSimulator.js`** [MODIFY] (< 195 dòng):
   - Tích hợp `quantaVnMarketRules` và trả về `todaySignal` trong kết quả mô phỏng.

### C. Quản Trị Chiến Lược & Giao Diện Tín Hiệu (Strategy Blueprint & UI)
7. **`frontend/src/features/simulation-lab/services/quantaBlueprintStorage.js`** [NEW] (< 110 dòng):
   - Quản lý lưu trữ/tải chiến lược tùy biến của người dùng vào LocalStorage/State (Save, Load, Export, Delete Blueprint).
8. **`frontend/src/features/simulation-lab/pages/components/SimLabTodaySignalBanner.jsx`** [NEW] (< 130 dòng):
   - Banner trực quan nổi bật trên biểu đồ: Hiển thị tín hiệu phiên hôm nay của chiến lược đối với mã đã chọn (BUY/SELL/HOLD, Risk Score, Stop-Loss).
9. **`frontend/src/features/simulation-lab/pages/components/SimLabBlueprintModal.jsx`** [NEW] (< 140 dòng):
   - Modal quản lý các bản thiết kế chiến lược đã lưu: Tải lại, sao chép, so sánh CAGR / Sharpe.
10. **`frontend/src/features/simulation-lab/pages/components/SimLabHeader.jsx`** [MODIFY] (< 190 dòng):
    - Bổ sung nút "Lưu chiến lược (Save Blueprint)" và "Mẫu chiến lược cá nhân".
11. **`frontend/src/features/simulation-lab/pages/SimulationLabWorkspace.jsx`** [MODIFY] (< 185 dòng):
    - Đón nhận tham số điều hướng từ Workflow Context và hiển thị `SimLabTodaySignalBanner`.

---

## 3. Luồng Dữ Liệu & Hợp Đồng Dữ Liệu (Data Contracts)

### Hợp đồng Tín hiệu Phiên Hôm Nay (`todaySignal`):
```typescript
interface TodaySignal {
  action: 'BUY' | 'SELL' | 'HOLD';
  actionLabel: string; // 'MUA MỚI' | 'BÁN CHỐT LỜI / CẮT LỖ' | 'NẮM GIỮ VỊ THẾ'
  date: string; // '2026-10-09'
  price: number; // 63890 (VND)
  stopLossPrice: number; // 60120 (VND)
  takeProfitPrice: number; // 71500 (VND)
  riskRewardRatio: number; // 2.05
  confidenceScore: number; // 85 (%)
  rationale: string; // 'Fast EMA(21) cắt lên Slow EMA(55) kèm thanh khoản vượt MA20'
  vnMarketFlags: {
    isNearCeiling: boolean; // Gần giá trần
    isNearFloor: boolean;   // Gần giá sàn
    liquidityStatus: 'SAFE' | 'WARNING_LOW';
  };
}
```

### Hợp đồng Bản thiết kế Chiến lược (`StrategyBlueprint`):
```typescript
interface StrategyBlueprint {
  id: string;
  name: string;
  ticker: string;
  period: string;
  interval: string;
  code: string;
  params: Record<string, number>;
  metrics: {
    totalReturn: number;
    cagr: number;
    sharpe: number;
    maxDrawdown: number;
    winRate: number;
  };
  savedAt: string;
}
```

---

## 4. Các Bước Thực Hiện Tuần Tự (Checklist Triển Khai)

- [ ] **Giai Đoạn 1: Xây Dựng Engine Khớp Lệnh Thực Tế & Tín Hiệu Hôm Nay**
  - [ ] Task 1.1: Tạo `quantaVnMarketRules.js` mô phỏng biên độ trần/sàn, thanh khoản tối thiểu và trượt giá.
  - [ ] Task 1.2: Tạo `quantaTodaySignalEngine.js` phân tích nến mới nhất và sinh khuyến nghị hành động phiên này.
  - [ ] Task 1.3: Cập nhật `quantaBacktestSimulator.js` tích hợp luật thị trường VN và xuất `todaySignal`.

- [ ] **Giai Đoạn 2: Xây Dựng Bộ Quản Lý Bản Thiết Kế Chiến Lược (Blueprint Storage & UI)**
  - [ ] Task 2.1: Tạo `quantaBlueprintStorage.js` lưu trữ và quản lý chiến lược cá nhân.
  - [ ] Task 2.2: Tạo `SimLabTodaySignalBanner.jsx` hiển thị tín hiệu phiên này trên biểu đồ.
  - [ ] Task 2.3: Tạo `SimLabBlueprintModal.jsx` cho phép lưu, mở và quản lý danh sách chiến lược.
  - [ ] Task 2.4: Nâng cấp `SimLabHeader.jsx` gắn nút Lưu Blueprint và tín hiệu.

- [ ] **Giai Đoạn 3: Cầu Nối Luồng Nghiệp Vụ Xuyên Suốt (Cross-Module Bridges)**
  - [ ] Task 3.1: Tạo `financialWorkflowContext.js` điều phối chuyển đổi ngữ cảnh giữa các phân hệ.
  - [ ] Task 3.2: Tích hợp CTA chuyển sang Lab trong `Learn Hub` (`QuantaLessonLabCta.jsx`).
  - [ ] Task 3.3: Tích hợp nút Backtest & Thêm Watchlist trong `BCTC Analysis` (`BctcActionBridge.jsx`).
  - [ ] Task 3.4: Cập nhật `SimulationLabWorkspace.jsx` đón nhận state từ Workflow Context.

- [ ] **Giai Đoạn 4: Kiểm Thử & Xác Minh Toàn Diện (Testing & Proof of Work)**
  - [ ] Task 4.1: Viết test case mới trong `frontend/src/__tests__/quantaVnRulesAndSignals.test.js`.
  - [ ] Task 4.2: Chạy `npm run test:unit` (đảm bảo 100% tests PASS).
  - [ ] Task 4.3: Chạy `npm run build` (đảm bảo 0 lỗi build).
  - [ ] Task 4.4: Dùng browser subagent kiểm tra trực quan luồng trải nghiệm trên trình duyệt.

---

## 5. Tiêu Chí Xác Minh (Verification Criteria)
1. **Kiểm tra tự động:**
   - `npm run test:unit` PASS toàn bộ suite tests (hiện tại 44 tests + test mới).
   - `npm run build` hoàn thành không có cảnh báo/lỗi.
2. **Kiểm tra trực quan:**
   - Banner `Tín hiệu hôm nay` hiển thị rõ ràng trên Quanta Studio (BUY/SELL/HOLD, Stop-Loss, Take-Profit).
   - Tính năng "Lưu chiến lược" hoạt động trơn tru, tải lại chiến lược bảo toàn nguyên vẹn tham số.
   - Luồng chuyển từ bài học trong Learn Hub sang Simulation Lab nạp đúng mã và code chỉ bằng 1 cú nhấp chuột.
