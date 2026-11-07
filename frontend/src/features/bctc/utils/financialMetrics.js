// Monetary fields use the same unit; market price and per-share amounts use VND.
export const FIELDS = [
  ['revenue', 'Doanh thu thuần', 'income'], ['cost_of_goods_sold', 'Giá vốn hàng bán (số dương)', 'income'],
  ['gross_profit', 'Lợi nhuận gộp', 'income'], ['operating_profit', 'Lợi nhuận hoạt động', 'income'],
  ['pretax_profit', 'Lợi nhuận trước thuế', 'income'], ['net_income', 'Lợi nhuận ròng', 'income'],
  ['interest_expense', 'Chi phí lãi vay (số dương)', 'income'], ['tax_expense', 'Chi phí thuế (số dương)', 'income'],
  ['cash', 'Tiền và tương đương tiền', 'balance'], ['receivables', 'Phải thu', 'balance'], ['inventory', 'Hàng tồn kho', 'balance'],
  ['current_assets', 'Tài sản ngắn hạn', 'balance'], ['current_liabilities', 'Nợ ngắn hạn', 'balance'],
  ['total_assets', 'Tổng tài sản', 'balance'], ['total_liabilities', 'Tổng nợ phải trả', 'balance'],
  ['equity', 'Vốn chủ sở hữu', 'balance'], ['debt', 'Tổng nợ vay có lãi', 'manual'],
  ['payables', 'Phải trả người bán', 'balance'], ['fixed_assets', 'Tài sản cố định', 'balance'],
  ['operating_cash_flow', 'Dòng tiền hoạt động', 'cash_flow'], ['capex', 'Chi đầu tư tài sản cố định (số dương)', 'cash_flow'],
  ['previous_revenue', 'Doanh thu kỳ so sánh', 'previous_income'], ['previous_net_income', 'Lợi nhuận ròng kỳ so sánh', 'previous_income'],
  ['previous_total_assets', 'Tổng tài sản đầu kỳ', 'previous_balance'], ['previous_equity', 'Vốn chủ sở hữu đầu kỳ', 'previous_balance'],
  ['previous_inventory', 'Hàng tồn kho đầu kỳ', 'previous_balance'], ['previous_receivables', 'Phải thu đầu kỳ', 'previous_balance'],
  ['previous_payables', 'Phải trả người bán đầu kỳ', 'previous_balance'], ['previous_fixed_assets', 'Tài sản cố định đầu kỳ', 'previous_balance'],
  ['days', 'Số ngày trong kỳ', 'calendar'],
  ['price', 'Giá cổ phiếu (VND/cổ phiếu)', 'market'], ['eps', 'EPS cơ bản (VND/cổ phiếu)', 'market'],
  ['book_value_per_share', 'Giá trị sổ sách/cổ phiếu (VND)', 'market'], ['dividend_per_share', 'Cổ tức/cổ phiếu (VND)', 'market'],
]
const ratio = (a, b, scale = 1) => b === 0 ? null : a / b * scale
const avg = (a, b) => (a + b) / 2
// Dependencies make missing input explicit and prevent accidental substitution with zero.
const m = (id, group, label, formula, deps, unit, calc, note = '') => ({ id, group, label, formula, deps, unit, calc, note })
export const METRICS = [
  m('gross_margin','Sinh lời','Biên lợi nhuận gộp','Lợi nhuận gộp / Doanh thu × 100',['gross_profit','revenue'],'%',(a,b)=>ratio(a,b,100)),
  m('operating_margin','Sinh lời','Biên lợi nhuận hoạt động','Lợi nhuận hoạt động / Doanh thu × 100',['operating_profit','revenue'],'%',(a,b)=>ratio(a,b,100)),
  m('pretax_margin','Sinh lời','Biên lợi nhuận trước thuế','Lợi nhuận trước thuế / Doanh thu × 100',['pretax_profit','revenue'],'%',(a,b)=>ratio(a,b,100)),
  m('net_margin','Sinh lời','Biên lợi nhuận ròng','Lợi nhuận ròng / Doanh thu × 100',['net_income','revenue'],'%',(a,b)=>ratio(a,b,100)),
  m('roe','Sinh lời','ROE','Lợi nhuận ròng / Vốn chủ sở hữu bình quân × 100',['net_income','previous_equity','equity'],'%',(a,b,c)=>ratio(a,avg(b,c),100),'Không quy đổi năm; dùng lợi nhuận của kỳ đã chọn.'),
  m('roa','Sinh lời','ROA','Lợi nhuận ròng / Tổng tài sản bình quân × 100',['net_income','previous_total_assets','total_assets'],'%',(a,b,c)=>ratio(a,avg(b,c),100),'Không quy đổi năm; dùng lợi nhuận của kỳ đã chọn.'),
  m('tax_rate','Sinh lời','Thuế suất hiệu dụng','Chi phí thuế / Lợi nhuận trước thuế × 100',['tax_expense','pretax_profit'],'%',(a,b)=>ratio(a,b,100)),
  m('current_ratio','Thanh khoản','Thanh toán hiện hành','Tài sản ngắn hạn / Nợ ngắn hạn',['current_assets','current_liabilities'],'lần',ratio),
  m('quick_ratio','Thanh khoản','Thanh toán nhanh','(Tài sản ngắn hạn − Hàng tồn kho) / Nợ ngắn hạn',['current_assets','inventory','current_liabilities'],'lần',(a,b,c)=>ratio(a-b,c)),
  m('cash_ratio','Thanh khoản','Thanh toán bằng tiền','Tiền và tương đương tiền / Nợ ngắn hạn',['cash','current_liabilities'],'lần',ratio),
  m('working_capital','Thanh khoản','Vốn lưu động ròng','Tài sản ngắn hạn − Nợ ngắn hạn',['current_assets','current_liabilities'],'money',(a,b)=>a-b),
  m('liabilities_assets','Đòn bẩy và chi trả','Nợ phải trả / Tài sản','Tổng nợ phải trả / Tổng tài sản × 100',['total_liabilities','total_assets'],'%',(a,b)=>ratio(a,b,100)),
  m('debt_assets','Đòn bẩy và chi trả','Nợ vay / Tài sản','Tổng nợ vay có lãi / Tổng tài sản × 100',['debt','total_assets'],'%',(a,b)=>ratio(a,b,100)),
  m('debt_equity','Đòn bẩy và chi trả','Nợ vay / Vốn chủ sở hữu','Tổng nợ vay có lãi / Vốn chủ sở hữu',['debt','equity'],'lần',ratio),
  m('liabilities_equity','Đòn bẩy và chi trả','Nợ phải trả / Vốn chủ sở hữu','Tổng nợ phải trả / Vốn chủ sở hữu',['total_liabilities','equity'],'lần',ratio),
  m('equity_assets','Đòn bẩy và chi trả','Tỷ lệ vốn chủ sở hữu','Vốn chủ sở hữu / Tổng tài sản × 100',['equity','total_assets'],'%',(a,b)=>ratio(a,b,100)),
  m('interest_coverage','Đòn bẩy và chi trả','Khả năng trả lãi (xấp xỉ EBIT)','(Lợi nhuận trước thuế + Chi phí lãi vay) / Chi phí lãi vay',['pretax_profit','interest_expense'],'lần',(a,b)=>ratio(a+b,b),'EBIT xấp xỉ; không điều chỉnh các khoản phi hoạt động.'),
  m('asset_turnover','Hiệu quả hoạt động','Vòng quay tài sản','Doanh thu / Tài sản bình quân',['revenue','previous_total_assets','total_assets'],'lần',(a,b,c)=>ratio(a,avg(b,c))),
  m('fixed_turnover','Hiệu quả hoạt động','Vòng quay tài sản cố định','Doanh thu / Tài sản cố định bình quân',['revenue','previous_fixed_assets','fixed_assets'],'lần',(a,b,c)=>ratio(a,avg(b,c))),
  m('inventory_turnover','Hiệu quả hoạt động','Vòng quay hàng tồn kho','Giá vốn / Hàng tồn kho bình quân',['cost_of_goods_sold','previous_inventory','inventory'],'lần',(a,b,c)=>ratio(a,avg(b,c))),
  m('receivable_turnover','Hiệu quả hoạt động','Vòng quay phải thu','Doanh thu / Phải thu bình quân',['revenue','previous_receivables','receivables'],'lần',(a,b,c)=>ratio(a,avg(b,c)),'Dùng doanh thu thuần làm xấp xỉ doanh thu bán chịu.'),
  m('payable_turnover','Hiệu quả hoạt động','Vòng quay phải trả','Giá vốn / Phải trả bình quân',['cost_of_goods_sold','previous_payables','payables'],'lần',(a,b,c)=>ratio(a,avg(b,c)),'Dùng giá vốn làm xấp xỉ giá trị mua chịu.'),
  m('inventory_days','Hiệu quả hoạt động','Số ngày tồn kho','Hàng tồn kho bình quân / Giá vốn × Số ngày trong kỳ',['previous_inventory','inventory','cost_of_goods_sold','days'],'ngày',(a,b,c,d)=>ratio(avg(a,b)*d,c)),
  m('receivable_days','Hiệu quả hoạt động','Số ngày phải thu','Phải thu bình quân / Doanh thu × Số ngày trong kỳ',['previous_receivables','receivables','revenue','days'],'ngày',(a,b,c,d)=>ratio(avg(a,b)*d,c),'Doanh thu thuần là xấp xỉ doanh thu bán chịu.'),
  m('payable_days','Hiệu quả hoạt động','Số ngày phải trả','Phải trả bình quân / Giá vốn × Số ngày trong kỳ',['previous_payables','payables','cost_of_goods_sold','days'],'ngày',(a,b,c,d)=>ratio(avg(a,b)*d,c),'Giá vốn là xấp xỉ giá trị mua chịu.'),
  m('cash_cycle','Hiệu quả hoạt động','Chu kỳ chuyển đổi tiền','Số ngày tồn kho + Số ngày phải thu − Số ngày phải trả',['previous_inventory','inventory','cost_of_goods_sold','previous_receivables','receivables','revenue','previous_payables','payables','days'],'ngày',(a,b,c,d,e,f,g,h,i)=>{ const inventory=ratio(avg(a,b)*i,c); const receivable=ratio(avg(d,e)*i,f); const payable=ratio(avg(g,h)*i,c); return inventory === null || receivable === null || payable === null ? null : inventory + receivable - payable },'Dùng doanh thu thuần và giá vốn làm xấp xỉ.'),
  m('cfo_margin','Dòng tiền','Biên dòng tiền hoạt động','Dòng tiền hoạt động / Doanh thu × 100',['operating_cash_flow','revenue'],'%',(a,b)=>ratio(a,b,100)),
  m('cash_conversion','Dòng tiền','Dòng tiền HĐ / Lợi nhuận ròng','Dòng tiền hoạt động / Lợi nhuận ròng',['operating_cash_flow','net_income'],'lần',ratio),
  m('fcf','Dòng tiền','Dòng tiền tự do','Dòng tiền hoạt động − Chi đầu tư tài sản cố định',['operating_cash_flow','capex'],'money',(a,b)=>a-b),
  m('cfo_current','Dòng tiền','Dòng tiền HĐ / Nợ ngắn hạn','Dòng tiền hoạt động / Nợ ngắn hạn',['operating_cash_flow','current_liabilities'],'lần',ratio),
  m('revenue_growth','Tăng trưởng','Tăng trưởng doanh thu','(Doanh thu − Doanh thu kỳ so sánh) / |Doanh thu kỳ so sánh| × 100',['revenue','previous_revenue'],'%',(a,b)=>ratio(a-b,Math.abs(b),100),'Kỳ so sánh: năm trước hoặc cùng quý năm trước.'),
  m('profit_growth','Tăng trưởng','Tăng trưởng lợi nhuận ròng','(Lợi nhuận ròng − Lợi nhuận kỳ so sánh) / |Lợi nhuận kỳ so sánh| × 100',['net_income','previous_net_income'],'%',(a,b)=>ratio(a-b,Math.abs(b),100),'Kết quả qua điểm hòa vốn cần diễn giải thận trọng.'),
  m('pe','Định giá thị trường','P/E','Giá cổ phiếu / EPS cơ bản',['price','eps'],'lần',ratio,'EPS phải tương ứng kỳ định giá, thường là 12 tháng gần nhất.'),
  m('pb','Định giá thị trường','P/B','Giá cổ phiếu / Giá trị sổ sách mỗi cổ phiếu',['price','book_value_per_share'],'lần',ratio),
  m('dividend_yield','Định giá thị trường','Tỷ suất cổ tức','Cổ tức/cổ phiếu / Giá cổ phiếu × 100',['dividend_per_share','price'],'%',(a,b)=>ratio(a,b,100),'Cần đối chiếu ngày giá và kỳ cổ tức.'),
]
export function calculateMetric(metric, values) {
  const numbers = metric.deps.map((key) => values[key] === '' || values[key] == null ? null : Number(values[key]))
  if (numbers.some((value) => value === null || !Number.isFinite(value))) return null
  if (metric.deps.includes('days') && numbers[metric.deps.indexOf('days')] <= 0) return null
  const result = metric.calc(...numbers)
  return result === null || !Number.isFinite(result) ? null : result
}
