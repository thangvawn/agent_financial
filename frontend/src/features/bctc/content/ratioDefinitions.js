/**
 * ratioDefinitions.js — Bộ chỉ số tài chính toàn diện cho Phòng Thực Hành BCTC
 *
 * 7 nhóm · 30 chỉ số · Đầy đủ công thức, ý nghĩa, đơn vị, ngưỡng đánh giá
 * Nguồn: CFA Institute, Damodaran, Piotroski, Corporate Finance Institute
 */

// ── Helpers ──────────────────────────────────────────────────

function safeDivide(numerator, denominator) {
  if (numerator == null || denominator == null || denominator === 0) return null
  return numerator / denominator
}

function pct(numerator, denominator) {
  const value = safeDivide(numerator, denominator)
  return value != null ? +(value * 100).toFixed(4) : null
}

// ── Ratio Catalog ────────────────────────────────────────────

export const RATIO_CATALOG = [
  // ━━━━━ 1. KHẢ NĂNG SINH LỜI (Profitability) ━━━━━
  {
    key: 'gross_margin_pct',
    group: 'profitability',
    label: 'Biên lợi nhuận gộp',
    labelEn: 'Gross Profit Margin',
    formula: 'Lợi nhuận gộp ÷ Doanh thu × 100',
    formulaCode: '(gross_profit / revenue) × 100',
    meaning: 'Đo lường hiệu quả kiểm soát giá vốn hàng bán. Biên gộp cao nghĩa là doanh nghiệp có lợi thế cạnh tranh về chi phí sản xuất hoặc định giá sản phẩm.',
    unit: '%',
    thresholds: { good: [30, Infinity], neutral: [15, 30], bad: [-Infinity, 15] },
    compute: (d) => pct(d.gross_profit, d.revenue),
  },
  {
    key: 'operating_margin_pct',
    group: 'profitability',
    label: 'Biên lợi nhuận hoạt động',
    labelEn: 'Operating Profit Margin',
    formula: 'LNHĐKD ÷ Doanh thu × 100',
    formulaCode: '(operating_profit / revenue) × 100',
    meaning: 'Phản ánh khả năng sinh lời từ hoạt động kinh doanh cốt lõi sau khi trừ chi phí bán hàng và quản lý. Cho biết doanh nghiệp quản lý chi phí vận hành tốt đến mức nào.',
    unit: '%',
    thresholds: { good: [15, Infinity], neutral: [5, 15], bad: [-Infinity, 5] },
    compute: (d) => pct(d.operating_profit, d.revenue),
  },
  {
    key: 'ebitda_margin_pct',
    group: 'profitability',
    label: 'Biên EBITDA',
    labelEn: 'EBITDA Margin',
    formula: 'EBITDA ÷ Doanh thu × 100',
    formulaCode: '(ebitda / revenue) × 100',
    meaning: 'Đo khả năng sinh lời trước lãi vay, thuế, khấu hao. Hữu ích để so sánh doanh nghiệp có cấu trúc vốn và chính sách khấu hao khác nhau.',
    unit: '%',
    thresholds: { good: [20, Infinity], neutral: [10, 20], bad: [-Infinity, 10] },
    compute: (d) => pct(d.ebitda, d.revenue),
  },
  {
    key: 'net_margin_pct',
    group: 'profitability',
    label: 'Biên lợi nhuận ròng',
    labelEn: 'Net Profit Margin',
    formula: 'LNST ÷ Doanh thu × 100',
    formulaCode: '(net_income / revenue) × 100',
    meaning: 'Tỷ lệ lợi nhuận cuối cùng giữ lại từ mỗi đồng doanh thu sau khi trừ toàn bộ chi phí, lãi vay và thuế.',
    unit: '%',
    thresholds: { good: [10, Infinity], neutral: [3, 10], bad: [-Infinity, 3] },
    compute: (d) => pct(d.net_income, d.revenue),
  },
  {
    key: 'roe_pct',
    group: 'profitability',
    label: 'ROE — Tỷ suất sinh lời trên VCSH',
    labelEn: 'Return on Equity',
    formula: 'LNST ÷ Vốn chủ sở hữu × 100',
    formulaCode: '(net_income / equity) × 100',
    meaning: 'Cho biết mỗi đồng vốn chủ sở hữu tạo ra bao nhiêu lợi nhuận. Chỉ số quan trọng nhất với cổ đông. ROE cao + bền vững = doanh nghiệp chất lượng.',
    unit: '%',
    thresholds: { good: [15, Infinity], neutral: [8, 15], bad: [-Infinity, 8] },
    compute: (d) => pct(d.net_income, d.equity),
  },
  {
    key: 'roa_pct',
    group: 'profitability',
    label: 'ROA — Tỷ suất sinh lời trên tổng tài sản',
    labelEn: 'Return on Assets',
    formula: 'LNST ÷ Tổng tài sản × 100',
    formulaCode: '(net_income / total_assets) × 100',
    meaning: 'Đo hiệu quả sử dụng toàn bộ tài sản để tạo lợi nhuận, bất kể nguồn vốn là nợ hay vốn chủ.',
    unit: '%',
    thresholds: { good: [8, Infinity], neutral: [3, 8], bad: [-Infinity, 3] },
    compute: (d) => pct(d.net_income, d.total_assets),
  },
  {
    key: 'roic_pct',
    group: 'profitability',
    label: 'ROIC — Tỷ suất sinh lời trên vốn đầu tư',
    labelEn: 'Return on Invested Capital',
    formula: 'NOPAT ÷ Vốn đầu tư × 100',
    formulaCode: '(operating_profit × 0.8) / (equity + debt − cash) × 100',
    meaning: 'So sánh lợi nhuận hoạt động sau thuế với tổng vốn đầu tư (cả nợ lẫn vốn chủ). ROIC > WACC nghĩa là doanh nghiệp tạo giá trị.',
    unit: '%',
    thresholds: { good: [12, Infinity], neutral: [7, 12], bad: [-Infinity, 7] },
    compute: (d) => {
      const invested = (d.equity || 0) + (d.debt || 0) - (d.cash || 0)
      return invested > 0 ? pct((d.operating_profit || 0) * 0.8, invested) : null
    },
  },

  // ━━━━━ 2. THANH KHOẢN (Liquidity) ━━━━━
  {
    key: 'current_ratio',
    group: 'liquidity',
    label: 'Hệ số thanh toán hiện hành',
    labelEn: 'Current Ratio',
    formula: 'Tài sản ngắn hạn ÷ Nợ ngắn hạn',
    formulaCode: 'current_assets / current_liabilities',
    meaning: 'Khả năng dùng tài sản ngắn hạn để trả nợ ngắn hạn. > 1 nghĩa là tài sản ngắn hạn vượt nợ ngắn hạn. < 1 là dấu hiệu rủi ro thanh khoản.',
    unit: 'x',
    thresholds: { good: [1.5, Infinity], neutral: [1, 1.5], bad: [-Infinity, 1] },
    compute: (d) => safeDivide(d.current_assets, d.current_liabilities),
  },
  {
    key: 'quick_ratio',
    group: 'liquidity',
    label: 'Hệ số thanh toán nhanh',
    labelEn: 'Quick Ratio (Acid-Test)',
    formula: '(TSNH − Hàng tồn kho) ÷ Nợ ngắn hạn',
    formulaCode: '(current_assets − inventory) / current_liabilities',
    meaning: 'Loại bỏ hàng tồn kho (khó thanh khoản) khỏi TSNH. Phản ánh khả năng trả nợ bằng tiền mặt, đầu tư ngắn hạn và khoản phải thu.',
    unit: 'x',
    thresholds: { good: [1, Infinity], neutral: [0.5, 1], bad: [-Infinity, 0.5] },
    compute: (d) => {
      const quick = d.current_assets != null ? d.current_assets - (d.inventory || 0) : null
      return safeDivide(quick, d.current_liabilities)
    },
  },
  {
    key: 'cash_ratio',
    group: 'liquidity',
    label: 'Hệ số thanh toán bằng tiền',
    labelEn: 'Cash Ratio',
    formula: 'Tiền và tương đương tiền ÷ Nợ ngắn hạn',
    formulaCode: 'cash / current_liabilities',
    meaning: 'Chỉ tính tiền mặt và tương đương tiền — nghiêm ngặt nhất. Cho biết doanh nghiệp có đủ tiền trả nợ ngay lập tức không.',
    unit: 'x',
    thresholds: { good: [0.5, Infinity], neutral: [0.2, 0.5], bad: [-Infinity, 0.2] },
    compute: (d) => safeDivide(d.cash, d.current_liabilities),
  },

  // ━━━━━ 3. ĐÒN BẨY TÀI CHÍNH (Leverage / Solvency) ━━━━━
  {
    key: 'debt_to_equity',
    group: 'leverage',
    label: 'Nợ vay / Vốn chủ sở hữu',
    labelEn: 'Debt-to-Equity Ratio',
    formula: 'Tổng nợ vay ÷ Vốn chủ sở hữu',
    formulaCode: 'debt / equity',
    meaning: 'Đo mức độ sử dụng nợ so với vốn chủ. D/E cao = đòn bẩy lớn = rủi ro tài chính cao nhưng có thể khuếch đại ROE.',
    unit: 'x',
    thresholds: { good: [-Infinity, 0.5], neutral: [0.5, 1.5], bad: [1.5, Infinity] },
    higherIsBetter: false,
    compute: (d) => safeDivide(d.debt, d.equity),
  },
  {
    key: 'liabilities_to_assets',
    group: 'leverage',
    label: 'Nợ phải trả / Tổng tài sản',
    labelEn: 'Debt-to-Assets Ratio',
    formula: 'Tổng nợ phải trả ÷ Tổng tài sản × 100',
    formulaCode: '(total_liabilities / total_assets) × 100',
    meaning: 'Tỷ lệ tài sản được tài trợ bằng nợ. > 70% là dấu hiệu phụ thuộc nợ cao.',
    unit: '%',
    thresholds: { good: [-Infinity, 50], neutral: [50, 70], bad: [70, Infinity] },
    higherIsBetter: false,
    compute: (d) => pct(d.total_liabilities, d.total_assets),
  },
  {
    key: 'debt_to_capital',
    group: 'leverage',
    label: 'Nợ vay / Tổng vốn',
    labelEn: 'Debt-to-Capital Ratio',
    formula: 'Nợ vay ÷ (Nợ vay + VCSH) × 100',
    formulaCode: 'debt / (debt + equity) × 100',
    meaning: 'Tỷ trọng nợ trong tổng cấu trúc vốn. Cho biết bao nhiêu % vốn đến từ nợ vay.',
    unit: '%',
    thresholds: { good: [-Infinity, 30], neutral: [30, 60], bad: [60, Infinity] },
    higherIsBetter: false,
    compute: (d) => {
      const capital = (d.debt || 0) + (d.equity || 0)
      return capital > 0 ? pct(d.debt, capital) : null
    },
  },
  {
    key: 'equity_multiplier',
    group: 'leverage',
    label: 'Hệ số đòn bẩy tài chính',
    labelEn: 'Equity Multiplier (Financial Leverage)',
    formula: 'Tổng tài sản ÷ Vốn chủ sở hữu',
    formulaCode: 'total_assets / equity',
    meaning: 'Thành phần của phân tích DuPont. Cho biết mỗi đồng vốn chủ hỗ trợ bao nhiêu đồng tài sản. Càng cao = đòn bẩy càng lớn.',
    unit: 'x',
    thresholds: { good: [-Infinity, 2], neutral: [2, 4], bad: [4, Infinity] },
    higherIsBetter: false,
    compute: (d) => safeDivide(d.total_assets, d.equity),
  },
  {
    key: 'net_debt_to_ebitda',
    group: 'leverage',
    label: 'Nợ ròng / EBITDA',
    labelEn: 'Net Debt / EBITDA',
    formula: '(Nợ vay − Tiền) ÷ EBITDA',
    formulaCode: '(debt − cash) / ebitda',
    meaning: 'Cho biết doanh nghiệp cần bao nhiêu năm EBITDA để trả hết nợ ròng. < 2 = an toàn, > 4 = rủi ro cao.',
    unit: 'x',
    thresholds: { good: [-Infinity, 2], neutral: [2, 4], bad: [4, Infinity] },
    higherIsBetter: false,
    compute: (d) => {
      const netDebt = (d.debt || 0) - (d.cash || 0)
      return safeDivide(netDebt, d.ebitda)
    },
  },
  {
    key: 'interest_coverage',
    group: 'leverage',
    label: 'Hệ số khả năng trả lãi vay',
    labelEn: 'Interest Coverage Ratio',
    formula: 'EBIT ÷ Chi phí lãi vay',
    formulaCode: 'ebit / interest_expense',
    meaning: 'Khả năng lợi nhuận trước thuế bao phủ chi phí lãi vay. < 1.5 = nguy hiểm, không đủ trả lãi. > 5 = rất an toàn.',
    unit: 'x',
    thresholds: { good: [5, Infinity], neutral: [1.5, 5], bad: [-Infinity, 1.5] },
    compute: (d) => safeDivide(d.ebit, d.interest_expense),
  },

  // ━━━━━ 4. HIỆU QUẢ HOẠT ĐỘNG (Efficiency / Activity) ━━━━━
  {
    key: 'asset_turnover',
    group: 'efficiency',
    label: 'Vòng quay tổng tài sản',
    labelEn: 'Total Asset Turnover',
    formula: 'Doanh thu ÷ Tổng tài sản',
    formulaCode: 'revenue / total_assets',
    meaning: 'Thành phần DuPont. Số vòng quay tài sản trong kỳ — mỗi đồng tài sản tạo ra bao nhiêu đồng doanh thu. Cao = dùng tài sản hiệu quả.',
    unit: 'x',
    thresholds: { good: [1.5, Infinity], neutral: [0.5, 1.5], bad: [-Infinity, 0.5] },
    compute: (d) => safeDivide(d.revenue, d.total_assets),
  },
  {
    key: 'inventory_turnover',
    group: 'efficiency',
    label: 'Vòng quay hàng tồn kho',
    labelEn: 'Inventory Turnover',
    formula: 'Giá vốn hàng bán ÷ Hàng tồn kho',
    formulaCode: 'cost_of_goods_sold / inventory',
    meaning: 'Số lần hàng tồn kho được bán và thay thế trong kỳ. Cao = bán hàng nhanh, thấp = ứ đọng hàng.',
    unit: 'x',
    thresholds: { good: [8, Infinity], neutral: [4, 8], bad: [-Infinity, 4] },
    compute: (d) => {
      const cogs = d.cost_of_goods_sold != null ? d.cost_of_goods_sold
        : (d.revenue != null && d.gross_profit != null ? d.revenue - d.gross_profit : null)
      return safeDivide(cogs, d.inventory)
    },
  },
  {
    key: 'inventory_days',
    group: 'efficiency',
    label: 'Số ngày tồn kho (DIO)',
    labelEn: 'Days Inventory Outstanding',
    formula: 'Hàng tồn kho ÷ (GVHB ÷ 365)',
    formulaCode: 'inventory / (cost_of_goods_sold / 365)',
    meaning: 'Trung bình bao nhiêu ngày để bán hết hàng tồn kho. Ngắn = hiệu quả. Dài = ứ đọng, tốn chi phí lưu kho.',
    unit: 'ngày',
    thresholds: { good: [-Infinity, 30], neutral: [30, 90], bad: [90, Infinity] },
    higherIsBetter: false,
    compute: (d) => {
      const cogs = d.cost_of_goods_sold != null ? d.cost_of_goods_sold
        : (d.revenue != null && d.gross_profit != null ? d.revenue - d.gross_profit : null)
      const days = d.quarter != null ? 90 : 365
      return safeDivide(d.inventory, cogs != null ? cogs / days : null)
    },
  },
  {
    key: 'receivable_days',
    group: 'efficiency',
    label: 'Số ngày phải thu (DSO)',
    labelEn: 'Days Sales Outstanding',
    formula: 'Khoản phải thu ÷ (Doanh thu ÷ 365)',
    formulaCode: 'receivables / (revenue / 365)',
    meaning: 'Trung bình bao nhiêu ngày để thu hồi tiền bán hàng. Ngắn = thu tiền nhanh, dài = bị chiếm dụng vốn.',
    unit: 'ngày',
    thresholds: { good: [-Infinity, 30], neutral: [30, 60], bad: [60, Infinity] },
    higherIsBetter: false,
    compute: (d) => {
      const days = d.quarter != null ? 90 : 365
      return safeDivide(d.receivables, d.revenue != null ? d.revenue / days : null)
    },
  },
  {
    key: 'payable_days',
    group: 'efficiency',
    label: 'Số ngày phải trả (DPO)',
    labelEn: 'Days Payable Outstanding',
    formula: 'Phải trả người bán ÷ (GVHB ÷ 365)',
    formulaCode: 'accounts_payable / (cost_of_goods_sold / 365)',
    meaning: 'Trung bình bao nhiêu ngày để trả tiền nhà cung cấp. Dài = chiếm dụng vốn nhà cung cấp (có lợi nếu hợp lý).',
    unit: 'ngày',
    thresholds: { good: [30, 90], neutral: [15, 30], bad: [-Infinity, 15] },
    compute: (d) => {
      const cogs = d.cost_of_goods_sold != null ? d.cost_of_goods_sold
        : (d.revenue != null && d.gross_profit != null ? d.revenue - d.gross_profit : null)
      const days = d.quarter != null ? 90 : 365
      return safeDivide(d.accounts_payable, cogs != null ? cogs / days : null)
    },
  },
  {
    key: 'cash_conversion_cycle',
    group: 'efficiency',
    label: 'Chu kỳ chuyển đổi tiền mặt (CCC)',
    labelEn: 'Cash Conversion Cycle',
    formula: 'DIO + DSO − DPO',
    formulaCode: 'inventory_days + receivable_days − payable_days',
    meaning: 'Tổng thời gian từ lúc trả tiền nguyên liệu → sản xuất → bán hàng → thu tiền. Âm = doanh nghiệp nhận tiền trước khi phải trả (rất tốt).',
    unit: 'ngày',
    thresholds: { good: [-Infinity, 30], neutral: [30, 90], bad: [90, Infinity] },
    higherIsBetter: false,
    compute: (d, allRatios) => {
      const dio = allRatios?.inventory_days
      const dso = allRatios?.receivable_days
      const dpo = allRatios?.payable_days
      if (dio == null || dso == null || dpo == null) return null
      return +(dio + dso - dpo).toFixed(2)
    },
  },
  {
    key: 'working_capital_turnover',
    group: 'efficiency',
    label: 'Vòng quay vốn lưu động',
    labelEn: 'Working Capital Turnover',
    formula: 'Doanh thu ÷ (TSNH − Nợ ngắn hạn)',
    formulaCode: 'revenue / (current_assets − current_liabilities)',
    meaning: 'Hiệu quả sử dụng vốn lưu động ròng để tạo doanh thu. Quá cao có thể thiếu vốn lưu động, quá thấp = sử dụng kém hiệu quả.',
    unit: 'x',
    thresholds: { good: [4, 20], neutral: [1.5, 4], bad: [-Infinity, 1.5] },
    compute: (d) => {
      const wc = d.current_assets != null && d.current_liabilities != null
        ? d.current_assets - d.current_liabilities : null
      return wc != null && wc !== 0 ? safeDivide(d.revenue, wc) : null
    },
  },

  // ━━━━━ 5. CHẤT LƯỢNG DÒNG TIỀN (Cash Flow Quality) ━━━━━
  {
    key: 'ocf_to_net_income',
    group: 'cash_quality',
    label: 'CFO / LNST',
    labelEn: 'Operating Cash Flow to Net Income',
    formula: 'Dòng tiền HĐKD ÷ LNST',
    formulaCode: 'operating_cash_flow / net_income',
    meaning: 'CFO > LNST nghĩa là lợi nhuận được hỗ trợ bằng tiền thật. CFO < LNST = lợi nhuận "giấy", có thể từ ghi nhận dồn tích.',
    unit: 'x',
    thresholds: { good: [1, Infinity], neutral: [0.8, 1], bad: [-Infinity, 0.8] },
    compute: (d) => safeDivide(d.operating_cash_flow, d.net_income),
  },
  {
    key: 'fcf_margin_pct',
    group: 'cash_quality',
    label: 'Biên dòng tiền tự do',
    labelEn: 'Free Cash Flow Margin',
    formula: 'FCF ÷ Doanh thu × 100',
    formulaCode: '(operating_cash_flow − |capex|) / revenue × 100',
    meaning: 'Tỷ lệ doanh thu được chuyển thành dòng tiền tự do — tiền thừa sau đầu tư có thể trả cổ tức, mua lại cổ phiếu hoặc trả nợ.',
    unit: '%',
    thresholds: { good: [10, Infinity], neutral: [0, 10], bad: [-Infinity, 0] },
    compute: (d) => {
      const fcf = d.operating_cash_flow != null ? d.operating_cash_flow - Math.abs(d.capex || 0) : null
      return pct(fcf, d.revenue)
    },
  },
  {
    key: 'cash_conversion_pct',
    group: 'cash_quality',
    label: 'Tỷ lệ chuyển đổi LN thành tiền',
    labelEn: 'Cash Conversion Ratio',
    formula: 'CFO ÷ LNST × 100',
    formulaCode: '(operating_cash_flow / net_income) × 100',
    meaning: 'Giống CFO/LNST nhưng biểu diễn dạng %. > 100% = xuất sắc, < 80% = cần điều tra accrual quality.',
    unit: '%',
    thresholds: { good: [100, Infinity], neutral: [80, 100], bad: [-Infinity, 80] },
    compute: (d) => pct(d.operating_cash_flow, d.net_income),
  },
  {
    key: 'capex_to_revenue',
    group: 'cash_quality',
    label: 'CAPEX / Doanh thu',
    labelEn: 'Capital Expenditure to Revenue',
    formula: '|CAPEX| ÷ Doanh thu × 100',
    formulaCode: '|capex| / revenue × 100',
    meaning: 'Tỷ lệ doanh thu dành cho đầu tư tài sản cố định. Quá cao có thể gây áp lực dòng tiền, quá thấp có thể thiếu đầu tư phát triển.',
    unit: '%',
    thresholds: { good: [3, 15], neutral: [15, 30], bad: [30, Infinity] },
    compute: (d) => pct(Math.abs(d.capex || 0), d.revenue),
  },

  // ━━━━━ 6. TĂNG TRƯỞNG (Growth) ━━━━━
  {
    key: 'revenue_growth_yoy_pct',
    group: 'growth',
    label: 'Tăng trưởng doanh thu YoY',
    labelEn: 'Revenue Growth Year-over-Year',
    formula: '(DT kỳ này − DT cùng kỳ) ÷ |DT cùng kỳ| × 100',
    formulaCode: '(revenue − revenue_yoy) / |revenue_yoy| × 100',
    meaning: 'Tốc độ tăng trưởng doanh thu so với cùng kỳ năm trước. Dương = mở rộng kinh doanh, âm = thu hẹp.',
    unit: '%',
    thresholds: { good: [10, Infinity], neutral: [0, 10], bad: [-Infinity, 0] },
    compute: (d, _, yoy) => {
      if (yoy == null || !yoy.revenue || yoy.revenue === 0) return null
      return +((((d.revenue || 0) - yoy.revenue) / Math.abs(yoy.revenue)) * 100).toFixed(4)
    },
  },
  {
    key: 'net_income_growth_yoy_pct',
    group: 'growth',
    label: 'Tăng trưởng LNST YoY',
    labelEn: 'Net Income Growth Year-over-Year',
    formula: '(LNST kỳ này − LNST cùng kỳ) ÷ |LNST cùng kỳ| × 100',
    formulaCode: '(net_income − net_income_yoy) / |net_income_yoy| × 100',
    meaning: 'Tốc độ tăng trưởng lợi nhuận sau thuế. Tăng trưởng LNST > tăng trưởng DT = biên lợi nhuận đang cải thiện.',
    unit: '%',
    thresholds: { good: [10, Infinity], neutral: [0, 10], bad: [-Infinity, 0] },
    compute: (d, _, yoy) => {
      if (yoy == null || !yoy.net_income || yoy.net_income === 0) return null
      return +((((d.net_income || 0) - yoy.net_income) / Math.abs(yoy.net_income)) * 100).toFixed(4)
    },
  },
  {
    key: 'gross_profit_growth_yoy_pct',
    group: 'growth',
    label: 'Tăng trưởng lợi nhuận gộp YoY',
    labelEn: 'Gross Profit Growth YoY',
    formula: '(LNG kỳ này − LNG cùng kỳ) ÷ |LNG cùng kỳ| × 100',
    formulaCode: '(gross_profit − gross_profit_yoy) / |gross_profit_yoy| × 100',
    meaning: 'Tăng trưởng lợi nhuận gộp phản ánh khả năng mở rộng kinh doanh đồng thời giữ biên lợi nhuận.',
    unit: '%',
    thresholds: { good: [10, Infinity], neutral: [0, 10], bad: [-Infinity, 0] },
    compute: (d, _, yoy) => {
      if (yoy == null || !yoy.gross_profit || yoy.gross_profit === 0) return null
      return +((((d.gross_profit || 0) - yoy.gross_profit) / Math.abs(yoy.gross_profit)) * 100).toFixed(4)
    },
  },

  // ━━━━━ 7. PHÂN TÍCH DUPONT (DuPont Decomposition) ━━━━━
  {
    key: 'dupont_npm',
    group: 'dupont',
    label: 'DuPont: Biên lợi nhuận ròng',
    labelEn: 'DuPont: Net Profit Margin',
    formula: 'LNST ÷ Doanh thu',
    formulaCode: 'net_income / revenue',
    meaning: 'Yếu tố 1/3 của DuPont: Hiệu quả quản lý chi phí — mỗi đồng doanh thu giữ lại bao nhiêu lợi nhuận.',
    unit: 'x',
    thresholds: { good: [0.1, Infinity], neutral: [0.03, 0.1], bad: [-Infinity, 0.03] },
    compute: (d) => safeDivide(d.net_income, d.revenue),
  },
  {
    key: 'dupont_at',
    group: 'dupont',
    label: 'DuPont: Vòng quay tài sản',
    labelEn: 'DuPont: Asset Turnover',
    formula: 'Doanh thu ÷ Tổng tài sản',
    formulaCode: 'revenue / total_assets',
    meaning: 'Yếu tố 2/3 của DuPont: Hiệu quả sử dụng tài sản — mỗi đồng tài sản tạo bao nhiêu đồng doanh thu.',
    unit: 'x',
    thresholds: { good: [1, Infinity], neutral: [0.5, 1], bad: [-Infinity, 0.5] },
    compute: (d) => safeDivide(d.revenue, d.total_assets),
  },
  {
    key: 'dupont_em',
    group: 'dupont',
    label: 'DuPont: Đòn bẩy tài chính',
    labelEn: 'DuPont: Equity Multiplier',
    formula: 'Tổng tài sản ÷ Vốn chủ sở hữu',
    formulaCode: 'total_assets / equity',
    meaning: 'Yếu tố 3/3 của DuPont: Mức độ sử dụng nợ. ROE = NPM × AT × EM — nếu ROE cao do EM cao, đó là đòn bẩy chứ không phải hiệu quả.',
    unit: 'x',
    thresholds: { good: [-Infinity, 2], neutral: [2, 4], bad: [4, Infinity] },
    higherIsBetter: false,
    compute: (d) => safeDivide(d.total_assets, d.equity),
  },
]

