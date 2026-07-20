import { useRef, useState } from 'react'
import {
  AlertTriangle, BarChart3, Building2, Database, FileUp, Gauge,
  LineChart, ShieldCheck, UsersRound,
} from 'lucide-react'

import {
  extractFinancialStatementUpload,
  uploadFinancialStatement,
} from '../services/financialsApi'

const CHART_SERIES = [
  ['revenue', 'DOANH THU THUẦN', 'var(--chart-cyan)', 'var(--chart-coral)'],
  ['net_income', 'LỢI NHUẬN SAU THUẾ', 'var(--chart-green)', 'var(--chart-yellow)'],
  ['gross_profit', 'LỢI NHUẬN GỘP', 'var(--chart-blue)', 'var(--chart-red)'],
  ['operating_cash_flow', 'DÒNG TIỀN KINH DOANH', 'var(--chart-purple)', 'var(--chart-teal)'],
  ['free_cash_flow', 'DÒNG TIỀN TỰ DO', 'var(--chart-amber)', 'var(--chart-magenta)'],
  ['total_assets', 'TỔNG TÀI SẢN', 'var(--chart-slate)', 'var(--blue)'],
]

function number(value) {
  const parsed = Number(value)
  return value === null || value === undefined || !Number.isFinite(parsed) ? null : parsed
}

function compact(value) {
  const parsed = number(value)
  if (parsed === null) return '—'
  return new Intl.NumberFormat('vi-VN', { notation: 'compact', maximumFractionDigits: 1 }).format(parsed)
}

function points(values, width = 440, height = 170, padding = 14) {
  const valid = values.map(number)
  const present = valid.filter((item) => item !== null)
  if (!present.length) return ''
  const min = Math.min(...present)
  const max = Math.max(...present)
  const spread = max - min || 1
  return valid.map((value, index) => {
    if (value === null) return null
    const x = padding + index * ((width - padding * 2) / Math.max(valid.length - 1, 1))
    const y = height - padding - ((value - min) / spread) * (height - padding * 2)
    return `${x},${y}`
  }).filter(Boolean).join(' ')
}

function FinancialChartCard({ source, title, barColor, lineColor }) {
  const values = source?.values || []
  const raw = values.map((item) => number(item.value))
  const absoluteMax = Math.max(...raw.filter((item) => item !== null).map(Math.abs), 1)
  const growth = raw.map((value, index) => {
    const previous = raw[index - 4]
    return value === null || previous === null || previous === undefined || previous === 0
      ? null
      : ((value - previous) / Math.abs(previous)) * 100
  })
  const labels = values.map((item) => item.period)
  return <article className="bctc-chart-card">
    <header><strong>{title}</strong><span>{values.length} kỳ</span></header>
    <div className="bctc-combo-chart">
      <div className="bctc-chart-gridlines"><i /><i /><i /></div>
      <div className="bctc-bars">{raw.map((value, index) => <i key={`${labels[index]}-${index}`} style={{ '--height': `${Math.max(2, Math.abs(value || 0) / absoluteMax * 82)}%`, '--bar': barColor }} title={`${labels[index]}: ${compact(value)}`} />)}</div>
      <svg viewBox="0 0 440 170" preserveAspectRatio="none" aria-label={`${title} và tăng trưởng cùng kỳ`}><polyline points={points(growth)} style={{ stroke: lineColor }} /></svg>
    </div>
    <div className="bctc-chart-periods"><span>{labels[0] || '—'}</span><span>{labels[Math.floor(labels.length / 2)] || '—'}</span><span>{labels.at(-1) || '—'}</span></div>
    <footer><span><i style={{ '--legend': barColor }} />{title.toLowerCase()}</span><span><i className="is-line" style={{ '--legend': lineColor }} />Tăng trưởng YoY</span></footer>
  </article>
}

