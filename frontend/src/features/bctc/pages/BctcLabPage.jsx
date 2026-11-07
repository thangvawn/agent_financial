import { useAccountId } from '../../../shared/auth/accountContext'
import { useWorkbookModel } from '../hooks/useWorkbookModel'
import { useEffect, useRef, useState } from 'react'
import {
  BarChart3, BookOpen, Calculator, Check, ChevronLeft,
  ChevronRight, ClipboardList, CloudUpload, FileSpreadsheet, FileText, FlaskConical,
  Save, Search, Share2,
  SlidersHorizontal, Table2, X,
} from 'lucide-react'

import FinancialCalculator from './FinancialCalculator'
import RatioPracticeLab from './RatioPracticeLab'
import BctcAnalysisWorkspace from './BctcAnalysisWorkspace'
import { useFinancialWorkflow } from '../../../shared/context/FinancialWorkflowContext'
import {
  fetchCompanyFinancialWorkspace,
  runFinancialScenario,
  uploadFinancialStatement,
} from '../services/financialsApi'
import { findRowWithAliases } from '../utils/statementMapper'
import MiniMarginChart from './MiniMarginChart'
import ReadingPanel from './ReadingPanel'
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

function MiniBarChart({ workspace }) {
  const periods = [...(workspace?.trend?.periods || [])]
  const series = new Map((workspace?.trend?.series || []).map((item) => [item.key, item]))
  const revenue = periods.map((period) => numeric(series.get('revenue')?.values?.find((item) => item.period === period)?.value))
  const netIncome = periods.map((period) => numeric(series.get('net_income')?.values?.find((item) => item.period === period)?.value))
  const max = Math.max(...revenue.filter((v) => v !== null), ...netIncome.filter((v) => v !== null), 1)
  return <div className="bcl-bar-chart" role="img" aria-label="Doanh thu và lợi nhuận ròng theo kỳ">
    <div className="bcl-chart-gridlines"><i /><i /><i /><i /></div>
    <div className="bcl-bars">{periods.map((period, index) => <div className="bcl-bar-group" key={period}>
      <div className="bcl-bar-pair">{revenue[index] !== null && revenue[index] >= 0 && <i className="is-revenue" style={{ height: `${revenue[index] / max * 100}%` }} />}{netIncome[index] !== null && netIncome[index] >= 0 && <i className="is-income" style={{ height: `${netIncome[index] / max * 100}%` }} />}</div>
      <span title={period}>{period}</span>
    </div>)}</div>
  </div>
}

function WorkbookTable({ workspace, tab, unit, selectedCell, onSelectCell, notes, onNotesChange, mode, scenarioResult, rowSearch, periodFilter }) {
  if (tab === 'notes') return <div className="bcl-notes-workspace"><div><span className="bcl-eyebrow">WORKING NOTES</span><h2>Ghi chú cho phiên học</h2><p>Ghi lại bằng chứng từ raw data, công thức và giới hạn của kết luận.</p></div><textarea aria-label="Ghi chú BCTC" value={notes} onChange={(event) => onNotesChange(event.target.value)} placeholder="Ví dụ: Biên lợi nhuận giảm vì giá vốn tăng nhanh hơn doanh thu…" rows={14} /><small>Ghi chú sẽ đi cùng phiên workbook khi bạn bấm Lưu.</small></div>
  const sourceTab = tab === 'model' || tab === 'ratios' ? 'income' : tab
  const statement = workspace?.statements?.[sourceTab]
  const allPeriods = displayPeriods(statement, workspace)
  const periods = allPeriods.filter((period) => !periodFilter || periodKey(period) === periodKey(periodFilter))
  const baseRows = tab === 'ratios' ? RATIO_ROWS : DATA_ROWS[sourceTab] || DATA_ROWS.income
  const knownKeys = new Set(baseRows.map(([key]) => key))
  const rawRows = tab === 'ratios' || tab === 'model' ? [] : (statement?.rows || [])
    .filter((row) => row?.key && !knownKeys.has(row.key))
    .map((row) => [row.key, row.label || row.label_en || row.key, 'VND', Boolean(row.emphasis)])
  const rowSpecs = [...baseRows, ...rawRows].filter(([key, label]) => `${key} ${label}`.toLocaleLowerCase('vi').includes(rowSearch.trim().toLocaleLowerCase('vi')))
  const statementRows = sourceMap(statement)
  const ratios = ratioMap(workspace)
  const trendRows = new Map((workspace?.trend?.series || []).map((series) => [series.key, series]))
  if (!periods.length) return <div className="bcl-empty"><FileSpreadsheet size={22} /><strong>Chưa có kỳ báo cáo</strong><span>Hãy tải dữ liệu hoặc chọn một doanh nghiệp khác.</span></div>
  // A fixed-layout table can otherwise squeeze twenty quarters into narrow
  // cells. Set the real content width so the horizontal scrollbar preserves
  // readable spacing instead of letting values overlap.
  if (!rowSpecs.length) return <div className="bcl-empty"><Search size={22} /><strong>Không tìm thấy chỉ tiêu</strong><span>Thử từ khóa khác hoặc xóa bộ lọc.</span></div>
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
        allPeriods.forEach((period) => {
          const canonicalPeriod = periodKey(period)
          if (values.get(canonicalPeriod) === undefined || values.get(canonicalPeriod) === null) {
            const revenue = numeric(revenueValues.get(canonicalPeriod))
            const gross = numeric(grossValues.get(canonicalPeriod))
            if (revenue !== null && gross !== null) values.set(canonicalPeriod, Math.abs(revenue - gross))
          }
        })
      }
      if (['gross_margin_pct', 'operating_margin_pct', 'net_margin_pct'].includes(key)) {
        allPeriods.forEach((period) => {
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
          return <td key={period} className={selected ? 'is-selected' : ''}><button type="button" onClick={() => onSelectCell(cellKey, key, period, value, metricUnit, label, allPeriods.map((item) => ({ period: item, value: values.get(periodKey(item)) ?? null })), metricUnit === '%' || Boolean(FORMULAS[key]) || Boolean(ratio))} aria-label={`${label} ${period}`} title={value === null ? 'Không có dữ liệu từ nguồn cho kỳ này; dấu — không có nghĩa là 0.' : undefined}>{formatNumber(value, unit, metricUnit)}</button></td>
        })}
      </tr>
    })}
  </tbody></table></div>
}