// ── Group metadata ───────────────────────────────────────────

export const RATIO_GROUPS = [
  {
    key: 'profitability',
    label: 'Khả năng sinh lời',
    labelEn: 'Profitability',
    icon: 'trending-up',
    description: 'Đo lường khả năng tạo lợi nhuận từ doanh thu, tài sản và vốn chủ sở hữu.',
  },
  {
    key: 'liquidity',
    label: 'Thanh khoản',
    labelEn: 'Liquidity',
    icon: 'droplets',
    description: 'Đánh giá khả năng doanh nghiệp trả các khoản nợ ngắn hạn đến hạn.',
  },
  {
    key: 'leverage',
    label: 'Đòn bẩy & Cấu trúc vốn',
    labelEn: 'Leverage & Solvency',
    icon: 'scale',
    description: 'Phân tích mức độ sử dụng nợ và khả năng trả nợ dài hạn.',
  },
  {
    key: 'efficiency',
    label: 'Hiệu quả hoạt động',
    labelEn: 'Efficiency & Activity',
    icon: 'refresh-cw',
    description: 'Đo tốc độ luân chuyển tài sản, hàng tồn kho và các khoản phải thu/trả.',
  },
  {
    key: 'cash_quality',
    label: 'Chất lượng dòng tiền',
    labelEn: 'Cash Flow Quality',
    icon: 'banknote',
    description: 'Kiểm tra lợi nhuận có được hỗ trợ bằng dòng tiền thật hay chỉ là "lợi nhuận giấy".',
  },
  {
    key: 'growth',
    label: 'Tăng trưởng',
    labelEn: 'Growth',
    icon: 'arrow-up-right',
    description: 'So sánh doanh thu, lợi nhuận với cùng kỳ năm trước để đánh giá đà tăng trưởng.',
  },
  {
    key: 'dupont',
    label: 'Phân tích DuPont',
    labelEn: 'DuPont Decomposition',
    icon: 'git-branch',
    description: 'Phân rã ROE = NPM × Asset Turnover × Equity Multiplier để hiểu nguồn gốc sinh lời.',
  },
]