export function FinancialChartsView({ workspace }) {
  const series = new Map((workspace?.trend?.series || []).map((item) => [item.key, item]))
  return <section className="bctc-insight-surface">
    <div className="bctc-chart-toolbar"><div><BarChart3 /><strong>Bộ biểu đồ tài chính</strong><span>Dữ liệu báo cáo hợp nhất · theo quý</span></div><small>Thanh: giá trị tuyệt đối · Đường: tăng trưởng cùng kỳ</small></div>
    <div className="bctc-financial-chart-grid">{CHART_SERIES.map(([key, title, barColor, lineColor]) => <FinancialChartCard key={key} source={series.get(key)} title={title} barColor={barColor} lineColor={lineColor} />)}</div>
  </section>
}

function average(values, size) {
  if (values.length < size) return null
  return values.slice(-size).reduce((sum, value) => sum + value, 0) / size
}

function rsi(values, size = 14) {
  if (values.length <= size) return null
  const changes = values.slice(-(size + 1)).slice(1).map((value, index) => value - values.slice(-(size + 1))[index])
  const gains = changes.reduce((sum, value) => sum + Math.max(value, 0), 0) / size
  const losses = changes.reduce((sum, value) => sum + Math.max(-value, 0), 0) / size
  if (!losses) return 100
  return 100 - (100 / (1 + gains / losses))
}

export function TechnicalView({ marketContext, loading }) {
  const bars = (marketContext?.prices?.bars || []).slice(-220)
  const closes = bars.map((item) => number(item.close)).filter((item) => item !== null)
  const ma20Series = bars.map((_, index) => {
    const window = bars.slice(Math.max(0, index - 19), index + 1).map((item) => number(item.close)).filter((item) => item !== null)
    return window.length === 20 ? window.reduce((sum, value) => sum + value, 0) / 20 : null
  })
  const last = closes.at(-1)
  const ma20 = average(closes, 20)
  const ma50 = average(closes, 50)
  const rsi14 = rsi(closes)
  const volumes = bars.map((item) => number(item.volume) || 0)
  const volumeMax = Math.max(...volumes, 1)
  if (loading) return <InsightLoading label="Đang tải lịch sử giá và khối lượng" />
  if (!bars.length) return <Unavailable title="Chưa lấy được lịch sử giá" detail="Nguồn OHLCV hiện không phản hồi và cache chưa có dữ liệu cho mã này." />
  return <section className="bctc-insight-surface">
    <div className="bctc-technical-kpis">
      <Metric label="Giá đóng cửa" value={last?.toLocaleString('vi-VN') || '—'} />
      <Metric label="MA20" value={ma20?.toLocaleString('vi-VN', { maximumFractionDigits: 1 }) || '—'} tone={last >= ma20 ? 'up' : 'down'} />
      <Metric label="MA50" value={ma50?.toLocaleString('vi-VN', { maximumFractionDigits: 1 }) || '—'} tone={last >= ma50 ? 'up' : 'down'} />
      <Metric label="RSI 14" value={rsi14?.toFixed(1) || '—'} tone={rsi14 > 70 ? 'down' : rsi14 < 30 ? 'up' : ''} />
    </div>
    <article className="bctc-price-chart"><header><div><LineChart /><strong>Giá và xu hướng MA20</strong></div><span>{marketContext?.prices?.source || 'OHLCV cache'}</span></header><div className="bctc-price-plot"><svg viewBox="0 0 960 300" preserveAspectRatio="none"><polyline className="price" points={points(bars.map((item) => item.close), 960, 300, 20)} /><polyline className="average" points={points(ma20Series, 960, 300, 20)} /></svg></div><div className="bctc-volume-bars">{volumes.slice(-120).map((value, index) => <i key={`${bars.at(-120 + index)?.time || index}`} style={{ '--height': `${Math.max(2, value / volumeMax * 100)}%` }} />)}</div></article>
  </section>
}

function Metric({ label, value, tone = '' }) {
  return <div className={`bctc-technical-metric ${tone ? `is-${tone}` : ''}`}><span>{label}</span><strong>{value}</strong></div>
}

