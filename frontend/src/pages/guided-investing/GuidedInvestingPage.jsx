import { useEffect, useMemo, useState } from 'react'

import {
  fetchBalanceSheetStrength,
  fetchFinancialAnalysis,
  fetchFinancialPeers,
  fetchFinancialQualityCharts,
  fetchFinancialStatus,
} from '../../modules/financials'
import { trackAnalyticsEvent } from '../../shared/analytics/trackEvent'
import './guided-investing.css'
import './bctc.css'

const DEFAULT_TICKER = 'FPT'
const REVENUE_INCOME_METRICS = [
  { key: 'revenue', label: 'Doanh thu thuần', color: '#16a16f', type: 'bar', scale: 'left', formatValue: formatCompactNumber },
  { key: 'net_income', label: 'LNST', color: '#1f4e79', type: 'bar', scale: 'left', formatValue: formatCompactNumber },
  { key: 'net_margin', label: 'Biên lợi nhuận ròng', color: '#f0a202', type: 'line', scale: 'right', formatValue: formatPercent },
]
const DEBT_EQUITY_METRICS = [
  { key: 'debt', label: 'Nợ vay', color: 'var(--bctc-debt)' },
  { key: 'equity', label: 'Vốn chủ', color: 'var(--bctc-equity)' },
]
const MARGIN_METRICS = [
  { key: 'gross_margin', label: 'Biên gộp', color: '#16a16f', type: 'line', formatValue: formatPercent },
  { key: 'operating_margin', label: 'Biên HĐKD', color: '#2f74d0', type: 'line', formatValue: formatPercent },
  { key: 'net_margin', label: 'Biên ròng', color: '#7b61d9', type: 'line', formatValue: formatPercent },
]

