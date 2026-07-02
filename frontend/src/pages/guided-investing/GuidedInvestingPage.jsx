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
} from '../../modules/financials'
import { trackAnalyticsEvent } from '../../shared/analytics/trackEvent'

import BctcUploadPanel from './components/BctcUploadPanel'
import { HealthScoreGauge, BalanceSheetSummaryCard, CashFlowQuality, MarginAnalysisDetails, MetricTrendChart, HealthRadar } from './components/BctcOverview'
import BctcSectionPanel from './components/BctcSectionPanel'
import LineItemExplainerModal from './components/LineItemExplainerModal'

const DEFAULT_TICKER = 'FPT'
const REVENUE_INCOME_METRICS = [
  { key: 'revenue', label: 'Doanh thu thuần', color: '#16a16f', type: 'bar', scale: 'left', formatValue: formatCompactNumber },
  { key: 'net_income', label: 'LNST', color: '#1f4e79', type: 'bar', scale: 'left', formatValue: formatCompactNumber },
  { key: 'net_margin', label: 'Biên lợi nhuận ròng', color: '#f0a202', type: 'line', scale: 'right', formatValue: formatPercent },
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
      <section className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-slate-50 dark:bg-zinc-950/20 rounded-2xl border border-slate-200 dark:border-zinc-800">
        <span className="text-[10px] text-teal-650 dark:text-teal-400 font-extrabold uppercase tracking-widest">Guided Investing Workspace</span>
        <h1 className="text-xl font-black text-slate-900 dark:text-white mt-2">Đang dựng workspace phân tích BCTC...</h1>
        <div className="w-12 h-12 rounded-full border-4 border-teal-500 border-t-transparent animate-spin mt-6" />
      </section>
    )
  }
  return (
    <section className="w-full min-h-[100dvh] bg-transparent text-slate-900 dark:text-zinc-150 font-sans py-6 md:py-8">
      <div className="max-w-[1720px] mx-auto w-full flex flex-col gap-6 px-6 md:px-10">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-200 dark:border-zinc-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg" role="img" aria-label="BCTC icon">📊</span>
            <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">{isOverview ? 'Phân tích BCTC' : activeTab.label}</h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">{describeSection(activeSection)}</p>
        </div>
        <div className="flex gap-2 flex-wrap text-xs font-semibold">
          <button type="button" className="px-4 py-2 rounded-full border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-slate-800 dark:text-zinc-200 hover:bg-slate-50 dark:hover:bg-zinc-750 transition-all cursor-pointer active:scale-95" onClick={() => void runAnalysis({ refresh: true })}>
            Refresh dữ liệu
          </button>
          <button type="button" className="px-4 py-2 rounded-full border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-slate-805 dark:text-zinc-200 hover:bg-slate-50 dark:hover:bg-zinc-750 transition-all cursor-pointer active:scale-95">
            Xuất báo cáo
          </button>
          <button type="button" className="px-4 py-2 rounded-full bg-teal-500 hover:bg-teal-600 text-white shadow-sm transition-all cursor-pointer active:scale-95" onClick={() => void runAnalysis({ refresh: false })}>
            {uploadResult?.status && uploadResult.status !== 'analyzed' ? 'Phân tích file upload' : 'Phân tích BCTC'}
          </button>
        </div>
      </header>

      {isOverview ? (
        <div className="flex flex-col gap-8">
          <section className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-8 items-start">
            <div className="flex flex-col gap-6">
              <div>
                <span className="text-[10px] text-teal-605 dark:text-teal-400 font-bold uppercase tracking-wider">BCTC Overview</span>
                <h2 className="text-lg font-black text-slate-900 dark:text-white mt-1">{dashboard.aiTitle}</h2>
                <p className="text-xs text-slate-550 dark:text-zinc-400 mt-1.5 leading-relaxed">Một màn tổng quan bắt đầu từ bảng BCTC đã đọc, rồi đối chiếu các dòng số liệu sang chart và insight trước khi đi vào tab phân tích sâu.</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs font-semibold">
                <label className="flex flex-col gap-1.5 text-slate-500">
                  <span>Ticker</span>
                  <input
                    value={ticker}
                    onChange={(event) => setTicker(event.target.value.toUpperCase())}
                    placeholder="Ví dụ: FPT"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-slate-500">
                  <span>Kỳ</span>
                  <select
                    value={mode}
                    onChange={(event) => setMode(event.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all text-xs font-bold"
                  >
                    {modeOptions.map((item) => (
                      <option key={item} value={item}>{modeLabel(item)}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {dashboard.kpis.slice(0, 4).map((item) => (
                  <div key={item.label} className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200 dark:border-zinc-850 flex flex-col justify-between min-w-0">
                    <span className="text-[10px] text-slate-450 uppercase font-bold truncate">{item.label}</span>
                    <strong className="text-base font-extrabold text-slate-900 dark:text-white mt-1.5 truncate">{item.value}</strong>
                    <em className="text-[9px] text-slate-450 mt-1 truncate not-italic">{item.note}</em>
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

            <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-5">
              <header className="flex justify-between items-center pb-2.5 border-b border-slate-100 dark:border-zinc-850">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-teal-50 dark:bg-teal-950/20 text-teal-655 dark:text-teal-400 font-extrabold text-sm flex items-center justify-center">
                    {(analysis?.ticker || ticker || 'NS').slice(0, 3)}
                  </div>
                  <div>
                    <strong className="block text-xs font-bold text-slate-900 dark:text-white truncate">{dashboard.companyName}</strong>
                    <span className="block text-[9px] text-slate-500 truncate mt-0.5">{dashboard.exchange} · {analysis?.latest_period || 'n/a'} · {analysis?.source || providerStatus?.provider || 'n/a'}</span>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 text-[10px] font-bold">{dashboard.dataQualityLabel}</span>
              </header>

              <div className="flex flex-col gap-6">
                <article className="flex flex-col gap-2">
                  <span className="text-[10px] text-slate-450 uppercase font-bold">Revenue quality</span>
                  <h3 className="text-xs font-bold text-slate-805 dark:text-white">Doanh thu & LNST</h3>
                  <MetricTrendChart
                    rows={trendRows}
                    metrics={REVENUE_INCOME_METRICS}
                    formatValue={formatCompactNumber}
                    height={205}
                    showEndpointLabels
                  />
                </article>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-6 border-t border-slate-100 dark:border-zinc-850/60 pt-4">
                  <article className="flex flex-col gap-3">
                    <span className="text-[10px] text-slate-455 uppercase font-bold">Financial health: {dashboard.healthScore}/100</span>
                    <div className="flex items-center gap-3 justify-center">
                      <HealthScoreGauge score={dashboard.healthScore} tone={dashboard.healthTone} />
                      <div className="flex-1 flex flex-col gap-1.5 text-[9px] font-semibold text-slate-650 dark:text-zinc-350">
                        {healthRows.slice(0, 4).map((row) => (
                          <div key={row.label} className="flex flex-col gap-0.5">
                            <span className="truncate">{row.label}: {row.value}/100</span>
                            <div className="w-full h-1 rounded bg-slate-100 dark:bg-zinc-800 overflow-hidden">
                              <div className="h-full bg-teal-500" style={{ width: `${row.value}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </article>

                  <article className="flex flex-col gap-2">
                    <span className="text-[10px] text-slate-455 uppercase font-bold">Margin</span>
                    <h3 className="text-xs font-bold text-slate-800 dark:text-white">Biên lợi nhuận</h3>
                    <MetricTrendChart
                      rows={dashboard.marginRows}
                      metrics={MARGIN_METRICS}
                      formatValue={formatPercent}
                      height={130}
                      showEndpointLabels={false}
                    />
                  </article>
                </div>
              </div>
            </div>
          </section>

          {status && isOverview && <p className="p-3.5 rounded-xl bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 text-xs text-slate-600 font-medium">{status}</p>}
          {error && <p className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 text-xs text-red-600 dark:text-red-400 font-semibold">{error}</p>}

          {analysis && (
            <section className="flex flex-col gap-8">
              <article className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-8 items-center p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm">
                <div className="flex flex-col gap-2">
                  <span className="text-[10px] text-slate-455 font-bold uppercase tracking-wider">01 / Tăng trưởng</span>
                  <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Doanh thu tăng có đi cùng lợi nhuận?</h2>
                  <p className="text-xs text-slate-500 leading-relaxed">Chart này là bằng chứng chính cho câu hỏi đầu tiên: tăng trưởng có thật sự chuyển hóa thành lợi nhuận hay chỉ phình quy mô.</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-150 dark:border-zinc-850 flex flex-col gap-3">
                  <header className="pb-1.5 border-b border-slate-100 dark:border-zinc-850">
                    <h3 className="text-xs font-bold text-slate-805 dark:text-white">Doanh thu & LNST ({modeLabel(mode)} · {analysis?.latest_period || 'Latest'})</h3>
                  </header>
                  <MetricTrendChart
                    rows={trendRows}
                    metrics={REVENUE_INCOME_METRICS}
                    formatValue={formatCompactNumber}
                    height={250}
                    showEndpointLabels
                  />
                </div>
              </article>

              <article className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-8 items-center p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm">
                <div className="flex flex-col gap-2">
                  <span className="text-[10px] text-slate-455 font-bold uppercase tracking-wider">02 / Chất lượng</span>
                  <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Lợi nhuận có bền và có tiền thật không?</h2>
                  <p className="text-xs text-slate-500 leading-relaxed">Hai visual đủ để đọc chất lượng: biên lợi nhuận cho thấy sức giữ lãi, dòng tiền cho thấy lợi nhuận có được xác nhận bằng tiền.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-150 dark:border-zinc-850 flex flex-col gap-2">
                    <h3 className="text-xs font-bold text-slate-805 dark:text-white">Biên lợi nhuận (Gộp · HĐKD · ròng)</h3>
                    <MetricTrendChart
                      rows={dashboard.marginRows}
                      metrics={MARGIN_METRICS}
                      formatValue={formatPercent}
                      height={200}
                      showEndpointLabels
                    />
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-150 dark:border-zinc-850 flex flex-col gap-2">
                    <h3 className="text-xs font-bold text-slate-805 dark:text-white">Dòng tiền (CFO, CFI, CFF và FCF)</h3>
                    <CashFlowQuality data={dashboard.cashFlow} />
                  </div>
                </div>
              </article>

              <article className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-8 items-center p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm">
                <div className="flex flex-col gap-2">
                  <span className="text-[10px] text-slate-455 font-bold uppercase tracking-wider">03 / Rủi ro</span>
                  <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Còn điểm nào phải kiểm tra trước khi tin?</h2>
                  <p className="text-xs text-slate-500 leading-relaxed">Overview chỉ nêu các câu hỏi quan trọng nhất. Nếu cần truy vết từng khoản mục, chuyển sang tab Bảng cân đối, Chỉ số hoặc Dòng tiền.</p>
                  <div className="flex flex-col gap-2 mt-2">
                    {dashboard.checkQuestions.slice(0, 3).map((item, idx) => (
                      <p key={idx} className="text-xs text-amber-700 dark:text-amber-450 bg-amber-50/50 dark:bg-amber-950/10 p-2.5 rounded-lg border border-amber-100/50 dark:border-amber-900/10 leading-relaxed font-semibold">✓ {item}</p>
                    ))}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-150 dark:border-zinc-850 flex flex-col gap-4">
                  <BalanceSheetSummaryCard data={dashboard.balanceSheetStrength} fallbackItems={dashboard.balanceItems} fallbackTotal={dashboard.balanceTotal} />
                  {analysis.flags?.length ? (
                    <ul className="flex flex-col gap-2.5 border-t border-slate-200 dark:border-zinc-800 pt-3">
                      {analysis.flags.slice(0, 3).map((flag, idx) => (
                        <li key={idx} className="text-xs text-slate-655 dark:text-zinc-350">
                          <strong className="block text-slate-900 dark:text-white font-bold">{flag.title}</strong>
                          <span className="block mt-0.5 text-slate-500 dark:text-zinc-400">{flag.detail}</span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </article>
            </section>
          )}
        </div>
      ) : (
        analysis && (
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
            onRowClick={setExplainerKey}
            cockpit={cockpit}
            extractionResult={extractionResult}
          />
        )
      )}

      {explainerKey && (
        <LineItemExplainerModal
          itemKey={explainerKey}
          ticker={ticker}
          period={analysis?.latest_period || 'T12/2024'}
          onClose={() => setExplainerKey(null)}
        />
      )}
      </div>
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

function latestPeriod(analysis) {
  return analysis?.periods?.[0] || null
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
    existing.net_margin = existing.revenue ? (existing.net_income / existing.revenue) * 105 : null
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
    summaryBullets: buildCockpitSummaryBullets(narrativeToObj(cockpitNarrative)) || buildSummaryBullets(summary, { cfo, netIncome, fcf, debt }),
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
    peerCompareRows: buildPeerRows(analysis, summary, peerResult, { roe, netMargin }),
    checkQuestions: buildCheckQuestions(summary, peerResult),
  }
}

function narrativeToObj(narrative) {
  return narrative || null
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

function describeSection(section) {
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
  return SECTION_DESCRIPTIONS[section] || SECTION_DESCRIPTIONS.overview
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

function firstNumber(...args) {
  for (const val of args) {
    if (val !== null && val !== undefined && val !== '') {
      const num = Number(val)
      if (Number.isFinite(num)) return num
    }
  }
  return null
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

function canAnalyzeUploadedStatement(uploadResult) {
  return uploadResult?.file_type?.pipeline === 'structured_table' || uploadResult?.extraction_status === 'markdown_ready'
}

function scoreLabel(tone) {
  if (tone === 'good') return 'Tốt'
  if (tone === 'warn') return 'Cảnh báo'
  return 'Trung bình'
}

function modeLabel(mode) {
  if (mode === 'quarter') return 'Theo quý'
  if (mode === 'month') return 'Theo tháng'
  if (mode === 'period') return 'Theo kỳ'
  return 'Theo năm'
}