function WhatIfPanel({ ticker, period, scenario, setScenario, result, status, onRun }) {
  const field = (key, label, suffix = '%') => <label key={key}><span>{label}</span><div><input type="number" min={key === 'taxRatePct' ? 0 : -100} max={key === 'taxRatePct' ? 100 : 500} step="0.1" value={scenario[key]} onChange={(event) => setScenario((current) => ({ ...current, [key]: event.target.value }))} /><b>{suffix}</b></div></label>
  return <section className="bcl-whatif"><div className="bcl-panel-heading"><div><span className="bcl-eyebrow">WHAT-IF ANALYSIS · GIẢ ĐỊNH</span><h2>Thử một kịch bản</h2><p>Chọn kỳ {period || 'mới nhất'} của {ticker}. Kết quả là mô phỏng giáo dục.</p></div><SlidersHorizontal size={18} /></div><div className="bcl-whatif-grid"><div className="bcl-whatif-inputs">{field('revenueGrowthPct', 'Tăng trưởng doanh thu')}{field('grossMarginPct', 'Biên lợi nhuận gộp')}{field('taxRatePct', 'Thuế suất')}{field('operatingExpenseGrowthPct', 'Tăng trưởng chi phí HĐ')}<button type="button" onClick={onRun} disabled={status === 'loading'}>{status === 'loading' ? 'Đang tính…' : 'Áp dụng giả định'}</button></div><div className="bcl-scenario-result">{result ? <><strong>Kết quả dự phóng</strong><small>{result.scenario.period}</small><div><span>Doanh thu</span><b>{formatNumber(result.scenario.revenue, 'billion', 'VND')}</b><em>{result.delta_pct.revenue === null ? '—' : `${result.delta_pct.revenue > 0 ? '+' : ''}${result.delta_pct.revenue.toFixed(1)}%`}</em></div><div><span>Lợi nhuận gộp</span><b>{formatNumber(result.scenario.gross_profit, 'billion', 'VND')}</b><em>{result.delta_pct.gross_profit === null ? '—' : `${result.delta_pct.gross_profit > 0 ? '+' : ''}${result.delta_pct.gross_profit.toFixed(1)}%`}</em></div><div><span>Lợi nhuận ròng</span><b>{formatNumber(result.scenario.net_income, 'billion', 'VND')}</b><em>{result.scenario.net_margin_pct === null ? '—' : `${result.scenario.net_margin_pct.toFixed(1)}%`}</em></div>{result.warnings?.length ? <p className="bcl-scenario-warning">{result.warnings[0]}</p> : null}</> : <div className="bcl-scenario-empty"><Calculator size={22} /><span>Nhập giả định rồi chạy để xem kết quả.</span></div>}</div></div></section>
}