export default function GuidedInvestingPage({ sessionId, onBack }) {
  const [ticker, setTicker] = useState(DEFAULT_TICKER)
  const [peersText, setPeersText] = useState('')
  const [mode, setMode] = useState('year')
  const [analysis, setAnalysis] = useState(null)
  const [qualityCharts, setQualityCharts] = useState(null)
  const [balanceSheetStrength, setBalanceSheetStrength] = useState(null)
  const [peerResult, setPeerResult] = useState(null)
  const [providerStatus, setProviderStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [peerLoading, setPeerLoading] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => {
    void bootstrap()
  }, [])

  async function bootstrap() {
    setLoading(true)
    setError('')
    try {
      const [statusPayload] = await Promise.all([
        fetchFinancialStatus().catch(() => null),
      ])
      setProviderStatus(statusPayload)
      await runAnalysis({ refresh: false, tickerValue: ticker, silent: true })
    } catch (err) {
      setError(err.message || 'Không tải được dữ liệu BCTC.')
    } finally {
      setLoading(false)
    }
  }

  async function runAnalysis({ refresh = false, tickerValue = ticker, silent = false } = {}) {
    const normalizedTicker = (tickerValue || '').toUpperCase().trim()
    if (!normalizedTicker) {
      setError('Vui lòng nhập ticker trước khi phân tích.')
      return
    }
    if (!silent) {
      setStatus(`Đang phân tích BCTC cho ${normalizedTicker}...`)
      setError('')
      setLoading(true)
    }
    try {
      const [payload, chartPayload, balancePayload] = await Promise.all([
        fetchFinancialAnalysis(normalizedTicker, { refresh }),
        fetchFinancialQualityCharts(normalizedTicker, { refresh }).catch(() => null),
        fetchBalanceSheetStrength(normalizedTicker, { refresh }).catch(() => null),
      ])
      setAnalysis(payload)
      setQualityCharts(chartPayload)
      setBalanceSheetStrength(balancePayload)
      const nextMode = inferDefaultMode(payload)
      if (nextMode) setMode(nextMode)
      setTicker(normalizedTicker)
      await runPeerCompare({ tickerValue: normalizedTicker, silent: true })
      setStatus(`Đã cập nhật phân tích cho ${normalizedTicker}.`)
      trackAnalyticsEvent({
        event_name: 'financial_analysis_loaded',
        module: 'guided_investing',
        surface: 'guided_investing',
        session_id: sessionId || undefined,
        properties: {
          ticker: normalizedTicker,
          refresh,
          trend_points: payload?.trends?.length || 0,
        },
      })
    } catch (err) {
      setError(err.message || 'Không lấy được phân tích BCTC.')
      setStatus('')
    } finally {
      if (!silent) setLoading(false)
    }
  }

  async function runPeerCompare({ tickerValue = ticker, silent = false } = {}) {
    const normalizedTicker = (tickerValue || '').toUpperCase().trim()
    if (!normalizedTicker) return
    if (!silent) {
      setPeerLoading(true)
      setStatus(`Đang so sánh peer cho ${normalizedTicker}...`)
    }
    try {
      const payload = await fetchFinancialPeers(normalizedTicker, peersText)
      setPeerResult(payload)
      if (!silent) setStatus(`Đã cập nhật peer compare cho ${normalizedTicker}.`)
      trackAnalyticsEvent({
        event_name: 'financial_peer_compare_loaded',
        module: 'guided_investing',
        surface: 'guided_investing',
        session_id: sessionId || undefined,
        properties: {
          ticker: normalizedTicker,
          peer_count: payload?.peer_tickers?.length || 0,
        },
      })
    } catch (err) {
      if (!silent) {
        setError(err.message || 'Không tải được peer compare.')
        setStatus('')
      }
      setPeerResult(null)
    } finally {
      if (!silent) setPeerLoading(false)
    }
  }

  const trendViews = useMemo(() => buildTrendViews(analysis), [analysis])
  const trendRows = trendViews[mode] || []
  const modeOptions = useMemo(
    () => Object.entries(trendViews).filter(([, rows]) => rows.length > 0).map(([key]) => key),
    [trendViews],
  )
  const healthRows = useMemo(() => buildHealthRows(analysis), [analysis])
  const dashboard = useMemo(
    () => buildDashboardModel(analysis, trendRows, peerResult, qualityCharts, balanceSheetStrength),
    [analysis, trendRows, peerResult, qualityCharts, balanceSheetStrength],
  )

  if (loading && !analysis) {
    return (
      <section className="bctc-page bctc-page--loading">
        <p className="bctc-eyebrow">Financial Statement Analysis</p>
        <h1>Đang dựng workspace phân tích BCTC...</h1>
      </section>
    )
  }

  return (
    <section className="bctc-page">
      <header className="bctc-topbar">
        <div>
          <h1>Phân tích BCTC</h1>
          <p>Đánh giá toàn diện hiệu quả tài chính và sức khỏe doanh nghiệp.</p>
        </div>
        <div className="bctc-topbar__actions">
          {onBack ? <button type="button" className="bctc-icon-btn" onClick={onBack}>Home</button> : null}
          <button type="button" className="bctc-btn bctc-btn--secondary" onClick={() => void runAnalysis({ refresh: true })}>
            Refresh dữ liệu
          </button>
          <button type="button" className="bctc-btn" onClick={() => void runAnalysis({ refresh: false })}>
            Phân tích BCTC
          </button>
        </div>
      </header>

      <section className="bctc-command-grid">
        <article className="bctc-company-card">
          <div className="bctc-company-card__identity">
            <div className="bctc-logo" aria-hidden="true">
              {(analysis?.ticker || ticker || 'NS').slice(0, 3)}
            </div>
            <div>
              <p className="bctc-eyebrow">Northstar Finance</p>
              <h2>{dashboard.companyName}</h2>
              <span>{analysis?.ticker || ticker} · {analysis?.industry || 'Ngành chưa xác định'}</span>
            </div>
          </div>
          <div className="bctc-controls">
            <label>
              Ticker
              <input
                value={ticker}
                onChange={(event) => setTicker(event.target.value.toUpperCase())}
                placeholder="Ví dụ: FPT"
              />
            </label>
            <label>
              Peer tickers
              <input
                value={peersText}
                onChange={(event) => setPeersText(event.target.value.toUpperCase())}
                placeholder="Ví dụ: CMG,DGW,MWG"
              />
            </label>
            <label>
              Kỳ hiển thị
              <select value={mode} onChange={(event) => setMode(event.target.value)}>
                {modeOptions.map((item) => (
                  <option key={item} value={item}>{modeLabel(item)}</option>
                ))}
              </select>
            </label>
            <button type="button" className="bctc-btn bctc-btn--secondary" onClick={() => void runPeerCompare()}>
              {peerLoading ? 'Đang so sánh...' : 'So sánh peers'}
            </button>
          </div>
          <div className="bctc-company-meta">
            <MetricBox label="Sàn" value={dashboard.exchange} />
            <MetricBox label="Kỳ báo cáo" value={analysis?.latest_period || 'n/a'} />
            <MetricBox label="Nguồn" value={analysis?.source || providerStatus?.provider || 'n/a'} />
            <MetricBox label="Đơn vị" value={dashboard.unit} />
          </div>
        </article>

        <article className="bctc-ai-summary">
          <div>
            <p className="bctc-eyebrow">AI Financial Summary</p>
            <h2>{dashboard.aiTitle}</h2>
          </div>
          <ul>
            {dashboard.summaryBullets.map((item) => (
              <li key={item.text} className={`bctc-ai-summary__item bctc-ai-summary__item--${item.tone}`}>
                <span>{item.tone === 'warn' ? '!' : '↑'}</span>
                <p>{item.text}</p>
              </li>
            ))}
          </ul>
        </article>
      </section>

      {status ? <p className="bctc-state">{status}</p> : null}
      {error ? <p className="bctc-state bctc-state--error">{error}</p> : null}

      {analysis ? (
        <>
          <section className="bctc-kpi-strip">
            {dashboard.kpis.map((item, index) => (
              <article key={item.label} className={`bctc-kpi ${item.tone ? `bctc-kpi--${item.tone}` : ''}`}>
                <div className="bctc-kpi__icon">{item.icon}</div>
                <div>
                  <p>{item.label}</p>
                  <h3>{item.value}</h3>
                  <span>{item.note}</span>
                </div>
                <Sparkline tone={item.tone} values={item.sparkValues} />
              </article>
            ))}
          </section>

          <section className="bctc-dashboard-grid">
            <article className="bctc-panel bctc-panel--health">
              <header>
                <h2>Financial Health Score</h2>
                <p>Score tổng hợp từ tăng trưởng, sinh lời, thanh khoản, đòn bẩy và dòng tiền.</p>
              </header>
              <div className="bctc-health-layout">
                <HealthScoreGauge score={dashboard.healthScore} tone={dashboard.healthTone} />
                <HealthRadar rows={healthRows} />
                <div className="bctc-health-bars">
                  {healthRows.map((row) => (
                    <div key={row.label} className="bctc-health-row">
                      <div>
                        <strong>{row.label}</strong>
                        <small>{row.value}/100</small>
                      </div>
                      <div className="bctc-health-track">
                        <i style={{ width: `${row.value}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bctc-tag-row">
                {dashboard.strengthTags.map((item) => <span key={item}>{item}</span>)}
              </div>
            </article>

            <article className="bctc-chart-card bctc-panel--revenue">
              <header className="bctc-panel-head">
                <div>
                  <h2>Xu hướng Doanh thu & LNST</h2>
                  <p>Đọc tăng trưởng và độ ổn định lợi nhuận qua các kỳ gần nhất.</p>
                </div>
                <span>{modeLabel(mode)}</span>
              </header>
              <MetricTrendChart
                rows={trendRows}
                metrics={REVENUE_INCOME_METRICS}
                formatValue={formatCompactNumber}
                height={218}
                showEndpointLabels
              />
            </article>

            <article className="bctc-chart-card bctc-panel--margin">
              <header className="bctc-panel-head">
                <div>
                  <h2>Phân tích biên lợi nhuận</h2>
                  <p>Biên ròng, biên hoạt động và biên gộp nếu dữ liệu có sẵn.</p>
                </div>
                <span>{analysis?.latest_period || 'Latest'}</span>
              </header>
              <MetricTrendChart
                rows={dashboard.marginRows}
                metrics={MARGIN_METRICS}
                formatValue={formatPercent}
                height={218}
                showEndpointLabels
              />
              <MarginAnalysisDetails data={dashboard.marginAnalysis} />
            </article>

            <article className="bctc-panel bctc-panel--balance">
              <header>
                <h2>Sức mạnh Bảng cân đối kế toán</h2>
                <p>Tài sản, nguồn vốn và chất lượng cấu trúc vốn theo dữ liệu thật.</p>
              </header>
              <BalanceSheetStrengthCard data={dashboard.balanceSheetStrength} fallbackItems={dashboard.balanceItems} fallbackTotal={dashboard.balanceTotal} />
            </article>

            <article className="bctc-panel bctc-panel--cashflow">
              <header>
                <h2>Chất lượng dòng tiền</h2>
                <p>So sánh CFO, CFI, CFF và FCF để đánh giá chất lượng lợi nhuận.</p>
              </header>
              <CashFlowQuality data={dashboard.cashFlow} />
            </article>

            <article className="bctc-panel bctc-panel--liquidity">
              <header>
                <h2>Đòn bẩy & Thanh khoản</h2>
                <p>Khả năng chịu đựng nợ và áp lực vốn lưu động.</p>
              </header>
              <div className="bctc-mini-metric-grid">
                {dashboard.leverageMetrics.map((item) => (
                  <div key={item.label} className={`bctc-mini-metric bctc-mini-metric--${item.tone}`}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                    <em>{item.note}</em>
                  </div>
                ))}
              </div>
            </article>

            <article className="bctc-panel bctc-panel--dupont">
              <header>
                <h2>DuPont Analysis</h2>
                <p>Tách ROE thành biên lợi nhuận, vòng quay tài sản và hệ số đòn bẩy.</p>
              </header>
              <DupontCard dupont={dashboard.dupont} />
            </article>

            <article className="bctc-panel bctc-panel--flags">
              <header>
                <h2>Red Flags & Điểm cần lưu ý</h2>
                <p>Các câu hỏi này giúp kiểm tra lại thesis trước khi kết luận.</p>
              </header>
              {analysis.flags?.length ? (
                <ul className="bctc-flag-list">
                  {analysis.flags.slice(0, 5).map((flag) => (
                    <li key={`${flag.level}-${flag.title}`} className={`bctc-flag bctc-flag--${(flag.level || '').toLowerCase()}`}>
                      <strong>{flag.title}</strong>
                      <p>{flag.detail}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="bctc-muted">Chưa có flag nổi bật ở lần chạy hiện tại.</p>
              )}
              <div className="bctc-check-questions">
                <h3>Câu hỏi cần kiểm tra</h3>
                {dashboard.checkQuestions.map((item) => <p key={item}>{item}</p>)}
              </div>
            </article>

            <article className="bctc-panel bctc-panel--peer">
              <header className="bctc-panel-head">
                <div>
                  <h2>So sánh với doanh nghiệp cùng ngành</h2>
                  <p>Đặt chỉ số của {analysis.ticker} cạnh trung bình peer để tránh nhìn một mã cô lập.</p>
                </div>
                <span>{peerLoading ? 'Syncing' : 'Ready'}</span>
              </header>
              {dashboard.peerRows.length ? (
                <div className="bctc-peer-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Doanh nghiệp</th>
                        <th>Doanh thu</th>
                        <th>Biên ròng</th>
                        <th>ROE</th>
                        <th>Debt / Equity</th>
                        <th>CFO Margin</th>
                        <th>Đánh giá so với ngành</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.peerRows.map((metric) => {
                        const tone = metric.tone
                        return (
                          <tr key={metric.company} className={`${metric.selected ? 'is-selected' : ''} ${tone ? `bctc-peer-row--${tone}` : ''}`}>
                            <td>{metric.company}</td>
                            <td>{metric.revenueGrowth}</td>
                            <td>{metric.netMargin}</td>
                            <td>{metric.roe}</td>
                            <td>{metric.debtToEquity}</td>
                            <td>{metric.cfoMargin}</td>
                            <td>{metric.assessment}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="bctc-muted">Chưa có peer compare. Bấm “So sánh peers” để tải.</p>
              )}
            </article>

            <article className="bctc-panel bctc-panel--ask">
              <header className="bctc-panel-head">
                <div>
                  <h2>Ask AI about this company</h2>
                  <p>Gợi ý câu hỏi dựa trên dữ liệu BCTC hiện có.</p>
                </div>
                <span>Beta</span>
              </header>
              <div className="bctc-ask-grid">
                {dashboard.aiQuestions.map((item) => (
                  <button key={item} type="button">{item}</button>
                ))}
              </div>
              <div className="bctc-ask-actions">
                <button type="button" className="bctc-btn">Mở Analyst</button>
                <button type="button" className="bctc-btn bctc-btn--secondary">Giải thích đơn giản</button>
              </div>
            </article>
          </section>
        </>
      ) : null}
    </section>
  )
}

function modeLabel(mode) {
  if (mode === 'quarter') return 'Theo quý'
  if (mode === 'month') return 'Theo tháng'
  if (mode === 'period') return 'Theo kỳ'
  return 'Theo năm'
}

function inferDefaultMode(analysis) {
  const views = buildTrendViews(analysis)
  if (views.year.length) return 'year'
  if (views.quarter.length) return 'quarter'
  if (views.month.length) return 'month'
  if (views.period.length) return 'period'
  return 'year'
}

function buildTrendViews(analysis) {
  const periods = [...(analysis?.periods || [])]
  const sorted = periods
    .slice()
    .sort((a, b) => {
      const ay = Number(a.year || 0)
      const by = Number(b.year || 0)
      if (ay !== by) return ay - by
      const aq = Number(a.quarter || 0)
      const bq = Number(b.quarter || 0)
      if (aq !== bq) return aq - bq
      return String(a.period || '').localeCompare(String(b.period || ''))
    })
    .map((item) => ({
      label: normalizePeriodLabel(item),
      revenue: toNumber(item.revenue),
      net_income: toNumber(item.net_income),
      net_margin: toNumber(item.net_margin_pct) ?? (toNumber(item.revenue) ? (toNumber(item.net_income) / toNumber(item.revenue)) * 100 : null),
      debt: toNumber(item.debt ?? item.total_liabilities),
      equity: toNumber(item.equity),
      year: item.year,
      quarter: item.quarter,
      period: item.period,
    }))

  const byQuarter = sorted.filter((item) => item.year && item.quarter)

  const byMonth = sorted.filter((item) => /\d{4}[-/]\d{1,2}/.test(String(item.period || '')))

  const byYearMap = new Map()
  for (const point of sorted) {
    if (!point.year) continue
    const key = String(point.year)
    const existing = byYearMap.get(key) || {
      label: key,
      revenue: 0,
      net_income: 0,
      debt: null,
      equity: null,
      year: point.year,
      quarter: null,
      period: key,
      _rank: -1,
    }
    existing.revenue = safeAdd(existing.revenue, point.revenue)
    existing.net_income = safeAdd(existing.net_income, point.net_income)
    existing.net_margin = existing.revenue ? (existing.net_income / existing.revenue) * 100 : null
    const pointRank = Number(point.quarter || 0)
    if (pointRank >= existing._rank) {
      existing.debt = point.debt
      existing.equity = point.equity
      existing._rank = pointRank
    }
    byYearMap.set(key, existing)
  }
  const byYear = [...byYearMap.values()]
    .sort((a, b) => Number(a.year || 0) - Number(b.year || 0))
    .map(({ _rank, ...item }) => item)

  const trends = [...(analysis?.trends || [])]
    .map((item) => ({
      label: item.period || '-',
      revenue: toNumber(item.revenue),
      net_income: toNumber(item.net_income),
      net_margin: toNumber(item.net_margin_pct),
      debt: toNumber(item.debt_to_equity),
      equity: toNumber(item.current_ratio),
      year: undefined,
      quarter: undefined,
      period: item.period || '',
    }))

  return {
    year: byYear,
    quarter: byQuarter,
    month: byMonth,
    period: trends.length ? trends : sorted,
  }
}

function normalizePeriodLabel(item) {
  if (item.year && item.quarter) return `${item.year} Q${item.quarter}`
  if (item.year && !item.quarter) return String(item.year)
  return String(item.period || '-')
}

function buildMetricCards(analysis) {
  const summary = analysis?.summary || {}
  return [
    {
      label: 'Doanh thu YoY',
      value: formatPercent(summary.revenue_growth_yoy_pct),
      note: 'Tăng trưởng doanh thu so với cùng kỳ.',
      tone: trendTone(summary.revenue_growth_yoy_pct),
    },
    {
      label: 'Lợi nhuận YoY',
      value: formatPercent(summary.net_income_growth_yoy_pct),
      note: 'Động lực lợi nhuận ròng.',
      tone: trendTone(summary.net_income_growth_yoy_pct),
    },
    {
      label: 'ROE',
      value: formatPercent(summary.roe_pct),
      note: 'Hiệu quả vốn chủ sở hữu.',
      tone: scoreTone(summary.roe_pct, 10, 16),
    },
    {
      label: 'Debt/Equity',
      value: formatMaybeNumber(summary.debt_to_equity),
      note: 'Đòn bẩy tài chính.',
      tone: reverseScoreTone(summary.debt_to_equity, 1.2, 0.7),
    },
  ]
}

function buildHealthRows(analysis) {
  const radar = analysis?.health_radar || {}
  return [
    { label: 'Profitability', value: sanitizeScore(radar.profitability) },
    { label: 'Growth', value: sanitizeScore(radar.growth) },
    { label: 'Efficiency', value: sanitizeScore(radar.efficiency) },
    { label: 'Liquidity', value: sanitizeScore(radar.liquidity) },
    { label: 'Leverage', value: sanitizeScore(radar.leverage) },
    { label: 'Cash quality', value: sanitizeScore(radar.cash_quality) },
  ]
}

function sanitizeScore(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 0
  return Math.max(0, Math.min(100, Math.round(numeric)))
}

function buildAttentionRows(analysis) {
  const summary = analysis?.summary || {}
  const altman = summary.altman_z?.score
  const altmanZone = summary.altman_z?.zone
  const fScore = summary.piotroski_f?.score

  return [
    {
      label: 'Biên ròng',
      value: formatPercent(summary.net_margin_pct),
      detail: 'Biên ròng thấp kéo giảm vùng đệm lợi nhuận khi thị trường xấu đi.',
      level: scoreTone(summary.net_margin_pct, 5, 12),
    },
    {
      label: 'ROE',
      value: formatPercent(summary.roe_pct),
      detail: 'ROE phản ánh hiệu quả tạo lợi nhuận trên vốn chủ.',
      level: scoreTone(summary.roe_pct, 10, 16),
    },
    {
      label: 'Debt/Equity',
      value: formatMaybeNumber(summary.debt_to_equity),
      detail: 'D/E cao thường làm doanh nghiệp nhạy hơn với lãi suất và dòng tiền.',
      level: reverseScoreTone(summary.debt_to_equity, 1.2, 0.7),
    },
    {
      label: 'Current ratio',
      value: formatMaybeNumber(summary.current_ratio),
      detail: 'Thanh khoản ngắn hạn dưới 1 có thể tạo áp lực vận hành.',
      level: scoreTone(summary.current_ratio, 1, 1.5),
    },
    {
      label: 'OCF / Net Income',
      value: formatMaybeNumber(summary.ocf_to_net_income),
      detail: 'Nếu thấp kéo dài, lợi nhuận kế toán có thể chưa chuyển hóa thành tiền.',
      level: scoreTone(summary.ocf_to_net_income, 0.8, 1.2),
    },
    {
      label: 'Altman Z-score',
      value: altman ? `${formatMaybeNumber(altman)} (${altmanZone || 'n/a'})` : 'n/a',
      detail: 'Dùng để nhận diện vùng an toàn tài chính tương đối.',
      level: altmanZone === 'distress' ? 'warn' : altmanZone === 'grey' ? 'caution' : 'good',
    },
    {
      label: 'Piotroski F-score',
      value: fScore != null ? `${fScore}/9` : 'n/a',
      detail: 'Điểm thấp cho thấy chất lượng fundamentals yếu đi.',
      level: fScore == null ? '' : (fScore < 5 ? 'warn' : fScore < 7 ? 'caution' : 'good'),
    },
  ]
}

function buildDashboardModel(analysis, trendRows, peerResult, qualityCharts, balanceSheetStrength) {
  const summary = analysis?.summary || {}
  const latest = latestPeriod(analysis)
  const healthRows = buildHealthRows(analysis)
  const healthScore = Math.round(healthRows.reduce((total, row) => total + row.value, 0) / Math.max(1, healthRows.length))
  const cfo = firstNumber(summary.cfo, summary.operating_cash_flow, latest?.cfo, latest?.operating_cash_flow, latest?.cash_flow_from_operations)
  const capex = firstNumber(summary.capex, latest?.capex, latest?.capital_expenditure)
  const fcf = firstNumber(summary.fcf, summary.free_cash_flow, latest?.fcf, latest?.free_cash_flow, Number.isFinite(cfo) && Number.isFinite(capex) ? cfo - Math.abs(capex) : null)
  const netIncome = firstNumber(summary.net_income, latest?.net_income)
  const revenue = firstNumber(summary.revenue, latest?.revenue)
  const assets = firstNumber(summary.total_assets, latest?.total_assets, latest?.assets)
  const liabilities = firstNumber(summary.total_liabilities, latest?.total_liabilities, latest?.liabilities)
  const equity = firstNumber(summary.equity, latest?.equity)
  const debt = firstNumber(summary.debt, latest?.debt, latest?.total_debt)
  const roe = firstNumber(summary.roe_pct)
  const netMargin = firstNumber(summary.net_margin_pct, revenue ? (netIncome / revenue) * 100 : null)
  const assetTurnover = firstNumber(summary.asset_turnover, revenue && assets ? revenue / assets : null)
  const equityMultiplier = firstNumber(summary.equity_multiplier, assets && equity ? assets / equity : null)
  const kpiSparks = buildKpiSparkSeries(analysis, trendRows, qualityCharts)

  return {
    companyName: analysis?.company_name || `CTCP ${analysis?.ticker || 'FPT'}`,
    exchange: analysis?.exchange || analysis?.market || 'HOSE',
    unit: analysis?.unit || 'tỷ VND',
    aiTitle: `${analysis?.ticker || 'Doanh nghiệp'} quality read`,
    healthScore,
    healthTone: healthScore >= 75 ? 'good' : healthScore >= 55 ? 'caution' : 'warn',
    strengthTags: buildStrengthTags(summary, healthScore),
    summaryBullets: buildSummaryBullets(summary, { cfo, netIncome, fcf, debt }),
    kpis: [
      {
        icon: '$',
        label: 'Doanh thu thuần',
        value: formatCompactNumber(revenue),
        note: `${formatPercent(summary.revenue_growth_yoy_pct)} YoY`,
        tone: trendTone(summary.revenue_growth_yoy_pct),
        sparkValues: kpiSparks.revenue,
      },
      {
        icon: 'Σ',
        label: 'LNST',
        value: formatCompactNumber(netIncome),
        note: `${formatPercent(summary.net_income_growth_yoy_pct)} YoY`,
        tone: trendTone(summary.net_income_growth_yoy_pct),
        sparkValues: kpiSparks.netIncome,
      },
      {
        icon: '%',
        label: 'Biên lợi nhuận ròng',
        value: formatPercent(netMargin),
        note: `${formatMaybeNumber(firstNumber(summary.ocf_to_net_income))}x OCF/LNST`,
        tone: scoreTone(netMargin, 5, 12),
        sparkValues: kpiSparks.netMargin,
      },
      {
        icon: '◎',
        label: 'ROE',
        value: formatPercent(roe),
        note: 'TTM / latest available',
        tone: scoreTone(roe, 10, 16),
        sparkValues: kpiSparks.roe,
      },
      {
        icon: '▣',
        label: 'CFO / Dòng tiền KD',
        value: formatCompactNumber(cfo),
        note: `${formatCompactNumber(fcf)} FCF`,
        tone: Number.isFinite(cfo) && cfo < 0 ? 'warn' : 'good',
        sparkValues: kpiSparks.cfo,
      },
      {
        icon: '⚖',
        label: 'Debt / Equity',
        value: formatMaybeNumber(summary.debt_to_equity),
        note: 'Đòn bẩy tài chính',
        tone: reverseScoreTone(summary.debt_to_equity, 1.2, 0.7),
        sparkValues: kpiSparks.debtToEquity,
      },
    ],
    marginAnalysis: qualityCharts?.margin_analysis || null,
    marginRows: buildMarginRows(analysis, trendRows, qualityCharts?.margin_analysis),
    balanceSheetStrength,
    balanceTotal: assets,
    balanceItems: [
      { label: 'Tiền & tương đương', value: firstNumber(summary.cash, latest?.cash, latest?.cash_and_equivalents), tone: 'cash' },
      { label: 'Phải thu / tồn kho', value: firstNumber(summary.working_capital_assets, latest?.receivables, latest?.inventory), tone: 'working' },
      { label: 'Tài sản khác', value: firstNumber(assets && equity ? assets - equity : null), tone: 'other' },
      { label: 'Nợ phải trả', value: liabilities, tone: 'debt' },
      { label: 'Vốn chủ sở hữu', value: equity, tone: 'equity' },
    ].filter((item) => Number.isFinite(item.value)),
    cashFlow: {
      cfo,
      cfi: firstNumber(summary.cfi, latest?.cfi, latest?.cash_flow_from_investing),
      cff: firstNumber(summary.cff, latest?.cff, latest?.cash_flow_from_financing),
      fcf,
      cfoToNetIncome: firstNumber(summary.ocf_to_net_income, cfo && netIncome ? cfo / netIncome : null),
      backend: qualityCharts?.cash_flow_quality || null,
    },
    leverageMetrics: [
      { label: 'Current Ratio', value: formatMaybeNumber(summary.current_ratio), note: scoreLabel(scoreTone(summary.current_ratio, 1, 1.5)), tone: scoreTone(summary.current_ratio, 1, 1.5) },
      { label: 'Quick Ratio', value: formatMaybeNumber(summary.quick_ratio), note: scoreLabel(scoreTone(summary.quick_ratio, 0.8, 1.2)), tone: scoreTone(summary.quick_ratio, 0.8, 1.2) },
      { label: 'Debt / Equity', value: formatMaybeNumber(summary.debt_to_equity), note: scoreLabel(reverseScoreTone(summary.debt_to_equity, 1.2, 0.7)), tone: reverseScoreTone(summary.debt_to_equity, 1.2, 0.7) },
      { label: 'Net Debt', value: formatCompactNumber(firstNumber(summary.net_debt, debt && latest?.cash ? debt - latest.cash : null)), note: 'Latest', tone: 'caution' },
    ],
    dupont: {
      netMargin,
      assetTurnover,
      equityMultiplier,
      roe,
    },
    peerRows: buildPeerRows(analysis, summary, peerResult, { roe, netMargin }),
    checkQuestions: buildCheckQuestions(summary, peerResult),
    aiQuestions: [
      'Lợi nhuận của công ty này có chất lượng không?',
      'Vì sao ROE tăng trong kỳ này?',
      'So với ngành, công ty mạnh ở đâu?',
    ],
  }
}

function buildPeerRows(analysis, summary, peerResult, context) {
  const revenueMetric = findPeerMetric(peerResult, ['revenue_growth_yoy_pct', 'revenue_growth', 'doanh thu'])
  const marginMetric = findPeerMetric(peerResult, ['net_margin_pct', 'net_margin', 'biên'])
  const roeMetric = findPeerMetric(peerResult, ['roe_pct', 'roe'])
  const debtMetric = findPeerMetric(peerResult, ['debt_to_equity', 'debt'])
  const cfoMetric = findPeerMetric(peerResult, ['ocf_to_net_income', 'cfo', 'cash'])
  const ticker = analysis?.ticker || peerResult?.ticker || DEFAULT_TICKER
  const sectorRevenue = firstNumber(revenueMetric?.peer_avg, summary.revenue_growth_yoy_pct)
  const sectorMargin = firstNumber(marginMetric?.peer_avg, context.netMargin)
  const sectorRoe = firstNumber(roeMetric?.peer_avg, context.roe)
  const sectorDebt = firstNumber(debtMetric?.peer_avg, summary.debt_to_equity)
  const sectorCfo = firstNumber(cfoMetric?.peer_avg, summary.ocf_to_net_income)

  return [
    {
      company: `${ticker} (${ticker})`,
      revenueGrowth: formatPercent(firstNumber(revenueMetric?.ticker_value, summary.revenue_growth_yoy_pct)),
      netMargin: formatPercent(firstNumber(marginMetric?.ticker_value, context.netMargin)),
      roe: formatPercent(firstNumber(roeMetric?.ticker_value, context.roe)),
      debtToEquity: formatMaybeNumber(firstNumber(debtMetric?.ticker_value, summary.debt_to_equity)),
      cfoMargin: formatPercent(firstNumber(cfoMetric?.ticker_value, summary.ocf_to_net_income ? summary.ocf_to_net_income * 10 : null)),
      assessment: peerAssessment(revenueMetric, roeMetric),
      selected: true,
      tone: 'good',
    },
    {
      company: 'Trung vị ngành',
      revenueGrowth: formatPercent(sectorRevenue),
      netMargin: formatPercent(sectorMargin),
      roe: formatPercent(sectorRoe),
      debtToEquity: formatMaybeNumber(sectorDebt),
      cfoMargin: formatPercent(sectorCfo),
      assessment: 'Mốc so sánh',
      tone: '',
    },
    {
      company: 'Nhóm peer',
      revenueGrowth: revenueMetric?.rank ? `${revenueMetric.rank}/${revenueMetric.total_peers}` : 'n/a',
      netMargin: marginMetric?.rank ? `${marginMetric.rank}/${marginMetric.total_peers}` : 'n/a',
      roe: roeMetric?.rank ? `${roeMetric.rank}/${roeMetric.total_peers}` : 'n/a',
      debtToEquity: debtMetric?.rank ? `${debtMetric.rank}/${debtMetric.total_peers}` : 'n/a',
      cfoMargin: cfoMetric?.rank ? `${cfoMetric.rank}/${cfoMetric.total_peers}` : 'n/a',
      assessment: 'Xếp hạng trong peer set',
      tone: 'caution',
    },
  ]
}

function buildKpiSparkSeries(analysis, trendRows, qualityCharts) {
  const orderedTrendRows = [...(trendRows || [])].slice(-10)
  const orderedPeriods = [...(analysis?.periods || [])]
    .slice()
    .sort((a, b) => {
      const ay = Number(a.year || 0)
      const by = Number(b.year || 0)
      if (ay !== by) return ay - by
      return Number(a.quarter || 0) - Number(b.quarter || 0)
    })
    .slice(-10)
  const qualityPoints = [...(qualityCharts?.cash_flow_quality?.points || [])].slice(-10)
  const marginPoints = [...(qualityCharts?.margin_analysis?.points || [])].slice(-10)

  return {
    revenue: preferSeries(
      orderedTrendRows.map((row) => row.revenue),
      orderedPeriods.map((row) => row.revenue),
    ),
    netIncome: preferSeries(
      orderedTrendRows.map((row) => row.net_income),
      orderedPeriods.map((row) => row.net_income),
    ),
    netMargin: preferSeries(
      marginPoints.map((row) => row.net_margin_pct),
      orderedTrendRows.map((row) => row.net_margin),
      orderedPeriods.map((row) => {
        const revenue = Number(row.revenue)
        const netIncome = Number(row.net_income)
        return Number.isFinite(revenue) && revenue !== 0 && Number.isFinite(netIncome) ? (netIncome / revenue) * 100 : null
      }),
    ),
    roe: preferSeries(
      [...(analysis?.trends || [])].slice().reverse().slice(-10).map((row) => row.roe_pct),
      orderedPeriods.map((row) => {
        const equity = Number(row.equity)
        const netIncome = Number(row.net_income)
        return Number.isFinite(equity) && equity !== 0 && Number.isFinite(netIncome) ? (netIncome / equity) * 100 : null
      }),
    ),
    cfo: preferSeries(
      qualityPoints.map((row) => row.cfo),
      [...(analysis?.trends || [])].slice().reverse().slice(-10).map((row) => row.operating_cash_flow),
      orderedPeriods.map((row) => row.operating_cash_flow),
    ),
    debtToEquity: preferSeries(
      [...(analysis?.trends || [])].slice().reverse().slice(-10).map((row) => row.debt_to_equity),
      orderedPeriods.map((row) => {
        const debt = Number(row.debt)
        const equity = Number(row.equity)
        return Number.isFinite(debt) && Number.isFinite(equity) && equity !== 0 ? debt / equity : null
      }),
    ),
  }
}

function preferSeries(...seriesList) {
  for (const series of seriesList) {
    const clean = series.map((value) => Number(value)).filter(Number.isFinite)
    if (clean.length >= 2) return clean
  }
  return []
}

function findPeerMetric(peerResult, needles) {
  const metrics = peerResult?.metrics || []
  return metrics.find((metric) => {
    const text = `${metric.field || ''} ${metric.label || ''}`.toLowerCase()
    return needles.some((needle) => text.includes(String(needle).toLowerCase()))
  })
}

function peerAssessment(revenueMetric, roeMetric) {
  const tones = [metricAttentionTone(revenueMetric), metricAttentionTone(roeMetric)]
  if (tones.includes('warn')) return 'Thấp hơn trung vị'
  if (tones.includes('caution')) return 'Tương đương'
  return 'Tốt hơn trung vị'
}

function buildSummaryBullets(summary, cash) {
  const bullets = [
    {
      tone: trendTone(summary.revenue_growth_yoy_pct) || 'caution',
      text: `Doanh thu ${formatPercent(summary.revenue_growth_yoy_pct)} YoY; kiểm tra động lực tăng đến từ sản lượng, giá hay one-off.`,
    },
    {
      tone: trendTone(summary.net_income_growth_yoy_pct) || 'caution',
      text: `LNST ${formatPercent(summary.net_income_growth_yoy_pct)} YoY; biên ròng hiện ở ${formatPercent(summary.net_margin_pct)}.`,
    },
    {
      tone: Number.isFinite(cash.cfo) && cash.cfo < 0 ? 'warn' : 'good',
      text: `Dòng tiền KD ${formatCompactNumber(cash.cfo)}; OCF/LNST ${formatMaybeNumber(summary.ocf_to_net_income)}x cho biết chất lượng lợi nhuận.`,
    },
    {
      tone: reverseScoreTone(summary.debt_to_equity, 1.2, 0.7) || 'caution',
      text: `Debt/Equity ${formatMaybeNumber(summary.debt_to_equity)}; đọc cùng current ratio để đánh giá sức chịu đòn bẩy.`,
    },
  ]
  return bullets
}

function buildStrengthTags(summary, healthScore) {
  const tags = []
  if (healthScore >= 75) tags.push('Sức khỏe tổng thể tốt')
  if (Number(summary.revenue_growth_yoy_pct) > 0) tags.push('Doanh thu tăng')
  if (Number(summary.ocf_to_net_income) >= 1) tags.push('Dòng tiền chất lượng')
  if (Number(summary.debt_to_equity) <= 0.7) tags.push('Đòn bẩy thấp')
  if (!tags.length) tags.push('Cần kiểm tra kỹ dữ liệu')
  return tags.slice(0, 4)
}

function buildMarginRows(analysis, trendRows, marginAnalysis) {
  const typedRows = [...(marginAnalysis?.points || [])].map((item) => ({
    label: item.period,
    period: item.period,
    year: item.year,
    quarter: item.quarter,
    gross_margin: firstNumber(item.gross_margin_pct),
    operating_margin: firstNumber(item.operating_margin_pct),
    ebit_margin: firstNumber(item.ebit_margin_pct),
    net_margin: firstNumber(item.net_margin_pct),
    net_margin_yoy_pp: firstNumber(item.net_margin_yoy_pp),
    net_margin_qoq_pp: firstNumber(item.net_margin_qoq_pp),
  }))
  if (typedRows.length) return typedRows

  const byPeriod = [...(analysis?.periods || [])].map((item, index) => {
    const revenue = firstNumber(item.revenue)
    const netIncome = firstNumber(item.net_income)
    return {
      label: normalizePeriodLabel(item),
      period: item.period,
      year: item.year,
      quarter: item.quarter,
      gross_margin: firstNumber(item.gross_margin_pct, item.gross_margin),
      operating_margin: firstNumber(item.operating_margin_pct, item.ebit_margin_pct),
      ebit_margin: firstNumber(item.ebit_margin_pct, item.ebit_margin),
      net_margin: firstNumber(item.net_margin_pct, revenue && netIncome ? (netIncome / revenue) * 100 : null),
      _index: index,
    }
  })
  const rows = byPeriod.filter((item) => Number.isFinite(item.gross_margin) || Number.isFinite(item.operating_margin) || Number.isFinite(item.net_margin))
  if (rows.length) return rows
  return trendRows.map((row) => ({
    ...row,
    gross_margin: null,
    operating_margin: null,
    net_margin: row.revenue ? (row.net_income / row.revenue) * 100 : null,
  }))
}

function buildCheckQuestions(summary, peerResult) {
  return [
    Number(summary.ocf_to_net_income) < 1 ? 'Lợi nhuận có chuyển hóa thành dòng tiền thật không?' : 'Dòng tiền vận hành có bền trong các quý tới không?',
    Number(summary.debt_to_equity) > 1 ? 'Đòn bẩy có làm doanh nghiệp nhạy với lãi suất không?' : 'Công ty có đang dùng vốn quá thận trọng so với cơ hội tăng trưởng không?',
    peerResult?.metrics?.length ? 'Chỉ số nào đang yếu hơn peer và nguyên nhân là gì?' : 'Cần chọn nhóm peer nào để so sánh công bằng hơn?',
  ]
}

function latestPeriod(analysis) {
  return [...(analysis?.periods || [])].at(-1) || null
}

function firstNumber(...values) {
  for (const value of values) {
    const numeric = Number(value)
    if (Number.isFinite(numeric)) return numeric
  }
  return null
}

function scoreLabel(tone) {
  if (tone === 'good') return 'Tốt'
  if (tone === 'warn') return 'Cần chú ý'
  if (tone === 'caution') return 'Trung bình'
  return 'n/a'
}

function Sparkline({ tone, values = [] }) {
  const model = buildSparklineModel(values)
  return (
    <svg className={`bctc-sparkline bctc-sparkline--${tone || 'neutral'}`} viewBox="0 0 90 34" aria-hidden="true">
      <polyline points={model.points} />
      {model.nodes.map((node) => (
        <circle key={`${node.x}-${node.y}`} cx={node.x} cy={node.y} r={node.latest ? 2.2 : 1.45} />
      ))}
    </svg>
  )
}

function buildSparklineModel(values) {
  const clean = values.map((value) => Number(value)).filter(Number.isFinite).slice(-10)
  const fallback = [12, 13, 12.5, 15, 14.4, 17, 16.2, 18, 17.4, 19]
  const series = clean.length >= 2 ? clean : fallback
  const min = Math.min(...series)
  const max = Math.max(...series)
  const span = max - min || Math.max(Math.abs(max), 1)
  const width = 86
  const height = 26
  const left = 2
  const top = 4
  const step = width / Math.max(1, series.length - 1)
  const nodes = series.map((value, index) => ({
    x: left + step * index,
    y: top + height - ((value - min) / span) * height,
    latest: index === series.length - 1,
  }))
  return {
    points: nodes.map((node) => `${roundSvg(node.x)},${roundSvg(node.y)}`).join(' '),
    nodes,
  }
}

function roundSvg(value) {
  return Math.round(value * 10) / 10
}

function HealthScoreGauge({ score, tone }) {
  return (
    <div className={`bctc-score-gauge bctc-score-gauge--${tone}`} style={{ '--score': `${score}%` }}>
      <strong>{score}</strong>
      <span>/100</span>
      <em>{scoreLabel(tone)}</em>
    </div>
  )
}

function HealthRadar({ rows }) {
  const center = 72
  const radius = 54
  const spokes = rows.slice(0, 6)
  const points = spokes.map((row, index) => {
    const angle = (-90 + (360 / spokes.length) * index) * (Math.PI / 180)
    const scoreRadius = radius * (sanitizeScore(row.value) / 100)
    return {
      label: row.label,
      axisX: center + radius * Math.cos(angle),
      axisY: center + radius * Math.sin(angle),
      x: center + scoreRadius * Math.cos(angle),
      y: center + scoreRadius * Math.sin(angle),
    }
  })
  const polygon = points.map((point) => `${point.x},${point.y}`).join(' ')
  const rings = [0.35, 0.62, 0.88].map((scale) => (
    spokes.map((_, index) => {
      const angle = (-90 + (360 / spokes.length) * index) * (Math.PI / 180)
      return `${center + radius * scale * Math.cos(angle)},${center + radius * scale * Math.sin(angle)}`
    }).join(' ')
  ))

  return (
    <svg className="bctc-health-radar" viewBox="0 0 144 144" aria-hidden="true">
      {rings.map((ring) => <polygon key={ring} points={ring} className="bctc-health-radar__ring" />)}
      {points.map((point) => (
        <g key={point.label}>
          <line x1={center} y1={center} x2={point.axisX} y2={point.axisY} className="bctc-health-radar__axis" />
          <circle cx={point.x} cy={point.y} r="3.2" className="bctc-health-radar__dot" />
        </g>
      ))}
      <polygon points={polygon} className="bctc-health-radar__shape" />
    </svg>
  )
}

function BalanceSheetCard({ items, total }) {
  const assets = items.filter((item) => !['debt', 'equity'].includes(item.tone))
  const funding = items.filter((item) => ['debt', 'equity'].includes(item.tone))
  const liabilities = funding.find((item) => item.tone === 'debt')?.value
  const liabilityRatio = ratioPercent(liabilities, total)

  return (
    <div className="bctc-balance">
      {items.length ? (
        <>
          <div className="bctc-balance__columns">
            <BalanceStack title="Tài sản" items={assets} total={total} />
            <BalanceStack title="Nguồn vốn" items={funding} total={total} />
          </div>
          <div className="bctc-balance__total">
            <span>Nợ phải trả / Tổng nguồn vốn</span>
            <strong>{formatPercent(liabilityRatio)}</strong>
          </div>
        </>
      ) : <p className="bctc-muted">Chưa đủ dữ liệu bảng cân đối để tách chi tiết.</p>}
    </div>
  )
}

function BalanceSheetStrengthCard({ data, fallbackItems, fallbackTotal }) {
  if (!data) {
    return <BalanceSheetCard items={fallbackItems || []} total={fallbackTotal} />
  }

  const liabilityRatio = data.ratios?.liabilities_to_assets
  return (
    <div className="bctc-bs-card">
      <div className="bctc-bs-period">{formatPeriodBadge(data.period)}</div>
      <div className="bctc-bs-grid">
        <CompositionColumn title={`Tài sản (${unitLabel(data.unit)})`} total={data.total_assets} items={data.asset_items} />
        <StackedCompositionBar items={data.funding_items} total={data.total_funding} />
        <CompositionColumn title={`Nguồn vốn (${unitLabel(data.unit)})`} total={data.total_funding} items={data.funding_items} />
      </div>
      <RatioFooter value={liabilityRatio} />
      <DataQualityWarning dataQuality={data.data_quality} redFlags={data.red_flags} />
    </div>
  )
}

function CompositionColumn({ title, total, items }) {
  return (
    <div className="bctc-bs-column">
      <div className="bctc-bs-column__head">
        <span>{title}</span>
        <strong>{formatCompactNumber(total)}</strong>
      </div>
      <div className="bctc-bs-list">
        {[...(items || [])].sort((a, b) => a.display_order - b.display_order).map((item) => (
          <CompositionItem key={item.key} item={item} />
        ))}
      </div>
    </div>
  )
}

function CompositionItem({ item }) {
  return (
    <div
      className="bctc-bs-item"
      title={`${item.label}: ${formatCompactNumber(item.value)} (${formatRatioPercent(item.percentage)})`}
    >
      <i className={`bctc-bs-dot bctc-bs-dot--${item.color_token}`} />
      <span>{item.label}</span>
      <strong>{formatCompactNumber(item.value)}</strong>
      <em>{formatRatioPercent(item.percentage)}</em>
    </div>
  )
}

function StackedCompositionBar({ items, total }) {
  const safeTotal = Math.max(Number(total) || 0, 1)
  return (
    <div className="bctc-bs-stack" aria-label="Funding composition">
      {[...(items || [])].sort((a, b) => a.display_order - b.display_order).map((item) => (
        <div
          key={item.key}
          className={`bctc-bs-stack__seg bctc-bs-stack__seg--${item.color_token}`}
          style={{ height: `${Math.max(5, (Number(item.value) / safeTotal) * 100)}%` }}
          title={`${item.label}: ${formatCompactNumber(item.value)} (${formatRatioPercent(item.percentage)})`}
        />
      ))}
    </div>
  )
}

function RatioFooter({ value }) {
  const tone = value == null ? 'neutral' : value < 0.4 ? 'good' : value <= 0.6 ? 'watch' : 'warn'
  return (
    <div className={`bctc-bs-footer bctc-bs-footer--${tone}`}>
      <span>Nợ phải trả / Tổng nguồn vốn</span>
      <strong>{formatRatioPercent(value)}</strong>
    </div>
  )
}

function DataQualityWarning({ dataQuality, redFlags }) {
  const warnings = [
    ...(dataQuality?.consistency_warnings || []),
    ...(redFlags || []).filter((flag) => flag.severity !== 'low').map((flag) => flag.message),
  ].slice(0, 3)
  if (!warnings.length && !(dataQuality?.estimated_fields || []).length) return null
  return (
    <div className="bctc-bs-quality">
      {warnings.map((item) => <span key={item}>{item}</span>)}
      {(dataQuality?.estimated_fields || []).length ? <span>Ước tính: {dataQuality.estimated_fields.join(', ')}</span> : null}
    </div>
  )
}

function BalanceStack({ title, items, total }) {
  const stackItems = items.filter((item) => Number.isFinite(Number(item.value)))
  const stackTotal = stackItems.reduce((sum, item) => sum + Math.abs(Number(item.value) || 0), 0) || Math.abs(Number(total)) || 1

  return (
    <div className="bctc-balance-stack">
      <div className="bctc-balance-stack__head">
        <span>{title}</span>
        <strong>{formatCompactNumber(stackItems.reduce((sum, item) => sum + Number(item.value || 0), 0))}</strong>
      </div>
      <div className="bctc-balance-stack__bar">
        {stackItems.map((item) => (
          <i
            key={item.label}
            className={`bctc-balance-stack__seg bctc-balance-stack__seg--${item.tone}`}
            style={{ width: `${Math.max(7, (Math.abs(Number(item.value) || 0) / stackTotal) * 100)}%` }}
          />
        ))}
      </div>
      <div className="bctc-balance-stack__list">
        {stackItems.map((item) => (
          <div key={item.label} className={`bctc-balance__row bctc-balance__row--${item.tone}`}>
            <span>{item.label}</span>
            <strong>{formatCompactNumber(item.value)}</strong>
            <em>{formatPercent(ratioPercent(item.value, total))}</em>
          </div>
        ))}
      </div>
    </div>
  )
}

function CashFlowQuality({ data }) {
  const backend = data.backend
  const latest = backend?.latest || {}
  const latestPoint = backend?.points?.at(-1) || {}
  const bars = [
    { label: 'CFO', value: firstNumber(latest.cfo, latestPoint.cfo, data.cfo), tone: 'good' },
    { label: 'CFI', value: firstNumber(latest.cfi, latestPoint.cfi, data.cfi), tone: 'warn' },
    { label: 'CFF', value: firstNumber(latest.cff, latestPoint.cff, data.cff), tone: 'caution' },
    {
      label: 'FCF',
      value: firstNumber(latest.fcf, latestPoint.fcf, data.fcf),
      tone: Number(firstNumber(latest.fcf, latestPoint.fcf, data.fcf)) >= 0 ? 'good' : 'warn',
    },
  ]
  const maxValue = Math.max(...bars.map((item) => Math.abs(Number(item.value) || 0)), 1)
  return (
    <div className="bctc-cashflow">
      <div className="bctc-cashflow__bars">
        {bars.map((item) => (
          <div key={item.label} className={`bctc-cashflow__bar bctc-cashflow__bar--${item.tone} ${Number(item.value) < 0 ? 'is-negative' : ''}`}>
            <i style={{ height: `${Math.max(8, (Math.abs(Number(item.value) || 0) / maxValue) * 100)}%` }} />
            <strong>{formatCompactNumber(item.value)}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </div>
      <div className="bctc-cashflow__ratio">
        <span>CFO / LNST</span>
        <strong>{formatMaybeNumber(firstNumber(latest.cfo_to_net_income, data.cfoToNetIncome))}x</strong>
        <em>{latest.quality_label || (Number(data.cfoToNetIncome) >= 1 ? 'Tốt' : 'Cần kiểm tra')}</em>
      </div>
      <div className="bctc-cashflow__metrics">
        <MiniQualityMetric label="CFO Margin" value={formatPercent(latest.cfo_margin_pct)} />
        <MiniQualityMetric label="FCF Margin" value={formatPercent(latest.fcf_margin_pct)} />
        <MiniQualityMetric
          label="Quality Score"
          value={`${formatMaybeNumber(latest.quality_score)}/100`}
          tone={Number(latest.quality_score) < 55 ? 'warn' : 'good'}
        />
      </div>
      {backend?.interpretation ? <p className="bctc-chart-insight">{backend.interpretation}</p> : null}
      {backend?.flags?.length ? (
        <div className="bctc-chart-flags">
          {backend.flags.slice(0, 3).map((flag) => (
            <span key={flag.code} className={`bctc-chart-flag bctc-chart-flag--${flag.severity}`}>{flag.message}</span>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function MarginAnalysisDetails({ data }) {
  if (!data) return null
  const latest = data.latest || {}
  return (
    <div className="bctc-margin-details">
      <div className="bctc-margin-latest">
        <MiniQualityMetric label="Gross" value={formatPercent(latest.gross_margin_pct)} />
        <MiniQualityMetric label="Operating" value={formatPercent(latest.operating_margin_pct)} />
        <MiniQualityMetric label="EBIT" value={formatPercent(latest.ebit_margin_pct)} />
        <MiniQualityMetric label="Net" value={formatPercent(latest.net_margin_pct)} tone={Number(latest.net_margin_pct) < 0 ? 'warn' : 'good'} />
      </div>
      {data.interpretation ? <p className="bctc-chart-insight">{data.interpretation}</p> : null}
      {data.flags?.length ? (
        <div className="bctc-chart-flags">
          {data.flags.slice(0, 3).map((flag) => (
            <span key={flag.code} className={`bctc-chart-flag bctc-chart-flag--${flag.severity}`}>{flag.message}</span>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function MiniQualityMetric({ label, value, tone }) {
  return (
    <div className={`bctc-quality-metric ${tone ? `bctc-quality-metric--${tone}` : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function DupontCard({ dupont }) {
  const items = [
    { label: 'Biên lợi nhuận ròng', value: formatPercent(dupont.netMargin) },
    { label: 'Vòng quay tài sản', value: `${formatMaybeNumber(dupont.assetTurnover)}x` },
    { label: 'Hệ số đòn bẩy', value: `${formatMaybeNumber(dupont.equityMultiplier)}x` },
    { label: 'ROE', value: formatPercent(dupont.roe), strong: true },
  ]
  return (
    <div className="bctc-dupont">
      {items.map((item, index) => (
        <div key={item.label} className={item.strong ? 'bctc-dupont__item bctc-dupont__item--strong' : 'bctc-dupont__item'}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          {index < items.length - 1 ? <em>{index === items.length - 2 ? '=' : '×'}</em> : null}
        </div>
      ))}
    </div>
  )
}

function ratioPercent(value, total) {
  const numeric = Math.abs(Number(value))
  const denominator = Math.abs(Number(total))
  if (!Number.isFinite(numeric) || !Number.isFinite(denominator) || denominator <= 0) return 0
  return Math.max(4, Math.min(100, (numeric / denominator) * 100))
}

function MetricTrendChart({ rows, metrics, formatValue, height = 288, showEndpointLabels = false }) {
  const [activeIndex, setActiveIndex] = useState(Math.max(0, rows.length - 1))
  const chart = useMemo(() => buildSvgChartModel(rows, metrics, height), [rows, metrics, height])
  const activePoint = rows[activeIndex] || rows.at(-1)

  useEffect(() => {
    setActiveIndex(Math.max(0, rows.length - 1))
  }, [rows.length])

  if (!rows.length) {
    return <p className="bctc-muted">Chưa đủ dữ liệu để vẽ chart cho chế độ này.</p>
  }

  return (
    <div className="bctc-trend-chart" onMouseLeave={() => setActiveIndex(Math.max(0, rows.length - 1))}>
      <div className="bctc-trend-chart__legend">
        {metrics.map((metric) => (
          <span key={metric.key}>
            <i style={{ '--line-color': metric.color }} />
            {metric.label}
          </span>
        ))}
      </div>
      <svg
        className="bctc-trend-chart__svg"
        viewBox={`0 0 ${chart.width} ${chart.height}`}
        role="img"
        aria-label="Financial trend chart"
        onMouseMove={(event) => {
          const rect = event.currentTarget.getBoundingClientRect()
          const ratio = (event.clientX - rect.left) / Math.max(1, rect.width)
          const nextIndex = Math.round((ratio * chart.width - chart.left) / Math.max(1, chart.step))
          setActiveIndex(Math.max(0, Math.min(rows.length - 1, nextIndex)))
        }}
      >
        <defs>
          <linearGradient id="bctcBarRevenue" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#19b985" />
            <stop offset="100%" stopColor="#0f766e" />
          </linearGradient>
          <linearGradient id="bctcBarIncome" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#2d75b8" />
            <stop offset="100%" stopColor="#173b66" />
          </linearGradient>
          <filter id="bctcLineGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="3" stdDeviation="3" floodColor="#0f766e" floodOpacity="0.16" />
          </filter>
        </defs>
        {chart.grid.map((line) => (
          <g key={line.y}>
            <line x1={chart.left} x2={chart.right} y1={line.y} y2={line.y} className="bctc-trend-chart__grid" />
            <text x={chart.left - 10} y={line.y + 4} textAnchor="end" className="bctc-trend-chart__axis">{line.leftLabel}</text>
            {chart.hasRightScale ? <text x={chart.right + 10} y={line.y + 4} className="bctc-trend-chart__axis">{line.rightLabel}</text> : null}
          </g>
        ))}
        <line x1={chart.left} x2={chart.right} y1={chart.bottom} y2={chart.bottom} className="bctc-trend-chart__axis-line" />
        {chart.barShapes.map((bar) => (
          <rect
            key={`${bar.key}-${bar.index}`}
            x={bar.x}
            y={bar.y}
            width={bar.width}
            height={bar.height}
            rx="3"
            className={`bctc-trend-chart__bar bctc-trend-chart__bar--${bar.key}`}
            fill={bar.key === 'net_income' ? 'url(#bctcBarIncome)' : 'url(#bctcBarRevenue)'}
          />
        ))}
        {chart.lines.map((line) => (
          <g key={line.key} filter="url(#bctcLineGlow)">
            <polyline points={line.points} fill="none" stroke={line.color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            {line.nodes.map((node) => (
              <circle key={`${line.key}-${node.index}`} cx={node.x} cy={node.y} r={node.index === activeIndex ? 4.8 : 3.4} fill="#ffffff" stroke={line.color} strokeWidth="2.2" />
            ))}
          </g>
        ))}
        {chart.xLabels.map((label) => (
          <text key={`${label.text}-${label.x}`} x={label.x} y={chart.height - 12} textAnchor="middle" className="bctc-trend-chart__axis">
            {label.text}
          </text>
        ))}
        {chart.xByIndex[activeIndex] ? (
          <line x1={chart.xByIndex[activeIndex]} x2={chart.xByIndex[activeIndex]} y1={chart.top} y2={chart.bottom} className="bctc-trend-chart__crosshair" />
        ) : null}
      </svg>
      <div className="bctc-trend-chart__hover">
        {activePoint ? (
          <>
            <strong>{activePoint.label}</strong>
            <div>
              {metrics.map((item) => (
                <span key={item.key}>
                  {item.label}: {(item.formatValue || formatValue)(activePoint[item.key])}
                </span>
              ))}
            </div>
          </>
        ) : (
          <span>Di chuột trên chart để đọc giá trị từng kỳ.</span>
        )}
      </div>
      {showEndpointLabels && activePoint ? (
        <div className="bctc-trend-chart__endpoints">
          {metrics.map((item) => (
            <span key={item.key}>
              <b>{item.label}</b>
              {(item.formatValue || formatValue)(activePoint[item.key])}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function buildSvgChartModel(rows, metrics, height) {
  const width = 760
  const left = 58
  const right = 704
  const top = 18
  const bottom = height - 42
  const plotHeight = bottom - top
  const step = rows.length > 1 ? (right - left) / (rows.length - 1) : right - left
  const barMetrics = metrics.filter((metric) => metric.type === 'bar')
  const lineMetrics = metrics.filter((metric) => metric.type !== 'bar')
  const leftValues = rows.flatMap((row) => barMetrics.map((metric) => Number(row[metric.key])).filter(Number.isFinite))
  const rightValues = rows.flatMap((row) => lineMetrics.map((metric) => Number(row[metric.key])).filter(Number.isFinite))
  const leftDomain = niceDomain(leftValues, true)
  const rightDomain = niceDomain(rightValues, false)
  const yLeft = (value) => bottom - ((Number(value) - leftDomain.min) / Math.max(1, leftDomain.max - leftDomain.min)) * plotHeight
  const yRight = (value) => bottom - ((Number(value) - rightDomain.min) / Math.max(1, rightDomain.max - rightDomain.min)) * plotHeight
  const xByIndex = rows.map((_, index) => left + index * step)
  const groupWidth = Math.min(54, Math.max(24, step * 0.58))
  const barWidth = Math.max(8, Math.min(20, groupWidth / Math.max(1, barMetrics.length) - 4))
  const zeroY = yLeft(0)

  const barShapes = rows.flatMap((row, index) => barMetrics.map((metric, metricIndex) => {
    const value = Number(row[metric.key])
    if (!Number.isFinite(value)) return null
    const y = yLeft(value)
    const x = xByIndex[index] - ((barWidth + 4) * barMetrics.length) / 2 + metricIndex * (barWidth + 4)
    return {
      key: metric.key,
      index,
      x,
      y: Math.min(y, zeroY),
      width: barWidth,
      height: Math.max(2, Math.abs(zeroY - y)),
    }
  }).filter(Boolean))

  const lines = lineMetrics.map((metric) => {
    const nodes = rows.map((row, index) => {
      const value = Number(row[metric.key])
      if (!Number.isFinite(value)) return null
      return { index, x: xByIndex[index], y: yRight(value), value }
    }).filter(Boolean)
    return {
      key: metric.key,
      color: metric.color,
      points: nodes.map((node) => `${node.x},${node.y}`).join(' '),
      nodes,
    }
  })

  const grid = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const y = top + ratio * plotHeight
    const leftValue = leftDomain.max - ratio * (leftDomain.max - leftDomain.min)
    const rightValue = rightDomain.max - ratio * (rightDomain.max - rightDomain.min)
    return {
      y,
      leftLabel: formatCompactNumber(leftValue),
      rightLabel: formatPercent(rightValue),
    }
  })

  const labelEvery = rows.length > 8 ? 2 : 1
  const xLabels = rows
    .map((row, index) => ({ text: shortPeriodLabel(row.label), x: xByIndex[index], index }))
    .filter((item, index) => index % labelEvery === 0 || index === rows.length - 1)

  return {
    width,
    height,
    left,
    right,
    top,
    bottom,
    step,
    grid,
    xByIndex,
    xLabels,
    barShapes,
    lines,
    hasRightScale: lineMetrics.length > 0,
  }
}

function niceDomain(values, includeZero) {
  const finite = values.filter((value) => Number.isFinite(Number(value))).map(Number)
  if (!finite.length) return { min: includeZero ? 0 : 0, max: includeZero ? 1 : 100 }
  let min = Math.min(...finite)
  let max = Math.max(...finite)
  if (includeZero) {
    min = Math.min(0, min)
    max = Math.max(0, max)
  }
  if (min === max) {
    const pad = Math.abs(max || 1) * 0.2
    min -= pad
    max += pad
  }
  const pad = (max - min) * 0.12
  return { min: min - pad, max: max + pad }
}

function shortPeriodLabel(label) {
  return String(label || '')
    .replace(/^20(\d{2}) Q/i, 'Q')
    .replace(/^20(\d{2})$/, "'$1")
}

function MetricBox({ label, value }) {
  return (
    <div className="bctc-box">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function formatCompactNumber(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return new Intl.NumberFormat('vi-VN', {
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(numeric)
}

function formatMaybeNumber(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(numeric)
}

function formatPercent(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(numeric)}%`
}

function formatRatioPercent(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(numeric * 100)}%`
}

function unitLabel(unit) {
  if (unit === 'ty_vnd') return 'tỷ VND'
  if (unit === 'trieu_vnd') return 'triệu VND'
  if (unit === 'nghin_vnd') return 'nghìn VND'
  return 'VND'
}

function formatPeriodBadge(period) {
  const match = String(period || '').match(/(20\d{2})-Q([1-4])/)
  if (match) return `Q${match[2]}/${match[1]}`
  return period || 'Latest'
}

function toNumber(value) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

function safeAdd(a, b) {
  const x = Number(a)
  const y = Number(b)
  if (!Number.isFinite(x) && !Number.isFinite(y)) return null
  if (!Number.isFinite(x)) return y
  if (!Number.isFinite(y)) return x
  return x + y
}

function trendTone(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  if (numeric < 0) return 'warn'
  if (numeric >= 10) return 'good'
  return 'caution'
}

function scoreTone(value, warnThreshold, goodThreshold) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  if (numeric < warnThreshold) return 'warn'
  if (numeric >= goodThreshold) return 'good'
  return 'caution'
}

function reverseScoreTone(value, warnThreshold, goodThreshold) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  if (numeric > warnThreshold) return 'warn'
  if (numeric <= goodThreshold) return 'good'
  return 'caution'
}

function metricAttentionTone(metric) {
  if (!metric?.rank || !metric?.total_peers) return ''
  const ratio = metric.rank / metric.total_peers
  if (ratio >= 0.75) return 'warn'
  if (ratio >= 0.55) return 'caution'
  return ''
}
