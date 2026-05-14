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
const BCTC_TABS = [
  { key: 'overview', label: 'Tổng quan' },
  { key: 'income', label: 'Kết quả kinh doanh' },
  { key: 'balance', label: 'Bảng cân đối kế toán' },
  { key: 'cash-flow', label: 'Lưu chuyển tiền tệ' },
  { key: 'ratios', label: 'Chỉ số tài chính' },
  { key: 'horizontal', label: 'Phân tích ngang' },
  { key: 'vertical', label: 'Phân tích dọc' },
  { key: 'risk', label: 'Cảnh báo rủi ro' },
  { key: 'report', label: 'Báo cáo' },
]

export default function GuidedInvestingPage({ sessionId }) {
  const [ticker, setTicker] = useState(DEFAULT_TICKER)
  const [peersText, setPeersText] = useState('')
  const [mode, setMode] = useState('quarter')
  const [analysis, setAnalysis] = useState(null)
  const [qualityCharts, setQualityCharts] = useState(null)
  const [balanceSheetStrength, setBalanceSheetStrength] = useState(null)
  const [peerResult, setPeerResult] = useState(null)
  const [providerStatus, setProviderStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [peerLoading, setPeerLoading] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [activeSection, setActiveSection] = useState('overview')

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
  const activeTab = BCTC_TABS.find((item) => item.key === activeSection) || BCTC_TABS[0]
  const isOverview = activeSection === 'overview'

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
        <div className="bctc-title-lockup">
          <div className="bctc-title-icon" aria-hidden="true">▥</div>
          <div>
            <h1>{isOverview ? 'Phân tích BCTC' : activeTab.label}</h1>
            <p>
              {activeSection === 'income'
                ? 'Phân tích hiệu quả hoạt động kinh doanh qua doanh thu, cơ cấu chi phí, biên lợi nhuận và chất lượng lợi nhuận.'
                : activeSection === 'balance'
                  ? 'Phân tích cơ cấu tài sản, nguồn vốn, thanh khoản và mức độ an toàn tài chính.'
                  : activeSection === 'cash-flow'
                    ? 'Phân tích chất lượng dòng tiền, khả năng tạo tiền từ hoạt động kinh doanh và nhu cầu tài trợ vốn.'
                    : 'Phân tích báo cáo tài chính để hiểu sức khỏe tài chính và hiệu quả hoạt động doanh nghiệp.'}
            </p>
          </div>
        </div>
        <div className="bctc-topbar__actions">
          <button type="button" className="bctc-btn bctc-btn--secondary" onClick={() => void runAnalysis({ refresh: true })}>
            Refresh dữ liệu
          </button>
          <button type="button" className="bctc-btn bctc-btn--secondary">
            Xuất báo cáo
          </button>
          <button type="button" className="bctc-btn" onClick={() => void runAnalysis({ refresh: false })}>
            Phân tích BCTC
          </button>
        </div>
      </header>

      {isOverview ? <BctcTabs activeSection={activeSection} onSelect={setActiveSection} /> : null}

      {isOverview ? <section className="bctc-command-grid">
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

        <article className="bctc-learning-card">
          <h2>Mục tiêu học tập</h2>
          <p>Trang Tổng quan giúp bạn nhanh chóng nắm bức tranh toàn cảnh về doanh nghiệp.</p>
          <ul>
            <li>Hiểu xu hướng doanh thu & lợi nhuận</li>
            <li>Đánh giá hiệu quả & chất lượng lợi nhuận</li>
            <li>Kiểm tra sức khỏe tài chính & rủi ro</li>
            <li>Đưa ra nhận định bước đầu</li>
          </ul>
          <div>
            <strong>Mẹo học tập:</strong> Hãy bắt đầu bằng AI Summary, sau đó khám phá các biểu đồ và chỉ số bên dưới.
          </div>
        </article>
      </section> : null}

      {status && isOverview ? <p className="bctc-state">{status}</p> : null}
      {error ? <p className="bctc-state bctc-state--error">{error}</p> : null}

      {analysis ? (
        isOverview ? (
        <>
          <section className="bctc-kpi-strip">
            {dashboard.kpis.map((item) => (
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
        ) : (
          <BctcSectionPanel
            section={activeSection}
            onSelectSection={setActiveSection}
            analysis={analysis}
            dashboard={dashboard}
            trendRows={trendRows}
            healthRows={healthRows}
            mode={mode}
            peerLoading={peerLoading}
          />
        )
      ) : null}
    </section>
  )
}

function BctcSectionPanel({ section, onSelectSection, analysis, dashboard, trendRows, healthRows, mode, peerLoading }) {
  const tab = BCTC_TABS.find((item) => item.key === section) || BCTC_TABS[0]
  const latest = latestPeriod(analysis) || {}
  const sectionTabs = <BctcTabs activeSection={section} onSelect={onSelectSection} />

  if (section === 'income') {
    const incomeCards = buildIncomeKpiCards(dashboard, latest, analysis?.summary)
    return (
      <section className="bctc-section-panel bctc-income-view" aria-label={tab.label}>
        <section className="bctc-income-control-band">
          <div className="bctc-income-company">
            <div className="bctc-logo" aria-hidden="true">{(analysis?.ticker || 'FPT').slice(0, 3)}</div>
            <div>
              <h2>{dashboard.companyName}</h2>
              <p>Ngành: {analysis?.industry || 'Công nghệ thông tin'} · {dashboard.exchange}: {analysis?.ticker || DEFAULT_TICKER}</p>
            </div>
          </div>
          <label>
            <span>Kỳ báo cáo</span>
            <select defaultValue={mode === 'quarter' ? 'quarter' : 'year'}>
              <option value="quarter">Quý</option>
              <option value="year">Năm</option>
            </select>
          </label>
          <label>
            <span>So sánh với</span>
            <select defaultValue="same-period">
              <option value="same-period">Cùng kỳ năm trước</option>
              <option value="previous-period">Kỳ liền trước</option>
            </select>
          </label>
          <AnalysisStepper />
        </section>
        {sectionTabs}

        <section className="bctc-income-kpis">
          {incomeCards.map((item) => (
            <article key={item.label} className={`bctc-income-kpi bctc-income-kpi--${item.tone || 'neutral'}`}>
              <div className="bctc-income-kpi__icon">{item.icon}</div>
              <div>
                <p>{item.label}</p>
                <h3>{item.value}</h3>
                <span>{item.delta}</span>
              </div>
              <Sparkline tone={item.tone} values={item.sparkValues} />
            </article>
          ))}
        </section>

        <section className="bctc-income-layout">
          <article className="bctc-chart-card bctc-income-chart bctc-income-chart--wide">
            <header className="bctc-panel-head">
              <div>
                <h2>Xu hướng doanh thu, giá vốn, lợi nhuận gộp và LNST</h2>
                <p>Đơn vị: {dashboard.unit}</p>
              </div>
              <span>{modeLabel(mode)}</span>
            </header>
            <MetricTrendChart rows={trendRows} metrics={REVENUE_INCOME_METRICS} formatValue={formatCompactNumber} height={250} showEndpointLabels />
          </article>
          <article className="bctc-chart-card bctc-income-chart">
            <header className="bctc-panel-head">
              <div>
                <h2>Xu hướng biên lợi nhuận (%)</h2>
                <p>Biên gộp, EBIT và biên ròng qua các kỳ.</p>
              </div>
              <span>{analysis?.latest_period || 'Latest'}</span>
            </header>
            <MetricTrendChart rows={dashboard.marginRows} metrics={MARGIN_METRICS} formatValue={formatPercent} height={250} showEndpointLabels />
          </article>
          <aside className="bctc-income-assistant">
            <IncomeAssistantCard dashboard={dashboard} />
          </aside>
          <StatementTable title="Báo cáo kết quả kinh doanh" rows={buildIncomeStatementTableRows(analysis, dashboard)} />
          <article className="bctc-panel bctc-income-highlights">
            <header>
              <h2>Điểm nhấn</h2>
              <p>Những tín hiệu đáng chú ý từ kỳ gần nhất.</p>
            </header>
            <ul>
              {dashboard.summaryBullets.slice(0, 3).map((item) => (
                <li key={item.text} className={`bctc-income-highlight bctc-income-highlight--${item.tone}`}>
                  <span>{item.tone === 'warn' ? '!' : '↗'}</span>
                  <p>{item.text}</p>
                </li>
              ))}
            </ul>
            <a href="#bctc-income-detail">Xem chi tiết phân tích →</a>
          </article>
        </section>
      </section>
    )
  }

  if (section === 'balance') {
    const balanceCards = buildBalanceKpiCards(dashboard, latest, analysis)
    const balanceRows = buildBalancePeriodRows(analysis)
    return (
      <section className="bctc-section-panel bctc-balance-view" aria-label={tab.label}>
        <section className="bctc-income-control-band bctc-balance-control-band">
          <div className="bctc-income-company">
            <div className="bctc-logo" aria-hidden="true">{(analysis?.ticker || 'FPT').slice(0, 3)}</div>
            <div>
              <h2>{dashboard.companyName}</h2>
              <p>Ngành: {analysis?.industry || 'Công nghệ thông tin'} · {dashboard.exchange}: {analysis?.ticker || DEFAULT_TICKER}</p>
            </div>
          </div>
          <label>
            <span>Kỳ báo cáo</span>
            <select defaultValue={mode === 'quarter' ? 'quarter' : 'year'}>
              <option value="quarter">Quý</option>
              <option value="year">Năm</option>
            </select>
          </label>
          <label>
            <span>So sánh với</span>
            <select defaultValue="same-period">
              <option value="same-period">Cùng kỳ năm trước</option>
              <option value="previous-period">Kỳ liền trước</option>
            </select>
          </label>
        </section>
        {sectionTabs}

        <section className="bctc-balance-kpis">
          {balanceCards.map((item) => (
            <article key={item.label} className={`bctc-balance-kpi bctc-balance-kpi--${item.tone || 'neutral'}`}>
              <div className="bctc-balance-kpi__icon">{item.icon}</div>
              <div>
                <p>{item.label}</p>
                <h3>{item.value}</h3>
                <span>{item.delta}</span>
              </div>
              <Sparkline tone={item.tone} values={item.sparkValues} />
            </article>
          ))}
        </section>

        <section className="bctc-balance-layout">
          <article className="bctc-chart-card bctc-balance-assets">
            <header className="bctc-panel-head">
              <div>
                <h2>Cơ cấu tài sản qua các kỳ</h2>
                <p>Đơn vị: {dashboard.unit}</p>
              </div>
              <span>Assets</span>
            </header>
            <BalanceAssetStackChart rows={balanceRows} />
          </article>

          <article className="bctc-chart-card bctc-balance-funding">
            <header className="bctc-panel-head">
              <div>
                <h2>Cơ cấu nguồn vốn (%)</h2>
                <p>Nợ ngắn hạn, nợ dài hạn và vốn chủ sở hữu.</p>
              </div>
              <span>{analysis?.latest_period || 'Latest'}</span>
            </header>
            <BalanceFundingDonut rows={balanceRows} latest={latest} />
          </article>

          <article className="bctc-chart-card bctc-balance-liquidity-chart">
            <header className="bctc-panel-head">
              <div>
                <h2>Xu hướng vốn lưu động & thanh khoản</h2>
                <p>Working capital, current ratio và quick ratio qua các kỳ.</p>
              </div>
              <span>Liquidity</span>
            </header>
            <BalanceLiquidityChart rows={balanceRows} />
          </article>

          <aside className="bctc-balance-assistant">
            <BalanceAssistantCard dashboard={dashboard} />
          </aside>

          <BalanceStatementTable rows={balanceRows} />

          <article className="bctc-panel bctc-balance-highlights">
            <header>
              <h2>Điểm nhấn</h2>
              <p>Các tín hiệu cần đọc khi phân tích cơ cấu tài chính.</p>
            </header>
            <ul>
              {buildBalanceHighlights(dashboard, latest).map((item) => (
                <li key={item.text} className={`bctc-income-highlight bctc-income-highlight--${item.tone}`}>
                  <span>{item.icon}</span>
                  <p>{item.text}</p>
                </li>
              ))}
            </ul>
            <a href="#bctc-balance-detail">Xem chi tiết phân tích →</a>
          </article>
        </section>
      </section>
    )
  }

  if (section === 'cash-flow') {
    const cashRows = buildCashFlowPeriodRows(analysis, dashboard.cashFlow)
    const cashCards = buildCashFlowKpiCards(dashboard, cashRows)
    return (
      <section className="bctc-section-panel bctc-cash-view" aria-label={tab.label}>
        <section className="bctc-income-control-band bctc-cash-control-band">
          <div className="bctc-income-company">
            <div className="bctc-logo" aria-hidden="true">{(analysis?.ticker || 'FPT').slice(0, 3)}</div>
            <div>
              <h2>{dashboard.companyName}</h2>
              <p>Ngành: {analysis?.industry || 'Công nghệ thông tin'} · {dashboard.exchange}: {analysis?.ticker || DEFAULT_TICKER}</p>
            </div>
          </div>
          <label>
            <span>Kỳ báo cáo</span>
            <select defaultValue={mode === 'quarter' ? 'quarter' : 'year'}>
              <option value="quarter">Quý</option>
              <option value="year">Năm</option>
            </select>
          </label>
          <label>
            <span>So sánh với</span>
            <select defaultValue="same-period">
              <option value="same-period">Cùng kỳ năm trước</option>
              <option value="previous-period">Kỳ liền trước</option>
            </select>
          </label>
        </section>
        {sectionTabs}

        <section className="bctc-cash-kpis">
          {cashCards.map((item) => (
            <article key={item.label} className={`bctc-cash-kpi bctc-cash-kpi--${item.tone || 'neutral'}`}>
              <div className="bctc-cash-kpi__icon">{item.icon}</div>
              <div>
                <p>{item.label}</p>
                <h3>{item.value}</h3>
                <span>{item.delta}</span>
              </div>
              <Sparkline tone={item.tone} values={item.sparkValues} />
            </article>
          ))}
        </section>

        <section className="bctc-cash-layout">
          <article className="bctc-chart-card bctc-cash-waterfall-card">
            <header className="bctc-panel-head">
              <div>
                <h2>Cầu nối dòng tiền {analysis?.latest_period || ''}</h2>
                <p>Đơn vị: {dashboard.unit}</p>
              </div>
              <span>Bridge</span>
            </header>
            <CashWaterfallChart rows={cashRows} />
          </article>

          <article className="bctc-chart-card bctc-cash-trend-card">
            <header className="bctc-panel-head">
              <div>
                <h2>Xu hướng dòng tiền qua các kỳ</h2>
                <p>CFO, CFI, CFF và Free Cash Flow.</p>
              </div>
              <span>Cash flow</span>
            </header>
            <CashFlowTrendChart rows={cashRows} />
          </article>

          <article className="bctc-chart-card bctc-cash-quality-card">
            <header className="bctc-panel-head">
              <div>
                <h2>Chất lượng lợi nhuận & chuyển hóa tiền mặt</h2>
                <p>OCF/LNST, capex ratio và cash conversion.</p>
              </div>
              <span>Quality</span>
            </header>
            <CashQualityLineChart rows={cashRows} />
          </article>

          <aside className="bctc-cash-assistant">
            <CashFlowAssistantCard dashboard={dashboard} />
          </aside>

          <CashFlowStatementTable rows={cashRows} />

          <article className="bctc-panel bctc-cash-highlights">
            <header>
              <h2>Điểm nhấn</h2>
              <p>Các tín hiệu cần đọc khi đánh giá chất lượng dòng tiền.</p>
            </header>
            <ul>
              {buildCashFlowHighlights(cashRows, dashboard).map((item) => (
                <li key={item.text} className={`bctc-income-highlight bctc-income-highlight--${item.tone}`}>
                  <span>{item.icon}</span>
                  <p>{item.text}</p>
                </li>
              ))}
            </ul>
            <a href="#bctc-cash-detail">Xem chi tiết phân tích →</a>
          </article>
        </section>
      </section>
    )
  }

  if (section === 'ratios') {
    const ratioRows = buildRatioPeriodRows(analysis, dashboard)
    const ratioCards = buildRatioKpiCards(ratioRows, dashboard)
    const ratioGroups = buildRatioGroups(ratioRows, dashboard)
    return (
      <section className="bctc-section-panel bctc-ratio-view" aria-label={tab.label}>
        <section className="bctc-income-control-band bctc-ratio-control-band">
          <div className="bctc-income-company">
            <div className="bctc-logo" aria-hidden="true">{(analysis?.ticker || 'FPT').slice(0, 3)}</div>
            <div>
              <h2>{dashboard.companyName}</h2>
              <p>Ngành: {analysis?.industry || 'Công nghệ thông tin'} · {dashboard.exchange}: {analysis?.ticker || DEFAULT_TICKER}</p>
            </div>
          </div>
          <label>
            <span>Kỳ báo cáo</span>
            <select defaultValue={mode === 'quarter' ? 'quarter' : 'year'}>
              <option value="quarter">Quý</option>
              <option value="year">Năm</option>
            </select>
          </label>
          <label>
            <span>So sánh với</span>
            <select defaultValue="same-period">
              <option value="same-period">Cùng kỳ năm trước</option>
              <option value="previous-period">Kỳ liền trước</option>
            </select>
          </label>
          <AnalysisStepper />
        </section>
        {sectionTabs}

        <section className="bctc-ratio-kpis">
          {ratioCards.map((item) => (
            <article key={item.label} className={`bctc-ratio-kpi bctc-ratio-kpi--${item.tone || 'neutral'}`}>
              <div className="bctc-ratio-kpi__icon">{item.icon}</div>
              <div>
                <p>{item.label}</p>
                <h3>{item.value}</h3>
                <span>{item.delta}</span>
              </div>
              <Sparkline tone={item.tone} values={item.sparkValues} />
            </article>
          ))}
        </section>

        <section className="bctc-ratio-layout">
          <section className="bctc-ratio-groups">
            {ratioGroups.map((group) => <RatioGroupCard key={group.title} group={group} />)}
          </section>

          <article className="bctc-chart-card bctc-ratio-health-card">
            <header>
              <h2>Bản đồ sức khỏe tài chính</h2>
              <p>Thang điểm 0-100 theo các nhóm chỉ số chính.</p>
            </header>
            <div className="bctc-ratio-health-map">
              <HealthRadar rows={healthRows} />
              <div className="bctc-ratio-health-legend">
                {healthRows.slice(0, 6).map((row) => (
                  <p key={row.label}><span>{row.label}</span><strong>{row.value}</strong></p>
                ))}
              </div>
            </div>
          </article>

          <article className="bctc-chart-card bctc-ratio-trend-card">
            <header className="bctc-panel-head">
              <div>
                <h2>Xu hướng các chỉ số trọng yếu</h2>
                <p>ROE, Current Ratio, Debt/Equity và biên lợi nhuận ròng.</p>
              </div>
              <span>{modeLabel(mode)}</span>
            </header>
            <RatioTrendChart rows={ratioRows} />
          </article>

          <article className="bctc-panel bctc-ratio-highlights">
            <header>
              <h2>Điểm nhấn</h2>
              <p>Tín hiệu học tập cần kiểm tra khi đọc nhóm chỉ số.</p>
            </header>
            <ul>
              {buildRatioHighlights(ratioRows).map((item) => (
                <li key={item.text} className={`bctc-income-highlight bctc-income-highlight--${item.tone}`}>
                  <span>{item.icon}</span>
                  <p>{item.text}</p>
                </li>
              ))}
            </ul>
            <a href="#bctc-ratio-detail">Xem chi tiết phân tích →</a>
          </article>

          <RatioStatementTable rows={ratioRows} />

          <aside className="bctc-ratio-assistant">
            <RatioAssistantCard />
          </aside>
        </section>
      </section>
    )
  }

  if (section === 'horizontal') {
    return (
      <section className="bctc-section-panel" aria-label={tab.label}>
        {sectionTabs}
        <SectionHeader title="Phân tích ngang" note="So sánh biến động từng chỉ tiêu giữa các kỳ gần nhất." />
        <AnalysisTable rows={buildHorizontalRows(analysis)} columns={['Chỉ tiêu', 'Kỳ trước', 'Kỳ hiện tại', 'Thay đổi', '% thay đổi']} />
      </section>
    )
  }

  if (section === 'vertical') {
    return (
      <section className="bctc-section-panel" aria-label={tab.label}>
        {sectionTabs}
        <SectionHeader title="Phân tích dọc" note="Đọc common-size: từng chỉ tiêu chiếm bao nhiêu trong doanh thu hoặc tổng tài sản." />
        <div className="bctc-section-grid">
          <AnalysisTable title="Kết quả kinh doanh / Doanh thu" rows={buildVerticalIncomeRows(latest, analysis?.summary)} columns={['Chỉ tiêu', 'Giá trị', 'Tỷ trọng']} />
          <AnalysisTable title="Bảng cân đối / Tổng tài sản" rows={buildVerticalBalanceRows(latest, analysis?.summary)} columns={['Chỉ tiêu', 'Giá trị', 'Tỷ trọng']} />
        </div>
      </section>
    )
  }

  if (section === 'risk') {
    return (
      <section className="bctc-section-panel" aria-label={tab.label}>
        {sectionTabs}
        <SectionHeader title="Cảnh báo rủi ro" note="Các điểm cần kiểm tra lại trước khi đưa ra nhận định cuối." />
        <div className="bctc-section-grid">
          <article className="bctc-panel">
            <header>
              <h2>Red Flags</h2>
              <p>Dựa trên dữ liệu phân tích và các kiểm tra chất lượng dòng tiền.</p>
            </header>
            {analysis.flags?.length ? (
              <ul className="bctc-flag-list">
                {analysis.flags.slice(0, 8).map((flag) => (
                  <li key={`${flag.level}-${flag.title}`} className={`bctc-flag bctc-flag--${(flag.level || '').toLowerCase()}`}>
                    <strong>{flag.title}</strong>
                    <p>{flag.detail}</p>
                  </li>
                ))}
              </ul>
            ) : <p className="bctc-muted">Chưa có flag nổi bật ở lần chạy hiện tại.</p>}
          </article>
          <article className="bctc-panel">
            <header>
              <h2>Câu hỏi kiểm tra</h2>
              <p>Checklist phân tích nhanh cho người học.</p>
            </header>
            <div className="bctc-check-questions">
              {dashboard.checkQuestions.map((item) => <p key={item}>{item}</p>)}
            </div>
          </article>
        </div>
      </section>
    )
  }

  return (
    <section className="bctc-section-panel" aria-label={tab.label}>
      {sectionTabs}
      <SectionHeader title="Báo cáo" note="Tóm tắt thành báo cáo học tập, không phải khuyến nghị mua bán." />
      <div className="bctc-section-grid">
        <article className="bctc-panel">
          <header>
            <h2>Nhận định tóm tắt</h2>
            <p>Luận điểm tự động từ dữ liệu hiện có.</p>
          </header>
          <ul className="bctc-report-list">
            {dashboard.summaryBullets.map((item) => <li key={item.text}>{item.text}</li>)}
          </ul>
          <p className="bctc-report-conclusion">
            {dashboard.companyName} có health score {dashboard.healthScore}/100. Cần đọc cùng chất lượng dòng tiền,
            biên lợi nhuận và đòn bẩy trước khi kết luận.
          </p>
        </article>
        <article className="bctc-panel bctc-panel--peer">
          <header className="bctc-panel-head">
            <div>
              <h2>So sánh peer</h2>
              <p>Đặt doanh nghiệp cạnh nhóm so sánh.</p>
            </div>
            <span>{peerLoading ? 'Syncing' : 'Ready'}</span>
          </header>
          <PeerTable rows={dashboard.peerRows} />
        </article>
      </div>
    </section>
  )
}

function SectionHeader({ title, note }) {
  return (
    <header className="bctc-section-head">
      <div>
        <p className="bctc-eyebrow">BCTC Section</p>
        <h2>{title}</h2>
      </div>
      <p>{note}</p>
    </header>
  )
}

function BctcTabs({ activeSection, onSelect }) {
  return (
    <nav className="bctc-tabs" aria-label="BCTC sections">
      {BCTC_TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          className={activeSection === tab.key ? 'is-active' : ''}
          aria-pressed={activeSection === tab.key}
          onClick={() => onSelect(tab.key)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}

function AnalysisStepper() {
  return (
    <div className="bctc-stepper" aria-label="Quy trình phân tích">
      {['Đọc số liệu', 'Tính chỉ số', 'Phân tích', 'Kết luận'].map((step, index) => (
        <span key={step} className={index === 0 ? 'is-active' : ''}>
          <b>{index + 1}</b>{step}
          <small>{index === 0 ? 'Hiểu bức tranh tổng thể' : index === 1 ? 'Tính toán các tỷ lệ' : index === 2 ? 'Đánh giá xu hướng' : 'Rút ra nhận định'}</small>
        </span>
      ))}
    </div>
  )
}

function MiniMetricGrid({ items }) {
  return (
    <div className="bctc-mini-metric-grid">
      {items.map((item) => (
        <div key={item.label} className={`bctc-mini-metric bctc-mini-metric--${item.tone}`}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          <em>{item.note}</em>
        </div>
      ))}
    </div>
  )
}

function StatementTable({ title, rows }) {
  return <AnalysisTable title={title} rows={rows} columns={['Chỉ tiêu', 'Giá trị', 'Ghi chú']} />
}

function AnalysisTable({ title, rows, columns }) {
  return (
    <article className="bctc-panel bctc-data-table">
      {title ? <h2>{title}</h2> : null}
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.join('-')}>
              {row.map((cell, index) => <td key={`${cell}-${index}`}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  )
}

function PeerTable({ rows }) {
  if (!rows.length) return <p className="bctc-muted">Chưa có peer compare. Bấm “So sánh peers” để tải.</p>
  return (
    <div className="bctc-peer-table">
      <table>
        <thead>
          <tr>
            <th>Doanh nghiệp</th>
            <th>Doanh thu</th>
            <th>Biên ròng</th>
            <th>ROE</th>
            <th>Debt / Equity</th>
            <th>Đánh giá</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((metric) => (
            <tr key={metric.company} className={`${metric.selected ? 'is-selected' : ''} ${metric.tone ? `bctc-peer-row--${metric.tone}` : ''}`}>
              <td>{metric.company}</td>
              <td>{metric.revenueGrowth}</td>
              <td>{metric.netMargin}</td>
              <td>{metric.roe}</td>
              <td>{metric.debtToEquity}</td>
              <td>{metric.assessment}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function IncomeAssistantCard({ dashboard }) {
  return (
    <div className="bctc-income-assistant__stack">
      <article className="bctc-income-assistant-card">
        <header>
          <h2>Trợ lý học tập <span>AI</span></h2>
        </header>
        <div className="bctc-income-assistant-block">
          <h3>Giải thích nhanh</h3>
          <p><strong>Biên lợi nhuận gộp:</strong> phản ánh hiệu quả kiểm soát giá vốn.</p>
          <p><strong>Biên lợi nhuận ròng:</strong> đo lường khả năng tạo lợi nhuận sau mọi chi phí.</p>
        </div>
        <div className="bctc-income-formulas">
          <span>Biên gộp = Lợi nhuận gộp / Doanh thu thuần</span>
          <span>Biên ròng = LNST / Doanh thu thuần</span>
        </div>
      </article>
      <article className="bctc-income-assistant-card">
        <h3>Gợi ý phân tích</h3>
        {dashboard.summaryBullets.slice(0, 3).map((item) => (
          <p key={item.text} className="bctc-income-check">✓ {item.text}</p>
        ))}
      </article>
      <article className="bctc-income-assistant-card">
        <h3>Câu hỏi học tập</h3>
        <p>Biên gộp giảm nhưng LNST vẫn tăng vì sao?</p>
        <p>Yếu tố nào ảnh hưởng đến biên lợi nhuận ròng?</p>
        <button type="button">Xem giải thích phân tích →</button>
      </article>
    </div>
  )
}

function BalanceAssetStackChart({ rows }) {
  const cleanRows = rows.slice(-5)
  const maxTotal = Math.max(...cleanRows.map((row) => Number(row.totalAssets) || 0), 1)
  return (
    <div className="bctc-balance-stack-chart">
      <div className="bctc-balance-legend">
        <span><i className="is-cash" />Tiền mặt</span>
        <span><i className="is-receivable" />Phải thu</span>
        <span><i className="is-inventory" />Hàng tồn kho</span>
        <span><i className="is-fixed" />Tài sản cố định</span>
        <span><i className="is-other" />Tài sản khác</span>
      </div>
      <div className="bctc-balance-bars">
        {cleanRows.map((row) => {
          const total = Math.max(Number(row.totalAssets) || 0, 1)
          const other = Math.max(0, total - row.cash - row.receivables - row.inventory - row.fixedAssets)
          const height = Math.max(32, (total / maxTotal) * 100)
          return (
            <div key={row.period} className="bctc-balance-bar-group">
              <div className="bctc-balance-bar" style={{ height: `${height}%` }}>
                <i className="is-cash" style={{ height: `${ratioPct(row.cash, total)}%` }} />
                <i className="is-receivable" style={{ height: `${ratioPct(row.receivables, total)}%` }} />
                <i className="is-inventory" style={{ height: `${ratioPct(row.inventory, total)}%` }} />
                <i className="is-fixed" style={{ height: `${ratioPct(row.fixedAssets, total)}%` }} />
                <i className="is-other" style={{ height: `${Math.max(4, ratioPct(other, total))}%` }} />
              </div>
              <span>{shortPeriodLabel(row.period)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function BalanceFundingDonut({ rows, latest }) {
  const row = rows.at(-1) || {}
  const shortDebt = firstNumber(latest.short_term_debt, row.shortTermDebt, row.totalLiabilities * 0.58)
  const longDebt = firstNumber(latest.long_term_debt, row.longTermDebt, row.totalLiabilities - shortDebt)
  const equity = firstNumber(row.equity, latest.equity)
  const total = Math.max(firstNumber(shortDebt, 0) + firstNumber(longDebt, 0) + firstNumber(equity, 0), 1)
  const shortPct = ratioPct(shortDebt, total)
  const longPct = ratioPct(longDebt, total)
  const equityPct = ratioPct(equity, total)
  return (
    <div className="bctc-balance-donut-wrap">
      <div
        className="bctc-balance-donut"
        style={{
          '--short': `${shortPct}%`,
          '--long': `${shortPct + longPct}%`,
        }}
      >
        <strong>{formatCompactNumber(row.totalAssets)}</strong>
        <span>Tổng tài sản</span>
      </div>
      <div className="bctc-balance-donut-list">
        <p><i className="is-short" />Nợ ngắn hạn <strong>{formatPercent(shortPct)}</strong></p>
        <p><i className="is-long" />Nợ dài hạn <strong>{formatPercent(longPct)}</strong></p>
        <p><i className="is-equity" />Vốn chủ sở hữu <strong>{formatPercent(equityPct)}</strong></p>
        <em>Tại {row.period || 'kỳ mới nhất'}</em>
      </div>
    </div>
  )
}

function BalanceLiquidityChart({ rows }) {
  const cleanRows = rows.slice(-6)
  const workingCapitalValues = cleanRows.map((row) => row.workingCapital).filter(Number.isFinite)
  const maxWorking = Math.max(...workingCapitalValues.map(Math.abs), 1)
  const currentPoints = chartPolyline(cleanRows.map((row) => row.currentRatio), 0, 3)
  const quickPoints = chartPolyline(cleanRows.map((row) => row.quickRatio), 0, 3)
  const workingPoints = chartPolyline(cleanRows.map((row) => row.workingCapital / maxWorking), 0, 1)
  return (
    <div className="bctc-balance-line-chart">
      <div className="bctc-balance-legend">
        <span><i className="is-working" />Vốn lưu động</span>
        <span><i className="is-current" />Current Ratio</span>
        <span><i className="is-quick" />Quick Ratio</span>
      </div>
      <svg viewBox="0 0 520 220" role="img" aria-label="Liquidity trend">
        {[40, 80, 120, 160].map((y) => <line key={y} x1="42" x2="500" y1={y} y2={y} className="bctc-balance-grid-line" />)}
        <polyline points={workingPoints} className="bctc-balance-line is-working" />
        <polyline points={currentPoints} className="bctc-balance-line is-current" />
        <polyline points={quickPoints} className="bctc-balance-line is-quick" />
        {cleanRows.map((row, index) => (
          <text key={row.period} x={52 + index * (438 / Math.max(1, cleanRows.length - 1))} y="204" textAnchor="middle">
            {shortPeriodLabel(row.period)}
          </text>
        ))}
      </svg>
    </div>
  )
}

function BalanceAssistantCard({ dashboard }) {
  return (
    <div className="bctc-income-assistant__stack">
      <article className="bctc-income-assistant-card bctc-balance-assistant-card">
        <header>
          <h2>Trợ lý học tập <span>AI</span></h2>
        </header>
        <div className="bctc-income-assistant-block">
          <h3>Giải thích nhanh</h3>
          <p><strong>Current Ratio:</strong> Khả năng thanh toán nợ ngắn hạn bằng tài sản ngắn hạn.</p>
          <p><strong>Debt/Equity:</strong> Đo lường mức độ đòn bẩy tài chính.</p>
          <p><strong>Working Capital:</strong> Tài sản ngắn hạn trừ nợ ngắn hạn. Dương là tốt.</p>
        </div>
        <div className="bctc-income-formulas">
          <span>Current Ratio = TSNH / NNH</span>
          <span>Debt/Equity = Nợ phải trả / Vốn CSH</span>
          <span>Working Capital = TSNH - NNH</span>
        </div>
      </article>
      <article className="bctc-income-assistant-card">
        <h3>Gợi ý phân tích</h3>
        {dashboard.leverageMetrics.slice(0, 3).map((item) => (
          <p key={item.label} className="bctc-income-check">✓ {item.label}: {item.value} - {item.note}</p>
        ))}
      </article>
      <article className="bctc-income-assistant-card">
        <h3>Câu hỏi học tập</h3>
        <p>Tại sao doanh nghiệp cần duy trì Current Ratio lớn hơn 1?</p>
        <p>Nợ/Vốn chủ tăng có luôn xấu không?</p>
        <p>Vốn lưu động âm ảnh hưởng thế nào đến hoạt động?</p>
        <button type="button">Xem giải thích phân tích →</button>
      </article>
    </div>
  )
}

function BalanceStatementTable({ rows }) {
  const visibleRows = rows.slice(-5)
  const lines = [
    ['cash', 'Tiền & tương đương tiền'],
    ['receivables', 'Phải thu khách hàng'],
    ['inventory', 'Hàng tồn kho'],
    ['currentAssets', 'Tài sản ngắn hạn'],
    ['fixedAssets', 'Tài sản cố định'],
    ['otherAssets', 'Tài sản khác dài hạn'],
    ['totalAssets', 'Tổng tài sản'],
    ['shortTermDebt', 'Nợ ngắn hạn'],
    ['longTermDebt', 'Nợ dài hạn'],
    ['totalLiabilities', 'Tổng nợ phải trả'],
    ['equity', 'Vốn chủ sở hữu'],
  ]
  return (
    <article className="bctc-panel bctc-data-table bctc-balance-table">
      <h2>Bảng cân đối kế toán</h2>
      <table>
        <thead>
          <tr>
            <th>Chỉ tiêu</th>
            {visibleRows.map((row) => <th key={row.period}>{row.period}</th>)}
            <th>YoY</th>
            <th>QoQ</th>
          </tr>
        </thead>
        <tbody>
          {lines.map(([key, label]) => {
            const current = visibleRows.at(-1)?.[key]
            const previous = visibleRows.at(-2)?.[key]
            const first = visibleRows[0]?.[key]
            return (
              <tr key={key} className={['currentAssets', 'totalAssets', 'totalLiabilities'].includes(key) ? 'is-emphasis' : ''}>
                <td>{label}</td>
                {visibleRows.map((row) => <td key={`${key}-${row.period}`}>{formatCompactNumber(row[key])}</td>)}
                <td>{formatSignedPercent(growthPercent(current, first))}</td>
                <td>{formatSignedPercent(growthPercent(current, previous))}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </article>
  )
}

function CashWaterfallChart({ rows }) {
  const latest = rows.at(-1) || {}
  const opening = firstNumber(latest.openingCash, latest.cash - latest.cfo - latest.cfi - latest.cff - latest.fxOther)
  const closing = firstNumber(latest.cash, opening + latest.cfo + latest.cfi + latest.cff + latest.fxOther)
  const steps = [
    { key: 'opening', label: 'Tiền đầu kỳ', value: opening, tone: 'base' },
    { key: 'cfo', label: 'CFO', value: latest.cfo, tone: 'positive' },
    { key: 'cfi', label: 'CFI', value: latest.cfi, tone: 'negative' },
    { key: 'cff', label: 'CFF', value: latest.cff, tone: 'negative' },
    { key: 'fx', label: 'FX & khác', value: latest.fxOther, tone: Number(latest.fxOther) >= 0 ? 'positive' : 'negative' },
    { key: 'closing', label: 'Tiền cuối kỳ', value: closing, tone: 'base' },
  ]
  const maxAbs = Math.max(...steps.map((item) => Math.abs(Number(item.value) || 0)), 1)
  return (
    <div className="bctc-cash-waterfall">
      {steps.map((item) => {
        const height = Math.max(18, (Math.abs(Number(item.value) || 0) / maxAbs) * 170)
        return (
          <div key={item.key} className={`bctc-cash-waterfall__step bctc-cash-waterfall__step--${item.tone}`}>
            <strong>{formatCompactNumber(item.value)}</strong>
            <i style={{ height: `${height}px` }} />
            <span>{item.label}</span>
          </div>
        )
      })}
    </div>
  )
}

function CashFlowTrendChart({ rows }) {
  const cleanRows = rows.slice(-7)
  const maxAbs = Math.max(...cleanRows.flatMap((row) => [row.cfo, row.cfi, row.cff, row.fcf].map((value) => Math.abs(Number(value) || 0))), 1)
  return (
    <div className="bctc-cash-trend">
      <div className="bctc-balance-legend">
        <span><i className="is-cfo" />CFO</span>
        <span><i className="is-cfi" />CFI</span>
        <span><i className="is-cff" />CFF</span>
        <span><i className="is-fcf" />FCF</span>
      </div>
      <div className="bctc-cash-trend__plot">
        {cleanRows.map((row) => (
          <div key={row.period} className="bctc-cash-trend__group">
            {[
              ['cfo', row.cfo],
              ['cfi', row.cfi],
              ['cff', row.cff],
              ['fcf', row.fcf],
            ].map(([key, value]) => (
              <i
                key={key}
                className={`is-${key} ${Number(value) < 0 ? 'is-negative' : ''}`}
                style={{ height: `${Math.max(6, (Math.abs(Number(value) || 0) / maxAbs) * 92)}%` }}
                title={`${key.toUpperCase()}: ${formatCompactNumber(value)}`}
              />
            ))}
            <span>{shortPeriodLabel(row.period)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function CashQualityLineChart({ rows }) {
  const cleanRows = rows.slice(-7)
  const ocfPoints = chartPolyline(cleanRows.map((row) => row.ocfToNetIncome), 0, 2)
  const capexPoints = chartPolyline(cleanRows.map((row) => row.capexRatio), 0, 60)
  const conversionPoints = chartPolyline(cleanRows.map((row) => row.cashConversion), 0, 120)
  return (
    <div className="bctc-balance-line-chart bctc-cash-quality">
      <div className="bctc-balance-legend">
        <span><i className="is-ocf" />OCF/LNST</span>
        <span><i className="is-capex" />Capex ratio</span>
        <span><i className="is-conversion" />Chuyển hóa tiền mặt</span>
      </div>
      <svg viewBox="0 0 520 220" role="img" aria-label="Cash quality trend">
        {[40, 80, 120, 160].map((y) => <line key={y} x1="42" x2="500" y1={y} y2={y} className="bctc-balance-grid-line" />)}
        <polyline points={ocfPoints} className="bctc-balance-line is-ocf" />
        <polyline points={capexPoints} className="bctc-balance-line is-capex" />
        <polyline points={conversionPoints} className="bctc-balance-line is-conversion" />
        {cleanRows.map((row, index) => (
          <text key={row.period} x={52 + index * (438 / Math.max(1, cleanRows.length - 1))} y="204" textAnchor="middle">
            {shortPeriodLabel(row.period)}
          </text>
        ))}
      </svg>
    </div>
  )
}

function CashFlowAssistantCard({ dashboard }) {
  return (
    <div className="bctc-income-assistant__stack">
      <article className="bctc-income-assistant-card bctc-cash-assistant-card">
        <header>
          <h2>Trợ lý học tập <span>AI</span></h2>
        </header>
        <div className="bctc-income-assistant-block">
          <h3>Giải thích nhanh</h3>
          <p><strong>CFO:</strong> tiền thuần từ hoạt động kinh doanh.</p>
          <p><strong>FCF:</strong> dòng tiền tự do sau khi trừ chi đầu tư tài sản cố định.</p>
          <p><strong>OCF/LNST:</strong> chỉ số phản ánh chất lượng lợi nhuận.</p>
        </div>
        <div className="bctc-income-formulas">
          <span>OCF/LNST = CFO / LNST</span>
          <span>FCF = CFO - Capex</span>
          <span>Capex ratio = Capex / Doanh thu</span>
        </div>
      </article>
      <article className="bctc-income-assistant-card">
        <h3>Gợi ý phân tích</h3>
        <p className="bctc-income-check">✓ CFO tăng trưởng tốt thường cho thấy doanh nghiệp tạo tiền bền hơn.</p>
        <p className="bctc-income-check">✓ CFI âm có thể bình thường nếu doanh nghiệp đang mở rộng.</p>
        <p className="bctc-income-check">✓ OCF/LNST lớn hơn 1 thường là tín hiệu lợi nhuận chất lượng.</p>
      </article>
      <article className="bctc-income-assistant-card">
        <h3>Câu hỏi học tập</h3>
        <p>Vì sao lợi nhuận dương nhưng CFO có thể âm?</p>
        <p>FCF dương có ý nghĩa gì với doanh nghiệp?</p>
        <p>OCF/LNST bao nhiêu là tốt?</p>
        <button type="button">Xem giải thích phân tích →</button>
      </article>
    </div>
  )
}

function CashFlowStatementTable({ rows }) {
  const visibleRows = rows.slice(-7)
  const lines = [
    ['netIncome', 'LNST'],
    ['depreciation', 'Khấu hao & phân bổ'],
    ['workingCapitalChange', 'Thay đổi vốn lưu động'],
    ['cfo', 'Lưu chuyển tiền từ HĐKD (CFO)'],
    ['capex', 'Chi đầu tư TSCĐ'],
    ['assetPurchase', 'Mua/bán đầu tư & góp vốn'],
    ['cfi', 'Lưu chuyển tiền từ HĐĐT (CFI)'],
    ['dividends', 'Cổ tức đã trả'],
    ['netBorrowing', 'Vay ròng'],
    ['cff', 'Lưu chuyển tiền từ HĐTC (CFF)'],
    ['fxOther', 'FX & các khoản khác'],
    ['openingCash', 'Tiền đầu kỳ'],
    ['cash', 'Tiền cuối kỳ'],
  ]
  return (
    <article className="bctc-panel bctc-data-table bctc-cash-table">
      <h2>Báo cáo lưu chuyển tiền tệ</h2>
      <table>
        <thead>
          <tr>
            <th>Chỉ tiêu</th>
            {visibleRows.map((row) => <th key={row.period}>{row.period}</th>)}
            <th>YoY</th>
            <th>QoQ</th>
          </tr>
        </thead>
        <tbody>
          {lines.map(([key, label]) => {
            const current = visibleRows.at(-1)?.[key]
            const previous = visibleRows.at(-2)?.[key]
            const first = visibleRows[0]?.[key]
            return (
              <tr key={key} className={['cfo', 'cfi', 'cff', 'cash'].includes(key) ? `is-${key}` : ''}>
                <td>{label}</td>
                {visibleRows.map((row) => <td key={`${key}-${row.period}`}>{formatCompactNumber(row[key])}</td>)}
                <td>{formatSignedPercent(growthPercent(current, first))}</td>
                <td>{formatSignedPercent(growthPercent(current, previous))}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </article>
  )
}

function RatioGroupCard({ group }) {
  return (
    <article className={`bctc-ratio-group bctc-ratio-group--${group.tone}`}>
      <header>
        <h2><span>{group.icon}</span>{group.title}</h2>
      </header>
      <div className="bctc-ratio-bars">
        {group.items.map((item) => (
          <div key={item.label} className={`bctc-ratio-bar bctc-ratio-bar--${item.tone || 'neutral'}`}>
            <div>
              <strong>{item.label}</strong>
              <em>{item.value}</em>
              <span>{scoreLabel(item.tone)}</span>
            </div>
            <div className="bctc-ratio-track">
              <i style={{ width: `${item.progress}%` }} />
              <b style={{ left: `${item.benchmark}%` }} />
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

function RatioTrendChart({ rows }) {
  const cleanRows = rows.slice(-7)
  const roePoints = chartPolyline(cleanRows.map((row) => row.roe), 0, 35)
  const currentPoints = chartPolyline(cleanRows.map((row) => row.currentRatio), 0, 3)
  const debtPoints = chartPolyline(cleanRows.map((row) => row.debtToEquity), 0, 2)
  const netMarginPoints = chartPolyline(cleanRows.map((row) => row.netMargin), 0, 25)
  return (
    <div className="bctc-ratio-trend">
      <div className="bctc-balance-legend">
        <span><i className="is-roe" />ROE</span>
        <span><i className="is-current-ratio" />Current Ratio</span>
        <span><i className="is-debt-equity" />Debt/Equity</span>
        <span><i className="is-net-margin" />Biên lợi nhuận ròng</span>
      </div>
      <svg viewBox="0 0 520 220" role="img" aria-label="Ratio trend chart">
        {[40, 80, 120, 160].map((y) => <line key={y} x1="42" x2="500" y1={y} y2={y} className="bctc-balance-grid-line" />)}
        <polyline points={roePoints} className="bctc-balance-line is-roe" />
        <polyline points={currentPoints} className="bctc-balance-line is-current-ratio" />
        <polyline points={debtPoints} className="bctc-balance-line is-debt-equity" />
        <polyline points={netMarginPoints} className="bctc-balance-line is-net-margin" />
        {cleanRows.map((row, index) => (
          <text key={row.period} x={52 + index * (438 / Math.max(1, cleanRows.length - 1))} y="204" textAnchor="middle">
            {shortPeriodLabel(row.period)}
          </text>
        ))}
      </svg>
    </div>
  )
}

function RatioStatementTable({ rows }) {
  const visibleRows = rows.slice(-7)
  const lines = [
    ['currentRatio', 'Current Ratio (lần)', 'ratio'],
    ['quickRatio', 'Quick Ratio (lần)', 'ratio'],
    ['cashRatio', 'Cash Ratio (lần)', 'ratio'],
    ['debtToEquity', 'Debt/Equity (lần)', 'ratio'],
    ['debtToAsset', 'Debt/Asset (lần)', 'ratio'],
    ['interestCoverage', 'Interest Coverage (lần)', 'ratio'],
    ['roa', 'ROA (%)', 'percent'],
    ['roe', 'ROE (%)', 'percent'],
    ['netMargin', 'Biên lợi nhuận ròng (%)', 'percent'],
  ]
  return (
    <article className="bctc-panel bctc-data-table bctc-ratio-table">
      <h2>Bảng chỉ số tài chính</h2>
      <table>
        <thead>
          <tr>
            <th>Chỉ tiêu</th>
            {visibleRows.map((row) => <th key={row.period}>{row.period}</th>)}
            <th>YoY</th>
            <th>Đánh giá</th>
          </tr>
        </thead>
        <tbody>
          {lines.map(([key, label, type]) => {
            const current = visibleRows.at(-1)?.[key]
            const first = visibleRows[0]?.[key]
            const tone = ratioTone(key, current)
            return (
              <tr key={key} className={tone === 'warn' ? 'is-warn' : tone === 'good' ? 'is-good' : ''}>
                <td>{label}</td>
                {visibleRows.map((row) => (
                  <td key={`${key}-${row.period}`}>{type === 'percent' ? formatPercent(row[key]) : formatMaybeNumber(row[key])}</td>
                ))}
                <td>{formatSignedPercent(growthPercent(current, first))}</td>
                <td><span className={`bctc-ratio-status bctc-ratio-status--${tone || 'neutral'}`}>{scoreLabel(tone)}</span></td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </article>
  )
}

function RatioAssistantCard() {
  return (
    <div className="bctc-income-assistant__stack">
      <article className="bctc-income-assistant-card bctc-ratio-assistant-card">
        <header>
          <h2>Trợ lý học tập <span>AI</span></h2>
        </header>
        <div className="bctc-income-assistant-block">
          <h3>Giải thích nhanh</h3>
          <p>Nhóm chỉ số giúp đọc sức khỏe tài chính theo 4 khía cạnh: thanh khoản, đòn bẩy, hiệu quả và sinh lời.</p>
        </div>
        <div className="bctc-income-formulas">
          <span>ROE = LNST / Vốn CSH bình quân</span>
          <span>Current Ratio = TSNH / Nợ ngắn hạn</span>
          <span>Quick Ratio = (TSNH - Hàng tồn kho) / Nợ ngắn hạn</span>
          <span>Debt/Equity = Tổng nợ phải trả / Vốn chủ sở hữu</span>
        </div>
      </article>
      <article className="bctc-income-assistant-card">
        <h3>Gợi ý phân tích</h3>
        <p className="bctc-income-check">✓ ROE duy trì trên mức hợp lý cho thấy khả năng sinh lời đáng chú ý.</p>
        <p className="bctc-income-check">✓ Thanh khoản hiện tại cần đọc cùng dòng tiền hoạt động.</p>
        <p className="bctc-income-check">✓ Đòn bẩy thấp giúp giảm rủi ro tài chính và chi phí lãi vay.</p>
        <p className="bctc-income-check">✓ Hiệu quả hoạt động ổn định nếu vòng quay phải thu tích cực.</p>
      </article>
      <article className="bctc-income-assistant-card">
        <h3>Câu hỏi học tập</h3>
        <p>Tại sao ROE được coi là chỉ số quan trọng nhất?</p>
        <p>Current Ratio quá cao có phải luôn tốt?</p>
        <p>Vì sao Interest Coverage càng cao càng tốt?</p>
        <button type="button">Xem giải thích phân tích →</button>
      </article>
    </div>
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
    .map((item) => {
      const next = { ...item }
      delete next._rank
      return next
    })

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

function buildIncomeRows(latest, summary = {}) {
  return [
    ['Doanh thu thuần', formatCompactNumber(firstNumber(latest.revenue, summary.revenue)), `${formatPercent(summary.revenue_growth_yoy_pct)} YoY`],
    ['Lợi nhuận sau thuế', formatCompactNumber(firstNumber(latest.net_income, summary.net_income)), `${formatPercent(summary.net_income_growth_yoy_pct)} YoY`],
    ['Biên lợi nhuận ròng', formatPercent(firstNumber(latest.net_margin_pct, summary.net_margin_pct)), 'LNST / Doanh thu'],
    ['ROE', formatPercent(firstNumber(summary.roe_pct)), 'LNST / Vốn chủ'],
  ]
}

function buildIncomeKpiCards(dashboard, latest, summary = {}) {
  const revenue = firstNumber(latest.revenue, summary.revenue)
  const netIncome = firstNumber(latest.net_income, summary.net_income)
  const grossMargin = firstNumber(latest.gross_margin_pct, summary.gross_margin_pct)
  const netMargin = firstNumber(latest.net_margin_pct, summary.net_margin_pct)
  const grossProfit = Number.isFinite(revenue) && Number.isFinite(grossMargin) ? revenue * grossMargin / 100 : null
  const ebit = firstNumber(latest.ebit, latest.operating_income, summary.ebit)

  return [
    {
      icon: '$',
      label: 'Doanh thu thuần',
      value: formatCompactNumber(revenue),
      delta: `▲ ${formatPercent(summary.revenue_growth_yoy_pct)} YoY`,
      tone: trendTone(summary.revenue_growth_yoy_pct) || 'good',
      sparkValues: dashboard.kpis[0]?.sparkValues || [],
    },
    {
      icon: '▦',
      label: 'Lợi nhuận gộp',
      value: formatCompactNumber(grossProfit),
      delta: '▲ kiểm tra giá vốn',
      tone: 'good',
      sparkValues: dashboard.kpis[0]?.sparkValues || [],
    },
    {
      icon: '⌁',
      label: 'EBIT',
      value: formatCompactNumber(ebit),
      delta: '▲ hiệu quả vận hành',
      tone: 'caution',
      sparkValues: dashboard.marginRows.map((row) => row.operating_margin),
    },
    {
      icon: '▣',
      label: 'LNST',
      value: formatCompactNumber(netIncome),
      delta: `▲ ${formatPercent(summary.net_income_growth_yoy_pct)} YoY`,
      tone: trendTone(summary.net_income_growth_yoy_pct) || 'good',
      sparkValues: dashboard.kpis[1]?.sparkValues || [],
    },
    {
      icon: '%',
      label: 'Biên lợi nhuận gộp',
      value: formatPercent(grossMargin),
      delta: '▼ đọc cùng giá vốn',
      tone: Number(grossMargin) < 25 ? 'warn' : 'good',
      sparkValues: dashboard.marginRows.map((row) => row.gross_margin),
    },
    {
      icon: '%',
      label: 'Biên lợi nhuận ròng',
      value: formatPercent(netMargin),
      delta: '▲ so với cùng kỳ',
      tone: scoreTone(netMargin, 5, 12) || 'good',
      sparkValues: dashboard.marginRows.map((row) => row.net_margin),
    },
  ]
}

function buildIncomeStatementTableRows(analysis, dashboard) {
  const latestRows = [...(analysis?.periods || [])].slice(-4)
  const summary = analysis?.summary || {}
  const latest = latestRows.at(-1) || latestPeriod(analysis) || {}
  const revenue = firstNumber(latest.revenue, summary.revenue)
  const netIncome = firstNumber(latest.net_income, summary.net_income)
  const grossMargin = firstNumber(latest.gross_margin_pct, summary.gross_margin_pct)
  const grossProfit = Number.isFinite(revenue) && Number.isFinite(grossMargin) ? revenue * grossMargin / 100 : null
  const cogs = Number.isFinite(revenue) && Number.isFinite(grossProfit) ? revenue - grossProfit : null
  const ebit = firstNumber(latest.ebit, latest.operating_income, summary.ebit)

  return [
    ['Doanh thu thuần', formatCompactNumber(revenue), `${formatPercent(summary.revenue_growth_yoy_pct)} YoY`],
    ['Giá vốn hàng bán', formatCompactNumber(cogs), 'Ước tính từ biên gộp nếu dữ liệu thiếu'],
    ['Lợi nhuận gộp', formatCompactNumber(grossProfit), `${formatPercent(grossMargin)} biên gộp`],
    ['EBIT', formatCompactNumber(ebit), 'Lợi nhuận trước lãi vay và thuế'],
    ['LNST', formatCompactNumber(netIncome), `${formatPercent(summary.net_income_growth_yoy_pct)} YoY`],
    ['Biên ròng', formatPercent(firstNumber(latest.net_margin_pct, summary.net_margin_pct)), 'LNST / Doanh thu thuần'],
    ['Quality read', `${dashboard.healthScore}/100`, 'Đọc cùng dòng tiền và bảng cân đối'],
  ]
}

function buildBalanceRows(latest, summary = {}) {
  return [
    ['Tổng tài sản', formatCompactNumber(firstNumber(latest.total_assets, latest.assets, summary.total_assets)), 'Quy mô bảng cân đối'],
    ['Nợ phải trả', formatCompactNumber(firstNumber(latest.total_liabilities, latest.liabilities, summary.total_liabilities)), 'Nguồn vốn vay/nợ'],
    ['Vốn chủ sở hữu', formatCompactNumber(firstNumber(latest.equity, summary.equity)), 'Vốn thuộc cổ đông'],
    ['Debt / Equity', formatMaybeNumber(summary.debt_to_equity), 'Đòn bẩy tài chính'],
    ['Current Ratio', formatMaybeNumber(summary.current_ratio), 'Thanh khoản ngắn hạn'],
  ]
}

function buildBalancePeriodRows(analysis) {
  return [...(analysis?.periods || [])]
    .slice()
    .sort((a, b) => {
      const ay = Number(a.year || 0)
      const by = Number(b.year || 0)
      if (ay !== by) return ay - by
      return Number(a.quarter || 0) - Number(b.quarter || 0)
    })
    .map((item) => {
      const totalAssets = firstNumber(item.total_assets, item.assets)
      const currentAssets = firstNumber(item.current_assets, totalAssets ? totalAssets * 0.55 : null)
      const currentLiabilities = firstNumber(item.current_liabilities, item.short_term_debt, item.total_liabilities ? item.total_liabilities * 0.58 : null)
      const inventory = firstNumber(item.inventory, currentAssets ? currentAssets * 0.1 : null)
      const cash = firstNumber(item.cash, currentAssets ? currentAssets * 0.28 : null)
      const receivables = firstNumber(item.receivables, currentAssets ? currentAssets * 0.34 : null)
      const fixedAssets = firstNumber(item.fixed_assets, totalAssets && currentAssets ? Math.max(0, (totalAssets - currentAssets) * 0.68) : null)
      const totalLiabilities = firstNumber(item.total_liabilities, item.liabilities)
      const equity = firstNumber(item.equity)
      const shortTermDebt = firstNumber(item.short_term_debt, currentLiabilities)
      const longTermDebt = firstNumber(item.long_term_debt, totalLiabilities && shortTermDebt ? totalLiabilities - shortTermDebt : null)
      const workingCapital = Number.isFinite(currentAssets) && Number.isFinite(currentLiabilities) ? currentAssets - currentLiabilities : null
      const currentRatio = Number.isFinite(currentAssets) && Number.isFinite(currentLiabilities) && currentLiabilities !== 0 ? currentAssets / currentLiabilities : null
      const quickRatio = Number.isFinite(currentAssets) && Number.isFinite(inventory) && Number.isFinite(currentLiabilities) && currentLiabilities !== 0
        ? (currentAssets - inventory) / currentLiabilities
        : null
      return {
        period: normalizePeriodLabel(item),
        rawPeriod: item.period,
        year: item.year,
        quarter: item.quarter,
        cash,
        receivables,
        inventory,
        currentAssets,
        fixedAssets,
        otherAssets: totalAssets && currentAssets && fixedAssets ? Math.max(0, totalAssets - currentAssets - fixedAssets) : null,
        totalAssets,
        shortTermDebt,
        longTermDebt,
        totalLiabilities,
        equity,
        workingCapital,
        currentRatio,
        quickRatio,
        debtToEquity: Number.isFinite(totalLiabilities) && Number.isFinite(equity) && equity !== 0 ? totalLiabilities / equity : null,
      }
    })
    .filter((item) => Number.isFinite(item.totalAssets) || Number.isFinite(item.equity) || Number.isFinite(item.totalLiabilities))
}

function buildBalanceKpiCards(dashboard, latest, analysis) {
  const rows = buildBalancePeriodRows(analysis)
  const latestRow = rows.at(-1) || {}
  const previousRow = rows.at(-2) || {}
  const summary = analysis?.summary || {}
  return [
    {
      icon: '$',
      label: 'Tổng tài sản',
      value: formatCompactNumber(latestRow.totalAssets),
      delta: `${formatSignedPercent(growthPercent(latestRow.totalAssets, previousRow.totalAssets))} QoQ`,
      tone: 'good',
      sparkValues: rows.map((row) => row.totalAssets),
    },
    {
      icon: '▣',
      label: 'Tài sản ngắn hạn',
      value: formatCompactNumber(latestRow.currentAssets),
      delta: `${formatSignedPercent(growthPercent(latestRow.currentAssets, previousRow.currentAssets))} QoQ`,
      tone: 'good',
      sparkValues: rows.map((row) => row.currentAssets),
    },
    {
      icon: '▥',
      label: 'Nợ phải trả',
      value: formatCompactNumber(latestRow.totalLiabilities),
      delta: `${formatSignedPercent(growthPercent(latestRow.totalLiabilities, previousRow.totalLiabilities))} QoQ`,
      tone: Number(summary.debt_to_equity) > 1.2 ? 'warn' : 'caution',
      sparkValues: rows.map((row) => row.totalLiabilities),
    },
    {
      icon: '●',
      label: 'Vốn chủ sở hữu',
      value: formatCompactNumber(latestRow.equity),
      delta: `${formatSignedPercent(growthPercent(latestRow.equity, previousRow.equity))} QoQ`,
      tone: 'good',
      sparkValues: rows.map((row) => row.equity),
    },
    {
      icon: '◉',
      label: 'Tiền & tương đương tiền',
      value: formatCompactNumber(latestRow.cash),
      delta: `${formatSignedPercent(growthPercent(latestRow.cash, previousRow.cash))} QoQ`,
      tone: 'good',
      sparkValues: rows.map((row) => row.cash),
    },
  ]
}

function buildBalanceHighlights(dashboard, latest) {
  const assets = firstNumber(latest.total_assets, latest.assets)
  const cash = firstNumber(latest.cash)
  const equity = firstNumber(latest.equity)
  return [
    {
      icon: '↗',
      tone: 'good',
      text: `Tiền & tương đương tiền ở mức ${formatCompactNumber(cash)}, cần đọc cùng nợ ngắn hạn để đánh giá thanh khoản.`,
    },
    {
      icon: '⚖',
      tone: Number(dashboard.leverageMetrics[2]?.value) > 1 ? 'warn' : 'good',
      text: `Debt/Equity hiện ${dashboard.leverageMetrics[2]?.value || 'n/a'}, dùng để đánh giá mức độ đòn bẩy tài chính.`,
    },
    {
      icon: '★',
      tone: 'good',
      text: `Vốn chủ sở hữu ${formatCompactNumber(equity)} trên tổng tài sản ${formatCompactNumber(assets)} cho biết nền tảng vốn của doanh nghiệp.`,
    },
  ]
}

function buildCashFlowPeriodRows(analysis, cashFlow = {}) {
  const qualityPoints = cashFlow?.backend?.points || []
  const pointByPeriod = new Map(qualityPoints.map((item) => [String(item.period || ''), item]))
  const sorted = [...(analysis?.periods || [])].sort((a, b) => String(a.period || '').localeCompare(String(b.period || '')))
  return sorted
    .map((item, index) => {
      const quality = pointByPeriod.get(String(item.period || '')) || {}
      const revenue = firstNumber(item.revenue, quality.revenue)
      const netIncome = firstNumber(item.net_income, quality.net_income)
      const cfo = firstNumber(item.operating_cash_flow, item.cfo, quality.cfo)
      const cfi = firstNumber(item.cash_flow_from_investing, item.cfi, quality.cfi)
      const cff = firstNumber(item.cash_flow_from_financing, item.cff, quality.cff)
      const capex = firstNumber(item.capex, item.capital_expenditure, quality.capex, Number.isFinite(cfi) ? cfi * 0.78 : null)
      const fcf = firstNumber(
        item.free_cash_flow,
        quality.fcf,
        Number.isFinite(cfo) && Number.isFinite(capex) ? cfo - Math.abs(capex) : null,
      )
      const cash = firstNumber(item.cash, item.cash_and_equivalents, quality.cash)
      const previousCash = firstNumber(sorted[index - 1]?.cash, sorted[index - 1]?.cash_and_equivalents)
      const fxOther = firstNumber(
        item.fx_other,
        quality.fx_other,
        Number.isFinite(cash) && Number.isFinite(previousCash) && Number.isFinite(cfo) && Number.isFinite(cfi) && Number.isFinite(cff)
          ? cash - previousCash - cfo - cfi - cff
          : null,
      )
      const depreciation = firstNumber(quality.depreciation, item.depreciation, Number.isFinite(netIncome) ? Math.abs(netIncome) * 0.52 : null)
      const workingCapitalChange = firstNumber(
        quality.working_capital_change,
        item.working_capital_change,
        Number.isFinite(cfo) && Number.isFinite(netIncome) && Number.isFinite(depreciation) ? cfo - netIncome - depreciation : null,
      )

      return {
        period: normalizePeriodLabel(item),
        rawPeriod: item.period,
        revenue,
        netIncome,
        depreciation,
        workingCapitalChange,
        cfo,
        cfi,
        cff,
        capex,
        assetPurchase: firstNumber(item.asset_purchase, quality.asset_purchase, capex),
        dividends: firstNumber(item.dividends, quality.dividends, Number.isFinite(cff) && cff < 0 ? cff * 0.35 : null),
        netBorrowing: firstNumber(item.net_borrowing, quality.net_borrowing, cff),
        fcf,
        fxOther,
        openingCash: previousCash,
        cash,
        ocfToNetIncome: Number.isFinite(cfo) && Number.isFinite(netIncome) && netIncome !== 0 ? cfo / netIncome : null,
        capexRatio: Number.isFinite(capex) && Number.isFinite(revenue) && revenue !== 0 ? (Math.abs(capex) / revenue) * 100 : null,
        cashConversion: Number.isFinite(cfo) && Number.isFinite(revenue) && revenue !== 0 ? (cfo / revenue) * 100 : null,
      }
    })
    .filter((item) => Number.isFinite(item.cfo) || Number.isFinite(item.cfi) || Number.isFinite(item.cff) || Number.isFinite(item.cash))
}

function buildCashFlowKpiCards(dashboard, rows) {
  const latest = rows.at(-1) || {}
  const previous = rows.at(-2) || {}
  return [
    {
      icon: '▣',
      label: 'CFO / Dòng tiền KD',
      value: formatCompactNumber(latest.cfo),
      delta: `${formatSignedPercent(growthPercent(latest.cfo, previous.cfo))} QoQ`,
      tone: Number(latest.cfo) >= 0 ? 'good' : 'warn',
      sparkValues: rows.map((row) => row.cfo),
    },
    {
      icon: '▥',
      label: 'CFI / Dòng tiền đầu tư',
      value: formatCompactNumber(latest.cfi),
      delta: `${formatSignedPercent(growthPercent(latest.cfi, previous.cfi))} QoQ`,
      tone: Number(latest.cfi) < 0 ? 'caution' : 'good',
      sparkValues: rows.map((row) => row.cfi),
    },
    {
      icon: '▤',
      label: 'CFF / Dòng tiền tài chính',
      value: formatCompactNumber(latest.cff),
      delta: `${formatSignedPercent(growthPercent(latest.cff, previous.cff))} QoQ`,
      tone: Number(latest.cff) < 0 ? 'caution' : 'neutral',
      sparkValues: rows.map((row) => row.cff),
    },
    {
      icon: '▧',
      label: 'Free Cash Flow',
      value: formatCompactNumber(firstNumber(latest.fcf, dashboard.cashFlow?.fcf)),
      delta: `${formatSignedPercent(growthPercent(latest.fcf, previous.fcf))} QoQ`,
      tone: Number(latest.fcf) >= 0 ? 'good' : 'warn',
      sparkValues: rows.map((row) => row.fcf),
    },
    {
      icon: '%',
      label: 'OCF/LNST',
      value: `${formatMaybeNumber(firstNumber(latest.ocfToNetIncome, dashboard.cashFlow?.cfoToNetIncome))} lần`,
      delta: `${formatMaybeNumber(latest.cashConversion)}% cash conversion`,
      tone: Number(latest.ocfToNetIncome) >= 1 ? 'good' : 'caution',
      sparkValues: rows.map((row) => row.ocfToNetIncome),
    },
  ]
}

function buildCashFlowHighlights(rows, dashboard) {
  const latest = rows.at(-1) || {}
  const previous = rows.at(-2) || {}
  const cfoTone = Number(latest.cfo) >= 0 ? 'good' : 'warn'
  const fcfTone = Number(latest.fcf) >= 0 ? 'good' : 'warn'
  return [
    {
      icon: '↗',
      tone: cfoTone,
      text: `CFO đạt ${formatCompactNumber(latest.cfo)}, ${formatSignedPercent(growthPercent(latest.cfo, previous.cfo))} QoQ; dùng để kiểm tra khả năng tạo tiền từ hoạt động kinh doanh.`,
    },
    {
      icon: '!',
      tone: Number(latest.cfi) < 0 ? 'caution' : 'good',
      text: `CFI ${formatCompactNumber(latest.cfi)}; dòng tiền đầu tư âm có thể phản ánh nhu cầu mở rộng tài sản hoặc đầu tư dài hạn.`,
    },
    {
      icon: '★',
      tone: fcfTone,
      text: `FCF ${formatCompactNumber(firstNumber(latest.fcf, dashboard.cashFlow?.fcf))}; đọc cùng CFO và capex để đánh giá phần tiền còn lại sau đầu tư.`,
    },
    {
      icon: '✓',
      tone: 'good',
      text: `Tiền cuối kỳ ${formatCompactNumber(latest.cash)}, cần so sánh với nợ ngắn hạn và kế hoạch chi vốn để kết luận thận trọng.`,
    },
  ]
}

function buildRatioPeriodRows(analysis, dashboard) {
  const summary = analysis?.summary || {}
  const sorted = [...(analysis?.periods || [])].sort((a, b) => String(a.period || '').localeCompare(String(b.period || '')))
  return sorted
    .map((item) => {
      const revenue = firstNumber(item.revenue)
      const netIncome = firstNumber(item.net_income)
      const totalAssets = firstNumber(item.total_assets, item.assets)
      const currentAssets = firstNumber(item.current_assets, item.short_term_assets, item.cash && item.receivables ? item.cash + item.receivables + firstNumber(item.inventory, 0) : null)
      const inventory = firstNumber(item.inventory)
      const cash = firstNumber(item.cash, item.cash_and_equivalents)
      const receivables = firstNumber(item.receivables, item.accounts_receivable)
      const currentLiabilities = firstNumber(item.current_liabilities, item.short_term_liabilities, item.short_term_debt)
      const totalLiabilities = firstNumber(item.total_liabilities, item.liabilities)
      const equity = firstNumber(item.equity)
      const cogs = firstNumber(item.cogs, item.cost_of_goods_sold)
      const grossProfit = firstNumber(item.gross_profit, Number.isFinite(revenue) && Number.isFinite(cogs) ? revenue - cogs : null)
      const ebit = firstNumber(item.ebit, item.operating_profit, item.profit_before_tax)
      const interestExpense = Math.abs(firstNumber(item.interest_expense, item.financial_expense, 0))
      const cfo = firstNumber(item.operating_cash_flow, item.cfo)
      const debt = firstNumber(item.debt, item.total_debt, totalLiabilities)

      return {
        period: normalizePeriodLabel(item),
        rawPeriod: item.period,
        currentRatio: firstNumber(item.current_ratio, currentAssets && currentLiabilities ? currentAssets / currentLiabilities : null, summary.current_ratio),
        quickRatio: firstNumber(item.quick_ratio, currentAssets && currentLiabilities ? (currentAssets - firstNumber(inventory, 0)) / currentLiabilities : null, summary.quick_ratio),
        cashRatio: firstNumber(item.cash_ratio, cash && currentLiabilities ? cash / currentLiabilities : null),
        debtToEquity: firstNumber(item.debt_to_equity, totalLiabilities && equity ? totalLiabilities / equity : null, summary.debt_to_equity),
        debtToAsset: firstNumber(item.debt_to_asset, totalLiabilities && totalAssets ? totalLiabilities / totalAssets : null),
        interestCoverage: firstNumber(item.interest_coverage, interestExpense ? ebit / interestExpense : null, summary.interest_coverage),
        dscr: firstNumber(item.dscr, cfo && debt ? cfo / Math.max(1, Math.abs(debt) * 0.08) : null),
        assetTurnover: firstNumber(item.asset_turnover, revenue && totalAssets ? revenue / totalAssets : null, summary.asset_turnover),
        inventoryTurnover: firstNumber(item.inventory_turnover, cogs && inventory ? Math.abs(cogs) / inventory : null),
        receivablesTurnover: firstNumber(item.receivables_turnover, revenue && receivables ? revenue / receivables : null),
        grossMargin: firstNumber(item.gross_margin_pct, revenue && grossProfit ? (grossProfit / revenue) * 100 : null),
        ebitMargin: firstNumber(item.ebit_margin_pct, revenue && ebit ? (ebit / revenue) * 100 : null),
        roa: firstNumber(item.roa_pct, totalAssets && netIncome ? (netIncome / totalAssets) * 100 : null, summary.roa_pct),
        roe: firstNumber(item.roe_pct, equity && netIncome ? (netIncome / equity) * 100 : null, summary.roe_pct),
        netMargin: firstNumber(item.net_margin_pct, revenue && netIncome ? (netIncome / revenue) * 100 : null, summary.net_margin_pct),
      }
    })
    .filter((item) => Number.isFinite(item.currentRatio) || Number.isFinite(item.roe) || Number.isFinite(item.netMargin))
}

function buildRatioKpiCards(rows, dashboard) {
  const latest = rows.at(-1) || {}
  const previous = rows.at(-2) || {}
  return [
    ratioKpiCard('▣', 'Current Ratio', latest.currentRatio, previous.currentRatio, ' lần', ratioTone('currentRatio', latest.currentRatio), rows.map((row) => row.currentRatio)),
    ratioKpiCard('▤', 'Quick Ratio', latest.quickRatio, previous.quickRatio, ' lần', ratioTone('quickRatio', latest.quickRatio), rows.map((row) => row.quickRatio)),
    ratioKpiCard('▥', 'ROE', latest.roe, previous.roe, '%', ratioTone('roe', latest.roe), rows.map((row) => row.roe)),
    ratioKpiCard('◉', 'ROA', latest.roa, previous.roa, '%', ratioTone('roa', latest.roa), rows.map((row) => row.roa)),
    ratioKpiCard('%', 'Biên lợi nhuận ròng', latest.netMargin, previous.netMargin, '%', ratioTone('netMargin', latest.netMargin), rows.map((row) => row.netMargin)),
    ratioKpiCard('⚖', 'Debt/Equity', latest.debtToEquity, previous.debtToEquity, ' lần', ratioTone('debtToEquity', latest.debtToEquity), rows.map((row) => row.debtToEquity)),
  ].map((item) => ({
    ...item,
    value: item.value === 'n/a' && item.label === 'ROE' ? formatPercent(dashboard.dupont?.roe) : item.value,
  }))
}

function ratioKpiCard(icon, label, value, previous, suffix, tone, sparkValues) {
  const isPercent = suffix === '%'
  return {
    icon,
    label,
    value: isPercent ? formatPercent(value) : `${formatMaybeNumber(value)}${suffix}`,
    delta: `${formatSignedPercent(growthPercent(value, previous))} QoQ`,
    tone,
    sparkValues,
  }
}

function buildRatioGroups(rows) {
  const latest = rows.at(-1) || {}
  return [
    {
      icon: '◌',
      title: 'Thanh khoản',
      tone: 'liquidity',
      items: [
        ratioBarItem('Current Ratio', latest.currentRatio, ' lần', 3, 1.5, ratioTone('currentRatio', latest.currentRatio)),
        ratioBarItem('Quick Ratio', latest.quickRatio, ' lần', 3, 1.2, ratioTone('quickRatio', latest.quickRatio)),
        ratioBarItem('Cash Ratio', latest.cashRatio, ' lần', 3, 1, ratioTone('cashRatio', latest.cashRatio)),
      ],
    },
    {
      icon: '▣',
      title: 'Đòn bẩy tài chính',
      tone: 'leverage',
      items: [
        ratioBarItem('Debt/Equity', latest.debtToEquity, ' lần', 3, 0.7, ratioTone('debtToEquity', latest.debtToEquity)),
        ratioBarItem('Debt/Asset', latest.debtToAsset, ' lần', 1, 0.5, ratioTone('debtToAsset', latest.debtToAsset)),
        ratioBarItem('Interest Coverage', latest.interestCoverage, ' lần', 15, 3, ratioTone('interestCoverage', latest.interestCoverage)),
        ratioBarItem('DSCR', latest.dscr, ' lần', 4, 1.2, ratioTone('dscr', latest.dscr)),
      ],
    },
    {
      icon: '↻',
      title: 'Hiệu quả hoạt động',
      tone: 'activity',
      items: [
        ratioBarItem('Asset Turnover', latest.assetTurnover, ' vòng', 1.5, 0.8, ratioTone('assetTurnover', latest.assetTurnover)),
        ratioBarItem('Inventory Turnover', latest.inventoryTurnover, ' vòng', 10, 5, ratioTone('inventoryTurnover', latest.inventoryTurnover)),
        ratioBarItem('Receivables Turnover', latest.receivablesTurnover, ' vòng', 12, 6, ratioTone('receivablesTurnover', latest.receivablesTurnover)),
      ],
    },
    {
      icon: '▥',
      title: 'Khả năng sinh lời',
      tone: 'profit',
      items: [
        ratioBarItem('Gross Margin', latest.grossMargin, '%', 50, 30, ratioTone('grossMargin', latest.grossMargin)),
        ratioBarItem('EBIT Margin', latest.ebitMargin, '%', 35, 12, ratioTone('ebitMargin', latest.ebitMargin)),
        ratioBarItem('ROA', latest.roa, '%', 25, 8, ratioTone('roa', latest.roa)),
        ratioBarItem('ROE', latest.roe, '%', 35, 16, ratioTone('roe', latest.roe)),
      ],
    },
  ]
}

function ratioBarItem(label, value, suffix, maxValue, benchmark, tone) {
  const numeric = Number(value)
  const max = Number(maxValue) || 1
  return {
    label,
    value: suffix === '%' ? formatPercent(numeric) : `${formatMaybeNumber(numeric)}${suffix}`,
    progress: Number.isFinite(numeric) ? Math.max(4, Math.min(100, (Math.abs(numeric) / max) * 100)) : 0,
    benchmark: Math.max(0, Math.min(100, (Number(benchmark) / max) * 100)),
    tone,
  }
}

function buildRatioHighlights(rows) {
  const latest = rows.at(-1) || {}
  return [
    {
      icon: '●',
      tone: ratioTone('currentRatio', latest.currentRatio),
      text: `Thanh khoản: Current Ratio ${formatMaybeNumber(latest.currentRatio)} lần, đọc cùng Quick Ratio để tránh phụ thuộc vào hàng tồn kho.`,
    },
    {
      icon: '⚖',
      tone: ratioTone('debtToEquity', latest.debtToEquity),
      text: `Đòn bẩy: Debt/Equity ${formatMaybeNumber(latest.debtToEquity)} lần, dùng để kiểm tra mức độ phụ thuộc vào nợ.`,
    },
    {
      icon: '▥',
      tone: ratioTone('roe', latest.roe),
      text: `Sinh lời: ROE ${formatPercent(latest.roe)}, cần tách thêm theo DuPont để biết đến từ biên lợi nhuận hay đòn bẩy.`,
    },
  ]
}

function ratioTone(key, value) {
  if (['debtToEquity'].includes(key)) return reverseScoreTone(value, 1.2, 0.7)
  if (['debtToAsset'].includes(key)) return reverseScoreTone(value, 0.65, 0.45)
  if (['currentRatio'].includes(key)) return scoreTone(value, 1, 1.5)
  if (['quickRatio'].includes(key)) return scoreTone(value, 0.8, 1.2)
  if (['cashRatio'].includes(key)) return scoreTone(value, 0.25, 0.5)
  if (['interestCoverage'].includes(key)) return scoreTone(value, 2, 5)
  if (['dscr'].includes(key)) return scoreTone(value, 1, 1.3)
  if (['assetTurnover'].includes(key)) return scoreTone(value, 0.5, 0.8)
  if (['inventoryTurnover'].includes(key)) return scoreTone(value, 3, 5)
  if (['receivablesTurnover'].includes(key)) return scoreTone(value, 4, 6)
  if (['grossMargin'].includes(key)) return scoreTone(value, 20, 30)
  if (['ebitMargin', 'netMargin'].includes(key)) return scoreTone(value, 8, 12)
  if (['roa'].includes(key)) return scoreTone(value, 5, 8)
  if (['roe'].includes(key)) return scoreTone(value, 10, 16)
  return ''
}

function buildCashFlowRows(latest, summary = {}, cashFlow = {}) {
  return [
    ['CFO', formatCompactNumber(firstNumber(cashFlow.cfo, latest.operating_cash_flow, summary.ocf_ttm)), 'Dòng tiền từ hoạt động kinh doanh'],
    ['CFI', formatCompactNumber(firstNumber(cashFlow.cfi, latest.cash_flow_from_investing)), 'Dòng tiền đầu tư'],
    ['CFF', formatCompactNumber(firstNumber(cashFlow.cff, latest.cash_flow_from_financing)), 'Dòng tiền tài chính'],
    ['FCF', formatCompactNumber(firstNumber(cashFlow.fcf, summary.free_cash_flow)), 'CFO - Capex'],
    ['CFO / LNST', `${formatMaybeNumber(firstNumber(cashFlow.cfoToNetIncome, summary.ocf_to_net_income))}x`, 'Chất lượng lợi nhuận'],
  ]
}

function buildHorizontalRows(analysis) {
  const periods = [...(analysis?.periods || [])].slice(-2)
  const previous = periods[0] || {}
  const current = periods[1] || previous
  return [
    horizontalRow('Doanh thu thuần', previous.revenue, current.revenue),
    horizontalRow('LNST', previous.net_income, current.net_income),
    horizontalRow('Tổng tài sản', firstNumber(previous.total_assets, previous.assets), firstNumber(current.total_assets, current.assets)),
    horizontalRow('Nợ phải trả', firstNumber(previous.total_liabilities, previous.liabilities), firstNumber(current.total_liabilities, current.liabilities)),
    horizontalRow('Vốn chủ sở hữu', previous.equity, current.equity),
    horizontalRow('CFO', previous.operating_cash_flow, current.operating_cash_flow),
  ]
}

function horizontalRow(label, previous, current) {
  const prev = Number(previous)
  const cur = Number(current)
  const change = Number.isFinite(cur) && Number.isFinite(prev) ? cur - prev : null
  const pct = Number.isFinite(change) && prev !== 0 ? (change / Math.abs(prev)) * 100 : null
  return [label, formatCompactNumber(prev), formatCompactNumber(cur), formatCompactNumber(change), formatPercent(pct)]
}

function buildVerticalIncomeRows(latest, summary = {}) {
  const revenue = firstNumber(latest.revenue, summary.revenue)
  return [
    ['Doanh thu thuần', formatCompactNumber(revenue), '100%'],
    ['LNST', formatCompactNumber(firstNumber(latest.net_income, summary.net_income)), formatPercent(commonSize(firstNumber(latest.net_income, summary.net_income), revenue))],
    ['CFO', formatCompactNumber(firstNumber(latest.operating_cash_flow, summary.ocf_ttm)), formatPercent(commonSize(firstNumber(latest.operating_cash_flow, summary.ocf_ttm), revenue))],
    ['FCF', formatCompactNumber(firstNumber(summary.free_cash_flow)), formatPercent(commonSize(firstNumber(summary.free_cash_flow), revenue))],
  ]
}

function buildVerticalBalanceRows(latest, summary = {}) {
  const assets = firstNumber(latest.total_assets, latest.assets, summary.total_assets)
  return [
    ['Tổng tài sản', formatCompactNumber(assets), '100%'],
    ['Nợ phải trả', formatCompactNumber(firstNumber(latest.total_liabilities, latest.liabilities, summary.total_liabilities)), formatPercent(commonSize(firstNumber(latest.total_liabilities, latest.liabilities, summary.total_liabilities), assets))],
    ['Vốn chủ sở hữu', formatCompactNumber(firstNumber(latest.equity, summary.equity)), formatPercent(commonSize(firstNumber(latest.equity, summary.equity), assets))],
    ['Tiền & tương đương', formatCompactNumber(firstNumber(latest.cash, summary.cash)), formatPercent(commonSize(firstNumber(latest.cash, summary.cash), assets))],
  ]
}

function commonSize(value, base) {
  const numeric = Number(value)
  const denominator = Number(base)
  if (!Number.isFinite(numeric) || !Number.isFinite(denominator) || denominator === 0) return null
  return (numeric / denominator) * 100
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
  const fallbackIndex = Math.max(0, rows.length - 1)
  const visibleIndex = Math.min(activeIndex, fallbackIndex)
  const activePoint = rows[visibleIndex] || rows.at(-1)

  if (!rows.length) {
    return <p className="bctc-muted">Chưa đủ dữ liệu để vẽ chart cho chế độ này.</p>
  }

  return (
    <div className="bctc-trend-chart" onMouseLeave={() => setActiveIndex(fallbackIndex)}>
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

function formatSignedPercent(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  const sign = numeric > 0 ? '▲ ' : numeric < 0 ? '▼ ' : ''
  return `${sign}${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(Math.abs(numeric))}%`
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

function ratioPct(value, total) {
  const numeric = Number(value)
  const denominator = Number(total)
  if (!Number.isFinite(numeric) || !Number.isFinite(denominator) || denominator <= 0) return 0
  return Math.max(0, Math.min(100, (numeric / denominator) * 100))
}

function growthPercent(current, previous) {
  const cur = Number(current)
  const prev = Number(previous)
  if (!Number.isFinite(cur) || !Number.isFinite(prev) || prev === 0) return null
  return ((cur - prev) / Math.abs(prev)) * 100
}

function chartPolyline(values, minValue, maxValue) {
  const cleanValues = values.map((value) => Number(value))
  const min = Number.isFinite(minValue) ? minValue : Math.min(...cleanValues.filter(Number.isFinite), 0)
  const max = Number.isFinite(maxValue) ? maxValue : Math.max(...cleanValues.filter(Number.isFinite), 1)
  const span = max - min || 1
  const left = 52
  const top = 24
  const width = 438
  const height = 150
  const step = width / Math.max(1, cleanValues.length - 1)
  return cleanValues.map((value, index) => {
    const safeValue = Number.isFinite(value) ? value : min
    const x = left + index * step
    const y = top + height - ((safeValue - min) / span) * height
    return `${roundSvg(x)},${roundSvg(y)}`
  }).join(' ')
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