export function AnalysisView({ workspace }) {
  const alerts = workspace?.quality?.alerts || []
  return <section className="bctc-insight-surface bctc-analysis-grid">
    <article className="bctc-analysis-panel"><header><Gauge /><div><strong>Sức khỏe tài chính</strong><span>Thang điểm định lượng 0–100</span></div></header><div className="bctc-health-list">{Object.entries(workspace?.health?.radar || {}).map(([key, value]) => <div key={key}><span>{({ profitability: 'Sinh lời', growth: 'Tăng trưởng', efficiency: 'Hiệu quả', liquidity: 'Thanh khoản', leverage: 'Đòn bẩy', cash_quality: 'Dòng tiền' })[key] || key}</span><i><b style={{ '--value': `${Math.max(0, Math.min(100, number(value) || 0))}%` }} /></i><strong>{Math.round(number(value) || 0)}</strong></div>)}</div></article>
    <article className="bctc-analysis-panel"><header><AlertTriangle /><div><strong>Cảnh báo cần kiểm tra</strong><span>Suy ra từ BCTC, không phải khuyến nghị</span></div></header>{alerts.length ? <div className="bctc-alert-list">{alerts.map((alert) => <div key={alert.code}><AlertTriangle /><p><strong>{alert.title}</strong><span>{alert.detail}</span></p></div>)}</div> : <Unavailable compact title="Chưa kích hoạt cảnh báo" detail="Không đồng nghĩa doanh nghiệp không có rủi ro." />}</article>
    {(workspace?.ratio_groups || []).map((group) => <article className="bctc-analysis-panel" key={group.key}><header><ShieldCheck /><div><strong>{group.label}</strong><span>Kỳ báo cáo mới nhất</span></div></header><div className="bctc-ratio-list">{group.metrics.map((metric) => <div key={metric.key}><span>{metric.label}</span><strong>{metric.value === null ? '—' : `${Number(metric.value).toLocaleString('vi-VN', { maximumFractionDigits: 2 })}${metric.unit === '%' ? '%' : metric.unit === 'x' ? 'x' : ''}`}</strong></div>)}</div></article>)}
  </section>
}

function first(item, keys, fallback = '—') {
  for (const key of keys) if (item?.[key] !== null && item?.[key] !== undefined && item?.[key] !== '') return item[key]
  return fallback
}

export function GovernanceView({ marketContext, loading }) {
  if (loading) return <InsightLoading label="Đang tải hồ sơ quản trị doanh nghiệp" />
  const profile = marketContext?.profile || {}
  const officers = marketContext?.officers?.officers || []
  const shareholders = marketContext?.shareholders?.shareholders || []
  return <section className="bctc-insight-surface bctc-governance-grid">
    <article className="bctc-governance-profile"><header><Building2 /><div><strong>Hồ sơ doanh nghiệp</strong><span>Nguồn hồ sơ provider</span></div></header><dl><div><dt>Website</dt><dd>{first(profile, ['website'])}</dd></div><div><dt>Ngày niêm yết</dt><dd>{first(profile, ['listing_date', 'issue_date'])}</dd></div><div><dt>Vốn điều lệ</dt><dd>{compact(first(profile, ['charter_capital'], null))}</dd></div><div><dt>Địa chỉ</dt><dd>{first(profile, ['address'])}</dd></div></dl></article>
    <article className="bctc-governance-table"><header><UsersRound /><div><strong>Ban lãnh đạo</strong><span>{officers.length} hồ sơ</span></div></header>{officers.length ? <table><tbody>{officers.slice(0, 12).map((item, index) => <tr key={`${first(item, ['name', 'officer_name'])}-${index}`}><td>{first(item, ['name', 'officer_name'])}</td><td>{first(item, ['position', 'position_name', 'title'])}</td></tr>)}</tbody></table> : <Unavailable compact title="Chưa có dữ liệu lãnh đạo" detail="Provider chưa trả hồ sơ cho mã này." />}</article>
    <article className="bctc-governance-table is-wide"><header><UsersRound /><div><strong>Cơ cấu cổ đông</strong><span>{shareholders.length} cổ đông được công bố</span></div></header>{shareholders.length ? <table><thead><tr><th>Cổ đông</th><th>Số cổ phần</th><th>Tỷ lệ</th></tr></thead><tbody>{shareholders.slice(0, 15).map((item, index) => <tr key={`${first(item, ['name', 'share_holder'])}-${index}`}><td>{first(item, ['name', 'share_holder', 'shareholder_name'])}</td><td>{compact(first(item, ['shares_owned', 'share_own'], null))}</td><td>{first(item, ['ownership_percentage', 'share_own_percent'], '—')}{first(item, ['ownership_percentage', 'share_own_percent'], null) !== null ? '%' : ''}</td></tr>)}</tbody></table> : <Unavailable compact title="Chưa có cơ cấu cổ đông" detail="Không tạo dữ liệu thay thế khi nguồn chưa cung cấp." />}</article>
  </section>
}

