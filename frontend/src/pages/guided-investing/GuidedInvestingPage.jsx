import { useEffect, useMemo, useState } from 'react'

import {
  analyzeFinancialStatementUpload,
  extractFinancialStatementUpload,
  fetchBalanceSheetStrength,
  fetchFinancialAnalysis,
  fetchFinancialCockpit,
  fetchFinancialPeers,
  fetchFinancialQualityCharts,
  fetchFinancialStatus,
  fetchFinancialUploadTypes,
  uploadFinancialStatement,
  submitStudentNote,
  fetchLineItemExplanation,
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

export default function GuidedInvestingPage({ sessionId, initialFocusCard = 'overview' }) {
  const [ticker, setTicker] = useState(DEFAULT_TICKER)
  const [peersText] = useState('')
  const [mode, setMode] = useState('quarter')
  const [explainerKey, setExplainerKey] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [cockpit, setCockpit] = useState(null)
  const [qualityCharts, setQualityCharts] = useState(null)
  const [balanceSheetStrength, setBalanceSheetStrength] = useState(null)
  const [peerResult, setPeerResult] = useState(null)
  const [providerStatus, setProviderStatus] = useState(null)
  const [uploadTypes, setUploadTypes] = useState(null)
  const [uploadResult, setUploadResult] = useState(null)
  const [extractionResult, setExtractionResult] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [peerLoading, setPeerLoading] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [activeSection, setActiveSection] = useState(initialFocusCard)
  const [comparisonMode, setComparisonMode] = useState('same-period')

  useBctcStoryMotion(Boolean(analysis), activeSection)

  useEffect(() => {
    setActiveSection(initialFocusCard || 'overview')
  }, [initialFocusCard])

  useEffect(() => {
    void bootstrap()
  }, [])

  async function bootstrap() {
    setLoading(true)
    setError('')
    try {
      const [statusPayload, uploadTypesPayload] = await Promise.all([
        fetchFinancialStatus().catch(() => null),
        fetchFinancialUploadTypes().catch(() => null),
      ])
      setProviderStatus(statusPayload)
      setUploadTypes(uploadTypesPayload)
      await runAnalysis({ refresh: false, tickerValue: ticker, silent: true })
    } catch (err) {
      setError(err.message || 'Không tải được dữ liệu BCTC.')
    } finally {
      setLoading(false)
    }
  }

  async function runAnalysis({ refresh = false, tickerValue = ticker, silent = false } = {}) {
    if (!refresh && uploadResult?.upload_id && uploadResult?.status !== 'analyzed') {
      await runUploadedStatementPipeline({ silent })
      return
    }
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
      const [payload, cockpitPayload, chartPayload, balancePayload] = await Promise.all([
        fetchFinancialAnalysis(normalizedTicker, { refresh }),
        fetchFinancialCockpit(normalizedTicker, { refresh }).catch(() => null),
        fetchFinancialQualityCharts(normalizedTicker, { refresh }).catch(() => null),
        fetchBalanceSheetStrength(normalizedTicker, { refresh }).catch(() => null),
      ])
      setAnalysis(payload)
      setCockpit(cockpitPayload)
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

  async function runUploadedStatementPipeline({ silent = false } = {}) {
    if (!uploadResult?.upload_id) return
    if (!silent) {
      setStatus(`Đang xử lý file BCTC ${uploadResult.filename}...`)
      setError('')
      setLoading(true)
    }
    try {
      let nextUpload = uploadResult
      if (!canAnalyzeUploadedStatement(nextUpload)) {
        const extraction = await extractFinancialStatementUpload(nextUpload.upload_id)
        setExtractionResult(extraction)
        nextUpload = {
          ...nextUpload,
          extraction_status: extraction.status,
          analysis_ready: extraction.analysis_ready,
          next_step: extraction.next_step,
          markdown_url: extraction.markdown?.url,
        }
        setUploadResult(nextUpload)
      }
      if (!canAnalyzeUploadedStatement(nextUpload)) {
        setStatus('')
        setError(nextUpload.next_step || 'File upload chưa đủ dữ liệu có cấu trúc để phân tích.')
        return
      }
      await analyzeUploadedStatement({ silent: true, uploadOverride: nextUpload })
    } finally {
      if (!silent) setLoading(false)
    }
  }

  async function analyzeUploadedStatement({ silent = false, uploadOverride = null } = {}) {
    const targetUpload = uploadOverride || uploadResult
    if (!targetUpload?.upload_id) return
    if (!silent) {
      setStatus(`Đang phân tích file BCTC ${targetUpload.filename}...`)
      setError('')
      setLoading(true)
    }
    try {
      const payload = await analyzeFinancialStatementUpload(targetUpload.upload_id)
      const nextTicker = payload.ticker || targetUpload.ticker || ticker
      setAnalysis(payload.analysis)
      setTicker(nextTicker)
      setUploadResult(payload.upload)
      const [cockpitPayload, chartPayload, balancePayload] = await Promise.all([
        fetchFinancialCockpit(nextTicker, { refresh: false }).catch(() => null),
        fetchFinancialQualityCharts(nextTicker, { refresh: false }).catch(() => null),
        fetchBalanceSheetStrength(nextTicker, { refresh: false }).catch(() => null),
      ])
      setCockpit(cockpitPayload)
      setQualityCharts(chartPayload)
      setBalanceSheetStrength(balancePayload)
      const nextMode = inferDefaultMode(payload.analysis)
      if (nextMode) setMode(nextMode)
      await runPeerCompare({ tickerValue: nextTicker, silent: true })
      setStatus(`Đã phân tích file upload và dựng chart cho ${nextTicker}.`)
      trackAnalyticsEvent({
        event_name: 'financial_uploaded_statement_analyzed',
        module: 'guided_investing',
        surface: 'guided_investing',
        session_id: sessionId || undefined,
        properties: {
          ticker: nextTicker,
          upload_id: targetUpload.upload_id,
          period_count: payload.periods,
        },
      })
    } catch (err) {
      setError(err.message || 'Không phân tích được file BCTC đã upload.')
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

  async function handleFinancialUpload(event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setUploading(true)
    setUploadResult(null)
    setExtractionResult(null)
    setError('')
    setStatus(`Đang upload BCTC: ${file.name}...`)
    try {
      const payload = await uploadFinancialStatement({
        file,
        ticker,
        reportType: 'auto',
        period: analysis?.latest_period || '',
      })
      setUploadResult(payload)
      setStatus(`Đã nhận file ${payload.filename}. Bước tiếp theo: ${payload.next_step}`)
      trackAnalyticsEvent({
        event_name: 'financial_statement_uploaded',
        module: 'guided_investing',
        surface: 'guided_investing',
        session_id: sessionId || undefined,
        properties: {
          ticker: payload.ticker || ticker,
          file_type: payload.file_type?.extension,
          pipeline: payload.file_type?.pipeline,
          size_bytes: payload.size_bytes,
        },
      })
    } catch (err) {
      setError(err.message || 'Không upload được file BCTC.')
      setStatus('')
    } finally {
      setUploading(false)
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
    () => buildDashboardModel(analysis, trendRows, peerResult, qualityCharts, balanceSheetStrength, cockpit),
    [analysis, trendRows, peerResult, qualityCharts, balanceSheetStrength, cockpit],
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
            <p>{describeSection(activeSection)}</p>
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
            {uploadResult?.status && uploadResult.status !== 'analyzed' ? 'Phân tích file upload' : 'Phân tích BCTC'}
          </button>
        </div>
      </header>

      {isOverview ? (
        <section className="bctc-overview-hero bctc-showcase-hero">
          <div className="bctc-showcase-copy">
            <p className="bctc-showcase-kicker">BCTC Overview</p>
            <h2>{dashboard.aiTitle}</h2>
            <p>Một màn tổng quan bắt đầu từ bảng BCTC đã đọc, rồi đối chiếu các dòng số liệu sang chart và insight trước khi đi vào tab phân tích sâu.</p>
            <div className="bctc-showcase-controls">
              <label>
                <span>Ticker</span>
                <input
                  value={ticker}
                  onChange={(event) => setTicker(event.target.value.toUpperCase())}
                  placeholder="Ví dụ: FPT"
                />
              </label>
              <label>
                <span>Kỳ</span>
                <select value={mode} onChange={(event) => setMode(event.target.value)}>
                  {modeOptions.map((item) => (
                    <option key={item} value={item}>{modeLabel(item)}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="bctc-showcase-metrics">
              {dashboard.kpis.slice(0, 4).map((item) => (
                <div key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                  <em>{item.note}</em>
                </div>
              ))}
            </div>
            <BctcUploadPanel
              uploadTypes={uploadTypes}
              uploadResult={uploadResult}
              extractionResult={extractionResult}
              uploading={uploading}
              onUpload={handleFinancialUpload}
              onAnalyze={() => void runUploadedStatementPipeline({ silent: false })}
            />
          </div>

          <div className="bctc-showcase-stage" aria-label="BCTC source table and overview dashboard preview">
            <div className="bctc-showcase-window">
              <header className="bctc-showcase-window__bar">
                <div className="bctc-showcase-brand">
                  <div className="bctc-logo" aria-hidden="true">
                    {(analysis?.ticker || ticker || 'NS').slice(0, 3)}
                  </div>
                  <div>
                    <strong>{dashboard.companyName}</strong>
                <span>{dashboard.exchange} · {analysis?.latest_period || 'n/a'} · {analysis?.source || providerStatus?.provider || 'n/a'}</span>
                  </div>
                </div>
                <span>{dashboard.dataQualityLabel}</span>
              </header>

              <BctcSourceStatementPreview analysis={analysis} cockpit={cockpit} extractionResult={extractionResult} />

              <div className="bctc-showcase-grid">
                <article className="bctc-showcase-card bctc-showcase-card--main">
                  <header>
                    <div>
                      <p>Revenue quality</p>
                      <h3>Doanh thu & LNST</h3>
                    </div>
                    <span>{modeLabel(mode)}</span>
                  </header>
                  <MetricTrendChart
                    rows={trendRows}
                    metrics={REVENUE_INCOME_METRICS}
                    formatValue={formatCompactNumber}
                    height={205}
                    showEndpointLabels
                  />
                </article>

                <article className="bctc-showcase-card bctc-showcase-card--health">
                  <header>
                    <div>
                      <p>Financial health</p>
                      <h3>{dashboard.healthScore}/100</h3>
                    </div>
                  </header>
                  <div className="bctc-showcase-health">
                    <HealthScoreGauge score={dashboard.healthScore} tone={dashboard.healthTone} />
                    <div className="bctc-health-bars">
                      {healthRows.slice(0, 4).map((row) => (
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
                </article>

                <article className="bctc-showcase-card bctc-showcase-card--mini">
                  <header>
                    <div>
                      <p>Margin</p>
                      <h3>Biên lợi nhuận</h3>
                    </div>
                  </header>
                  <MetricTrendChart
                    rows={dashboard.marginRows}
                    metrics={MARGIN_METRICS}
                    formatValue={formatPercent}
                    height={130}
                    showEndpointLabels={false}
                  />
                </article>

                <article className="bctc-showcase-card bctc-showcase-card--mini">
                  <header>
                    <div>
                      <p>Cash conversion</p>
                      <h3>Dòng tiền</h3>
                    </div>
                  </header>
                  <CashFlowQuality data={dashboard.cashFlow} />
                </article>
              </div>
            </div>

            {dashboard.summaryBullets[0] ? (
              <aside className="bctc-floating-insight bctc-floating-insight--left">
                <span>Insight</span>
                <strong>{dashboard.summaryBullets[0].text}</strong>
              </aside>
            ) : null}
            {dashboard.summaryBullets[2] ? (
              <aside className="bctc-floating-insight bctc-floating-insight--right">
                <span>Cần kiểm tra</span>
                <strong>{dashboard.summaryBullets[2].text}</strong>
              </aside>
            ) : null}
          </div>
        </section>
      ) : null}

      {status && isOverview ? <p className="bctc-state bctc-state--compact">{status}</p> : null}
      {error ? <p className="bctc-state bctc-state--error">{error}</p> : null}

      {analysis ? (
        isOverview ? (
        <>
          <section className="bctc-story-flow">
            <article className="bctc-story-panel bctc-story-panel--growth">
              <div className="bctc-story-copy">
                <span>01 / Tăng trưởng</span>
                <h2>Doanh thu tăng có đi cùng lợi nhuận?</h2>
                <p>Chart này là bằng chứng chính cho câu hỏi đầu tiên: tăng trưởng có thật sự chuyển hóa thành lợi nhuận hay chỉ phình quy mô.</p>
                <a href="#income">Xem phân tích KQKD</a>
              </div>
              <div className="bctc-story-visual bctc-evidence-card bctc-evidence-card--growth">
                <header className="bctc-panel-head">
                  <div>
                    <h3>Doanh thu & LNST</h3>
                    <p>{modeLabel(mode)} · {analysis?.latest_period || 'Latest'}</p>
                  </div>
                </header>
                <MetricTrendChart
                  rows={trendRows}
                  metrics={REVENUE_INCOME_METRICS}
                  formatValue={formatCompactNumber}
                  height={280}
                  showEndpointLabels
                />
                <div className="bctc-evidence-metrics">
                  {dashboard.kpis.slice(0, 3).map((item) => (
                    <p key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                      <em>{item.note}</em>
                    </p>
                  ))}
                </div>
              </div>
            </article>

            <article className="bctc-story-panel bctc-story-panel--two">
              <div className="bctc-story-copy">
                <span>02 / Chất lượng</span>
                <h2>Lợi nhuận có bền và có tiền thật không?</h2>
                <p>Hai visual đủ để đọc chất lượng: biên lợi nhuận cho thấy sức giữ lãi, dòng tiền cho thấy lợi nhuận có được xác nhận bằng tiền.</p>
                <a href="#cashflow">Xem phân tích dòng tiền</a>
              </div>
              <div className="bctc-story-visual-grid">
                <div className="bctc-story-visual bctc-evidence-card bctc-evidence-card--margin">
                  <header className="bctc-panel-head">
                    <div>
                      <h3>Biên lợi nhuận</h3>
                      <p>Gộp · HĐKD · ròng</p>
                    </div>
                  </header>
                  <MetricTrendChart
                    rows={dashboard.marginRows}
                    metrics={MARGIN_METRICS}
                    formatValue={formatPercent}
                    height={220}
                    showEndpointLabels
                  />
                </div>
                <div className="bctc-story-visual bctc-evidence-card bctc-evidence-card--cash">
                  <header className="bctc-panel-head">
                    <div>
                      <h3>Dòng tiền</h3>
                      <p>CFO, CFI, CFF và FCF</p>
                    </div>
                  </header>
                  <CashFlowQuality data={dashboard.cashFlow} />
                </div>
              </div>
            </article>

            <article className="bctc-story-panel bctc-story-panel--risk">
              <div className="bctc-story-copy">
                <span>03 / Rủi ro</span>
                <h2>Còn điểm nào phải kiểm tra trước khi tin?</h2>
                <p>Overview chỉ nêu các câu hỏi quan trọng nhất. Nếu cần truy vết từng khoản mục, chuyển sang tab Bảng cân đối, Chỉ số hoặc Dòng tiền.</p>
                <div className="bctc-story-points">
                  {dashboard.checkQuestions.slice(0, 3).map((item) => (
                    <p key={item} className="bctc-story-point bctc-story-point--warn">{item}</p>
                  ))}
                </div>
              </div>
              <div className="bctc-story-visual bctc-evidence-card bctc-risk-board">
                <BalanceSheetSummaryCard data={dashboard.balanceSheetStrength} fallbackItems={dashboard.balanceItems} fallbackTotal={dashboard.balanceTotal} />
                {analysis.flags?.length ? (
                  <ul className="bctc-story-flag-list">
                    {analysis.flags.slice(0, 3).map((flag) => (
                      <li key={`${flag.level}-${flag.title}`}>
                        <strong>{flag.title}</strong>
                        <span>{flag.detail}</span>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </article>
          </section>
        </>
        ) : (
          <BctcSectionPanel
            section={activeSection}
            analysis={analysis}
            dashboard={dashboard}
            trendRows={trendRows}
            healthRows={healthRows}
            mode={mode}
            onChangeMode={setMode}
            comparisonMode={comparisonMode}
            onChangeComparisonMode={setComparisonMode}
            peerLoading={peerLoading}
          />
        )
      ) : null}
      
      {explainerKey && (
        <LineItemExplainerModal 
          itemKey={explainerKey} 
          ticker={ticker}
          period={analysis?.latest_period || 'T12/2024'}
          onClose={() => setExplainerKey(null)} 
        />
      )}
    </section>
  )
}

function useBctcStoryMotion(enabled, activeSection) {
  useEffect(() => {
    if (!enabled || activeSection !== 'overview') return undefined
    const root = document.querySelector('.bctc-page')
    const flow = document.querySelector('.bctc-story-flow')
    const hero = document.querySelector('.bctc-showcase-hero')
    if (!root || !flow) return undefined

    const panels = [...flow.querySelectorAll('.bctc-story-panel')]
    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) {
      panels.forEach((item) => item.classList.add('is-visible'))
      return undefined
    }

    flow.classList.add('is-motion-ready')

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.18, rootMargin: '0px 0px -10% 0px' },
    )

    panels.forEach((item) => observer.observe(item))

    function handlePointerMove(event) {
      const target = hero?.contains(event.target) ? hero : flow
      const rect = target.getBoundingClientRect()
      const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2
      const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2
      flow.style.setProperty('--story-x', x.toFixed(3))
      flow.style.setProperty('--story-y', y.toFixed(3))
      hero?.style.setProperty('--story-x', x.toFixed(3))
      hero?.style.setProperty('--story-y', y.toFixed(3))
    }

    flow.addEventListener('pointermove', handlePointerMove)
    hero?.addEventListener('pointermove', handlePointerMove)

    return () => {
      observer.disconnect()
      flow.removeEventListener('pointermove', handlePointerMove)
      hero?.removeEventListener('pointermove', handlePointerMove)
      flow.classList.remove('is-motion-ready')
    }
  }, [enabled, activeSection])
}

function SimplizeDataViewToggle({ viewMode, onChange }) {
  return (
    <div className="bctc-view-toggle">
      <button className={viewMode === 'absolute' ? 'is-active' : ''} onClick={() => onChange('absolute')}>Giá trị tuyệt đối</button>
      <button className={viewMode === 'growth' ? 'is-active' : ''} onClick={() => onChange('growth')}>% Tăng trưởng</button>
      <button className={viewMode === 'ratio' ? 'is-active' : ''} onClick={() => onChange('ratio')}>% Tỷ trọng</button>
    </div>
  )
}

function SimplizeDataTable({ title, data, lines, viewMode, onRowClick }) {
  const periods = data.map(d => d.period);
  return (
    <article className="bctc-panel bctc-data-table bctc-simplize-table">
      <header className="bctc-panel-head" style={{ borderBottom: '1px solid rgba(37, 43, 59, 0.08)', paddingBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ padding: 0, margin: 0 }}>{title}</h2>
        {viewMode && <span style={{ fontSize: '0.78rem', color: '#607975', fontWeight: 600 }}>Chế độ: {viewMode === 'absolute' ? 'Giá trị' : viewMode === 'growth' ? 'Tăng trưởng' : 'Tỷ trọng'}</span>}
      </header>
      <div style={{ overflowX: 'auto', width: '100%' }}>
        <table style={{ minWidth: '800px' }}>
          <thead>
            <tr>
              <th className="bctc-sticky-col">Chỉ tiêu</th>
              {periods.map((period, i) => <th key={`${period}-${i}`}>{period}</th>)}
            </tr>
          </thead>
          <tbody>
            {lines.map(line => {
              const key = line.key;
              const label = line.label;
              const isEmphasis = line.isEmphasis;
              return (
                <tr key={key} className={isEmphasis ? 'is-emphasis' : ''} onClick={() => onRowClick && onRowClick(label)} style={onRowClick ? {cursor: 'pointer'} : {}}>
                  <td className="bctc-sticky-col bctc-cell-label">{label}</td>
                  {data.map((row, index) => {
                    let cellValue = row[key];
                    let displayValue = '-';
                    let tone = null;
                    
                    if (viewMode === 'growth') {
                      if (index > 0) {
                        const prevValue = data[index - 1][key];
                        if (prevValue && cellValue) {
                          const growth = growthPercent(cellValue, prevValue);
                          displayValue = formatSignedPercent(growth);
                          tone = growth > 0 ? 'pos' : (growth < 0 ? 'neg' : null);
                        }
                      }
                    } else if (viewMode === 'ratio') {
                      const total = row[line.ratioBaseKey];
                      if (total && cellValue != null) {
                        displayValue = formatPercent(cellValue / total * 100);
                      }
                    } else {
                      displayValue = line.format ? line.format(cellValue) : formatCompactNumber(cellValue);
                    }
                    
                    const className = [
                      'bctc-cell-num',
                      tone ? `bctc-cell-${tone}` : ''
                    ].filter(Boolean).join(' ');
                    
                    return <td key={`${key}-${index}`} className={className}>{displayValue}</td>;
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </article>
  )
}

function buildIncomePeriodRows(analysis) {
  return [...(analysis?.periods || [])]
    .slice()
    .sort((a, b) => {
      const ay = Number(a.year || 0)
      const by = Number(b.year || 0)
      if (ay !== by) return ay - by
      return Number(a.quarter || 0) - Number(b.quarter || 0)
    })
    .map((item) => {
      const revenue = firstNumber(item.revenue)
      const netIncome = firstNumber(item.net_income)
      const grossMarginPct = firstNumber(item.gross_margin_pct)
      const grossProfit = Number.isFinite(revenue) && Number.isFinite(grossMarginPct) ? revenue * grossMarginPct / 100 : null
      const cogs = Number.isFinite(revenue) && Number.isFinite(grossProfit) ? revenue - grossProfit : null
      const ebit = firstNumber(item.ebit, item.operating_income)
      const netMarginPct = firstNumber(item.net_margin_pct, revenue ? (netIncome / revenue) * 100 : null)
      return {
        period: normalizePeriodLabel(item),
        rawPeriod: item.period,
        year: item.year,
        quarter: item.quarter,
        revenue,
        cogs,
        grossProfit,
        ebit,
        netIncome,
        grossMarginPct,
        netMarginPct,
      }
    })
    .filter((item) => Number.isFinite(item.revenue) || Number.isFinite(item.netIncome))
}

function BctcSectionPanel({ section, analysis, dashboard, trendRows, healthRows, mode, onChangeMode, comparisonMode, onChangeComparisonMode, peerLoading }) {
  const tab = BCTC_TABS.find((item) => item.key === section) || BCTC_TABS[0]
  const latest = latestPeriod(analysis) || {}

  if (section === 'income') {
    const incomeCards = buildIncomeKpiCards(dashboard, latest, analysis?.summary)
    return (
      <section className="bctc-section-panel bctc-income-view" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

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
          <div style={{ gridColumn: '1 / -1' }}>
            <SimplizeDataViewToggle viewMode={dataViewMode} onChange={setDataViewMode} />
            <SimplizeDataTable
              title="Báo cáo kết quả kinh doanh"
              data={buildIncomePeriodRows(analysis).slice(-5)}
              lines={[
                { key: 'revenue', label: 'Doanh thu thuần', isEmphasis: true, ratioBaseKey: 'revenue' },
                { key: 'cogs', label: 'Giá vốn hàng bán', ratioBaseKey: 'revenue' },
                { key: 'grossProfit', label: 'Lợi nhuận gộp', isEmphasis: true, ratioBaseKey: 'revenue' },
                { key: 'grossMarginPct', label: 'Biên gộp (%)', format: (val) => formatPercent(val) },
                { key: 'ebit', label: 'EBIT', ratioBaseKey: 'revenue' },
                { key: 'netIncome', label: 'LNST', isEmphasis: true, ratioBaseKey: 'revenue' },
                { key: 'netMarginPct', label: 'Biên ròng (%)', format: (val) => formatPercent(val) },
              ]}
              viewMode={dataViewMode}
              onRowClick={setExplainerKey}
            />
          </div>
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
          </article>
          <WhatIfSimulator analysis={analysis} />
          <StudentNotePanel companyId={ticker} period={analysis?.latest_period} sectionName="Kết quả kinh doanh" />
          <article className="bctc-panel">
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
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

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

          <div style={{ gridColumn: '1 / -1' }}>
            <SimplizeDataViewToggle viewMode={dataViewMode} onChange={setDataViewMode} />
            <SimplizeDataTable
              title="Bảng cân đối kế toán"
              data={balanceRows.slice(-5)}
              lines={[
                { key: 'cash', label: 'Tiền & tương đương tiền', ratioBaseKey: 'totalAssets' },
                { key: 'receivables', label: 'Phải thu khách hàng', ratioBaseKey: 'totalAssets' },
                { key: 'inventory', label: 'Hàng tồn kho', ratioBaseKey: 'totalAssets' },
                { key: 'currentAssets', label: 'Tài sản ngắn hạn', isEmphasis: true, ratioBaseKey: 'totalAssets' },
                { key: 'fixedAssets', label: 'Tài sản cố định', ratioBaseKey: 'totalAssets' },
                { key: 'otherAssets', label: 'Tài sản khác dài hạn', ratioBaseKey: 'totalAssets' },
                { key: 'totalAssets', label: 'Tổng tài sản', isEmphasis: true, ratioBaseKey: 'totalAssets' },
                { key: 'shortTermDebt', label: 'Nợ ngắn hạn', ratioBaseKey: 'totalLiabilities' },
                { key: 'longTermDebt', label: 'Nợ dài hạn', ratioBaseKey: 'totalLiabilities' },
                { key: 'totalLiabilities', label: 'Tổng nợ phải trả', isEmphasis: true, ratioBaseKey: 'totalLiabilities' },
                { key: 'equity', label: 'Vốn chủ sở hữu', isEmphasis: true, ratioBaseKey: 'totalAssets' },
              ]}
              viewMode={dataViewMode}
              onRowClick={setExplainerKey}
            />
          </div>
          <StudentNotePanel companyId={ticker} period={analysis?.latest_period} sectionName="Bảng cân đối kế toán" />

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
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

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

          <article className="bctc-chart-card bctc-cash-chart">
            <header className="bctc-panel-head">
              <div>
                <h2>Lưu chuyển tiền tệ</h2>
                <p>HĐKD, HĐĐT và HĐTC.</p>
              </div>
              <span>Cash Flow</span>
            </header>
            <CashFlowStackChart rows={cashRows} />
          </article>
          
          <div style={{ gridColumn: '1 / -1' }}>
            <SimplizeDataViewToggle viewMode={dataViewMode} onChange={setDataViewMode} />
            <SimplizeDataTable
              title="Lưu chuyển tiền tệ"
              data={cashRows.slice(-5)}
              lines={[
                { key: 'operatingCash', label: 'Lưu chuyển tiền từ HĐKD', isEmphasis: true },
                { key: 'investingCash', label: 'Lưu chuyển tiền từ HĐĐT' },
                { key: 'financingCash', label: 'Lưu chuyển tiền từ HĐTC' },
                { key: 'netCashFlow', label: 'Lưu chuyển tiền thuần', isEmphasis: true },
              ]}
              viewMode={dataViewMode}
              onRowClick={setExplainerKey}
            />
          </div>

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
            <CashFlowAssistantCard />
          </aside>

          <StudentNotePanel companyId={ticker} period={analysis?.latest_period} sectionName="Lưu chuyển tiền tệ" />

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
    const ratioRows = buildRatioPeriodRows(analysis)
    const ratioCards = buildRatioKpiCards(ratioRows, dashboard)
    const ratioGroups = buildRatioGroups(ratioRows, dashboard)
    return (
      <section className="bctc-section-panel bctc-ratio-view" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

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

          <RatioStatementTable rows={ratioRows} onRowClick={setExplainerKey} />

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
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />
        <AnalysisTable rows={buildHorizontalRows(analysis)} columns={['Chỉ tiêu', 'Kỳ trước', 'Kỳ hiện tại', 'Thay đổi', '% thay đổi']} onRowClick={setExplainerKey} />
      </section>
    )
  }

  if (section === 'vertical') {
    return (
      <section className="bctc-section-panel" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />
        <div className="bctc-section-grid">
          <AnalysisTable title="Kết quả kinh doanh / Doanh thu" rows={buildVerticalIncomeRows(latest, analysis?.summary)} columns={['Chỉ tiêu', 'Giá trị', 'Tỷ trọng']} onRowClick={setExplainerKey} />
          <AnalysisTable title="Bảng cân đối / Tổng tài sản" rows={buildVerticalBalanceRows(latest, analysis?.summary)} columns={['Chỉ tiêu', 'Giá trị', 'Tỷ trọng']} onRowClick={setExplainerKey} />
        </div>
      </section>
    )
  }

  if (section === 'risk') {
    return (
      <section className="bctc-section-panel" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />
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
      <BctcSectionControlBand
        analysis={analysis}
        dashboard={dashboard}
        mode={mode}
        onChangeMode={onChangeMode}
        comparisonMode={comparisonMode}
        onChangeComparisonMode={onChangeComparisonMode}
      />
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

const SECTION_DESCRIPTIONS = {
  overview: 'Phân tích báo cáo tài chính để hiểu sức khỏe tài chính và hiệu quả hoạt động doanh nghiệp.',
  income: 'Phân tích hiệu quả hoạt động kinh doanh qua doanh thu, cơ cấu chi phí, biên lợi nhuận và chất lượng lợi nhuận.',
  balance: 'Phân tích cơ cấu tài sản, nguồn vốn, thanh khoản và mức độ an toàn tài chính.',
  'cash-flow': 'Phân tích chất lượng dòng tiền, khả năng tạo tiền từ hoạt động kinh doanh và nhu cầu tài trợ vốn.',
  ratios: 'Đọc các nhóm chỉ số tài chính trọng yếu — thanh khoản, đòn bẩy, hiệu quả và sinh lời.',
  horizontal: 'So sánh biến động từng chỉ tiêu giữa các kỳ gần nhất để thấy xu hướng tăng/giảm.',
  vertical: 'Đọc common-size: từng chỉ tiêu chiếm bao nhiêu trong doanh thu hoặc tổng tài sản.',
  risk: 'Các điểm cần kiểm tra lại trước khi đưa ra nhận định cuối — red flags & checklist.',
  report: 'Tóm tắt thành báo cáo học tập, không phải khuyến nghị mua bán.',
}

function describeSection(section) {
  return SECTION_DESCRIPTIONS[section] || SECTION_DESCRIPTIONS.overview
}



function BctcSectionControlBand({ analysis, dashboard, mode, onChangeMode, comparisonMode, onChangeComparisonMode }) {
  return (
    <section className="bctc-income-control-band">
      <div className="bctc-income-company">
        <div className="bctc-logo" aria-hidden="true">{(analysis?.ticker || 'FPT').slice(0, 3)}</div>
        <div>
          <h2>
            {dashboard.companyName}
            {analysis?.source?.startsWith('upload') && (
              <span style={{ fontSize: '0.75rem', marginLeft: '8px', backgroundColor: '#fef08a', color: '#854d0e', padding: '2px 6px', borderRadius: '4px', verticalAlign: 'middle', fontWeight: 'bold' }}>
                Mô phỏng BCTC
              </span>
            )}
          </h2>
          <p>{analysis?.source?.startsWith('upload') ? 'Dữ liệu học tập/thực hành' : `Ngành: ${analysis?.industry || 'Công nghệ thông tin'} · ${dashboard.exchange}`}: {analysis?.ticker || DEFAULT_TICKER}</p>
        </div>
      </div>
      <label>
        <span>Kỳ báo cáo</span>
        <select value={mode === 'quarter' ? 'quarter' : 'year'} onChange={(event) => onChangeMode(event.target.value)}>
          <option value="quarter">Quý</option>
          <option value="year">Năm</option>
        </select>
      </label>
      <label>
        <span>So sánh với</span>
        <select value={comparisonMode} onChange={(event) => onChangeComparisonMode(event.target.value)}>
          <option value="same-period">Cùng kỳ năm trước</option>
          <option value="previous-period">Kỳ liền trước</option>
        </select>
      </label>
      <AnalysisStepper />
    </section>
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

function BctcUploadPanel({ uploadTypes, uploadResult, extractionResult, uploading, onUpload, onAnalyze }) {
  const accept = uploadTypes?.accept || '.pdf,.xlsx,.xls,.csv,.docx,.doc,.png,.jpg,.jpeg,.tif,.tiff,.webp,.html,.htm,.xml,.zip'
  const typeSummary = summarizeUploadTypes(uploadTypes)
  const canAnalyze = canAnalyzeUploadedStatement(uploadResult)
  const needsMarkdown = uploadResult && !canAnalyze && uploadResult.status !== 'analyzed'
  return (
    <div className="bctc-upload-panel">
      <div>
        <span>Upload BCTC</span>
        <strong>{uploading ? 'Đang nhận file...' : 'File BCTC -> Markdown -> chart'}</strong>
        <small>{typeSummary}</small>
      </div>
      <label className="bctc-upload-panel__button">
        <input type="file" accept={accept} onChange={onUpload} disabled={uploading} />
        {uploading ? 'Đang upload' : 'Chọn file BCTC'}
      </label>
      {uploadResult && uploadResult.status !== 'analyzed' ? (
        <button
          type="button"
          className="bctc-upload-panel__analyze"
          onClick={onAnalyze}
          disabled={uploading}
          title="Tạo Markdown context, map bảng BCTC rồi dựng chart từ các dòng số liệu đã trích xuất."
        >
          Phân tích file
        </button>
      ) : null}
      {uploadResult ? (
        <p>
          <b>{uploadResult.file_type?.label || 'File'}</b>
          <span>{uploadStatusText(uploadResult)} · {formatBytes(uploadResult.size_bytes)} · {uploadResult.file_type?.pipeline}</span>
          {needsMarkdown ? <i>Hệ thống sẽ tạo Markdown context và bảng dòng BCTC trước khi vẽ chart.</i> : null}
        </p>
      ) : null}
      {extractionResult ? <BctcExtractionSummary result={extractionResult} /> : null}
    </div>
  )
}

function BctcExtractionSummary({ result }) {
  const pages = result?.pages || []
  const warnings = result?.warnings || []
  const rowCount = result?.markdown_row_count || result?.quality?.ocr_statement_row_count || result?.raw_tables?.[0]?.rows?.length || 0
  return (
    <div className={`bctc-extraction-summary bctc-extraction-summary--${result.status || 'unknown'}`}>
      <div>
        <span>{extractionStatusLabel(result.status)}</span>
        <strong>{result.source_kind || 'unknown source'}</strong>
        <small>
          {pages.length ? `${pages.length} trang preview` : 'Chưa có preview'} · {rowCount} dòng Markdown · text layer {result.quality?.text_layer_chars ?? 0} ký tự · OCR fallback {result.quality?.ocr_engine_available ? result.quality?.ocr_engine : 'chưa sẵn sàng'}
        </small>
      </div>
      {pages.length || result.markdown?.url ? (
        <div className="bctc-extraction-pages">
          {result.markdown?.url ? (
            <a href={result.markdown.url} target="_blank" rel="noreferrer">
              Markdown
            </a>
          ) : null}
          {pages.slice(0, 4).map((page) => (
            <a key={page.page} href={page.preview_url} target="_blank" rel="noreferrer">
              Trang {page.page}
            </a>
          ))}
        </div>
      ) : null}
      {warnings.length ? (
        <ul>
          {warnings.slice(0, 3).map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
      ) : null}
    </div>
  )
}

function StatementTable({ title, rows, onRowClick }) {
  return <AnalysisTable title={title} rows={rows} columns={['Chỉ tiêu', 'Giá trị', 'Ghi chú']} onRowClick={onRowClick} />
}

function BctcSourceStatementPreview({ analysis, cockpit, extractionResult }) {
  const report = buildSourceStatementReport(analysis, cockpit, extractionResult)
  return (
    <article className={`bctc-source-preview ${report.hasData ? '' : 'bctc-source-preview--empty'}`}>
      <header>
        <div>
          <p>{report.hasData ? 'BCTC đã đọc' : 'Chưa có bảng nguồn'}</p>
          <h3>{report.title}</h3>
          <small>{report.subtitle}</small>
        </div>
        <span>{report.unit}</span>
      </header>
      {report.hasData ? (
        <div className="bctc-source-preview__table" aria-label="BCTC source report table">
          <table>
            <thead>
              <tr>
                {report.columns.map((column) => (
                  <th key={column.key}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {report.rows.map((row) => (
                row.type === 'section' ? (
                  <tr key={row.key} className="bctc-source-preview__section">
                    <th colSpan={report.columns.length}>{row.label}</th>
                  </tr>
                ) : (
                  <tr key={row.key} className={`bctc-source-preview__line bctc-source-preview__line--${row.tone || 'default'} ${row.isTotal ? 'is-total' : ''}`}>
                    <th scope="row">
                      <span>{row.label}</span>
                      {row.note ? <small>{row.note}</small> : null}
                    </th>
                    <td className={statementCellClass(row.current)}>{formatStatementCell(row.current, row.valueType)}</td>
                    <td className={statementCellClass(row.compare)}>{formatStatementCell(row.compare, row.valueType)}</td>
                    <td className={changeCellClass(row.changePct)}>{formatPercent(row.changePct)}</td>
                    <td className={statementCellClass(row.ytdCurrent)}>{formatStatementCell(row.ytdCurrent, row.valueType)}</td>
                    <td className={statementCellClass(row.ytdCompare)}>{formatStatementCell(row.ytdCompare, row.valueType)}</td>
                    <td className={changeCellClass(row.ytdChangePct)}>{formatPercent(row.ytdChangePct)}</td>
                    <td><EvidenceBadge evidence={row.evidence} derived={row.derived} /></td>
                    <td><em>{row.chart}</em></td>
                  </tr>
                )
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bctc-source-preview__empty" role="status">
          <strong>Chưa đọc được các dòng BCTC nguồn.</strong>
          <span>Hãy bấm “Phân tích BCTC” hoặc kiểm tra pipeline dữ liệu; chart sẽ chỉ có ý nghĩa khi các dòng doanh thu, LNST, CFO và bảng cân đối được nạp vào đây.</span>
        </div>
      )}
    </article>
  )
}

function EvidenceBadge({ evidence, derived }) {
  if (evidence?.page) {
    return (
      <span className="bctc-source-preview__evidence">
        P{evidence.page}
        {Number.isFinite(Number(evidence.confidence)) ? <small>{Math.round(Number(evidence.confidence))}%</small> : null}
      </span>
    )
  }
  if (derived) return <span className="bctc-source-preview__evidence is-derived">Tính toán</span>
  return <span className="bctc-source-preview__evidence is-missing">Chưa đọc</span>
}

function AnalysisTable({ title, rows, columns, onRowClick }) {
  return (
    <article className="bctc-panel bctc-data-table">
      {title ? <h2>{title}</h2> : null}
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const labelCell = row[0]
            return (
            <tr key={row.join('-')} onClick={() => onRowClick && onRowClick(labelCell)} className={onRowClick ? 'bctc-row-clickable' : ''} style={onRowClick ? {cursor: 'pointer'} : {}}>
              {row.map((cell, index) => {
                const tone = index === 0 ? null : detectNumberTone(cell)
                const className = [
                  index === 0 ? 'bctc-cell-label' : 'bctc-cell-num',
                  tone ? `bctc-cell-${tone}` : '',
                ].filter(Boolean).join(' ') || undefined
                return <td key={`${cell}-${index}`} className={className}>{cell}</td>
              })}
            </tr>
          )})}
        </tbody>
      </table>
    </article>
  )
}

/** Lightweight sign detection on formatted strings ("-12,5%" → 'neg', "+3,1%" → 'pos'). Returns null for plain values. */
function detectNumberTone(cell) {
  if (cell == null) return null
  const s = String(cell).trim()
  if (!s || s === '—' || s === '-' || s === 'n/a') return null
  if (s.startsWith('-') || s.startsWith('−')) return 'neg'
  if (s.startsWith('+')) return 'pos'
  return null
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

function BalanceStatementTable({ rows, onRowClick }) {
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
              <tr key={key} className={['currentAssets', 'totalAssets', 'totalLiabilities'].includes(key) ? 'is-emphasis' : ''} onClick={() => onRowClick && onRowClick(label)} style={onRowClick ? {cursor: 'pointer'} : {}}>
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

function CashFlowAssistantCard() {
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
      revenue: null,
      net_income: null,
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

function buildDashboardModel(analysis, trendRows, peerResult, qualityCharts, balanceSheetStrength, cockpit = null) {
  const summary = analysis?.summary || {}
  const latest = latestPeriod(analysis)
  const cockpitCompany = cockpit?.company || {}
  const cockpitQuality = cockpit?.data_quality || null
  const cockpitNarrative = cockpit?.narrative || null
  const cockpitKpis = buildCockpitKpis(cockpit)
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
    companyName: cockpitCompany.name || analysis?.company_name || `CTCP ${analysis?.ticker || 'FPT'}`,
    exchange: cockpitCompany.exchange || analysis?.exchange || analysis?.market || 'HOSE',
    unit: analysis?.unit || 'tỷ VND',
    aiTitle: `Đọc nhanh BCTC ${analysis?.ticker || cockpitCompany.ticker || 'doanh nghiệp'}`,
    healthScore,
    healthTone: healthScore >= 75 ? 'good' : healthScore >= 55 ? 'caution' : 'warn',
    strengthTags: buildStrengthTags(summary, healthScore),
    summaryBullets: buildCockpitSummaryBullets(cockpitNarrative) || buildSummaryBullets(summary, { cfo, netIncome, fcf, debt }),
    dataQualityLabel: cockpitQuality ? dataQualityLabel(cockpitQuality) : 'Nguồn dữ liệu hiện có',
    dataQualityNote: cockpitQuality ? dataQualityNote(cockpitQuality) : 'Đang dùng kết quả phân tích đã chuẩn hóa.',
    dataQualityItems: buildDataQualityItems(cockpitQuality, analysis),
    kpis: cockpitKpis || [
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

function buildCockpitKpis(cockpit) {
  const items = cockpit?.headline_kpis || []
  if (!items.length) return null
  const iconMap = {
    revenue_ttm: 'R',
    net_income_ttm: 'N',
    roe: 'E',
    net_margin: 'M',
    cfo_to_net_income: 'C',
    debt_to_equity: 'D',
  }
  return items.map((item) => ({
    icon: iconMap[item.key] || '·',
    label: item.label,
    value: formatCockpitValue(item.value, item.value_type),
    note: item.delta_pct == null ? valueTypeLabel(item.value_type) : `${formatSignedPercent(item.delta_pct)} YoY`,
    tone: cockpitTone(item),
    sparkValues: [],
  }))
}

function buildCockpitSummaryBullets(narrative) {
  if (!narrative) return null
  const strengths = (narrative.strengths || []).map((text) => ({ tone: 'good', text }))
  const cautions = (narrative.cautions || []).map((text) => ({ tone: 'warn', text }))
  const bullets = [...strengths, ...cautions].filter((item) => item.text)
  return bullets.length ? bullets.slice(0, 4) : null
}

function buildDataQualityItems(quality, analysis) {
  if (!quality) {
    return [
      { label: 'Nguồn', value: analysis?.source || 'n/a' },
      { label: 'Kỳ mới nhất', value: analysis?.latest_period || 'n/a' },
      { label: 'Ghi chú', value: `${analysis?.provider_notes?.length || 0}` },
    ]
  }
  return [
    { label: 'Nguồn', value: quality.source || 'n/a' },
    { label: 'Số kỳ', value: String(quality.period_count || 0) },
    { label: 'Thiếu field', value: String(quality.missing_fields?.length || 0) },
    { label: 'Coverage', value: `${quality.period_coverage?.from || '-'} → ${quality.period_coverage?.to || '-'}` },
  ]
}

function dataQualityLabel(quality) {
  const missingCount = quality?.missing_fields?.length || 0
  if (missingCount === 0) return 'Đủ dữ liệu lõi'
  if (missingCount <= 4) return 'Thiếu nhẹ'
  return 'Cần kiểm tra dữ liệu'
}

function dataQualityNote(quality) {
  const missing = quality?.missing_fields || []
  if (!missing.length) return 'Các nhóm KQKD, CĐKT và dòng tiền có đủ trường chính.'
  return `Thiếu: ${missing.slice(0, 4).join(', ')}${missing.length > 4 ? '...' : ''}`
}

function formatCockpitValue(value, valueType) {
  if (valueType === 'money') return formatCompactNumber(value)
  if (valueType === 'percent') return formatPercent(value)
  if (valueType === 'ratio') return `${formatMaybeNumber(value)}x`
  return formatMaybeNumber(value)
}

function valueTypeLabel(valueType) {
  if (valueType === 'money') return 'TTM / latest'
  if (valueType === 'percent') return 'Latest'
  if (valueType === 'ratio') return 'Ratio'
  return 'Latest'
}

function cockpitTone(item) {
  if (item.key === 'debt_to_equity') return reverseScoreTone(item.value, 1.2, 0.7)
  if (item.key === 'cfo_to_net_income') return scoreTone(item.value, 0.8, 1)
  if (item.tone === 'warning') return 'warn'
  if (item.tone === 'positive') return 'good'
  return item.tone || 'neutral'
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
    const grossProfit = firstNumber(item.gross_profit)
    const operatingProfit = firstNumber(item.operating_profit, item.ebit)
    return {
      label: normalizePeriodLabel(item),
      period: item.period,
      year: item.year,
      quarter: item.quarter,
      gross_margin: firstNumber(item.gross_margin_pct, Number.isFinite(revenue) && Number.isFinite(grossProfit) ? (grossProfit / revenue) * 100 : null),
      operating_margin: firstNumber(item.operating_margin_pct, item.ebit_margin_pct, Number.isFinite(revenue) && Number.isFinite(operatingProfit) ? (operatingProfit / revenue) * 100 : null),
      ebit_margin: firstNumber(item.ebit_margin_pct, Number.isFinite(revenue) && Number.isFinite(operatingProfit) ? (operatingProfit / revenue) * 100 : null),
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

function buildSourceStatementReport(analysis, cockpit, extractionResult) {
  const periods = [...(analysis?.periods || [])]
    .slice()
    .sort((a, b) => {
      const ay = Number(a.year || 0)
      const by = Number(b.year || 0)
      if (ay !== by) return ay - by
      return Number(a.quarter || 0) - Number(b.quarter || 0)
    })
  const latest = periods.at(-1) || null
  const compare = latest ? sameQuarterPreviousYear(periods, latest) || periods.at(-2) || null : null
  const latestLabel = normalizePeriodLabel(latest || {})
  const compareLabel = normalizePeriodLabel(compare || {})
  const ytdLabels = buildYtdLabels(latest, compare)
  const columns = [
    { key: 'line_item', label: 'Khoản mục BCTC' },
    { key: 'current', label: latestLabel || 'Kỳ hiện tại' },
    { key: 'compare', label: compareLabel || 'Kỳ so sánh' },
    { key: 'change', label: 'Thay đổi' },
    { key: 'ytd_current', label: ytdLabels.current },
    { key: 'ytd_compare', label: ytdLabels.compare },
    { key: 'ytd_change', label: 'Thay đổi' },
    { key: 'source', label: 'Nguồn' },
    { key: 'chart', label: 'Chart dùng' },
  ]
  const evidenceByMetric = buildExtractionEvidenceMap(extractionResult)
  const rowGroups = [
    {
      key: 'income',
      label: 'Kết quả kinh doanh',
      rows: [
        { key: 'revenue', label: 'Doanh thu thuần', chart: 'Tăng trưởng', tone: 'income', total: true },
        { key: 'cogs', label: 'Giá vốn hàng bán', note: 'Ước tính = Doanh thu - Lợi nhuận gộp nếu BCTC thiếu dòng gốc', chart: 'Biên gộp', tone: 'income', derived: true },
        { key: 'gross_profit', label: 'Lợi nhuận gộp', chart: 'Biên gộp', tone: 'income' },
        { key: 'operating_profit', fallback: 'ebit', label: 'Lợi nhuận HĐKD / EBIT', chart: 'Biên HĐKD', tone: 'income' },
        { key: 'net_income', label: 'LNST', chart: 'Lợi nhuận', tone: 'income', total: true },
      ],
    },
    {
      key: 'balance',
      label: 'Bảng cân đối kế toán',
      rows: [
        { key: 'cash', label: 'Tiền & tương đương tiền', chart: 'Thanh khoản', tone: 'balance' },
        { key: 'receivables', label: 'Phải thu khách hàng', chart: 'Chất lượng tài sản', tone: 'balance' },
        { key: 'inventory', label: 'Hàng tồn kho', chart: 'Hiệu quả vốn lưu động', tone: 'balance' },
        { key: 'current_assets', label: 'Tài sản ngắn hạn', chart: 'Thanh khoản', tone: 'balance' },
        { key: 'fixed_assets', label: 'Tài sản cố định', chart: 'Cấu trúc tài sản', tone: 'balance' },
        { key: 'total_assets', fallback: 'assets', label: 'Tổng tài sản', chart: 'Bảng cân đối', tone: 'balance', total: true },
        { key: 'current_liabilities', label: 'Nợ ngắn hạn', chart: 'Rủi ro thanh khoản', tone: 'balance' },
        { key: 'non_current_liabilities', label: 'Nợ dài hạn', chart: 'Cấu trúc vốn', tone: 'balance' },
        { key: 'total_liabilities', fallback: 'liabilities', label: 'Nợ phải trả', chart: 'Rủi ro', tone: 'balance', total: true },
        { key: 'equity', label: 'Vốn chủ sở hữu', chart: 'Đòn bẩy', tone: 'balance', total: true },
      ],
    },
    {
      key: 'cashflow',
      label: 'Lưu chuyển tiền tệ',
      rows: [
        { key: 'operating_cash_flow', label: 'CFO - Dòng tiền HĐKD', chart: 'Dòng tiền', tone: 'cashflow', total: true },
        { key: 'investing_cash_flow', label: 'CFI - Dòng tiền đầu tư', chart: 'Dòng tiền', tone: 'cashflow' },
        { key: 'financing_cash_flow', label: 'CFF - Dòng tiền tài chính', chart: 'Dòng tiền', tone: 'cashflow' },
        { key: 'capex', label: 'CAPEX', chart: 'FCF', tone: 'cashflow' },
        { key: 'free_cash_flow', label: 'FCF', note: 'Ước tính = CFO - |CAPEX| nếu provider chưa có sẵn', chart: 'Chất lượng lợi nhuận', tone: 'cashflow', total: true },
      ],
    },
  ]
  const reportRows = rowGroups.flatMap((group) => [
    { type: 'section', key: `section-${group.key}`, label: group.label },
    ...group.rows.map((line) => buildStatementReportRow(line, periods, latest, compare, evidenceByMetric)),
  ])
  const cockpitRows = Object.values(cockpit?.statement_tables || {}).flatMap((table) => table?.rows || [])
  const hasData = reportRows.some((row) => row.type !== 'section' && [
    row.current,
    row.compare,
    row.ytdCurrent,
    row.ytdCompare,
  ].some((value) => Number.isFinite(value))) || cockpitRows.some((row) => Number.isFinite(firstNumber(...(row.values || []))))
  return {
    title: `Bảng BCTC nguồn ${analysis?.ticker || cockpit?.ticker || ''}`.trim(),
    subtitle: 'Parse từ Word/PDF/scan/provider về dạng bảng có cấu trúc, để chart lấy đúng dòng số liệu thay vì tự “đoán”.',
    unit: normalizeUnitLabel(analysis?.unit || cockpit?.unit),
    columns,
    rows: reportRows,
    hasData,
  }
}

function buildStatementReportRow(line, periods, latest, compare, evidenceByMetric = new Map()) {
  const current = statementValue(latest, line)
  const compareValue = statementValue(compare, line)
  const ytdCurrent = ytdStatementValue(periods, latest, line)
  const ytdCompare = ytdStatementValue(periods, compare, line)
  return {
    type: 'line',
    key: line.key,
    label: line.label,
    note: line.note,
    chart: line.chart,
    tone: line.tone,
    isTotal: line.total,
    current,
    compare: compareValue,
    changePct: growthPct(current, compareValue),
    ytdCurrent,
    ytdCompare,
    ytdChangePct: growthPct(ytdCurrent, ytdCompare),
    evidence: evidenceByMetric.get(line.key) || (line.fallback ? evidenceByMetric.get(line.fallback) : null),
    derived: line.derived,
  }
}

function buildExtractionEvidenceMap(extractionResult) {
  const rows = (extractionResult?.raw_tables || []).flatMap((table) => table?.rows || [])
  const evidence = new Map()
  rows.forEach((row) => {
    const metric = row?.metric
    if (!metric || evidence.has(metric)) return
    evidence.set(metric, {
      page: row.page,
      confidence: row.confidence,
      label: row.label,
      code: row.code,
    })
  })
  return evidence
}

function statementValue(period, line) {
  if (!period) return null
  if (line.key === 'cogs') {
    const revenue = firstNumber(period.revenue)
    const grossProfit = firstNumber(period.gross_profit)
    return Number.isFinite(revenue) && Number.isFinite(grossProfit) ? revenue - grossProfit : null
  }
  if (line.key === 'free_cash_flow') {
    const cfo = firstNumber(period.operating_cash_flow, period.cfo)
    const capex = firstNumber(period.capex)
    return Number.isFinite(cfo) && Number.isFinite(capex) ? cfo - Math.abs(capex) : null
  }
  return firstNumber(period[line.key], line.fallback ? period[line.fallback] : null)
}

function ytdStatementValue(periods, anchor, line) {
  if (!anchor?.year) return null
  const quarter = Number(anchor.quarter)
  const yearlyRows = periods.filter((item) => Number(item.year) === Number(anchor.year))
  const rows = Number.isFinite(quarter) && quarter > 0
    ? yearlyRows.filter((item) => Number(item.quarter || 0) > 0 && Number(item.quarter) <= quarter)
    : yearlyRows
  if (!rows.length) return null
  const flowKeys = new Set(['revenue', 'cogs', 'gross_profit', 'operating_profit', 'ebit', 'net_income', 'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'capex', 'free_cash_flow'])
  if (!flowKeys.has(line.key)) return statementValue(anchor, line)
  const values = rows.map((item) => statementValue(item, line)).filter((value) => Number.isFinite(value))
  if (!values.length) return null
  return values.reduce((total, value) => total + value, 0)
}

function sameQuarterPreviousYear(periods, anchor) {
  if (!anchor?.year) return null
  const targetYear = Number(anchor.year) - 1
  const targetQuarter = Number(anchor.quarter || 0)
  return periods.find((item) => Number(item.year) === targetYear && Number(item.quarter || 0) === targetQuarter) || null
}

function buildYtdLabels(latest, compare) {
  const latestQuarter = Number(latest?.quarter || 0)
  const compareQuarter = Number(compare?.quarter || latestQuarter || 0)
  if (latest?.year && latestQuarter > 0) {
    return {
      current: `${latestQuarter * 3}T${latest.year}`,
      compare: compare?.year ? `${(compareQuarter || latestQuarter) * 3}T${compare.year}` : 'Lũy kế so sánh',
    }
  }
  return { current: 'Lũy kế hiện tại', compare: 'Lũy kế so sánh' }
}

function growthPct(current, base) {
  const currentNumber = Number(current)
  const baseNumber = Number(base)
  if (!Number.isFinite(currentNumber) || !Number.isFinite(baseNumber) || baseNumber === 0) return null
  return ((currentNumber - baseNumber) / Math.abs(baseNumber)) * 100
}

function formatStatementCell(value, valueType) {
  if (value === null || value === undefined || value === '') return 'Chưa đọc'
  if (valueType === 'percent') return formatPercent(value)
  return formatCompactNumber(value)
}

function statementCellClass(value) {
  return value === null || value === undefined || value === '' ? 'is-missing' : ''
}

function changeCellClass(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  if (numeric > 0) return 'is-positive'
  if (numeric < 0) return 'is-negative'
  return 'is-flat'
}

function summarizeUploadTypes(uploadTypes) {
  const types = uploadTypes?.types || {}
  const count = Object.values(types).reduce((total, items) => total + (items?.length || 0), 0)
  const maxSize = uploadTypes?.max_file_size_mb
  if (!count) return 'Hỗ trợ PDF, XLSX, CSV, DOCX, ảnh scan và XML/XBRL.'
  return `${count} định dạng · tối đa ${maxSize || 25}MB/file · ưu tiên PDF gốc hoặc Excel.`
}

function uploadStatusText(uploadResult) {
  if (uploadResult?.status === 'analyzed') return `đã phân tích ${uploadResult.period_count || 0} kỳ`
  if (uploadResult?.extraction_status === 'markdown_ready') return 'đã có Markdown bảng BCTC, sẵn sàng dựng chart'
  if (uploadResult?.extraction_status === 'needs_ocr') return 'đã có Markdown thô nhưng chưa đủ bảng số liệu'
  if (uploadResult?.extraction_status) return `đã trích xuất: ${uploadResult.extraction_status}`
  if (uploadResult?.status === 'uploaded') return 'đã upload, bấm Phân tích file upload'
  return uploadResult?.status || 'ready'
}

function canAnalyzeUploadedStatement(uploadResult) {
  return uploadResult?.file_type?.pipeline === 'structured_table' || uploadResult?.extraction_status === 'markdown_ready'
}

function extractionStatusLabel(status) {
  if (status === 'markdown_ready') return 'Markdown ready'
  if (status === 'needs_ocr') return 'Markdown thô'
  if (status === 'text_detected') return 'Có text layer'
  if (status === 'extracted') return 'Đã trích xuất'
  if (status === 'unsupported') return 'Chưa hỗ trợ'
  return 'Extraction'
}

function normalizeUnitLabel(unit) {
  const normalized = String(unit || '').trim().toLowerCase()
  if (!normalized || normalized === 'ty_vnd' || normalized === 'billion_vnd') return 'tỷ VND'
  return unit
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

function buildRatioPeriodRows(analysis) {
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
  return [label, formatCompactNumber(prev), formatCompactNumber(cur), formatSignedCompact(change), formatSignedPercentPlain(pct)]
}

function formatSignedCompact(value) {
  if (value == null || !Number.isFinite(value)) return 'n/a'
  const formatted = formatCompactNumber(Math.abs(value))
  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
}

function formatSignedPercentPlain(value) {
  if (value == null || !Number.isFinite(value)) return 'n/a'
  const formatted = `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(Math.abs(value))}%`
  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
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
    if (value === null || value === undefined || value === '') continue
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

function BalanceSheetSummaryCard({ data, fallbackItems, fallbackTotal }) {
  const fundingItems = data?.funding_items || fallbackItems?.filter((item) => ['debt', 'equity'].includes(item.tone)) || []
  const assetItems = data?.asset_items || fallbackItems?.filter((item) => !['debt', 'equity'].includes(item.tone)) || []
  const totalAssets = firstNumber(data?.total_assets, fallbackTotal)
  const totalFunding = firstNumber(data?.total_funding, fallbackTotal, totalAssets)
  const liabilities = firstNumber(
    data?.funding_items?.find((item) => item.key?.includes('liabilit') || item.label?.toLowerCase().includes('nợ'))?.value,
    fundingItems.find((item) => item.tone === 'debt')?.value,
  )
  const equity = firstNumber(
    data?.funding_items?.find((item) => item.key?.includes('equity') || item.label?.toLowerCase().includes('vốn'))?.value,
    fundingItems.find((item) => item.tone === 'equity')?.value,
  )
  const cash = firstNumber(
    data?.asset_items?.find((item) => item.key?.includes('cash') || item.label?.toLowerCase().includes('tiền'))?.value,
    assetItems.find((item) => item.label?.toLowerCase().includes('tiền'))?.value,
  )
  const liabilityRatio = firstNumber(data?.ratios?.liabilities_to_assets, ratioPercent(liabilities, totalFunding) / 100)
  const estimatedCount = data?.data_quality?.estimated_fields?.length || 0

  return (
    <div className="bctc-balance-summary">
      <div className="bctc-balance-summary__score">
        <span>Nợ / nguồn vốn</span>
        <strong>{formatRatioPercent(liabilityRatio)}</strong>
      </div>
      <div className="bctc-balance-summary__grid">
        <p>
          <span>Tổng tài sản</span>
          <strong>{formatCompactNumber(totalAssets)}</strong>
        </p>
        <p>
          <span>Vốn chủ</span>
          <strong>{formatCompactNumber(equity)}</strong>
        </p>
        <p>
          <span>Tiền mặt</span>
          <strong>{formatCompactNumber(cash)}</strong>
        </p>
      </div>
      {estimatedCount ? <em>{estimatedCount} trường dữ liệu đang được ước tính.</em> : null}
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
  const drawableRows = useMemo(
    () => rows.filter((row) => metrics.some((metric) => chartNumber(row[metric.key]) !== null)),
    [rows, metrics],
  )
  const [activeIndex, setActiveIndex] = useState(Math.max(0, drawableRows.length - 1))
  const chart = useMemo(() => buildSvgChartModel(drawableRows, metrics, height), [drawableRows, metrics, height])
  const fallbackIndex = Math.max(0, drawableRows.length - 1)
  const visibleIndex = Math.min(activeIndex, fallbackIndex)
  const activePoint = drawableRows[visibleIndex] || drawableRows.at(-1)

  if (!drawableRows.length) {
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
          setActiveIndex(Math.max(0, Math.min(drawableRows.length - 1, nextIndex)))
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
  const leftValues = rows.flatMap((row) => barMetrics.map((metric) => chartNumber(row[metric.key])).filter((value) => value !== null))
  const rightValues = rows.flatMap((row) => lineMetrics.map((metric) => chartNumber(row[metric.key])).filter((value) => value !== null))
  const leftDomain = niceDomain(leftValues, true)
  const rightDomain = niceDomain(rightValues, false)
  const yLeft = (value) => bottom - ((Number(value) - leftDomain.min) / Math.max(1, leftDomain.max - leftDomain.min)) * plotHeight
  const yRight = (value) => bottom - ((Number(value) - rightDomain.min) / Math.max(1, rightDomain.max - rightDomain.min)) * plotHeight
  const xByIndex = rows.map((_, index) => left + index * step)
  const groupWidth = Math.min(54, Math.max(24, step * 0.58))
  const barWidth = Math.max(8, Math.min(20, groupWidth / Math.max(1, barMetrics.length) - 4))
  const zeroY = yLeft(0)

  const barShapes = rows.flatMap((row, index) => barMetrics.map((metric, metricIndex) => {
    const value = chartNumber(row[metric.key])
    if (value === null) return null
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
      const value = chartNumber(row[metric.key])
      if (value === null) return null
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

function chartNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
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

function formatCompactNumber(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return new Intl.NumberFormat('vi-VN', {
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(numeric)
}

function formatBytes(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  if (numeric < 1024) return `${numeric} B`
  if (numeric < 1024 * 1024) return `${(numeric / 1024).toFixed(1)} KB`
  return `${(numeric / (1024 * 1024)).toFixed(1)} MB`
}

function formatMaybeNumber(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(numeric)
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(numeric)}%`
}

function formatSignedPercent(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  const sign = numeric > 0 ? '▲ ' : numeric < 0 ? '▼ ' : ''
  return `${sign}${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(Math.abs(numeric))}%`
}

function formatRatioPercent(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(numeric * 100)}%`
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

function safeAdd(a, b) {
  const hasA = a !== null && a !== undefined && a !== ''
  const hasB = b !== null && b !== undefined && b !== ''
  if (!hasA && !hasB) return null
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

function StudentNotePanel({ companyId, period, sectionName }) {
  const [note, setNote] = useState('')
  const [status, setStatus] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!note.trim()) return
    setStatus('Đang nộp...')
    try {
      await submitStudentNote({
        student_id: 'student-123',
        company_id: companyId,
        period: period || 'current',
        note_content: note,
        related_metrics: [sectionName]
      })
      setStatus('Nộp thành công!')
      setNote('')
      setTimeout(() => setStatus(''), 3000)
    } catch (err) {
      setStatus(`Lỗi: ${err.message}`)
    }
  }

  return (
    <article className="bctc-panel bctc-student-note" style={{marginTop: '2rem'}}>
      <header className="bctc-panel-header">
        <h2>Nhật ký phân tích (Student Notes)</h2>
        <p>Ghi lại nhận định của bạn về {sectionName} để gửi cho Giảng viên.</p>
      </header>
      <form onSubmit={handleSubmit} className="bctc-note-form" style={{display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem'}}>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder={`Nhập nhận định của bạn về ${sectionName}...`}
          rows={4}
          style={{width: '100%', padding: '0.75rem', borderRadius: '4px', border: '1px solid #ccc', backgroundColor: '#fff', color: '#333', fontSize: '0.9rem'}}
        />
        <div className="bctc-note-footer" style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
          <button type="submit" className="bctc-btn" disabled={!note.trim() || status === 'Đang nộp...'}>Nộp nhận định</button>
          {status && <span className="bctc-note-status" style={{fontSize: '0.9rem', color: status.includes('Lỗi') ? '#dc2626' : '#16a34a'}}>{status}</span>}
        </div>
      </form>
    </article>
  )
}

function WhatIfSimulator({ analysis }) {
  const [revenueChange, setRevenueChange] = useState(0)
  const [marginChange, setMarginChange] = useState(0)

  const latest = analysis?.periods?.[0] || {}
  const currentRev = Number(latest.revenue) || 0
  const currentGrossMargin = Number(latest.gross_margin_pct) || 0
  const currentNetMargin = Number(latest.net_margin_pct) || 0
  const currentNetIncome = Number(latest.net_income) || 0

  const simRev = currentRev * (1 + revenueChange / 100)
  const simNetMargin = currentNetMargin + marginChange
  const simNetIncome = simRev * (simNetMargin / 100)
  const diff = simNetIncome - currentNetIncome

  return (
    <article className="bctc-panel bctc-what-if" style={{marginTop: '1.5rem', padding: '1rem', border: '1px dashed #cbd5e1', borderRadius: '8px', backgroundColor: '#f8fafc'}}>
      <header className="bctc-panel-header" style={{marginBottom: '1rem'}}>
        <h2 style={{fontSize: '1rem', fontWeight: 600, color: '#0f172a'}}>Mô phỏng tác động (What-If)</h2>
      </header>
      <div className="bctc-what-if-controls" style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
        <label style={{display: 'flex', flexDirection: 'column', fontSize: '0.85rem'}}>
          <span>Tăng/giảm Doanh thu: <strong style={{color: '#2f74d0'}}>{revenueChange > 0 ? '+' : ''}{revenueChange}%</strong></span>
          <input type="range" min="-50" max="50" step="5" value={revenueChange} onChange={(e) => setRevenueChange(Number(e.target.value))} />
        </label>
        <label style={{display: 'flex', flexDirection: 'column', fontSize: '0.85rem'}}>
          <span>Tăng/giảm Biên gộp: <strong style={{color: '#2f74d0'}}>{marginChange > 0 ? '+' : ''}{marginChange}%</strong></span>
          <input type="range" min="-20" max="20" step="1" value={marginChange} onChange={(e) => setMarginChange(Number(e.target.value))} />
        </label>
        <div style={{marginTop: '0.5rem', padding: '0.75rem', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #e2e8f0'}}>
          <p style={{fontSize: '0.85rem', color: '#64748b'}}>LNST Dự phóng:</p>
          <h3 style={{fontSize: '1.25rem', color: '#0f172a', margin: '0.25rem 0'}}>{formatCompactNumber(simNetIncome)}</h3>
          <p style={{fontSize: '0.8rem', color: diff >= 0 ? '#16a34a' : '#dc2626'}}>
             {diff >= 0 ? '▲' : '▼'} {formatCompactNumber(Math.abs(diff))} so với hiện tại
          </p>
        </div>
      </div>
    </article>
  )
}

function LineItemExplainerModal({ itemKey, ticker, period, onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchLineItemExplanation(ticker, period, itemKey)
        setData(result)
      } catch (err) {
        console.error('Failed to fetch explanation:', err)
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [ticker, period, itemKey])

  return (
    <div className="bctc-modal-overlay" onClick={onClose} style={{
      position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="bctc-modal-content bctc-panel" onClick={e => e.stopPropagation()} style={{
        maxWidth: 600, width: '100%', maxHeight: '80vh', overflow: 'auto', padding: '1.5rem',
        backgroundColor: '#fff', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, color: 'var(--bctc-text-primary)' }}>Tra cứu thuật ngữ: {itemKey}</h2>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: '#666' }}>&times;</button>
        </div>
        
        {loading ? (
          <p>Đang tải giải thích...</p>
        ) : data ? (
          <div>
            <p style={{ fontWeight: 500, fontSize: '1.1rem', marginBottom: '0.5rem' }}>{data.definition}</p>
            {data.formula && (
              <div style={{ background: '#f5f5f5', padding: '0.5rem 1rem', borderRadius: 4, fontFamily: 'monospace', marginBottom: '1rem' }}>
                <strong>Công thức:</strong> {data.formula}
              </div>
            )}
            <p style={{ marginBottom: '1rem' }}><strong>Ý nghĩa:</strong> {data.significance}</p>
            {data.red_flags && data.red_flags.length > 0 && (
              <div>
                <strong style={{ color: 'var(--bctc-red)' }}>Dấu hiệu bất thường cần lưu ý:</strong>
                <ul style={{ paddingLeft: '1.2rem', marginTop: '0.5rem', color: 'var(--bctc-text-secondary)' }}>
                  {data.red_flags.map((flag, idx) => (
                    <li key={idx} style={{ marginBottom: '0.25rem' }}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}
            {data.examples && data.examples.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <strong>Ví dụ phân tích:</strong>
                <ul style={{ paddingLeft: '1.2rem', marginTop: '0.5rem', color: 'var(--bctc-text-secondary)' }}>
                  {data.examples.map((ex, idx) => (
                    <li key={idx} style={{ marginBottom: '0.25rem' }}>{ex}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p>Không tìm thấy dữ liệu giải thích cho chỉ tiêu này.</p>
        )}
      </div>
    </div>
  )
}
