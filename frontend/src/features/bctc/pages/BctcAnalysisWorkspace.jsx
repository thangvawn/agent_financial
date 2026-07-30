import { useEffect, useMemo, useState } from 'react'
import {
  Activity, BarChart3, Building2, CalendarRange, ChevronDown, ChevronLeft, ChevronRight, Database,
  DollarSign, Download, FileSpreadsheet, FileText, GraduationCap, Info, PieChart, RefreshCw, Search, Star, TrendingUp,
} from 'lucide-react'
import '../../market-portfolio/pages/market-portfolio-panels.css'

import { fetchCompanyFinancialWorkspace } from '../services/financialsApi'
import {
  AnalysisView, DocumentsView, EvaluationView, FinancialChartsView, GovernanceView,
  TechnicalView,
} from './CompanyInsightTabs'
import { useCompanyMarketContext } from './useCompanyMarketContext'
import RatioPracticeLab from './RatioPracticeLab'
import './bctc-workspace.css'

const BCTC_NAV_TABS = [
  { id: 'charts', label: 'Biểu đồ tổng quan', icon: TrendingUp },
  { id: 'financials', label: 'Báo cáo tài chính', icon: FileSpreadsheet },
  { id: 'practice', label: 'Thực hành chỉ số', icon: GraduationCap },
  { id: 'evaluation', label: 'Đánh giá sức khỏe', icon: Activity },
  { id: 'technical', label: 'Kỹ thuật', icon: BarChart3 },
  { id: 'analysis', label: 'Phân tích chuyên sâu', icon: PieChart },
  { id: 'governance', label: 'Quản trị', icon: Building2 },
  { id: 'documents', label: 'Tài liệu & Bóc tách', icon: FileText },
]

