import { FIELDS } from './financialMetrics'
import { ROW_KEY_ALIASES } from './statementMapper'

export function periodKey(value) {
  const text = String(value || '').toUpperCase().replace(/\s+/g, '')
  const first = text.match(/^Q([1-4])[-/]?(\d{4})$/)
  const second = text.match(/^(\d{4})[-/]?Q([1-4])$/)
  if (first) return `${first[2]}-Q${first[1]}`
  if (second) return `${second[1]}-Q${second[2]}`
  return text.replace(/^FY/, '').replace(/(?:FY|A)$/, '')
}
function priorPeriod(period, comparable = false) {
  const key = periodKey(period)
  const quarter = key.match(/^(\d{4})-Q([1-4])$/)
  if (quarter) {
    const year = Number(quarter[1]); const q = Number(quarter[2])
    return comparable ? `${year - 1}-Q${q}` : q === 1 ? `${year - 1}-Q4` : `${year}-Q${q - 1}`
  }
  return /^\d{4}$/.test(key) ? String(Number(key) - 1) : ''
}
const LABELS = {
  pretax_profit: ['lãi/(lỗ) trước thuế', 'lợi nhuận trước thuế', 'profit before tax'],
  interest_expense: ['chi phí lãi vay', 'interest expense'],
  tax_expense: ['chi phí thuế thu nhập doanh nghiệp', 'chi phí thuế thu nhập doanh nghiệp hiện hành và hoãn lại', 'income tax expense'],
  payables: ['phải trả người bán', 'trade accounts payable', 'accounts payable'],
  operating_cash_flow: ['lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh', 'lưu chuyển tiền thuần từ hoạt động kinh doanh', 'operating cash flow'],
  capex: ['tiền chi để mua sắm, xây dựng tscđ và các tài sản dài hạn khác', 'purchases of fixed assets', 'capital expenditure'],
  short_term_debt: ['vay ngắn hạn', 'vay và nợ thuê tài chính ngắn hạn', 'short-term borrowings'],
  long_term_debt: ['vay dài hạn', 'vay và nợ thuê tài chính dài hạn', 'long-term borrowings'],
}
function normalizeLabel(value) { return String(value || '').trim().toLocaleLowerCase('vi').replace(/\s+/g, ' ') }
function reportValue(workspace, section, key, period) {
  const rows = workspace?.statements?.[section]?.rows || []
  // Raw cash-flow identifiers vary by provider: validate labels instead of guessing from codes.
  const aliases = section === 'cash_flow' ? [key] : key === 'payables' ? ['payables', 'accounts_payable'] : [key, ...(ROW_KEY_ALIASES[key] || [])]
  const exactLabels = LABELS[key] || []
  const candidates = [...new Set(aliases)].flatMap((alias) => rows.filter((row) => row.key === alias))
  rows.forEach((row) => { if (exactLabels.includes(normalizeLabel(row.label)) || exactLabels.includes(normalizeLabel(row.label_en))) candidates.push(row) })
  for (const row of candidates) {
    const raw = row.values?.find((item) => periodKey(item.period) === period)?.value
    if (raw !== null && raw !== undefined && raw !== '' && Number.isFinite(Number(raw))) return Number(raw)
  }
  // A normalized trend may fill a period absent from a partial statement row.
  if (section === 'income' && ['revenue', 'gross_profit', 'operating_profit', 'net_income'].includes(key)) {
    const raw = workspace?.trend?.series?.find((item) => item.key === key)?.values?.find((item) => periodKey(item.period) === period)?.value
    if (raw !== null && raw !== undefined && raw !== '' && Number.isFinite(Number(raw))) return Number(raw)
  }
  return null
}
export function readCalculatorReport(workspace, period, divisor) {
  const values = {}; const sources = {}
  const normalized = periodKey(period)
  const quarter = normalized.match(/^(\d{4})-Q([1-4])$/)
  const year = Number(quarter?.[1] || normalized)
  if (Number.isInteger(year) && year >= 1900 && year <= 9999) {
    const startMonth = quarter ? (Number(quarter[2]) - 1) * 3 : 0
    const endMonth = quarter ? startMonth + 3 : 12
    values.days = String((Date.UTC(year, endMonth, 1) - Date.UTC(year, startMonth, 1)) / 86400000)
    sources.days = 'Tính theo lịch dương; có thể sửa'
  }
  FIELDS.forEach(([key, , section]) => {
    if (['manual', 'market', 'calendar'].includes(section)) return
    const previous = section.startsWith('previous_')
    const statement = previous ? section.slice(9) : section
    const field = previous ? key.slice(9) : key
    const wanted = previous ? priorPeriod(period, statement === 'income') : normalized
    const raw = reportValue(workspace, statement, field, wanted)
    if (raw !== null) {
      const value = raw / divisor
      values[key] = String(['cost_of_goods_sold', 'capex', 'interest_expense', 'tax_expense'].includes(field) ? Math.abs(value) : value)
      sources[key] = `Báo cáo kỳ ${wanted}`
    }
  })
  const short = reportValue(workspace, 'balance', 'short_term_debt', normalized)
  const long = reportValue(workspace, 'balance', 'long_term_debt', normalized)
  if (short !== null && long !== null) {
    values.debt = String((short + long) / divisor)
    sources.debt = `Vay ngắn hạn + dài hạn, kỳ ${normalized}`
  }
  return { values, sources }
}