// ── Source data fields needed ────────────────────────────────

export const SOURCE_DATA_FIELDS = [
  { key: 'revenue', label: 'Doanh thu thuần', source: 'income' },
  { key: 'gross_profit', label: 'Lợi nhuận gộp', source: 'income' },
  { key: 'operating_profit', label: 'Lợi nhuận hoạt động (EBIT)', source: 'income' },
  { key: 'ebit', label: 'EBIT', source: 'income' },
  { key: 'ebitda', label: 'EBITDA', source: 'income' },
  { key: 'net_income', label: 'Lợi nhuận sau thuế (LNST)', source: 'income' },
  { key: 'interest_expense', label: 'Chi phí lãi vay', source: 'income' },
  { key: 'current_assets', label: 'Tài sản ngắn hạn', source: 'balance' },
  { key: 'cash', label: 'Tiền và tương đương tiền', source: 'balance' },
  { key: 'receivables', label: 'Các khoản phải thu', source: 'balance' },
  { key: 'inventory', label: 'Hàng tồn kho', source: 'balance' },
  { key: 'total_assets', label: 'Tổng tài sản', source: 'balance' },
  { key: 'accounts_payable', label: 'Phải trả người bán', source: 'balance' },
  { key: 'current_liabilities', label: 'Nợ ngắn hạn', source: 'balance' },
  { key: 'total_liabilities', label: 'Tổng nợ phải trả', source: 'balance' },
  { key: 'debt', label: 'Tổng nợ vay (ngắn hạn + dài hạn)', source: 'balance' },
  { key: 'equity', label: 'Vốn chủ sở hữu', source: 'balance' },
  { key: 'operating_cash_flow', label: 'Dòng tiền HĐKD (CFO)', source: 'cash_flow' },
  { key: 'capex', label: 'Chi đầu tư TSCĐ (CAPEX)', source: 'cash_flow' },
]

