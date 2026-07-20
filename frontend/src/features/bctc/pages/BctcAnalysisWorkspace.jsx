import { useEffect, useMemo, useState } from 'react'
import {
  ChevronDown, ChevronRight, Download, FileText, RefreshCw, Search, Star,
} from 'lucide-react'

import { fetchCompanyFinancialWorkspace } from '../services/financialsApi'
import {
  AnalysisView, DocumentsView, FinancialChartsView, GovernanceView,
  TechnicalView,
} from './CompanyInsightTabs'
import { useCompanyMarketContext } from './useCompanyMarketContext'
import './bctc-workspace.css'

const COMPANY_TABS = [
  ['charts', 'BIỂU ĐỒ'], ['financials', 'TÀI CHÍNH'], ['technical', 'KỸ THUẬT'],
  ['analysis', 'PHÂN TÍCH'], ['governance', 'QUẢN TRỊ'], ['documents', 'TÀI LIỆU'],
]
const REPORT_TABS = [
  ['balance', 'Cân đối kế toán'],
  ['income', 'Báo cáo thu nhập'],
  ['cash_flow', 'Lưu chuyển tiền tệ'],
  ['notes', 'Thuyết minh'],
  ['ratios', 'Chỉ số tài chính'],
  ['peers', 'So sánh cùng ngành'],
]

function numeric(value) {
  const parsed = Number(value)
  return value === null || value === undefined || !Number.isFinite(parsed) ? null : parsed
}

function formatReportValue(value, unit) {
  const number = numeric(value)
  if (number === null) return '—'
  const divisor = unit === 'million' ? 1e6 : unit === 'raw' ? 1 : 1e9
  return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: unit === 'raw' ? 0 : 2 }).format(number / divisor)
}

