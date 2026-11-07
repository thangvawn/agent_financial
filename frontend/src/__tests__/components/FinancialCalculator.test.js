import { describe, it, after } from 'node:test'
import assert from 'node:assert/strict'
import { closeViteServer, getViteServer, React, renderToString } from '../test-helpers.js'

describe('BCTC financial calculator', () => {
  after(closeViteServer)
  it('shows formulas and a period selector without inventing missing results', async () => {
    const module = await (await getViteServer()).ssrLoadModule('./src/features/bctc/pages/FinancialCalculator.jsx')
    const html = renderToString(React.createElement(module.default, { workspace: { statements: { income: { periods: ['2025', '2024'] } } }, unit: 'billion' }))
    assert.match(html, /2025/)
    assert.match(html, /Lợi nhuận gộp \/ Doanh thu × 100/)
    assert.match(html, /Chưa có số/)
    assert.match(html, /Tự điền từ báo cáo/)
    assert.match(html, /Định giá thị trường/)
    assert.match(html, /Thanh khoản/)
    assert.match(html, /P\/E/)
    assert.match(html, /Công thức chỉ số đang chọn/)
    assert.match(html, /—/)
  })
  it('calculates zero and negative values but refuses missing or zero denominators', async () => {
    const { calculateRatio } = await import('../../features/bctc/utils/calculateRatio.js')
    assert.equal(calculateRatio('20', '100', 100), 20)
    assert.equal(calculateRatio('0', '100', 100), 0)
    assert.equal(calculateRatio('-20', '100', 100), -20)
    assert.equal(calculateRatio('', '100'), null)
    assert.equal(calculateRatio('20', '0'), null)
  })
  it('uses average balances and keeps missing or zero-denominator metrics unavailable', async () => {
    const { METRICS, calculateMetric } = await import('../../features/bctc/utils/financialMetrics.js')
    const get = (id) => METRICS.find((metric) => metric.id === id)
    assert.equal(calculateMetric(get('roe'), { net_income: '20', previous_equity: '80', equity: '120' }), 20)
    assert.equal(calculateMetric(get('roe'), { net_income: '20', equity: '120' }), null)
    assert.equal(calculateMetric(get('quick_ratio'), { current_assets: '100', inventory: '20', current_liabilities: '40' }), 2)
    assert.equal(calculateMetric(get('current_ratio'), { current_assets: '100', current_liabilities: '0' }), null)
    assert.equal(calculateMetric(get('revenue_growth'), { revenue: '80', previous_revenue: '100' }), -20)
    assert.equal(calculateMetric(get('pe'), { price: '25000' }), null)
    assert.equal(calculateMetric(get('fcf'), { operating_cash_flow: '40', capex: '60' }), -20)
  })

  it('fills and charts available periods while leaving a missing period blank', async () => {
    const Calculator = (await (await getViteServer()).ssrLoadModule('./src/features/bctc/pages/FinancialCalculator.jsx')).default
    const workspace = { statements: { income: { periods: ['2025', '2024', '2023'], rows: [
      { key: 'revenue', values: [{ period: '2025', value: 100e9 }, { period: '2024', value: 100e9 }, { period: '2023', value: 100e9 }] },
      { key: 'gross_profit', values: [{ period: '2025', value: 40e9 }, { period: '2024', value: 30e9 }] },
    ] } } }
    const html = renderToString(React.createElement(Calculator, { workspace, unit: 'billion' }))
    assert.match(html, /value="100"/)
    assert.match(html, /value="40"/)
    assert.match(html, /2025: 40 %/)
    assert.match(html, /2024: 30 %/)
    assert.match(html, /2023: —/)
  })

  it('fills each period from available report rows without mistaking loan receipts for capex', async () => {
    const { readCalculatorReport } = await (await getViteServer()).ssrLoadModule('./src/features/bctc/utils/calculatorReport.js')
    const workspace = { statements: {
      income: { rows: [
        { key: 'revenue', values: [{ period: '2025-Q1', value: null }] },
        { key: 'isa3', values: [{ period: '2025-Q1', value: 100e9 }] },
        { key: 'isa16', label: 'Lãi/(lỗ) trước thuế', values: [{ period: '2025-Q1', value: 20e9 }] },
        { key: 'isa8', label: 'Chi phí lãi vay', values: [{ period: '2025-Q1', value: -5e9 }] },
      ] },
      balance: { rows: [
        { key: 'accounts_payable', values: [{ period: '2025-Q1', value: 20e9 }, { period: '2024-Q4', value: 10e9 }] },
        { key: 'bsa56', label: 'Vay ngắn hạn', values: [{ period: '2025-Q1', value: 3e9 }] },
        { key: 'bsa71', label: 'Vay dài hạn', values: [{ period: '2025-Q1', value: 2e9 }] },
      ] },
      cash_flow: { rows: [{ key: 'cfa22', label: 'Tiền thu hồi cho vay', values: [{ period: '2025-Q1', value: 999e9 }] }, { key: 'cfa20', label: 'Tiền thu thanh lý tài sản', values: [{ period: '2025-Q1', value: 777e9 }] }] },
    } }
    const { values, sources } = readCalculatorReport(workspace, '2025-Q1', 1e9)
    assert.equal(values.revenue, '100')
    assert.equal(values.pretax_profit, '20')
    assert.equal(values.interest_expense, '5')
    assert.equal(values.payables, '20')
    assert.equal(values.previous_payables, '10')
    assert.equal(values.debt, '5')
    assert.equal(values.capex, undefined)
    assert.equal(values.operating_cash_flow, undefined)
    assert.match(sources.previous_payables, /2024-Q4/)
    workspace.statements.balance.rows.pop()
    assert.equal(readCalculatorReport(workspace, '2025-Q1', 1e9).values.debt, undefined)
  })

  it('offers a closed formula dialog with categorized metrics', async () => {
    const Reference = (await (await getViteServer()).ssrLoadModule('./src/features/bctc/pages/FormulaReference.jsx')).default
    const html = renderToString(React.createElement(Reference, { onSelectMetric: () => {} }))
    assert.match(html, /<dialog[^>]*aria-labelledby="bcl-reference-title"/)
    assert.doesNotMatch(html, /<dialog[^>]*\sopen(?:=|\s|>)/)
    assert.match(html, /Thanh khoản/)
    assert.match(html, /Phân tích DuPont/)
    assert.match(html, /Biên lợi nhuận gộp/)
    assert.match(html, /Mở trong bộ tính/)
  })
  it('plots margin ratios from the API and computes missing periods from reported data', async () => {
    const { marginChartData } = await (await getViteServer()).ssrLoadModule('./src/features/bctc/utils/marginChartData.js')
    const workspace = { trend: { periods: ['2024', '2025'], series: [{ key: 'revenue', values: [{ period: '2025', value: 100 }] }, { key: 'net_income', values: [{ period: '2025', value: 20 }] }] }, ratio_groups: [{ metrics: [{ key: 'gross_margin_pct', series: [{ period: '2024', value: 30 }, { period: '2025', value: 40 }] }] }] }
    const { lines } = marginChartData(workspace)
    assert.deepEqual(lines[0].values, [30, 40])
    assert.deepEqual(lines[1].values, [null, null])
    assert.deepEqual(lines[2].values, [null, 20])
  })

  it('renders the margin chart with gaps and single data points', async () => {
    const Chart = (await (await getViteServer()).ssrLoadModule('./src/features/bctc/pages/MiniMarginChart.jsx')).default
    const workspace = { trend: { periods: ['2023', '2024', '2025', '2026'] }, ratio_groups: [{ metrics: [{ key: 'gross_margin_pct', series: [
      { period: '2023', value: 20 }, { period: '2024', value: 30 }, { period: '2026', value: 40 },
    ] }] }] }
    const html = renderToString(React.createElement(Chart, { workspace }))
    assert.match(html, /<polyline[^>]*points="[\d.]+,[\d.]+ [\d.]+,[\d.]+"/)
    assert.equal((html.match(/<circle/g) || []).length, 3)
    assert.match(html, /2025/)
    assert.match(html, /Xem số liệu/)
  })

  it('compares only matching periods and preserves missing or zero-base values', async () => {
    const { comparablePeriods, compareReading } = await (await getViteServer()).ssrLoadModule('./src/features/bctc/utils/readingHistory.js')
    assert.deepEqual(comparablePeriods('2025-Q1'), { previous: '2024-Q4', yearAgo: '2024-Q1' })
    assert.deepEqual(compareReading(120, 100), { difference: 20, relative: 20 })
    assert.deepEqual(compareReading(10, 0), { difference: 10, relative: null })
    assert.equal(compareReading(null, 10), null)
  })
  it('renders selected value, same-quarter comparison, and unavailable history honestly', async () => {
    const Panel = (await (await getViteServer()).ssrLoadModule('./src/features/bctc/pages/ReadingPanel.jsx')).default
    const selected = { label: 'Revenue', period: '2025-Q1', value: 120e9, unit: 'VND', tableTab: 'income', tableMode: 'actual', periodMode: 'quarter', loadNonce: 0, series: [{ period: '2025-Q1', value: 120e9 }, { period: '2024-Q4', value: 100e9 }, { period: '2024-Q1', value: null }] }
    const html = renderToString(React.createElement(Panel, { workspace: { company: { ticker: 'FPT' } }, selected, activeTab: 'income', mode: 'actual', periodMode: 'quarter', loadNonce: 0, unit: 'billion', rightTab: 'assistant', notes: '' }))
    assert.match(html, /120 tỷ VND/)
    assert.match(html, /\+20 tỷ VND/)
    assert.match(html, /2024-Q1/)
    assert.match(html, /Không đủ số liệu/)
    assert.match(html, /Lịch sử chỉ tiêu/)
  })

})