// ── Evaluation helper ────────────────────────────────────────

export function evaluateRatio(ratioKey, value) {
  if (value == null) return 'neutral'
  const definition = RATIO_CATALOG.find((r) => r.key === ratioKey)
  if (!definition || !definition.thresholds) return 'neutral'
  const { good, bad } = definition.thresholds
  if (value >= good[0] && value <= good[1]) return 'good'
  if (value >= bad[0] && value <= bad[1]) return 'bad'
  return 'neutral'
}

// ── Compute all ratios from raw period data ──────────────────

export function computeAllRatios(periodData, yoyData = null) {
  const results = {}
  // First pass: compute simple ratios
  for (const ratio of RATIO_CATALOG) {
    if (ratio.key === 'cash_conversion_cycle') continue
    results[ratio.key] = ratio.compute(periodData, null, yoyData)
  }
  // Second pass: compute composite ratios (CCC)
  const ccc = RATIO_CATALOG.find((r) => r.key === 'cash_conversion_cycle')
  if (ccc) {
    results.cash_conversion_cycle = ccc.compute(periodData, results, yoyData)
  }
  return results
}

// ── Tolerance for student grading ────────────────────────────

export function gradeAnswer(studentAnswer, correctAnswer, unit) {
  if (studentAnswer == null || correctAnswer == null) return { status: 'skip', delta: null }
  const studentNum = Number(studentAnswer)
  if (!Number.isFinite(studentNum)) return { status: 'invalid', delta: null }
  const delta = studentNum - correctAnswer
  const tolerance = unit === '%' ? 0.5 : unit === 'ngày' ? 2 : 0.05
  const absDelta = Math.abs(delta)
  if (absDelta <= tolerance) return { status: 'correct', delta }
  if (absDelta <= tolerance * 3) return { status: 'close', delta }
  return { status: 'incorrect', delta }
}