function formatHeadline(value, unit = 'VND') {
  const number = numeric(value)
  if (number === null) return '—'
  if (unit === '%') return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(number)}%`
  if (unit === 'x') return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(number)}x`
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(number / 1e9)} tỷ`
}

function LoadingState() {
  return <div className="bctc-loading"><RefreshCw /><strong>Đang đồng bộ báo cáo tài chính</strong><span>Nguồn dữ liệu đang được chuẩn hóa theo từng khoản mục.</span></div>
}

function ReportTable({ statement, unit }) {
  const periods = statement?.periods || []
  const rows = statement?.rows || []
  if (!rows.length) {
    return <div className="bctc-empty-report"><FileText /><strong>Chưa có dữ liệu cho mục này</strong><span>Adapter nguồn đã sẵn sàng để bổ sung khi provider cung cấp dữ liệu.</span></div>
  }
  return <div className="bctc-report-scroll">
    <table className="bctc-report-table">
      <thead><tr><th>Chỉ tiêu</th>{periods.map((period) => <th key={period}><span>{period.replace(/(\d{4})-Q([1-4])/, 'Q$2/$1')}</span><FileText aria-label={`Báo cáo ${period}`} /></th>)}</tr></thead>
      <tbody>{rows.map((row) => {
        const values = new Map((row.values || []).map((item) => [item.period, item.value]))
        return <tr key={row.key} className={`${row.emphasis ? 'is-total' : ''} ${row.is_group ? 'is-group' : ''}`}>
          <th style={{ '--level': row.level || 0 }}>{row.is_group ? <ChevronRight /> : <i />}{row.label}</th>
          {periods.map((period) => {
            const value = numeric(values.get(period))
            return <td key={period} className={value !== null && value < 0 ? 'is-negative' : ''}>{formatReportValue(value, unit)}</td>
          })}
        </tr>
      })}</tbody>
    </table>
  </div>
}

export default function BctcAnalysisWorkspace({ initialTicker = 'HPG', onBack }) {
  const [tickerInput, setTickerInput] = useState(initialTicker)
  const [ticker, setTicker] = useState(initialTicker.toUpperCase())
  const [periodMode, setPeriodMode] = useState('quarter')
  const [periodLimit, setPeriodLimit] = useState(20)
  const [activeCompanyTab, setActiveCompanyTab] = useState('charts')
  const [activeReport, setActiveReport] = useState('balance')
  const [unit, setUnit] = useState('billion')
  const [refreshToken, setRefreshToken] = useState(0)
  const [workspace, setWorkspace] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    fetchCompanyFinancialWorkspace(ticker, { periodMode, limit: periodLimit, refresh: refreshToken > 0 })
      .then((payload) => { if (!cancelled) { setWorkspace(payload); setStatus('ready') } })
      .catch((reason) => { if (!cancelled) { setError(reason.message || 'Không tải được dữ liệu BCTC.'); setStatus('error') } })
    return () => { cancelled = true }
  }, [ticker, periodMode, periodLimit, refreshToken])

  const company = workspace?.company || {}
  const headline = useMemo(() => Object.fromEntries((workspace?.headline_metrics || []).map((item) => [item.key, item])), [workspace])
  const statement = workspace?.statements?.[activeReport]
  const marketContext = useCompanyMarketContext(ticker)

  function submitTicker(event) {
    event.preventDefault()
    const symbol = tickerInput.trim().toUpperCase()
    if (/^[A-Z0-9][A-Z0-9._-]{0,19}$/.test(symbol)) {
      setStatus('loading')
      setTicker(symbol)
      setRefreshToken(0)
      setError('')
    }
  }

  function exportCsv() {
    if (!statement?.rows?.length) return
    const periods = statement.periods || []
    const lines = [['Chỉ tiêu', ...periods], ...statement.rows.map((row) => {
      const values = new Map((row.values || []).map((item) => [item.period, item.value]))
      return [row.label, ...periods.map((period) => values.get(period) ?? '')]
    })]
    const csv = `\uFEFF${lines.map((line) => line.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n')}`
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${ticker}-${activeReport}-${periodMode}.csv`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return <main className="bctc-workspace">
    <header className="bctc-company-bar">
      <div className="bctc-symbol-block">
        {onBack && <button type="button" className="bctc-back" onClick={onBack}>←</button>}
        <div className="bctc-logo">{ticker}</div>
        <div><div className="bctc-company-title"><h1>{ticker}</h1><span>{company.exchange || 'HOSE'}</span><Star /></div><p>{company.name || `CTCP ${ticker}`} · {company.industry || 'Chưa phân loại ngành'}</p></div>
      </div>
      <form className="bctc-symbol-search" onSubmit={submitTicker}><Search /><input aria-label="Mã chứng khoán" value={tickerInput} onChange={(event) => setTickerInput(event.target.value.toUpperCase())} /><button type="submit">Tra cứu</button></form>
    </header>

    <section className="bctc-company-facts">
      <div><span>Kỳ báo cáo mới nhất</span><strong>{company.latest_period || '—'}</strong><small>Báo cáo hợp nhất</small></div>
      <div><span>Doanh thu</span><strong>{formatHeadline(headline.revenue?.value)}</strong><small className={(headline.revenue?.yoy_pct || 0) >= 0 ? 'up' : 'down'}>{headline.revenue?.yoy_pct > 0 ? '+' : ''}{headline.revenue?.yoy_pct?.toFixed?.(1) || '—'}% YoY</small></div>
      <div><span>Lợi nhuận sau thuế</span><strong>{formatHeadline(headline.net_income?.value)}</strong><small className={(headline.net_income?.yoy_pct || 0) >= 0 ? 'up' : 'down'}>{headline.net_income?.yoy_pct > 0 ? '+' : ''}{headline.net_income?.yoy_pct?.toFixed?.(1) || '—'}% YoY</small></div>
      <div><span>Biên lợi nhuận gộp</span><strong>{formatHeadline(headline.gross_margin_pct?.value, '%')}</strong><small>Kỳ mới nhất</small></div>
      <div><span>ROE</span><strong>{formatHeadline(headline.roe_pct?.value, '%')}</strong><small>Tính từ BCTC</small></div>
      <div><span>Nợ vay / VCSH</span><strong>{formatHeadline(headline.debt_to_equity?.value, 'x')}</strong><small>Đòn bẩy tài chính</small></div>
    </section>

    <nav className="bctc-company-tabs" aria-label="Phân tích doanh nghiệp">{COMPANY_TABS.map(([key, label]) => <button type="button" key={key} className={activeCompanyTab === key ? 'is-active' : ''} onClick={() => setActiveCompanyTab(key)}>{label}</button>)}</nav>

    <section className="bctc-stage">
      {activeCompanyTab === 'charts' && status === 'ready' && <FinancialChartsView workspace={workspace} />}
      {activeCompanyTab === 'technical' && <TechnicalView marketContext={marketContext.data} loading={marketContext.loading} />}
      {activeCompanyTab === 'analysis' && status === 'ready' && <AnalysisView workspace={workspace} />}
      {activeCompanyTab === 'governance' && <GovernanceView marketContext={marketContext.data} loading={marketContext.loading} />}
      {activeCompanyTab === 'documents' && status === 'ready' && <DocumentsView ticker={ticker} workspace={workspace} onImported={() => { setStatus('loading'); setRefreshToken((value) => value + 1) }} />}
      {activeCompanyTab !== 'financials' && status === 'loading' && <LoadingState />}
      {activeCompanyTab !== 'financials' && status === 'error' && <div className="bctc-error"><strong>Không tải được dữ liệu {ticker}</strong><span>{error}</span><button type="button" onClick={() => { setStatus('loading'); setRefreshToken((value) => value + 1) }}>Thử lại nguồn</button></div>}
      {activeCompanyTab === 'financials' && <div className="bctc-report-window">
        <div className="bctc-report-topline">
          <label>Báo cáo hợp nhất <ChevronDown /></label>
          <div className="bctc-source-stamp"><i />{workspace?.data_provenance?.provider || 'Nguồn dữ liệu'}</div>
        </div>
        <div className="bctc-report-tabs">{REPORT_TABS.map(([key, label]) => <button type="button" key={key} className={activeReport === key ? 'is-active' : ''} onClick={() => setActiveReport(key)}>{label}</button>)}</div>
        <div className="bctc-report-controls">
          <div className="bctc-period-range"><button type="button">‹</button><span>{statement?.periods?.at(-1) || '—'}</span><b>–</b><span>{statement?.periods?.[0] || '—'}</span><button type="button">›</button></div>
          <div className="bctc-control-spacer" />
          <label>Đơn vị<select value={unit} onChange={(event) => setUnit(event.target.value)}><option value="billion">Tỷ đồng</option><option value="million">Triệu đồng</option><option value="raw">Đồng</option></select><ChevronDown /></label>
          <label>Kỳ<select value={periodMode} onChange={(event) => { setStatus('loading'); setPeriodMode(event.target.value) }}><option value="quarter">Quý</option><option value="year">Năm</option></select><ChevronDown /></label>
          <label>Phạm vi<select value={periodLimit} onChange={(event) => { setStatus('loading'); setPeriodLimit(Number(event.target.value)) }}><option value="4">4 kỳ</option><option value="8">8 kỳ</option><option value="12">12 kỳ</option><option value="20">20 kỳ</option></select><ChevronDown /></label>
          <button type="button" className="bctc-refresh" onClick={() => { setStatus('loading'); setRefreshToken((value) => value + 1) }} disabled={status === 'loading'}><RefreshCw />Cập nhật</button>
          <button type="button" className="bctc-export" onClick={exportCsv}><Download />Xuất Excel</button>
        </div>
        <div className="bctc-expand-row"><button type="button"><ChevronRight />Mở rộng tất cả</button><span>{statement?.rows?.length || 0} khoản mục · số liệu {unit === 'billion' ? 'tỷ đồng' : unit === 'million' ? 'triệu đồng' : 'đồng'}</span></div>
        {status === 'loading' && <LoadingState />}
        {status === 'error' && <div className="bctc-error"><strong>Không tải được BCTC {ticker}</strong><span>{error}</span><button type="button" onClick={() => { setStatus('loading'); setRefreshToken((value) => value + 1) }}>Thử lại nguồn</button></div>}
        {status === 'ready' && <ReportTable statement={statement} unit={unit} />}
        <footer className="bctc-report-footer"><span>Nguồn: {workspace?.data_provenance?.provider || '—'} · cập nhật {workspace?.data_provenance?.fetched_at ? new Date(workspace.data_provenance.fetched_at).toLocaleString('vi-VN') : '—'}</span><span>Dữ liệu phục vụ phân tích, không phải khuyến nghị đầu tư.</span></footer>
      </div>}
    </section>
  </main>
}