export default function BctcLabPage({ initialTicker = 'HPG', onBack, sessionId }) {
  const accountId = useAccountId()
  const workflow = useFinancialWorkflow()
  const effectiveInitial = (workflow.activeTicker || initialTicker).toUpperCase()
  const [tickerInput, setTickerInput] = useState(effectiveInitial)
  const [ticker, setTicker] = useState(effectiveInitial)
  const [periodMode, setPeriodMode] = useState('year')
  const [unit, setUnit] = useState('billion')
  const [rowSearch, setRowSearch] = useState('')
  const [periodFilter, setPeriodFilter] = useState('')
  const [workspace, setWorkspace] = useState(null)
  const [status, setStatus] = useState('loading')
  const [loadNonce, setLoadNonce] = useState(0)
  const [error, setError] = useState('')
  const [activeView, setActiveView] = useState('workbook')
  const [rightTab, setRightTab] = useState('assistant')
  const [selectedCell, setSelectedCell] = useState('net_margin_pct:2025')
  const [selected, setSelected] = useState({ key: 'net_margin_pct', label: 'Net Margin', period: '', value: null, unit: '%' })
  const [mode, setMode] = useState('actual')
  const [scenarioResult, setScenarioResult] = useState(null)
  const [scenarioStatus, setScenarioStatus] = useState('idle')
  const [notice, setNotice] = useState('')
  const [modelSessionId] = useState(localWorkbookSessionId)
  const workbook = useWorkbookModel(ticker, sessionId || modelSessionId, accountId)
  const { active_tab: activeTab, setActiveTab, formula, setFormula, assumptions: scenario, setScenario, notes, setNotes } = workbook
  const uploadRef = useRef(null)
  const analyticsRef = useRef(null)
  const calculatorRef = useRef(null)
  const sheetRef = useRef(null)
  const availablePeriods = [...new Set(Object.values(workspace?.statements || {}).flatMap((statement) => statement?.periods || []))].sort().reverse()

  const [lastWorkflowTicker, setLastWorkflowTicker] = useState(workflow.activeTicker)
  if (workflow.activeTicker !== lastWorkflowTicker) {
    setLastWorkflowTicker(workflow.activeTicker)
    if (workflow.activeTicker) {
      setTicker(workflow.activeTicker.toUpperCase())
      setTickerInput(workflow.activeTicker.toUpperCase())
    }
  }

  useEffect(() => {
    let cancelled = false
    fetchCompanyFinancialWorkspace(ticker, { periodMode, limit: 20 })
      .then((payload) => { if (!cancelled) { setWorkspace(payload); setStatus('ready'); setError(''); setScenarioResult(null); setMode('actual') } })
      .catch((reason) => { if (!cancelled) { setStatus('error'); setError(reason.message || 'Không tải được dữ liệu BCTC.') } })
    return () => { cancelled = true }
  }, [ticker, periodMode, loadNonce])

  const scope = `${sessionId}:${ticker}`
  const [lastScope, setLastScope] = useState(scope)
  if (lastScope !== scope) {
    setLastScope(scope)
    setSelectedCell('')
    setSelected({ key: 'net_margin_pct', label: 'Net Margin', period: '', value: null, unit: '%' })
    setScenarioResult(null)
    setNotice('')
  }

  const period = selected.period || latestPeriod(workspace)

  function selectCell(cellKey, key, cellPeriod, value, metricUnit, label, series, calculated) {
    setSelectedCell(cellKey)
    setSelected({ key, label: label || key, period: cellPeriod, value, unit: metricUnit, series, kind: calculated ? 'calculated' : 'reported', formula: FORMULAS[key] || ratioMap(workspace).get(key)?.formula, tableTab: activeTab, tableMode: mode, periodMode, loadNonce })
    setFormula(`=${(key === 'net_margin_pct' ? 'NET_INCOME / REVENUE' : FORMULAS[key] || key).toUpperCase()}`)
    setRightTab('assistant')
  }

  function submitTicker(event) {
    event.preventDefault()
    const symbol = tickerInput.trim().toUpperCase()
    if (/^[A-Z0-9][A-Z0-9._-]{0,19}$/.test(symbol)) { setStatus('loading'); setError(''); if (symbol === ticker) setLoadNonce((value) => value + 1); else setTicker(symbol) }
    else setError('Mã doanh nghiệp chỉ gồm chữ, số, dấu chấm, gạch ngang hoặc gạch dưới.')
  }

  async function saveModel() {
    try { const message = await workbook.save(); if (message) setNotice(message) }
    catch (reason) { setNotice(reason.message || 'Không thể lưu workbook.') }
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
      <form className="bcl-company-picker" onSubmit={submitTicker}><Search size={15} /><input aria-label="Mã doanh nghiệp" value={tickerInput} onChange={(event) => setTickerInput(event.target.value.toUpperCase())} /><span>{workspace?.company?.name || 'Chọn doanh nghiệp'}</span><button type="submit" aria-label="Tra cứu doanh nghiệp">Tìm</button></form>
      <label className="bcl-top-select"><span>Năm tài chính</span><select value={periodMode} onChange={(event) => { setStatus('loading'); setPeriodMode(event.target.value); setPeriodFilter('') }}><option value="year">Theo năm</option><option value="quarter">Theo quý</option></select></label>
      <label className="bcl-top-select"><span>Đơn vị</span><select value={unit} onChange={(event) => setUnit(event.target.value)}><option value="billion">VND (Tỷ)</option><option value="million">VND (Triệu)</option><option value="raw">VND</option></select></label>
      <div className="bcl-mode-switch" role="group" aria-label="Chế độ workbook">{[['actual', 'Actual'], ['forecast', 'Forecast'], ['scenario', 'Scenario']].map(([key, label]) => <button type="button" className={mode === key ? 'is-active' : ''} key={key} onClick={() => { if (key === 'actual') setMode('actual'); else { runScenario(key); analyticsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }) } }}>{label}</button>)}</div>
      <div className="bcl-top-actions"><button type="button" onClick={saveModel} disabled={workbook.loading || workbook.saving || Boolean(workbook.error) || workbook.conflict}><Save size={15} /> Lưu</button><button type="button" onClick={shareModel}><Share2 size={15} /> Chia sẻ</button></div>
    </header>
    <div className="bcl-layout">
      <aside className="bcl-sidebar">
        <div className="bcl-sidebar-title">Dữ liệu</div>
        <button className={['income', 'balance', 'cash_flow'].includes(activeTab) ? 'is-active' : ''} aria-current={['income', 'balance', 'cash_flow'].includes(activeTab) ? 'page' : undefined} type="button" onClick={() => { setActiveTab('income'); setMode('actual'); sheetRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }}><FileText size={15} /> BCTC gốc</button>

        <button type="button" onClick={() => uploadRef.current?.click()}><CloudUpload size={15} /> Tải dữ liệu mới</button>
        <div className="bcl-sidebar-title">Phân tích</div>
        <button type="button" onClick={() => calculatorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}><Calculator size={15} /> Chỉ số & công thức</button>
        <button className={activeTab === 'ratios' ? 'is-active' : ''} aria-current={activeTab === 'ratios' ? 'page' : undefined} type="button" onClick={() => { setActiveTab('ratios'); sheetRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }}><Table2 size={15} /> Bảng chỉ số báo cáo</button>
        <button type="button" onClick={() => analyticsRef.current?.scrollIntoView({ behavior: 'smooth' })}><BarChart3 size={15} /> Biểu đồ</button>
        <button type="button" onClick={() => setActiveView('analysis')}><ClipboardList size={15} /> Báo cáo chi tiết</button>
        <div className="bcl-sidebar-title">Học tập</div>
        <button type="button" onClick={() => setRightTab('notes')}><BookOpen size={15} /> Ghi chú báo cáo</button>
        <button type="button" onClick={() => setActiveView('practice')}><FlaskConical size={15} /> Bài tập thực hành</button>
        <button type="button" onClick={() => setRightTab('assistant')}><ClipboardList size={15} /> Kiểm tra công thức</button>
        <input ref={uploadRef} className="bcl-hidden-file" type="file" accept=".csv,text/csv" onChange={handleUpload} />
      </aside>
      <section className="bcl-main">
        <div className="bcl-workbook-tabs" role="tablist" aria-label="BCTC statements">{WORKBOOK_TABS.map(([key, label]) => <button type="button" role="tab" title={`Mở ${label}`} aria-selected={activeTab === key} className={activeTab === key ? 'is-active' : ''} key={key} onClick={() => setActiveTab(key)}>{label}</button>)}</div>
        {workbook.restoredDraft && <p role="status">Đã khôi phục bản nháp trên thiết bị; bấm Lưu để đồng bộ.</p>}
        {workbook.conflict && <section role="alert"><p>Bản máy chủ đã thay đổi. Bản nháp của bạn vẫn được giữ. Chọn bản muốn sử dụng trước khi lưu.</p><button onClick={() => { if (window.confirm('Bỏ bản nháp và dùng bản máy chủ?')) workbook.resolveConflict(false) }}>Dùng bản máy chủ</button><button onClick={() => workbook.resolveConflict(true)}>Giữ bản nháp để lưu lại</button></section>}
        {workbook.error && <p role="alert">{workbook.error}</p>}
        {notice && <div className="bcl-notice" role="status"><Check size={14} /> {notice}<button type="button" aria-label="Đóng thông báo" onClick={() => setNotice('')}><X size={14} /></button></div>}
        {error && <div className="bcl-error" role="alert">{error}<button type="button" onClick={() => { setError(''); setStatus('loading'); setLoadNonce((value) => value + 1) }}>Thử lại</button></div>}
        {status === 'loading' && <div className="bcl-loading"><CloudUpload className="is-spinning" size={22} /> Đang đồng bộ dữ liệu BCTC…</div>}
        {status === 'error' && <div className="bcl-error" role="alert">Không tải được dữ liệu {ticker}. {error}</div>}
        {status === 'ready' && <>
          <div ref={sheetRef} className="bcl-sheet-toolbar"><div className="bcl-cell-ref">{selectedCell.split(':')[0].toUpperCase()}</div><span className="bcl-fx">fx</span><input value={formula} aria-label="Thanh công thức" onChange={(event) => setFormula(event.target.value)} /></div>
          <div className="bcl-sheet-meta"><div><strong>{workspace?.company?.name || ticker}</strong><span>{workspace?.company?.industry || 'Chưa phân loại ngành'} · {mode === 'actual' ? 'Số liệu báo cáo' : mode === 'forecast' ? 'Dự phóng theo giả định' : 'Kịch bản đang chọn'}</span></div><div><span className="bcl-status-dot" /> {workspace?.data_provenance?.provider || 'Nguồn chuẩn hóa'} <span className="bcl-missing-legend">— không có dữ liệu ≠ 0</span><button type="button" onClick={() => { setStatus('loading'); setLoadNonce((value) => value + 1) }} aria-label="Làm mới dữ liệu">↻</button></div></div>
          <div className="bcl-table-filters"><label><Search size={15} /><input value={rowSearch} onChange={(event) => setRowSearch(event.target.value)} placeholder="Tìm chỉ tiêu" aria-label="Tìm chỉ tiêu trong bảng" /></label><label>Kỳ <select value={periodFilter} onChange={(event) => setPeriodFilter(event.target.value)}><option value="">Tất cả các kỳ</option>{availablePeriods.map((item) => <option key={item}>{item}</option>)}</select></label></div>
          <div className="bcl-sheet"><WorkbookTable workspace={workspace} tab={activeTab} unit={unit} mode={mode} scenarioResult={scenarioResult} selectedCell={selectedCell} onSelectCell={selectCell} notes={notes} onNotesChange={setNotes} rowSearch={rowSearch} periodFilter={periodFilter} /></div>
          <div ref={analyticsRef} className="bcl-analytics-grid"><section className="bcl-chart-card"><div className="bcl-panel-heading"><div><h2>Doanh thu và Lợi nhuận ròng</h2><span><i className="legend-revenue" /> Revenue <i className="legend-income" /> Net Income</span><small>Giá trị âm không hiển thị trên biểu đồ cột.</small></div><select aria-label="Kiểu biểu đồ"><option>Biểu đồ cột</option></select></div><MiniBarChart workspace={workspace} /></section><section className="bcl-chart-card"><div className="bcl-panel-heading"><div><h2>Biên lợi nhuận</h2><span><i className="legend-gross" /> Gross Margin <i className="legend-operating" /> Operating Margin <i className="legend-net" /> Net Margin</span></div><select aria-label="Kiểu biểu đồ"><option>Biểu đồ đường</option></select></div><MiniMarginChart workspace={workspace} /></section><WhatIfPanel ticker={ticker} period={period} scenario={scenario} setScenario={setScenario} result={scenarioResult} status={scenarioStatus} onRun={runScenario} /></div>
        </>}
        {status !== 'loading' && <div ref={calculatorRef}><FinancialCalculator key={`${ticker}:${periodMode}:${unit}:${loadNonce}:${status}`} workspace={status === 'ready' ? workspace : null} unit={unit} /></div>}
      </section>
      <ReadingPanel key={`${ticker}:${periodMode}`} workspace={workspace} selected={selected} activeTab={activeTab} mode={mode} periodMode={periodMode} loadNonce={loadNonce} unit={unit} rightTab={rightTab} setRightTab={setRightTab} notes={notes} onNotesChange={setNotes} onOpenCalculator={() => calculatorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })} onSelectHistory={(item) => { setPeriodFilter(''); selectCell(`${selected.key}:${item.period}`, selected.key, item.period, item.value, selected.unit, selected.label, selected.series, selected.kind === 'calculated') }} />
    </div>
  </main>
}
