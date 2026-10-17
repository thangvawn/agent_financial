import { useEffect, useRef, useState } from 'react'
import {
  BarChart3, BookOpen, Calculator, Check, CheckCircle2, ChevronDown, ChevronLeft,
  ChevronRight, ClipboardList, CloudUpload, FileSpreadsheet, FileText, FlaskConical,
  HelpCircle, LineChart, MoreHorizontal, PanelRight, Save, Search, Share2,
  SlidersHorizontal, Sparkles, Table2, X,
} from 'lucide-react'

import RatioPracticeLab from './RatioPracticeLab'
import BctcAnalysisWorkspace from './BctcAnalysisWorkspace'
import { useFinancialWorkflow } from '../../../shared/context/FinancialWorkflowContext'
import {
  fetchCompanyFinancialWorkspace,
  fetchFinancialWorkbookModel,
  runFinancialScenario,
  saveFinancialWorkbookModel,
  uploadFinancialStatement,
} from '../services/financialsApi'
import { findRowWithAliases } from '../utils/statementMapper'
import './bctc-lab.css'

const WORKBOOK_TABS = [
  ['income', 'Income Statement'],
  ['balance', 'Balance Sheet'],
  ['cash_flow', 'Cash Flow'],
  ['ratios', 'Ratios'],
  ['model', 'My Model'],
  ['notes', 'Notes'],
]

const DATA_ROWS = {
  income: [
    ['revenue', 'Revenue', 'VND', true],
    ['cost_of_goods_sold', 'Cost of Revenue', 'VND', false],
    ['gross_profit', 'Gross Profit', 'VND', true],
    ['operating_profit', 'Operating Income', 'VND', true],
    ['net_income', 'Net Income', 'VND', true],
    ['gross_margin_pct', 'Gross Margin', '%', false],
    ['operating_margin_pct', 'Operating Margin', '%', false],
    ['net_margin_pct', 'Net Margin', '%', true],
  ],
  balance: [
    ['cash', 'Cash & Equivalents', 'VND', false],
    ['receivables', 'Receivables', 'VND', false],
    ['inventory', 'Inventory', 'VND', false],
    ['current_assets', 'Current Assets', 'VND', true],
    ['total_assets', 'Total Assets', 'VND', true],
    ['current_liabilities', 'Current Liabilities', 'VND', false],
    ['total_liabilities', 'Total Liabilities', 'VND', true],
    ['equity', 'Shareholders’ Equity', 'VND', true],
    ['debt', 'Debt', 'VND', false],
  ],
  cash_flow: [
    ['operating_cash_flow', 'Operating Cash Flow', 'VND', true],
    ['investing_cash_flow', 'Investing Cash Flow', 'VND', false],
    ['financing_cash_flow', 'Financing Cash Flow', 'VND', false],
    ['capex', 'Capital Expenditure', 'VND', false],
    ['free_cash_flow', 'Free Cash Flow', 'VND', true],
    ['cash_conversion_pct', 'Cash Conversion', '%', true],
  ],
}

const FORMULAS = {
  cost_of_goods_sold: 'Revenue − Gross Profit',
  gross_margin_pct: 'Gross Profit / Revenue × 100',
  operating_margin_pct: 'Operating Income / Revenue × 100',
  net_margin_pct: 'Net Income / Revenue × 100',
  free_cash_flow: 'Operating Cash Flow − |Capital Expenditure|',
  cash_conversion_pct: 'Operating Cash Flow / Net Income × 100',
  current_ratio: 'Current Assets / Current Liabilities',
  quick_ratio: '(Current Assets − Inventory) / Current Liabilities',
  debt_to_equity: 'Debt / Shareholders’ Equity',
  roe_pct: 'Net Income / Shareholders’ Equity × 100',
  roa_pct: 'Net Income / Total Assets × 100',
}

const RATIO_ROWS = [
  ['gross_margin_pct', 'Gross Margin', '%', true],
  ['operating_margin_pct', 'Operating Margin', '%', false],
  ['net_margin_pct', 'Net Margin', '%', true],
  ['roe_pct', 'ROE', '%', false],
  ['roa_pct', 'ROA', '%', false],
  ['current_ratio', 'Current Ratio', 'x', false],
  ['quick_ratio', 'Quick Ratio', 'x', false],
  ['debt_to_equity', 'Debt / Equity', 'x', false],
  ['ocf_to_net_income', 'CFO / Net Income', 'x', false],
]

function latestPeriod(workspace) {
  return workspace?.company?.latest_period || workspace?.statements?.income?.periods?.[0] || ''
}

function displayPeriods(statement, workspace) {
  const statementPeriods = statement?.periods || []
  if (statementPeriods.length) return [...statementPeriods].reverse()
  return [...(workspace?.trend?.periods || [])]
}

function numeric(value) {
  if (value === null || value === undefined || (typeof value === 'string' && value.trim() === '')) return null
  const number = Number(value)
  return !Number.isFinite(number) ? null : number
}