export function DocumentsView({ ticker, workspace, onImported }) {
  const inputRef = useRef(null)
  const [uploadState, setUploadState] = useState({ status: 'idle', message: '' })
  async function upload(file) {
    if (!file) return
    setUploadState({ status: 'loading', message: `Đang tải ${file.name}` })
    try {
      const created = await uploadFinancialStatement({ file, ticker, reportType: 'auto' })
      await extractFinancialStatementUpload(created.upload_id)
      setUploadState({ status: 'success', message: 'Đã tiếp nhận và trích xuất tài liệu.' })
      onImported?.()
    } catch (error) {
      setUploadState({ status: 'error', message: error.message || 'Không xử lý được tài liệu.' })
    }
  }
  const periods = workspace?.statements?.balance?.periods || []
  return <section className="bctc-insight-surface bctc-documents-view">
    <article className="bctc-document-upload"><FileUp /><div><strong>Thêm báo cáo doanh nghiệp</strong><span>PDF, XLSX hoặc CSV · backend sẽ lưu nguồn và trích xuất khoản mục</span></div><button type="button" onClick={() => inputRef.current?.click()} disabled={uploadState.status === 'loading'}>{uploadState.status === 'loading' ? 'Đang xử lý…' : 'Chọn tài liệu'}</button><input ref={inputRef} type="file" accept=".pdf,.xlsx,.xls,.csv" hidden onChange={(event) => upload(event.target.files?.[0])} /></article>
    {uploadState.message && <div className={`bctc-upload-status is-${uploadState.status}`}>{uploadState.message}</div>}
    <article className="bctc-document-table"><header><Database /><div><strong>Kỳ dữ liệu đang lưu</strong><span>Nguồn {workspace?.data_provenance?.provider || '—'}</span></div></header><table><thead><tr><th>Kỳ báo cáo</th><th>Phạm vi</th><th>Trạng thái dữ liệu</th></tr></thead><tbody>{periods.map((period) => <tr key={period}><td>{period}</td><td>Hợp nhất</td><td><i />Đã chuẩn hóa</td></tr>)}</tbody></table></article>
    <div className="bctc-source-warning"><AlertTriangle /><p><strong>Chưa kết nối kho công bố chính thức</strong><span>Cần hợp đồng hoặc connector HOSE/HNX/SSC để tự động tải PDF, nghị quyết và báo cáo kiểm toán. Hệ thống không giả lập liên kết tài liệu.</span></p></div>
  </section>
}

function InsightLoading({ label }) {
  return <div className="bctc-insight-loading"><Database /><strong>{label}</strong></div>
}

function Unavailable({ title, detail, compact: isCompact = false }) {
  return <div className={`bctc-insight-empty ${isCompact ? 'is-compact' : ''}`}><Database /><strong>{title}</strong><span>{detail}</span></div>
}
