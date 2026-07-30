import { Fragment, useRef, useState } from 'react'
import {
  AlertTriangle, BarChart3, BookOpen, Building2, Check, CheckCircle2, ChevronDown, CircleAlert, CircleCheck,
  Database, FileUp, Gauge, GitCompareArrows, LineChart, Scale, ShieldCheck, Sparkles, TrendingUp,
  UsersRound, X,
} from 'lucide-react'

import {
  extractFinancialStatementUpload,
  fetchFinancialPeers,
  uploadFinancialStatement,
} from '../services/financialsApi'

const CHART_SERIES = [
  ['revenue', 'Doanh thu thuần'],
  ['net_income', 'Lợi nhuận sau thuế'],
  ['gross_profit', 'Lợi nhuận gộp'],
  ['operating_cash_flow', 'Dòng tiền kinh doanh'],
  ['free_cash_flow', 'Dòng tiền tự do'],
  ['total_assets', 'Tổng tài sản'],
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

function points(values, width = 440, height = 170, padding = 14, sharedDomain = null) {
  const valid = values.map(number)
  const present = sharedDomain || valid.filter((item) => item !== null)
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

function lineSegments(values, xFor, yFor) {
  const segments = []
  let current = []
  values.forEach((value, index) => {
    if (value === null) {
      if (current.length > 1) segments.push(current)
      current = []
      return
    }
    current.push(`${xFor(index)},${yFor(value)}`)
  })
  if (current.length > 1) segments.push(current)
  return segments
}

function FinancialChartCard({ source, title, periodMode }) {
  const [activeIndex, setActiveIndex] = useState(null)
  const values = source?.values || []
  const raw = values.map((item) => number(item.value))
  const lag = periodMode === 'year' ? 1 : 4
  const growth = raw.map((value, index) => {
    const previous = raw[index - lag]
    return value === null || previous === null || previous === undefined || previous === 0
      ? null
      : ((value - previous) / Math.abs(previous)) * 100
  })
  const labels = values.map((item) => item.period)
  const present = raw.filter((item) => item !== null)
  if (!present.length) {
    return <article className="bctc-chart-card is-empty">
      <header><div><strong>{title}</strong><span>Chưa có dữ liệu trong giai đoạn này</span></div></header>
      <div className="bctc-chart-empty"><BarChart3 /><span>Không có số liệu để lập biểu đồ</span></div>
    </article>
  }

  const chart = { width: 680, height: 250, left: 58, right: 54, top: 22, bottom: 40 }
  const plotWidth = chart.width - chart.left - chart.right
  const plotHeight = chart.height - chart.top - chart.bottom
  const minValue = Math.min(0, ...present)
  const maxValue = Math.max(0, ...present)
  const valueSpread = maxValue - minValue || Math.abs(maxValue) || 1
  const yValue = (value) => chart.top + ((maxValue - value) / valueSpread) * plotHeight
  const zeroY = yValue(0)
  const slotWidth = plotWidth / Math.max(values.length, 1)
  const barWidth = Math.min(26, slotWidth * .54)
  const xValue = (index) => chart.left + slotWidth * index + slotWidth / 2
  const growthPresent = growth.filter((item) => item !== null)
  const growthMin = Math.min(0, ...growthPresent)
  const growthMax = Math.max(0, ...growthPresent)
  const growthSpread = growthMax - growthMin || Math.abs(growthMax) || 1
  const yGrowth = (value) => chart.top + ((growthMax - value) / growthSpread) * plotHeight
  const growthPaths = lineSegments(growth, xValue, yGrowth)
  const latestIndex = raw.reduce((result, value, index) => value === null ? result : index, -1)
  const selectedIndex = activeIndex ?? latestIndex
  const selectedValue = raw[selectedIndex]
  const selectedGrowth = growth[selectedIndex]
  const selectedLabel = labels[selectedIndex]

  return <article className="bctc-chart-card">
    <header>
      <div><strong>{title}</strong><span>{values.length} kỳ · {periodMode === 'year' ? 'theo năm' : 'theo quý'}</span></div>
      <div className="bctc-chart-current">
        <span>{selectedLabel || '—'}</span>
        <strong>{compact(selectedValue)}</strong>
        <small className={selectedGrowth > 0 ? 'is-positive' : selectedGrowth < 0 ? 'is-negative' : ''}>
          {selectedGrowth === null || selectedGrowth === undefined ? 'Chưa đủ YoY' : `${selectedGrowth > 0 ? '+' : ''}${selectedGrowth.toFixed(1)}% YoY`}
        </small>
      </div>
    </header>
    <div className="bctc-combo-chart" onMouseLeave={() => setActiveIndex(null)}>
      <svg viewBox={`0 0 ${chart.width} ${chart.height}`} role="img" aria-label={`${title}: giá trị tuyệt đối và tăng trưởng cùng kỳ`}>
        {[0, .5, 1].map((ratio) => {
          const y = chart.top + plotHeight * ratio
          return <line key={ratio} className="bctc-chart-gridline" x1={chart.left} x2={chart.width - chart.right} y1={y} y2={y} />
        })}
        <line className="bctc-chart-zero" x1={chart.left} x2={chart.width - chart.right} y1={zeroY} y2={zeroY} />
        <text className="bctc-chart-axis" x={chart.left - 8} y={chart.top + 4} textAnchor="end">{compact(maxValue)}</text>
        <text className="bctc-chart-axis" x={chart.left - 8} y={zeroY + 4} textAnchor="end">0</text>
        {minValue < 0 ? <text className="bctc-chart-axis" x={chart.left - 8} y={chart.top + plotHeight} textAnchor="end">{compact(minValue)}</text> : null}
        {growthPresent.length ? <>
          <text className="bctc-chart-axis is-growth" x={chart.width - chart.right + 8} y={chart.top + 4}>{growthMax.toFixed(0)}%</text>
          <text className="bctc-chart-axis is-growth" x={chart.width - chart.right + 8} y={chart.top + plotHeight}>{growthMin.toFixed(0)}%</text>
        </> : null}
        {raw.map((value, index) => {
          if (value === null) return null
          const y = yValue(value)
          const height = Math.max(2, Math.abs(zeroY - y))
          return <rect
            key={`${labels[index]}-${index}`}
            className={`bctc-chart-bar ${value < 0 ? 'is-negative' : 'is-positive'} ${selectedIndex === index ? 'is-active' : ''}`}
            x={xValue(index) - barWidth / 2}
            y={value >= 0 ? y : zeroY}
            width={barWidth}
            height={height}
            rx="2"
            tabIndex="0"
            onMouseEnter={() => setActiveIndex(index)}
            onFocus={() => setActiveIndex(index)}
            onBlur={() => setActiveIndex(null)}
            aria-label={`${labels[index]}: ${compact(value)}${growth[index] === null ? '' : `, tăng trưởng ${growth[index].toFixed(1)} phần trăm`}`}
          />
        })}
        {growthPaths.map((segment, index) => <polyline key={index} className="bctc-chart-growth-line" points={segment.join(' ')} />)}
        {growth.map((value, index) => value === null ? null : <circle key={`${labels[index] || 'period'}-${index}`} className={`bctc-chart-growth-dot ${selectedIndex === index ? 'is-active' : ''}`} cx={xValue(index)} cy={yGrowth(value)} r={selectedIndex === index ? 4 : 2.5} />)}
        {labels.map((label, index) => {
          const show = values.length <= 8 || index === 0 || index === values.length - 1 || index === Math.floor(values.length / 2)
          return show ? <text key={`${label || 'period'}-${index}`} className="bctc-chart-period" x={xValue(index)} y={chart.height - 13} textAnchor="middle">{label}</text> : null
        })}
      </svg>
    </div>
    <footer><span><i className="is-value" />Giá trị báo cáo</span><span><i className="is-line" />Tăng trưởng YoY</span><span><i className="is-negative" />Giá trị âm</span></footer>
  </article>
}

export function FinancialChartsView({ workspace }) {
  const series = new Map((workspace?.trend?.series || []).map((item) => [item.key, item]))
  const periodMode = workspace?.controls?.period_mode || 'quarter'
  return <section className="bctc-insight-surface">
    <div className="bctc-chart-toolbar"><div><BarChart3 /><strong>Bộ biểu đồ tài chính</strong><span>Dữ liệu báo cáo hợp nhất · {periodMode === 'year' ? 'theo năm' : 'theo quý'}</span></div><small>Di chuột hoặc dùng Tab trên từng cột để xem số liệu</small></div>
    <div className="bctc-chart-reading-guide"><span><i className="is-value" />Cột: giá trị báo cáo</span><span><i className="is-growth" />Đường: tăng trưởng cùng kỳ</span><span><i className="is-risk" />Cột đỏ: giá trị âm</span><small>Hai trục được tính độc lập: giá trị bên trái · YoY bên phải</small></div>
    <div className="bctc-financial-chart-grid">{CHART_SERIES.map(([key, title]) => <FinancialChartCard key={key} source={series.get(key)} title={title} periodMode={periodMode} />)}</div>
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
  const sharedPriceDomain = [...bars.map((item) => number(item.close)), ...ma20Series].filter((item) => item !== null)
  if (loading) return <InsightLoading label="Đang tải lịch sử giá và khối lượng" />
  if (!bars.length) return <Unavailable title="Chưa lấy được lịch sử giá" detail="Nguồn OHLCV hiện không phản hồi và cache chưa có dữ liệu cho mã này." />
  return <section className="bctc-insight-surface">
    <div className="bctc-technical-kpis">
      <Metric label="Giá đóng cửa" value={last?.toLocaleString('vi-VN') || '—'} />
      <Metric label="MA20" value={ma20?.toLocaleString('vi-VN', { maximumFractionDigits: 1 }) || '—'} tone={last != null && ma20 != null ? (last >= ma20 ? 'up' : 'down') : ''} />
      <Metric label="MA50" value={ma50?.toLocaleString('vi-VN', { maximumFractionDigits: 1 }) || '—'} tone={last != null && ma50 != null ? (last >= ma50 ? 'up' : 'down') : ''} />
      <Metric label="RSI 14" value={rsi14?.toFixed(1) || '—'} tone={rsi14 > 70 ? 'down' : rsi14 < 30 ? 'up' : ''} />
    </div>
    <article className="bctc-price-chart">
      <header><div><LineChart /><strong>Giá và xu hướng MA20</strong></div><span>{marketContext?.prices?.source || 'OHLCV cache'}</span></header>
      <div className="bctc-price-plot">
        <svg viewBox="0 0 960 300" preserveAspectRatio="none">
          <polyline className="price" points={points(bars.map((item) => item.close), 960, 300, 20, sharedPriceDomain)} />
          <polyline className="average" points={points(ma20Series, 960, 300, 20, sharedPriceDomain)} />
        </svg>
      </div>
      <div className="bctc-volume-bars">
        {volumes.map((value, index) => {
          const barKey = `${bars[index]?.time || index}`
          return <i key={barKey} style={{ '--height': `${Math.max(2, value / volumeMax * 100)}%` }} />
        })}
      </div>
    </article>
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

const EVALUATION_STATUS = {
  good: { label: 'Tốt', icon: CircleCheck },
  watch: { label: 'Theo dõi', icon: CircleAlert },
  risk: { label: 'Rủi ro', icon: AlertTriangle },
  unavailable: { label: 'Thiếu dữ liệu', icon: Database },
}

function evaluationNumber(value, unit = '') {
  const parsed = number(value)
  if (parsed === null) return '—'
  const suffix = unit === '%' ? '%' : unit === 'x' ? 'x' : unit === 'ngày' ? ' ngày' : ''
  return `${parsed.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}${suffix}`
}

function StatusBadge({ status }) {
  const config = EVALUATION_STATUS[status] || EVALUATION_STATUS.unavailable
  const Icon = config.icon
  return <span className={`bctc-eval-status is-${status || 'unavailable'}`}><Icon />{config.label}</span>
}

function relativeStatus(value, reference, higherIsBetter, tolerance) {
  const current = number(value)
  const baseline = number(reference)
  if (current === null || baseline === null) return 'unavailable'
  const delta = (current - baseline) / Math.max(Math.abs(baseline), 1)
  if (Math.abs(delta) <= tolerance) return 'watch'
  return (delta > 0) === higherIsBetter ? 'good' : 'risk'
}

function previousComparablePeriod(period) {
  const raw = String(period || '')
  const matched = raw.match(/^(\d{4})(-Q[1-4])?$/)
  if (!matched) return 'Kỳ trước'
  return `${Number(matched[1]) - 1}${matched[2] || ''}`
}

function EvaluationReport({ evaluation, workspace }) {
  const categories = evaluation.categories || []
  const latestPeriod = workspace?.company?.latest_period || 'Kỳ hiện tại'
  const comparisonPeriod = previousComparablePeriod(latestPeriod)
  return <section className="bctc-health-report">
    <header>
      <div><strong>Báo cáo sức khỏe tài chính</strong><span>Giá trị · xu hướng cùng kỳ · vị thế so với nhóm đối chứng</span></div>
      <div className="bctc-health-report-legend"><StatusBadge status="good" /><StatusBadge status="watch" /><StatusBadge status="risk" /></div>
    </header>
    <div className="bctc-health-table-wrap">
      <table className="bctc-health-table">
        <caption className="bctc-sr-only">Bảng đánh giá chi tiết sức khỏe tài chính của doanh nghiệp</caption>
        <thead>
          <tr>
            <th rowSpan="2" scope="col">Chỉ tiêu</th>
            <th colSpan="3" scope="colgroup">Số liệu đối chiếu</th>
            <th colSpan="3" scope="colgroup">Đánh giá kết quả</th>
          </tr>
          <tr>
            <th scope="col">{latestPeriod}</th>
            <th scope="col">{comparisonPeriod}</th>
            <th scope="col">Trung vị đối chứng</th>
            <th scope="col">So với cùng kỳ</th>
            <th scope="col">So với đối chứng</th>
            <th scope="col">Tổng hợp</th>
          </tr>
        </thead>
        <tbody>
          {categories.map((category) => <Fragment key={category.key}>
            <tr className="bctc-health-group">
              <th colSpan="6" scope="rowgroup"><span>{category.label}</span><small>Trọng số {category.weight_pct}%</small></th>
              <td><span className="bctc-health-group-score">{category.score ?? '—'}/100</span></td>
            </tr>
            {category.metrics.map((metric) => {
              const trendStatus = relativeStatus(metric.value, metric.yoy_reference, metric.higher_is_better, .03)
              const peerStatus = relativeStatus(metric.value, metric.peer_median, metric.higher_is_better, .10)
              return <tr key={metric.key}>
                <th scope="row"><span>{metric.label}</span><small>{metric.evidence?.join(' · ') || 'Chưa đủ dữ liệu để đối chiếu'}</small></th>
                <td>{evaluationNumber(metric.value, metric.unit)}</td>
                <td>{evaluationNumber(metric.yoy_reference, metric.unit)}</td>
                <td>{evaluationNumber(metric.peer_median, metric.unit)}</td>
                <td><StatusBadge status={trendStatus} /></td>
                <td><StatusBadge status={peerStatus} /></td>
                <td><StatusBadge status={metric.status} /></td>
              </tr>
            })}
          </Fragment>)}
        </tbody>
      </table>
    </div>
  </section>
}

function EvaluationGuide() {
  return <section className="bctc-evaluation-guide" aria-label="Cách đọc kết quả đánh giá">
    <header><strong>Cách đọc kết quả</strong><span>Không dùng một tỷ số đơn lẻ để kết luận</span></header>
    <div className="bctc-evaluation-guide-grid">
      <article className="is-good"><StatusBadge status="good" /><p><strong>Tốt</strong> khi tín hiệu thuận chiếm ưu thế: cải thiện so với cùng kỳ, tốt hơn trung vị đối chứng hoặc đạt ngưỡng nền tảng phù hợp.</p></article>
      <article className="is-watch"><StatusBadge status="watch" /><p><strong>Theo dõi</strong> khi kết quả gần như đi ngang, tín hiệu cân bằng hoặc chênh lệch chưa đủ lớn để kết luận.</p></article>
      <article className="is-risk"><StatusBadge status="risk" /><p><strong>Rủi ro</strong> khi suy yếu so với cùng kỳ/đối chứng hoặc có dấu hiệu như thanh khoản dưới 1 lần, biên âm hay CFO không bao phủ LNST.</p></article>
    </div>
  </section>
}

function ComparisonTable({ comparison, ticker, peerTicker }) {
  const metrics = comparison?.metrics || []
  if (!metrics.length) return <Unavailable compact title="Chưa có dữ liệu so sánh" detail="Hãy nhập một mã có dữ liệu BCTC đã chuẩn hóa trong hệ thống." />
  return <div className="bctc-compare-table-wrap">
    <table className="bctc-compare-table">
      <thead><tr><th>Tiêu chí</th><th>{ticker}</th><th>{peerTicker}</th><th>Đánh giá tương đối</th></tr></thead>
      <tbody>{metrics.map((metric) => {
        const target = number(metric.ticker_value)
        const peer = number(metric.peer_median ?? metric.peer_avg)
        let leader = 'Không đủ dữ liệu'
        if (target !== null && peer !== null) {
          const targetWins = metric.higher_is_better ? target > peer : target < peer
          const tied = Math.abs(target - peer) <= Math.max(Math.abs(peer), 1) * .03
          leader = tied ? 'Tương đương' : targetWins ? `${ticker} tốt hơn` : `${peerTicker} tốt hơn`
        }
        const unit = metric.field?.includes('_pct') ? '%' : metric.field === 'debt_to_equity' || metric.field === 'current_ratio' || metric.field === 'ocf_to_net_income' || metric.field === 'asset_turnover' ? 'x' : ''
        return <tr key={metric.field}><th scope="row">{metric.label}</th><td>{evaluationNumber(target, unit)}</td><td>{evaluationNumber(peer, unit)}</td><td><span className={leader.includes(ticker) ? 'is-target' : leader.includes(peerTicker) ? 'is-peer' : ''}>{leader}</span></td></tr>
      })}</tbody>
    </table>
  </div>
}

const PIOTROSKI_CRITERIA_MAP = [
  { key: 'roa_positive', label: '1. ROA dương (> 0)', desc: 'Lợi nhuận sau thuế / Tổng tài sản mang dấu dương' },
  { key: 'ocf_positive', label: '2. Dòng tiền HĐKD dương (CFO > 0)', desc: 'Dòng tiền từ hoạt động kinh doanh dương' },
  { key: 'roa_improving', label: '3. ROA tăng trưởng', desc: 'ROA kỳ hiện tại cao hơn kỳ cùng kỳ năm trước' },
  { key: 'accruals_quality', label: '4. Chất lượng dồn tích (CFO > LNST)', desc: 'LNST được hỗ trợ thực tế bằng dòng tiền mặt HĐKD' },
  { key: 'leverage_decreasing', label: '5. Giảm đòn bẩy nợ', desc: 'Tỷ lệ Nợ vay/VCSH kỳ này giảm so với năm trước' },
  { key: 'liquidity_improving', label: '6. Tăng thanh khoản ngắn hạn', desc: 'Hệ số thanh toán hiện hành (Current Ratio) cải thiện' },
  { key: 'no_dilution', label: '7. Không pha loãng cổ phiếu', desc: 'Vốn chủ sở hữu & số lượng cổ phần bảo toàn' },
  { key: 'margin_improving', label: '8. Biên lợi nhuận gộp cải thiện', desc: 'Biên LN gộp cao hơn kỳ cùng kỳ năm trước' },
  { key: 'turnover_improving', label: '9. Vòng quay tài sản tăng', desc: 'Asset Turnover cao hơn cùng kỳ năm trước' },
]

const PEER_SUGGESTION_MAP = {
  HPG: ['HSG', 'NKG', 'TLH', 'SMC'],
  HSG: ['HPG', 'NKG', 'TLH'],
  NKG: ['HPG', 'HSG', 'TLH'],
  FPT: ['CMG', 'ELC', 'ITD', 'FOX'],
  VNM: ['MSN', 'MCH', 'QNS', 'KDC'],
  MWG: ['FRT', 'DGW', 'PET', 'PNJ'],
  VIC: ['VHM', 'VRE', 'NVL'],
  VHM: ['VIC', 'VRE', 'NVL', 'KDH'],
  VCB: ['BID', 'CTG', 'TCB', 'MBB'],
  TCB: ['VPB', 'MBB', 'ACB', 'VCB'],
}

function ExecutiveHighlights({ categories }) {
  const strengths = []
  const risks = []

  for (const cat of categories || []) {
    for (const m of cat.metrics || []) {
      if (m.status === 'good') {
        strengths.push({ label: m.label, value: evaluationNumber(m.value, m.unit), evidence: m.evidence?.[0] })
      } else if (m.status === 'risk') {
        risks.push({ label: m.label, value: evaluationNumber(m.value, m.unit), evidence: m.evidence?.[0] })
      }
    }
  }

  return (
    <div className="bctc-highlights-grid">
      <div className="bctc-highlight-card is-strengths">
        <h4><CheckCircle2 size={16} className="is-pos" /> Điểm mạnh nổi bật ({strengths.length})</h4>
        <ul>
          {strengths.slice(0, 4).map((item, idx) => (
            <li key={idx}>
              <strong>{item.label}:</strong> <span>{item.value}</span>
              {item.evidence && <small> — {item.evidence}</small>}
            </li>
          ))}
          {strengths.length === 0 && <li>Chưa ghi nhận điểm mạnh nổi bật.</li>}
        </ul>
      </div>

      <div className="bctc-highlight-card is-risks">
        <h4><AlertTriangle size={16} className="is-neg" /> Cảnh báo & rủi ro trọng yếu ({risks.length})</h4>
        <ul>
          {risks.slice(0, 4).map((item, idx) => (
            <li key={idx}>
              <strong>{item.label}:</strong> <span>{item.value}</span>
              {item.evidence && <small> — {item.evidence}</small>}
            </li>
          ))}
          {risks.length === 0 && <li>Tất cả chỉ số nằm trong ngưỡng an toàn/theo dõi.</li>}
        </ul>
      </div>
    </div>
  )
}

function PiotroskiBreakdown({ piotroski }) {
  const [showDetails, setShowDetails] = useState(false)
  const details = piotroski?.details || {}
  const score = piotroski?.score ?? 0

  return (
    <div className="bctc-piotroski-box">
      <div className="bctc-model-header">
        <div>
          <ShieldCheck size={20} style={{ color: 'var(--accent)' }} />
          <div>
            <strong>Piotroski F-Score</strong>
            <span>Mô hình đánh giá 9 tiêu chí sức khỏe tài chính nền tảng</span>
          </div>
        </div>
        <div className="bctc-model-score">
          <strong>{score}<small>/9</small></strong>
          <span className={`bctc-badge is-${score >= 7 ? 'good' : score <= 3 ? 'risk' : 'watch'}`}>
            {score >= 7 ? 'Tốt (7-9)' : score <= 3 ? 'Cảnh báo (0-3)' : 'Trung bình (4-6)'}
          </span>
        </div>
      </div>

      <button
        type="button"
        className="bctc-toggle-details"
        onClick={() => setShowDetails(!showDetails)}
      >
        {showDetails ? 'Thu gọn bóc tách 9 tiêu chí' : 'Xem bóc tách 9 tiêu chí Piotroski'} <ChevronDown className={showDetails ? 'is-open' : ''} />
      </button>

      {showDetails && (
        <div className="bctc-piotroski-grid">
          {PIOTROSKI_CRITERIA_MAP.map((item) => {
            const passed = details[item.key] === true
            return (
              <div key={item.key} className={`bctc-piotroski-item ${passed ? 'is-pass' : 'is-fail'}`}>
                <span className="bctc-piotroski-icon">{passed ? <Check size={12} /> : <X size={12} />}</span>
                <div>
                  <strong>{item.label}</strong>
                  <small>{item.desc}</small>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function AltmanGauge({ altman }) {
  const zScore = number(altman?.score) ?? 0
  const zone = altman?.zone || 'grey'

  // Map zScore (0..5) to percentage (0..100)
  const pct = Math.min(100, Math.max(0, (zScore / 5) * 100))

  return (
    <div className="bctc-altman-box">
      <div className="bctc-model-header">
        <div>
          <AlertTriangle size={20} style={{ color: zone === 'safe' ? 'var(--pos)' : zone === 'distress' ? 'var(--neg)' : 'var(--warn)' }} />
          <div>
            <strong>Altman Z-Score</strong>
            <span>Thước đo nguy cơ kiệt quệ tài chính (Corporate Bankruptcy)</span>
          </div>
        </div>
        <div className="bctc-model-score">
          <strong>{zScore ? zScore.toFixed(2) : '—'}</strong>
          <span className={`bctc-badge is-${zone === 'safe' ? 'good' : zone === 'distress' ? 'risk' : 'watch'}`}>
            {zone === 'safe' ? 'An toàn (>2.99)' : zone === 'distress' ? 'Nguy cơ cao (<1.81)' : 'Vùng xám (1.81-2.99)'}
          </span>
        </div>
      </div>

      <div className="bctc-z-meter">
        <div className="bctc-z-track">
          <div className="bctc-z-zone is-distress">Distress (&lt;1.81)</div>
          <div className="bctc-z-zone is-grey">Vùng xám (1.81-2.99)</div>
          <div className="bctc-z-zone is-safe">An toàn (&gt;2.99)</div>
        </div>
        {zScore > 0 && (
          <div className="bctc-z-pin" style={{ left: `${pct}%` }}>
            ▼ Z = {zScore.toFixed(2)}
          </div>
        )}
      </div>
    </div>
  )
}

export function EvaluationView({ workspace, ticker }) {
  const evaluation = workspace?.evaluation || {}
  const overall = evaluation.overall || {}
  const categories = evaluation.categories || []
  const defaultPeer = workspace?.peers?.peer_tickers?.[0] || ''
  const [peerInput, setPeerInput] = useState(defaultPeer)
  const [peerTicker, setPeerTicker] = useState(defaultPeer)
  const [comparison, setComparison] = useState(null)
  const [compareState, setCompareState] = useState({ status: 'idle', message: '' })

  const suggestions = PEER_SUGGESTION_MAP[ticker] || workspace?.peers?.peer_tickers || []

  async function runCompare(symbol) {
    const targetSymbol = (symbol || peerInput).trim().toUpperCase()
    if (!targetSymbol || targetSymbol === ticker) {
      setCompareState({ status: 'error', message: 'Nhập một mã khác doanh nghiệp hiện tại.' })
      return
    }
    setPeerInput(targetSymbol)
    setCompareState({ status: 'loading', message: '' })
    try {
      const payload = await fetchFinancialPeers(ticker, targetSymbol)
      setPeerTicker(targetSymbol)
      setComparison(payload)
      setCompareState({ status: 'ready', message: '' })
    } catch (error) {
      setComparison(null)
      setCompareState({ status: 'error', message: error.message || 'Không tải được dữ liệu so sánh.' })
    }
  }

  function handleFormSubmit(event) {
    event.preventDefault()
    runCompare(peerInput)
  }

  return <section className="bctc-insight-surface bctc-evaluation">
    {/* Hero section */}
    <header className="bctc-evaluation-hero">
      <div className="bctc-evaluation-score">
        <span>Điểm sàng lọc BCTC</span>
        <strong>{overall.score ?? '—'}<small>/100</small></strong>
        <StatusBadge status={overall.status} />
      </div>
      <div className="bctc-evaluation-summary">
        <span className="bctc-report-kicker">ĐÁNH GIÁ ĐA TIÊU CHÍ TOÀN DIỆN</span>
        <h2>{workspace?.company?.name || ticker}</h2>
        <p>Tổng hợp sức khỏe tài chính, xu hướng cùng kỳ và vị thế tương đối với doanh nghiệp so sánh. Độ phủ dữ liệu {overall.coverage_pct ?? 0}% · độ tin cậy {({ high: 'cao', medium: 'trung bình', low: 'thấp' })[overall.confidence] || 'chưa xác định'}.</p>
        <div className="bctc-evaluation-notice"><Scale />Đây là công cụ sàng lọc và học tập, không phải khuyến nghị mua hoặc bán.</div>
      </div>
    </header>

    {/* Executive Highlights: Điểm mạnh vs Cảnh báo rủi ro */}
    <ExecutiveHighlights categories={categories} />

    {/* Guide & Detailed Multi-Criteria Report */}
    <EvaluationGuide />
    <EvaluationReport evaluation={evaluation} workspace={workspace} />

    {/* Advanced Financial Models: Piotroski F-Score & Altman Z-Score */}
    <div className="bctc-models-wrapper">
      <PiotroskiBreakdown piotroski={evaluation.models?.piotroski_f} />
      <AltmanGauge altman={evaluation.models?.altman_z} />
    </div>

    {/* Company Comparison Section */}
    <section className="bctc-company-compare">
      <header><GitCompareArrows /><div><strong>So sánh hai doanh nghiệp</strong><span>Cùng bộ chỉ tiêu, ưu tiên doanh nghiệp cùng ngành</span></div></header>
      <form onSubmit={handleFormSubmit}>
        <label><span className="bctc-sr-only">Mã doanh nghiệp so sánh</span><input value={peerInput} onChange={(event) => setPeerInput(event.target.value.toUpperCase())} placeholder="Ví dụ: FPT" maxLength={20} /></label>
        <button type="submit" disabled={compareState.status === 'loading'}>{compareState.status === 'loading' ? 'Đang so sánh…' : 'So sánh'}</button>
      </form>

      {/* Peer suggestion chips */}
      {suggestions.length > 0 && (
        <div className="bctc-peer-chips">
          <span>Gợi ý đối thủ cùng ngành:</span>
          {suggestions.map((p) => (
            <button key={p} type="button" className="bctc-chip" onClick={() => runCompare(p)}>
              {p}
            </button>
          ))}
        </div>
      )}

      {compareState.status === 'error' && <p className="bctc-compare-error">{compareState.message}</p>}
      {comparison && <ComparisonTable comparison={comparison} ticker={ticker} peerTicker={peerTicker} />}
    </section>

    {/* Methodology Details */}
    <details className="bctc-evaluation-method">
      <summary><BookOpen />Phương pháp, nguồn tham khảo và giới hạn</summary>
      <p>{evaluation.methodology?.description}</p>
      <div>{(evaluation.methodology?.sources || []).map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.title}</a>)}</div>
      <ul>{(evaluation.methodology?.limitations || []).map((item) => <li key={item}>{item}</li>)}</ul>
    </details>
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