const REPORT_TABS = [
  ['balance', 'Cân đối kế toán'],
  ['income', 'Báo cáo thu nhập'],
  ['cash_flow', 'Lưu chuyển tiền tệ'],
  ['ratios', 'Chỉ số tài chính'],
  ['notes', 'Thuyết minh'],
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

function formatPeriodLabel(period) {
  return String(period || '—').replace(/(\d{4})-Q([1-4])/, 'Q$2/$1')
}

function LoadingState() {
  return <div className="bctc-loading"><RefreshCw /><strong>Đang đồng bộ báo cáo tài chính</strong><span>Nguồn dữ liệu đang được chuẩn hóa theo từng khoản mục.</span></div>
}

function ReportTable({ statement, unit, collapsedGroups, onToggleGroup }) {
  const periods = statement?.periods || []
  const rows = statement?.rows || []
  if (!rows.length) {
    return <div className="bctc-empty-report"><FileText /><strong>Chưa có dữ liệu cho mục này</strong><span>Adapter nguồn đã sẵn sàng để bổ sung khi provider cung cấp dữ liệu.</span></div>
  }

  const visibleRows = rows.reduce((state, row) => {
    const level = Number(row.level) || 0
    if (state.hiddenBelowLevel !== null && level > state.hiddenBelowLevel) return state
    return {
      items: [...state.items, row],
      hiddenBelowLevel: row.is_group && collapsedGroups.has(row.key) ? level : null,
    }
  }, { items: [], hiddenBelowLevel: null }).items

  return <div className="bctc-report-scroll">
    <table className="bctc-report-table" style={{ width: `${Math.max(940, 360 + periods.length * 140)}px` }}>
      <caption className="bctc-sr-only">Bảng {statement?.label || 'báo cáo tài chính'} theo từng kỳ</caption>
      <thead><tr><th scope="col">Chỉ tiêu</th>{periods.map((period) => <th scope="col" key={period}><span>{formatPeriodLabel(period)}</span><FileText aria-hidden="true" /></th>)}</tr></thead>
      <tbody>{visibleRows.map((row) => {
        const values = new Map((row.values || []).map((item) => [item.period, item.value]))
        return <tr key={row.key} className={`${row.emphasis ? 'is-total' : ''} ${row.is_group ? 'is-group' : ''}`}>
          <th scope="row" style={{ '--level': row.level || 0 }}>
            {row.is_group
              ? <button type="button" className="bctc-row-toggle" aria-expanded={!collapsedGroups.has(row.key)} onClick={() => onToggleGroup(row.key)}>
                {collapsedGroups.has(row.key) ? <ChevronRight /> : <ChevronDown />}
                <span>{row.label}</span>
              </button>
              : <><i aria-hidden="true" /><span>{row.label}</span></>}
          </th>
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
  const [activeReport, setActiveReport] = useState('balance')
  const [unit, setUnit] = useState('billion')
  const [refreshToken, setRefreshToken] = useState(0)
  const [workspace, setWorkspace] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [collapsedGroups, setCollapsedGroups] = useState(() => new Set())

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
  const reportGroups = useMemo(() => (statement?.rows || []).filter((row) => row.is_group).map((row) => row.key), [statement])
  const allGroupsCollapsed = reportGroups.length > 0 && reportGroups.every((key) => collapsedGroups.has(key))
  const marketContext = useCompanyMarketContext(ticker)

  function submitTicker(event) {
    event.preventDefault()
    const symbol = tickerInput.trim().toUpperCase()
    if (/^[A-Z0-9][A-Z0-9._-]{0,19}$/.test(symbol)) {
      setStatus('loading')
      setTicker(symbol)
      setRefreshToken(0)
      setError('')
      setCollapsedGroups(new Set())
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

  function changePeriodLimit(nextLimit) {
    const normalized = Math.min(20, Math.max(4, nextLimit))
    if (normalized === periodLimit) return
    setStatus('loading')
    setPeriodLimit(normalized)
  }

  function toggleReportGroups() {
    setCollapsedGroups(allGroupsCollapsed ? new Set() : new Set(reportGroups))
  }
  const [activeTab, setActiveTab] = useState('charts')

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

    {/* Unified Single Navigation Tab Bar */}
    <div className="mp-desk__tabs" role="tablist" aria-label="BCTC Nav Tabs">
      {BCTC_NAV_TABS.map((item) => {
        const Icon = item.icon
        const isActive = activeTab === item.id
        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={isActive ? 'is-active' : ''}
            onClick={() => setActiveTab(item.id)}
          >
            <Icon size={14} />
            <span>{item.label}</span>
          </button>
        )
      })}
    </div>

    <section className="bctc-stage">
      {activeTab === 'practice' && status === 'ready' && <RatioPracticeLab workspace={workspace} />}
      {activeTab === 'charts' && status === 'ready' && <FinancialChartsView workspace={workspace} />}
      {activeTab === 'evaluation' && status === 'ready' && <EvaluationView key={ticker} workspace={workspace} ticker={ticker} />}
      {activeTab === 'technical' && <TechnicalView marketContext={marketContext.data} loading={marketContext.loading} />}
      {activeTab === 'analysis' && status === 'ready' && <AnalysisView workspace={workspace} />}
      {activeTab === 'governance' && <GovernanceView marketContext={marketContext.data} loading={marketContext.loading} />}
      {activeTab === 'documents' && status === 'ready' && <DocumentsView ticker={ticker} workspace={workspace} onImported={() => { setStatus('loading'); setRefreshToken((value) => value + 1) }} />}
      {activeTab !== 'financials' && status === 'loading' && <LoadingState />}
      {activeTab !== 'financials' && status === 'error' && <div className="bctc-error"><strong>Không tải được dữ liệu {ticker}</strong><span>{error}</span><button type="button" onClick={() => { setStatus('loading'); setRefreshToken((value) => value + 1) }}>Thử lại nguồn</button></div>}
      {activeTab === 'financials' && <div className="bctc-report-window">
        <div className="bctc-report-heading">
          <div>
            <span className="bctc-report-kicker">BÁO CÁO TÀI CHÍNH</span>
            <h2>{statement?.label || 'Cân đối kế toán'}</h2>
            <p>{company.name || ticker} · {periodMode === 'quarter' ? 'Dữ liệu theo quý' : 'Dữ liệu theo năm'}</p>
          </div>
          <div className="bctc-source-stamp"><Database /><span><small>Nguồn dữ liệu</small><strong>{workspace?.data_provenance?.provider || 'Chưa xác định'}</strong></span><i aria-label="Nguồn đang hoạt động" /></div>
        </div>
        <div className="bctc-report-nav">
          <label className="bctc-report-scope"><Building2 /><span className="bctc-sr-only">Loại báo cáo</span><select aria-label="Loại báo cáo" defaultValue="consolidated"><option value="consolidated">Báo cáo hợp nhất</option></select><ChevronDown /></label>
          <div className="bctc-report-tabs" role="tablist" aria-label="Loại báo cáo">{REPORT_TABS.map(([key, label]) => <button type="button" role="tab" aria-selected={activeReport === key} key={key} className={activeReport === key ? 'is-active' : ''} onClick={() => { setActiveReport(key); setCollapsedGroups(new Set()) }}>{label}</button>)}</div>
        </div>
        <div className="bctc-report-controls">
          <div className="bctc-period-control">
            <span className="bctc-control-label"><CalendarRange />Khoảng dữ liệu</span>
            <div className="bctc-period-range"><button type="button" aria-label="Hiển thị ít hơn 4 kỳ" title="Hiển thị ít hơn 4 kỳ" onClick={() => changePeriodLimit(periodLimit - 4)} disabled={periodLimit <= 4}><ChevronLeft /></button><span>{formatPeriodLabel(statement?.periods?.[0])}</span><b>–</b><span>{formatPeriodLabel(statement?.periods?.at(-1))}</span><button type="button" aria-label="Hiển thị thêm 4 kỳ" title="Hiển thị thêm 4 kỳ" onClick={() => changePeriodLimit(periodLimit + 4)} disabled={periodLimit >= 20}><ChevronRight /></button></div>
          </div>
          <div className="bctc-control-spacer" />
          <label><span className="bctc-control-label">Đơn vị</span><select value={unit} onChange={(event) => setUnit(event.target.value)}><option value="billion">Tỷ đồng</option><option value="million">Triệu đồng</option><option value="raw">Đồng</option></select><ChevronDown /></label>
          <label><span className="bctc-control-label">Tần suất</span><select value={periodMode} onChange={(event) => { setStatus('loading'); setPeriodMode(event.target.value); setCollapsedGroups(new Set()) }}><option value="quarter">Quý</option><option value="year">Năm</option></select><ChevronDown /></label>
          <label><span className="bctc-control-label">Phạm vi</span><select value={periodLimit} onChange={(event) => changePeriodLimit(Number(event.target.value))}><option value="4">4 kỳ</option><option value="8">8 kỳ</option><option value="12">12 kỳ</option><option value="20">20 kỳ</option></select><ChevronDown /></label>
          <button type="button" className="bctc-refresh" onClick={() => { setStatus('loading'); setRefreshToken((value) => value + 1) }} disabled={status === 'loading'}><RefreshCw className={status === 'loading' ? 'is-spinning' : ''} />Cập nhật</button>
          <button type="button" className="bctc-export" onClick={exportCsv} disabled={!statement?.rows?.length}><Download />Xuất CSV</button>
        </div>
        <div className="bctc-expand-row"><button type="button" onClick={toggleReportGroups} disabled={!reportGroups.length}>{allGroupsCollapsed ? <ChevronRight /> : <ChevronDown />}{allGroupsCollapsed ? 'Mở rộng tất cả' : 'Thu gọn tất cả'}</button><span><FileSpreadsheet />{statement?.rows?.length || 0} khoản mục · {statement?.periods?.length || 0} kỳ · đơn vị {unit === 'billion' ? 'tỷ đồng' : unit === 'million' ? 'triệu đồng' : 'đồng'}</span></div>
        {status === 'loading' && <LoadingState />}
        {status === 'error' && <div className="bctc-error"><strong>Không tải được BCTC {ticker}</strong><span>{error}</span><button type="button" onClick={() => { setStatus('loading'); setRefreshToken((value) => value + 1) }}>Thử lại nguồn</button></div>}
        {status === 'ready' && <ReportTable statement={statement} unit={unit} collapsedGroups={collapsedGroups} onToggleGroup={(key) => setCollapsedGroups((current) => { const next = new Set(current); if (next.has(key)) next.delete(key); else next.add(key); return next })} />}
        <footer className="bctc-report-footer"><span><Info />Nguồn: {workspace?.data_provenance?.provider || '—'} · cập nhật {workspace?.data_provenance?.fetched_at ? new Date(workspace.data_provenance.fetched_at).toLocaleString('vi-VN') : '—'}</span><span>Dữ liệu phục vụ học tập và phân tích, không phải khuyến nghị đầu tư.</span></footer>
      </div>}
    </section>
  </main>
}