/** Normalize provider period spellings before joining report and trend rows. */
function periodKey(value) {
  const text = String(value ?? '').trim().toUpperCase().replace(/\s+/g, '')
  const quarterFirst = text.match(/^Q([1-4])[-/]?(\d{4})$/)
  if (quarterFirst) return `${quarterFirst[2]}-Q${quarterFirst[1]}`
  const yearFirst = text.match(/^(\d{4})[-/]?Q([1-4])$/)
  if (yearFirst) return `${yearFirst[1]}-Q${yearFirst[2]}`
  const annual = text.match(/^(?:FY)?(\d{4})(?:FY|A)?$/)
  return annual ? annual[1] : text
}

function mergedPeriodValues(...sources) {
  const values = new Map()
  // Keep the first finite value for a period. Sources are ordered from the
  // normalized trend/ratio fallback to the provider's reported row, so a
  // reported value wins without allowing nulls to erase a valid fallback.
  for (const source of sources) {
    for (const item of source || []) {
      const key = periodKey(item?.period)
      const value = numeric(item?.value)
      if (key && value !== null) values.set(key, value)
    }
  }
  return values
}

function localWorkbookSessionId() {
  if (typeof window === 'undefined') return 'server-rendered'
  try {
    const storageKey = 'northstar:bctc:session'
    const stored = window.localStorage.getItem(storageKey)
    if (stored) return stored
    const generated = typeof window.crypto?.randomUUID === 'function'
      ? window.crypto.randomUUID()
      : `local-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
    window.localStorage.setItem(storageKey, generated)
    return generated
  } catch {
    return 'local-fallback'
  }
}

function formatNumber(value, unit, metricUnit) {
  const number = numeric(value)
  if (number === null) return '—'
  if (metricUnit === '%') return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(number)}%`
  if (metricUnit === 'x') return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(number)}x`
  const divisor = unit === 'million' ? 1e6 : unit === 'raw' ? 1 : 1e9
  return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: unit === 'raw' ? 0 : 1 }).format(number / divisor)
}

function sourceMap(statement) {
  return new Map((statement?.rows || []).map((row) => [row.key, row]))
}

function ratioMap(workspace) {
  return new Map((workspace?.ratio_groups || []).flatMap((group) => (group.metrics || []).map((metric) => [metric.key, metric])))
}

function linePoints(values, width = 380, height = 120) {
  const finite = values.filter((value) => Number.isFinite(value))
  if (!finite.length) return ''
  const min = Math.min(...finite)
  const max = Math.max(...finite)
  const span = max - min || 1
  return values.map((value, index) => {
    const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width
    const y = height - ((value - min) / span) * (height - 16) - 8
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

function MiniBarChart({ workspace }) {
  const periods = [...(workspace?.trend?.periods || [])]
  const series = new Map((workspace?.trend?.series || []).map((item) => [item.key, item]))
  const revenue = periods.map((period) => numeric(series.get('revenue')?.values?.find((item) => item.period === period)?.value) || 0)
  const netIncome = periods.map((period) => numeric(series.get('net_income')?.values?.find((item) => item.period === period)?.value) || 0)
  const max = Math.max(...revenue, ...netIncome, 1)
  return <div className="bcl-bar-chart" role="img" aria-label="Doanh thu và lợi nhuận ròng theo kỳ">
    <div className="bcl-chart-gridlines"><i /><i /><i /><i /></div>
    <div className="bcl-bars">{periods.map((period, index) => <div className="bcl-bar-group" key={period}>
      <div className="bcl-bar-pair"><i className="is-revenue" style={{ height: `${Math.max(3, revenue[index] / max * 100)}%` }} /><i className="is-income" style={{ height: `${Math.max(3, netIncome[index] / max * 100)}%` }} /></div>
      <span>{String(period).replace(/.*?(\d{4})/, '$1')}</span>
    </div>)}</div>
  </div>
}

function MiniMarginChart({ workspace }) {
  const periods = [...(workspace?.trend?.periods || [])]
  const series = new Map((workspace?.trend?.series || []).map((item) => [item.key, item]))
  const metricValues = (key) => periods.map((period) => numeric(series.get(key)?.values?.find((item) => item.period === period)?.value)).filter((item) => item !== null)
  const gross = metricValues('gross_margin_pct')
  const operating = metricValues('operating_margin_pct')
  const net = metricValues('net_margin_pct')
  return <div className="bcl-line-chart" role="img" aria-label="Biên lợi nhuận theo kỳ">
    <svg viewBox="0 0 380 140" preserveAspectRatio="none"><path className="is-gross" d={`M ${linePoints(gross, 380, 120)}`} /><path className="is-operating" d={`M ${linePoints(operating, 380, 120)}`} /><path className="is-net" d={`M ${linePoints(net, 380, 120)}`} /></svg>
    <div className="bcl-line-labels">{periods.map((period) => <span key={period}>{String(period).replace(/.*?(\d{4})/, '$1')}</span>)}</div>
  </div>
}

function WorkbookTable({ workspace, tab, unit, selectedCell, onSelectCell, notes, onNotesChange, mode, scenarioResult }) {
  if (tab === 'notes') return <div className="bcl-notes-workspace"><div><span className="bcl-eyebrow">WORKING NOTES</span><h2>Ghi chú cho phiên học</h2><p>Ghi lại bằng chứng từ raw data, công thức và giới hạn của kết luận.</p></div><textarea aria-label="Ghi chú BCTC" value={notes} onChange={(event) => onNotesChange(event.target.value)} placeholder="Ví dụ: Biên lợi nhuận giảm vì giá vốn tăng nhanh hơn doanh thu…" rows={14} /><small>Ghi chú sẽ đi cùng phiên workbook khi bạn bấm Lưu.</small></div>
  const sourceTab = tab === 'model' || tab === 'ratios' ? 'income' : tab
  const statement = workspace?.statements?.[sourceTab]
  const periods = displayPeriods(statement, workspace)
  const baseRows = tab === 'ratios' ? RATIO_ROWS : DATA_ROWS[sourceTab] || DATA_ROWS.income
  const knownKeys = new Set(baseRows.map(([key]) => key))
  const rawRows = tab === 'ratios' || tab === 'model' ? [] : (statement?.rows || [])
    .filter((row) => row?.key && !knownKeys.has(row.key))
    .map((row) => [row.key, row.label || row.label_en || row.key, 'VND', Boolean(row.emphasis)])
  const rowSpecs = [...baseRows, ...rawRows]
  const statementRows = sourceMap(statement)
  const ratios = ratioMap(workspace)
  const trendRows = new Map((workspace?.trend?.series || []).map((series) => [series.key, series]))
  if (!periods.length) return <div className="bcl-empty"><FileSpreadsheet size={22} /><strong>Chưa có kỳ báo cáo</strong><span>Hãy tải dữ liệu hoặc chọn một doanh nghiệp khác.</span></div>
  // A fixed-layout table can otherwise squeeze twenty quarters into narrow
  // cells. Set the real content width so the horizontal scrollbar preserves
  // readable spacing instead of letting values overlap.
  const tableWidth = `${245 + periods.length * 124}px`
  return <div className="bcl-table-scroll"><table className="bcl-table tabular-nums" style={{ width: tableWidth, minWidth: tableWidth }}><caption className="bcl-sr-only">Bảng {tab}</caption><thead><tr><th scope="col"><span className="bcl-col-letter">A</span>Chỉ tiêu</th>{periods.map((period, index) => <th scope="col" key={period}><span className="bcl-col-letter">{String.fromCharCode(66 + index)}</span>{period}</th>)}</tr></thead><tbody>
    {rowSpecs.map(([key, label, metricUnit, emphasis]) => {
      const row = findRowWithAliases(statementRows, key)
      const ratio = ratios.get(key)
      const trend = trendRows.get(key)
      const rowValues = (row?.values || []).map((item) => ({
        ...item,
        value: key === 'cost_of_goods_sold' && numeric(item?.value) !== null ? Math.abs(numeric(item.value)) : item?.value,
      }))
      // A provider may return a canonical row with only one populated period
      // while the normalized trend/ratio series contains the complete history.
      // Merge by period instead of letting that partial row hide the other
      // reported values. Later sources are preferred when they contain a
      // finite value for the same period.
      const values = mergedPeriodValues(trend?.values, ratio?.series, rowValues)
      if (key === 'cost_of_goods_sold') {
        const revenueValues = mergedPeriodValues(trendRows.get('revenue')?.values, findRowWithAliases(statementRows, 'revenue')?.values)
        const grossValues = mergedPeriodValues(trendRows.get('gross_profit')?.values, findRowWithAliases(statementRows, 'gross_profit')?.values)
        periods.forEach((period) => {
          const canonicalPeriod = periodKey(period)
          if (values.get(canonicalPeriod) === undefined || values.get(canonicalPeriod) === null) {
            const revenue = numeric(revenueValues.get(canonicalPeriod))
            const gross = numeric(grossValues.get(canonicalPeriod))
            if (revenue !== null && gross !== null) values.set(canonicalPeriod, Math.abs(revenue - gross))
          }
        })
      }
      if (['gross_margin_pct', 'operating_margin_pct', 'net_margin_pct'].includes(key)) {
        periods.forEach((period) => {
          const canonicalPeriod = periodKey(period)
          if (values.get(canonicalPeriod) === undefined || values.get(canonicalPeriod) === null) {
            const revenueValues = mergedPeriodValues(trendRows.get('revenue')?.values, findRowWithAliases(statementRows, 'revenue')?.values)
            const targetKey = key === 'gross_margin_pct' ? 'gross_profit' : key === 'operating_margin_pct' ? 'operating_profit' : 'net_income'
            const targetValues = mergedPeriodValues(trendRows.get(targetKey)?.values, findRowWithAliases(statementRows, targetKey)?.values)
            const rev = numeric(revenueValues.get(canonicalPeriod))
            const tgt = numeric(targetValues.get(canonicalPeriod))
            if (rev && tgt !== null) {
              values.set(canonicalPeriod, (tgt / rev) * 100)
            }
          }
        })
      }
      const projection = scenarioResult?.scenario
      const projectionPeriod = scenarioResult?.base?.period
      if (mode !== 'actual' && sourceTab === 'income' && projection && projectionPeriod) {
        const projectedValues = {
          revenue: projection.revenue,
          cost_of_goods_sold: numeric(projection.revenue) !== null && numeric(projection.gross_profit) !== null
            ? projection.revenue - projection.gross_profit
            : null,
          gross_profit: projection.gross_profit,
          operating_profit: projection.operating_profit,
          net_income: projection.net_income,
          gross_margin_pct: projection.gross_margin_pct,
          operating_margin_pct: numeric(projection.operating_profit) !== null && numeric(projection.revenue) !== null && numeric(projection.revenue) !== 0
            ? projection.operating_profit / projection.revenue * 100
            : null,
          net_margin_pct: projection.net_margin_pct,
        }
        if (Object.prototype.hasOwnProperty.call(projectedValues, key)) values.set(periodKey(projectionPeriod), projectedValues[key])
      }
      return <tr key={key} className={emphasis ? 'is-emphasis' : ''}>
        <th scope="row"><span>{label}</span><small>{metricUnit === '%' ? 'Calculated' : row || trend ? 'Reported' : ratio ? 'Calculated' : 'Derived'}</small></th>
        {periods.map((period) => {
          const cellKey = `${key}:${period}`
          const selected = selectedCell === cellKey
          const value = values.get(periodKey(period))
          return <td key={period} className={selected ? 'is-selected' : ''}><button type="button" onClick={() => onSelectCell(cellKey, key, period, value, metricUnit)} aria-label={`${label} ${period}`} title={value === null ? 'Không có dữ liệu từ nguồn cho kỳ này; dấu — không có nghĩa là 0.' : undefined}>{formatNumber(value, unit, metricUnit)}</button></td>
        })}
      </tr>
    })}
  </tbody></table></div>
}

function TutorPanel({ workspace, selected, formula, onFormulaChange, rightTab, setRightTab, notes, onNotesChange }) {
  const ratio = ratioMap(workspace).get(selected?.key)
  const value = selected?.value
  const expected = FORMULAS[selected?.key] || ratio?.formula || 'Khoản mục được lấy trực tiếp từ dữ liệu báo cáo.'
  const normalizedFormula = formula.toLowerCase().replace(/\s+/g, '')
  const formulaValid = selected?.key === 'net_margin_pct'
    ? normalizedFormula.includes('net_income') && normalizedFormula.includes('revenue')
    : selected?.key === 'gross_margin_pct'
      ? normalizedFormula.includes('gross_profit') && normalizedFormula.includes('revenue')
      : formula.trim().length > 2
  return <aside className="bcl-tutor">
    <div className="bcl-right-tabs" role="tablist" aria-label="BCTC Lab assistant"><button className={rightTab === 'assistant' ? 'is-active' : ''} onClick={() => setRightTab('assistant')} type="button"><PanelRight size={14} /> Trợ lý phân tích</button><button className={rightTab === 'chart' ? 'is-active' : ''} onClick={() => setRightTab('chart')} type="button"><BarChart3 size={14} /> Biểu đồ</button><button className={rightTab === 'notes' ? 'is-active' : ''} onClick={() => setRightTab('notes')} type="button"><FileText size={14} /> Ghi chú</button><button className={rightTab === 'lesson' ? 'is-active' : ''} onClick={() => setRightTab('lesson')} type="button"><BookOpen size={14} /> Bài học</button></div>
    {rightTab === 'assistant' && <div className="bcl-tutor-body"><div className="bcl-tutor-heading"><div><span className="bcl-eyebrow">CÂU HỎI TRUNG TÂM</span><h2>{selected?.label || 'Chọn một ô để bắt đầu'}</h2></div><HelpCircle size={19} /></div><p className="bcl-tutor-intro">Đọc dữ liệu gốc, kiểm tra công thức và tự giải thích ý nghĩa của chỉ tiêu trước khi đưa ra kết luận.</p><section className="bcl-formula-card"><strong>Công thức chuẩn</strong><code>{expected}</code><small>Registry · version 1.0</small></section><section className="bcl-formula-check"><div className="bcl-check-title"><strong>Công thức của bạn</strong><span className={formulaValid ? 'is-valid' : 'is-invalid'}>{formulaValid ? <><CheckCircle2 size={14} /> Hợp lệ</> : 'Cần kiểm tra'}</span></div><div className="bcl-formula-input"><input aria-label="Công thức của bạn" value={formula} onChange={(event) => onFormulaChange(event.target.value)} /><span>fx</span></div><div className={formulaValid ? 'bcl-result is-valid' : 'bcl-result is-invalid'}>{formulaValid ? <CheckCircle2 size={17} /> : <HelpCircle size={17} />}<div><strong>{formulaValid ? 'Công thức hợp lệ' : 'Công thức chưa đủ đầu vào'}</strong><span>Kết quả: {formatNumber(value, 'billion', selected?.unit)} {selected?.period ? `(${selected.period})` : ''}</span></div></div></section><section className="bcl-suggestion"><Sparkles size={16} /><div><strong>Gợi ý học tập</strong><p>Hãy so sánh {selected?.label || 'chỉ tiêu này'} với kỳ trước và kiểm tra khoản mục gốc trước khi kết luận.</p><button type="button" onClick={() => setRightTab('lesson')}>Mở bài học <ChevronRight size={14} /></button></div></section><section className="bcl-related"><strong>Các chỉ số liên quan</strong>{['gross_margin_pct', 'operating_margin_pct', 'roe_pct', 'ocf_to_net_income'].map((key) => { const item = ratioMap(workspace).get(key); return <div key={key}><span>{item?.label || key}</span><b>{formatNumber(item?.value, 'billion', item?.unit)}</b></div> })}</section></div>}
    {rightTab === 'chart' && <div className="bcl-side-content"><span className="bcl-eyebrow">READ THE TREND</span><h2>Đọc xu hướng trước khi tính</h2><p>Đường xu hướng chỉ là điểm bắt đầu. Hãy mở raw input và kiểm tra kỳ so sánh.</p><MiniMarginChart workspace={workspace} /></div>}
    {rightTab === 'notes' && <div className="bcl-side-content"><span className="bcl-eyebrow">WORKING NOTES</span><h2>Ghi chú phiên học</h2><textarea aria-label="Ghi chú phiên học" value={notes} onChange={(event) => onNotesChange(event.target.value)} placeholder="Viết quan sát, bằng chứng và giới hạn của kết luận…" rows={12} /></div>}
    {rightTab === 'lesson' && <div className="bcl-side-content"><span className="bcl-eyebrow">LEARN BY DOING</span><h2>Biên lợi nhuận ròng</h2><p>Net Margin cho biết cứ 1 đồng doanh thu tạo ra bao nhiêu đồng lợi nhuận sau thuế.</p><div className="bcl-lesson-step"><b>01</b><span>Đọc LNST và doanh thu trên bảng gốc.</span></div><div className="bcl-lesson-step"><b>02</b><span>Chia LNST cho doanh thu, không tự bù số thiếu.</span></div><div className="bcl-lesson-step"><b>03</b><span>Đối chiếu với biên gộp, biên hoạt động và CFO.</span></div></div>}
  </aside>
}

function WhatIfPanel({ ticker, period, scenario, setScenario, result, status, onRun }) {
  const field = (key, label, suffix = '%') => <label key={key}><span>{label}</span><div><input type="number" min={key === 'taxRatePct' ? 0 : -100} max={key === 'taxRatePct' ? 100 : 500} step="0.1" value={scenario[key]} onChange={(event) => setScenario((current) => ({ ...current, [key]: event.target.value }))} /><b>{suffix}</b></div></label>
  return <section className="bcl-whatif"><div className="bcl-panel-heading"><div><span className="bcl-eyebrow">WHAT-IF ANALYSIS · GIẢ ĐỊNH</span><h2>Thử một kịch bản</h2><p>Chọn kỳ {period || 'mới nhất'} của {ticker}. Kết quả là mô phỏng giáo dục.</p></div><SlidersHorizontal size={18} /></div><div className="bcl-whatif-grid"><div className="bcl-whatif-inputs">{field('revenueGrowthPct', 'Tăng trưởng doanh thu')}{field('grossMarginPct', 'Biên lợi nhuận gộp')}{field('taxRatePct', 'Thuế suất')}{field('operatingExpenseGrowthPct', 'Tăng trưởng chi phí HĐ')}<button type="button" onClick={onRun} disabled={status === 'loading'}>{status === 'loading' ? 'Đang tính…' : 'Áp dụng giả định'}</button></div><div className="bcl-scenario-result">{result ? <><strong>Kết quả dự phóng</strong><small>{result.scenario.period}</small><div><span>Doanh thu</span><b>{formatNumber(result.scenario.revenue, 'billion', 'VND')}</b><em>{result.delta_pct.revenue === null ? '—' : `${result.delta_pct.revenue > 0 ? '+' : ''}${result.delta_pct.revenue.toFixed(1)}%`}</em></div><div><span>Lợi nhuận gộp</span><b>{formatNumber(result.scenario.gross_profit, 'billion', 'VND')}</b><em>{result.delta_pct.gross_profit === null ? '—' : `${result.delta_pct.gross_profit > 0 ? '+' : ''}${result.delta_pct.gross_profit.toFixed(1)}%`}</em></div><div><span>Lợi nhuận ròng</span><b>{formatNumber(result.scenario.net_income, 'billion', 'VND')}</b><em>{result.scenario.net_margin_pct === null ? '—' : `${result.scenario.net_margin_pct.toFixed(1)}%`}</em></div>{result.warnings?.length ? <p className="bcl-scenario-warning">{result.warnings[0]}</p> : null}</> : <div className="bcl-scenario-empty"><Calculator size={22} /><span>Nhập giả định rồi chạy để xem kết quả.</span></div>}</div></div></section>
}

export default function BctcLabPage({ initialTicker = 'HPG', onBack, sessionId }) {
  const workflow = useFinancialWorkflow()
  const effectiveInitial = (workflow.activeTicker || initialTicker).toUpperCase()
  const [tickerInput, setTickerInput] = useState(effectiveInitial)
  const [ticker, setTicker] = useState(effectiveInitial)
  const [periodMode, setPeriodMode] = useState('year')
  const [unit, setUnit] = useState('billion')
  const [workspace, setWorkspace] = useState(null)
  const [status, setStatus] = useState('loading')
  const [loadNonce, setLoadNonce] = useState(0)
  const [error, setError] = useState('')
  const [activeView, setActiveView] = useState('workbook')
  const [activeTab, setActiveTab] = useState('income')
  const [rightTab, setRightTab] = useState('assistant')
  const [selectedCell, setSelectedCell] = useState('net_margin_pct:2025')
  const [selected, setSelected] = useState({ key: 'net_margin_pct', label: 'Net Margin', period: '', value: null, unit: '%' })
  const [formula, setFormula] = useState('=NET_INCOME / REVENUE')
  const [mode, setMode] = useState('actual')
  const [scenario, setScenario] = useState({ revenueGrowthPct: '5', grossMarginPct: '45', taxRatePct: '20', operatingExpenseGrowthPct: '3' })
  const [scenarioResult, setScenarioResult] = useState(null)
  const [scenarioStatus, setScenarioStatus] = useState('idle')
  const [modelRevision, setModelRevision] = useState(0)
  const [notes, setNotes] = useState('')
  const [notice, setNotice] = useState('')
  const [modelSessionId] = useState(localWorkbookSessionId)
  const uploadRef = useRef(null)
  const analyticsRef = useRef(null)

  useEffect(() => {
    if (workflow.activeTicker && workflow.activeTicker !== ticker) {
      setTicker(workflow.activeTicker.toUpperCase())
      setTickerInput(workflow.activeTicker.toUpperCase())
    }
  }, [workflow.activeTicker])

  useEffect(() => {
    let cancelled = false
    fetchCompanyFinancialWorkspace(ticker, { periodMode, limit: 20 })
      .then((payload) => { if (!cancelled) { setWorkspace(payload); setStatus('ready'); setError(''); setScenarioResult(null); setMode('actual') } })
      .catch((reason) => { if (!cancelled) { setStatus('error'); setError(reason.message || 'Không tải được dữ liệu BCTC.') } })
    return () => { cancelled = true }
  }, [ticker, periodMode, loadNonce])

  useEffect(() => {
    let cancelled = false
    const ownerSession = sessionId || modelSessionId
    fetchFinancialWorkbookModel(ticker, ownerSession)
      .then((payload) => {
        if (cancelled || !payload?.model) return
        const saved = payload.model
        setModelRevision(Number(saved.revision) || 0)
        if (saved.formula) setFormula(saved.formula)
        if (saved.active_tab) setActiveTab(saved.active_tab)
        if (typeof saved.notes === 'string') setNotes(saved.notes)
        if (saved.assumptions) {
          setScenario((current) => ({
            ...current,
            ...Object.fromEntries(Object.entries(saved.assumptions).map(([key, value]) => [key, String(value)])),
          }))
        }
      })
      .catch(() => {
        if (cancelled) return
        try {
          const local = JSON.parse(window.localStorage.getItem(`northstar:bctc:model:${ticker}`) || 'null')
          if (local?.formula) setFormula(local.formula)
          if (local?.scenario) setScenario((current) => ({ ...current, ...local.scenario }))
          if (typeof local?.notes === 'string') setNotes(local.notes)
        } catch { /* localStorage may be unavailable in a private context */ }
      })
    return () => { cancelled = true }
  }, [ticker, sessionId, modelSessionId])

  const period = selected.period || latestPeriod(workspace)

  function selectCell(cellKey, key, cellPeriod, value, metricUnit) {
    setSelectedCell(cellKey)
    setSelected({ key, label: [...(DATA_ROWS.income || []), ...(DATA_ROWS.balance || []), ...(DATA_ROWS.cash_flow || []), ...RATIO_ROWS].find((row) => row[0] === key)?.[1] || key, period: cellPeriod, value, unit: metricUnit })
    setFormula(`=${(key === 'net_margin_pct' ? 'NET_INCOME / REVENUE' : FORMULAS[key] || key).toUpperCase()}`)
    setRightTab('assistant')
  }

  function submitTicker(event) {
    event.preventDefault()
    const symbol = tickerInput.trim().toUpperCase()
    if (/^[A-Z0-9][A-Z0-9._-]{0,19}$/.test(symbol)) { setStatus('loading'); setTicker(symbol) }
    else setError('Mã doanh nghiệp chỉ gồm chữ, số, dấu chấm, gạch ngang hoặc gạch dưới.')
  }

  async function saveModel() {
    const assumptions = Object.fromEntries(
      Object.entries(scenario)
        .map(([key, value]) => [key, Number(value)])
        .filter(([, value]) => Number.isFinite(value)),
    )
    const payload = {
      expected_revision: modelRevision,
      active_tab: activeTab,
      formula,
      assumptions,
      notes,
    }
    try {
      const result = await saveFinancialWorkbookModel(ticker, payload, sessionId || modelSessionId)
      setModelRevision(Number(result?.model?.revision) || modelRevision + 1)
      setNotice('Mô hình đã lưu vào phiên học.')
    } catch {
      try {
        localStorage.setItem(`northstar:bctc:model:${ticker}`, JSON.stringify({ ticker, owner: sessionId || modelSessionId, scenario, formula, notes, updatedAt: new Date().toISOString() }))
        setNotice('Máy chủ chưa sẵn sàng; mô hình đã lưu cục bộ trên thiết bị này.')
      } catch { setNotice('Không thể lưu mô hình trên thiết bị này.') }
    }
  }

  async function shareModel() {
    const url = window.location.href
    try { await navigator.clipboard?.writeText(url); setNotice('Đã sao chép liên kết BCTC Lab.') } catch { setNotice(url) }
  }

  async function runScenario(targetMode = 'scenario') {
    setScenarioStatus('loading')
    setNotice('')
    try {
      const result = await runFinancialScenario(ticker, { period, revenueGrowthPct: scenario.revenueGrowthPct, grossMarginPct: scenario.grossMarginPct, taxRatePct: scenario.taxRatePct, operatingExpenseGrowthPct: scenario.operatingExpenseGrowthPct })
      setScenarioResult(result); setScenarioStatus('ready'); setMode(targetMode)
    } catch (reason) { setScenarioStatus('error'); setNotice(reason.message || 'Không chạy được scenario.') }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setNotice('Đang kiểm tra file dữ liệu…')
    try {
      const payload = await uploadFinancialStatement({ file, ticker })
      setNotice(payload?.message || 'Đã nhận file. Hãy làm mới dữ liệu để xem bản chuẩn hóa.')
    } catch (reason) { setNotice(reason.message || 'Không thể tải file dữ liệu.') }
    event.target.value = ''
  }

  if (activeView === 'practice') return <main className="bcl-practice-view"><button type="button" className="bcl-return" onClick={() => setActiveView('workbook')}><ChevronLeft size={16} /> Về workbook</button><RatioPracticeLab workspace={workspace} /></main>
  if (activeView === 'analysis') return <main className="bcl-analysis-view"><button type="button" className="bcl-return" onClick={() => setActiveView('workbook')}><ChevronLeft size={16} /> Về workbook</button><BctcAnalysisWorkspace initialTicker={ticker} onBack={onBack} /></main>

  return <main className="bctc-lab-page">
    <header className="bcl-topbar">
      <div className="bcl-brand"><div className="bcl-brand-mark"><FileSpreadsheet size={22} /></div><div><strong>BCTC Lab</strong><span>Học · Tính toán · Phân tích · Ứng dụng</span></div></div>
      <form className="bcl-company-picker" onSubmit={submitTicker}><Search size={15} /><input aria-label="Mã doanh nghiệp" value={tickerInput} onChange={(event) => setTickerInput(event.target.value.toUpperCase())} /><span>{workspace?.company?.name || 'Chọn doanh nghiệp'}</span><button type="submit" aria-label="Tra cứu"><ChevronDown size={14} /></button></form>
      <label className="bcl-top-select"><span>Năm tài chính</span><select value={periodMode} onChange={(event) => { setStatus('loading'); setPeriodMode(event.target.value) }}><option value="year">Theo năm</option><option value="quarter">Theo quý</option></select></label>
      <label className="bcl-top-select"><span>Đơn vị</span><select value={unit} onChange={(event) => setUnit(event.target.value)}><option value="billion">VND (Tỷ)</option><option value="million">VND (Triệu)</option><option value="raw">VND</option></select></label>
      <div className="bcl-mode-switch" role="group" aria-label="Chế độ workbook">{[['actual', 'Actual'], ['forecast', 'Forecast'], ['scenario', 'Scenario']].map(([key, label]) => <button type="button" className={mode === key ? 'is-active' : ''} key={key} onClick={() => { if (key === 'actual') setMode('actual'); else { runScenario(key); analyticsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }) } }}>{label}</button>)}</div>
      <div className="bcl-top-actions"><button type="button" onClick={saveModel}><Save size={15} /> Lưu</button><button type="button" onClick={shareModel}><Share2 size={15} /> Chia sẻ</button><button type="button" aria-label="Thêm"><MoreHorizontal size={17} /></button></div>
    </header>
    <div className="bcl-layout">
      <aside className="bcl-sidebar">
        <div className="bcl-sidebar-title">Dữ liệu</div>
        <button className={activeTab === 'income' ? 'is-active' : ''} type="button" onClick={() => { setActiveTab('income'); setMode('actual') }}><FileText size={15} /> BCTC gốc</button>
        <button type="button" onClick={() => { setRightTab('lesson'); setNotice('Mẫu ngành sẽ được bổ sung theo ngành và kỳ tương đồng.') }}><Table2 size={15} /> Mẫu ngành</button>
        <button type="button" onClick={() => uploadRef.current?.click()}><CloudUpload size={15} /> Tải dữ liệu mới</button>
        <div className="bcl-sidebar-title">Phân tích</div>
        <button type="button" onClick={() => { setActiveTab('income'); setRightTab('assistant') }}><LineChart size={15} /> So sánh theo năm</button>
        <button type="button" onClick={() => { setActiveTab('ratios'); setRightTab('assistant') }}><BarChart3 size={15} /> Common-size</button>
        <button type="button" onClick={() => { setActiveTab('ratios'); setRightTab('chart') }}><LineChart size={15} /> YoY Growth</button>
        <button type="button" onClick={() => setActiveTab('ratios')}><Calculator size={15} /> Chỉ số tài chính</button>
        <button type="button" onClick={() => analyticsRef.current?.scrollIntoView({ behavior: 'smooth' })}><BarChart3 size={15} /> Biểu đồ</button>
        <button type="button" onClick={() => setActiveView('analysis')}><ClipboardList size={15} /> Báo cáo chi tiết</button>
        <div className="bcl-sidebar-title">Học tập</div>
        <button type="button" onClick={() => setRightTab('lesson')}><BookOpen size={15} /> Bài học liên quan</button>
        <button type="button" onClick={() => setActiveView('practice')}><FlaskConical size={15} /> Bài tập thực hành</button>
        <button type="button" onClick={() => setRightTab('assistant')}><ClipboardList size={15} /> Kiểm tra công thức</button>
        <input ref={uploadRef} className="bcl-hidden-file" type="file" accept=".csv,text/csv" onChange={handleUpload} />
      </aside>
      <section className="bcl-main">
        <div className="bcl-workbook-tabs" role="tablist" aria-label="BCTC statements">{WORKBOOK_TABS.map(([key, label]) => <button type="button" role="tab" aria-selected={activeTab === key} className={activeTab === key ? 'is-active' : ''} key={key} onClick={() => setActiveTab(key)}>{label}</button>)}</div>
        {notice && <div className="bcl-notice" role="status"><Check size={14} /> {notice}<button type="button" aria-label="Đóng thông báo" onClick={() => setNotice('')}><X size={14} /></button></div>}
        {error && <div className="bcl-error" role="alert">{error}<button type="button" onClick={() => { setError(''); setStatus('loading'); setLoadNonce((value) => value + 1) }}>Thử lại</button></div>}
        {status === 'loading' && <div className="bcl-loading"><CloudUpload className="is-spinning" size={22} /> Đang đồng bộ dữ liệu BCTC…</div>}
        {status === 'error' && <div className="bcl-error" role="alert">Không tải được dữ liệu {ticker}. {error}</div>}
        {status === 'ready' && <>
          <div className="bcl-sheet-toolbar"><div className="bcl-cell-ref">{selectedCell.split(':')[0].toUpperCase()}</div><span className="bcl-fx">fx</span><input value={formula} aria-label="Thanh công thức" onChange={(event) => setFormula(event.target.value)} /><button type="button" aria-label="Hoàn tác"><ChevronLeft size={16} /></button><button type="button" aria-label="Làm lại"><ChevronRight size={16} /></button><button type="button" className="bcl-function-btn">Hàm <ChevronDown size={13} /></button></div>
          <div className="bcl-sheet-meta"><div><strong>{workspace?.company?.name || ticker}</strong><span>{workspace?.company?.industry || 'Chưa phân loại ngành'} · {mode === 'actual' ? 'Số liệu báo cáo' : mode === 'forecast' ? 'Dự phóng theo giả định' : 'Kịch bản đang chọn'}</span></div><div><span className="bcl-status-dot" /> {workspace?.data_provenance?.provider || 'Nguồn chuẩn hóa'} <span className="bcl-missing-legend">— không có dữ liệu ≠ 0</span><button type="button" onClick={() => setTicker((value) => value)}>↻</button></div></div>
          <div className="bcl-sheet"><WorkbookTable workspace={workspace} tab={activeTab} unit={unit} mode={mode} scenarioResult={scenarioResult} selectedCell={selectedCell} onSelectCell={selectCell} notes={notes} onNotesChange={setNotes} /></div>
          <div ref={analyticsRef} className="bcl-analytics-grid"><section className="bcl-chart-card"><div className="bcl-panel-heading"><div><h2>Doanh thu và Lợi nhuận ròng</h2><span><i className="legend-revenue" /> Revenue <i className="legend-income" /> Net Income</span></div><select aria-label="Kiểu biểu đồ"><option>Biểu đồ cột</option></select></div><MiniBarChart workspace={workspace} /></section><section className="bcl-chart-card"><div className="bcl-panel-heading"><div><h2>Biên lợi nhuận</h2><span><i className="legend-gross" /> Gross Margin <i className="legend-operating" /> Operating Margin <i className="legend-net" /> Net Margin</span></div><select aria-label="Kiểu biểu đồ"><option>Biểu đồ đường</option></select></div><MiniMarginChart workspace={workspace} /></section><WhatIfPanel ticker={ticker} period={period} scenario={scenario} setScenario={setScenario} result={scenarioResult} status={scenarioStatus} onRun={runScenario} /></div>
        </>}
      </section>
      <TutorPanel workspace={workspace} selected={selected} formula={formula} onFormulaChange={setFormula} rightTab={rightTab} setRightTab={setRightTab} notes={notes} onNotesChange={setNotes} />
    </div>
  </main>
}
