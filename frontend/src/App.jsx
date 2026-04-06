import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  createChart,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
} from 'lightweight-charts'
import './App.css'

const VIEW_META = {
  'view-overview': {
    icon: '📊',
    label: 'Tổng quan Rủi ro',
    title: 'Tổng quan Rủi ro Thị trường',
    sub: 'Đánh giá rủi ro VN-INDEX thời gian thực.',
  },
  'view-explain': {
    icon: '🧠',
    label: 'Giải thích Mô hình',
    title: 'Giải thích Mô hình AI (SHAP)',
    sub: 'Chi tiết mức đóng góp của các yếu tố vĩ mô và kỹ thuật.',
  },
  'view-scenario': {
    icon: '🎛️',
    label: 'Mô phỏng Kịch bản',
    title: 'Mô phỏng Kịch bản Vĩ mô',
    sub: 'What-if analysis theo thời gian thực.',
  },
  'view-sectors': {
    icon: '🏢',
    label: 'Ngành & Thị trường',
    title: 'Screener Ngành & Cổ Phiếu',
    sub: 'So sánh rủi ro ngang giữa thị trường, ngành và cổ phiếu.',
  },
  'view-financials': {
    icon: '📘',
    label: 'Financial Analysis',
    title: 'Phân tích Báo cáo Tài chính',
    sub: 'Đọc nhanh sức khỏe tài chính doanh nghiệp từ dữ liệu fundamentals.',
  },
}

const FEATURE_LABELS = {
  usd_vnd_1m_change_pct: 'Tốc độ tăng tỷ giá (1M)',
  usd_vnd_rate: 'Tỷ giá USD/VND hiện tại',
  sbv_interest_rate_pct: 'Lãi suất điều hành',
  vn_index: 'Định giá VN-INDEX',
  ret_1d: 'Đà giảm ngắn hạn (1D)',
  ret_5d: 'Đà giảm tuần (5D)',
  ret_10d: 'Đà giảm 10 phiên',
  vol_regime_5d_20d: 'Áp lực đột biến thanh khoản',
  realized_vol_20d: 'Biến động giá quá mức (20D)',
  downside_vol_10d: 'Rủi ro rơi tự do',
  ma_gap_20: 'Độ lệch so với MA20',
  ma_slope_10: 'Mất động lượng MA10',
  breadth_advancers_pct: 'Độ rộng: số mã tăng',
  volume_1w_trend_pct: 'Lực bán tháo mạnh',
  cpi_yoy_pct: 'Lạm phát CPI',
  fdi_disbursement_yoy_pct: 'Dòng tiền FDI',
  drawdown_10d: 'Cú rơi sâu 10 ngày',
  drawdown_20d: 'Cú rơi sâu 20 ngày',
}

const BOARD_TABS = [
  { key: 'market', label: 'Market' },
  { key: 'sector', label: 'Sectors' },
  { key: 'ticker', label: 'Tickers' },
]

const CHAT_PROMPTS = [
  'Sao rủi ro tăng?',
  'Nếu Tỷ giá vượt 25.5k?',
  'Stress test danh mục',
  'Rủi ro FPT',
]

const INITIAL_CHAT_MESSAGES = [
  {
    id: 'welcome',
    role: 'assistant',
    text: 'Chào bạn, tôi là Quant AI. Bạn có thể hỏi tôi về phân tích rủi ro thị trường, giải thích số liệu hiện tại, mô phỏng tỷ giá. Hôm nay tôi có thể giúp gì cho bạn?',
  },
]

const DEFAULT_STATUS = {
  tone: 'neutral',
  headline: 'Đang kiểm tra backend...',
  details: [],
}

const EMPTY_BOARD = { market: [], sector: [], ticker: [] }

function pct(value) {
  return Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '--%'
}

function fixedPct(value) {
  return Number.isFinite(value) ? `${value.toFixed(2)}%` : '--%'
}

function humanize(featureKey) {
  return FEATURE_LABELS[featureKey] || featureKey || '--'
}

function formatRegimeLabel(regime) {
  if (!regime) return 'UNKNOWN'
  return String(regime).replaceAll('_', ' ').toUpperCase()
}

function riskClass(regime) {
  const key = String(regime || '').toLowerCase()
  if (key.includes('bear') || key.includes('very_high') || key.includes('crisis')) {
    return 'very_high'
  }
  if (key.includes('high') || key.includes('risk_on_selloff')) {
    return 'high'
  }
  if (key.includes('neutral') || key.includes('sideway') || key.includes('range')) {
    return 'neutral'
  }
  return 'low'
}

function deriveAllocation(score) {
  if (!Number.isFinite(score)) {
    return { cashPct: 50, stockPct: 50 }
  }
  if (score > 0.75) return { cashPct: 80, stockPct: 20 }
  if (score > 0.55) return { cashPct: 60, stockPct: 40 }
  if (score > 0.35) return { cashPct: 30, stockPct: 70 }
  return { cashPct: 10, stockPct: 90 }
}

function normalizeHistoryItem(item) {
  const rawTime = item?.time
  const parsedTime =
    typeof rawTime === 'number'
      ? rawTime
      : Math.floor(new Date(`${rawTime}T00:00:00`).getTime() / 1000)

  return {
    time: parsedTime,
    value: Number(item?.value ?? 0),
    risk_score: Number(item?.risk_score ?? 0),
  }
}

function chartColorForRisk(score) {
  if (score > 0.75) return 'rgba(225, 29, 72, 0.7)'
  if (score > 0.55) return 'rgba(245, 158, 11, 0.7)'
  return 'rgba(16, 185, 129, 0.5)'
}

function buildBoards(quant) {
  if (!quant?.horizons) return EMPTY_BOARD

  return {
    market: [
      {
        symbol: 'VNINDEX',
        kind: 'Market core',
        regime: quant.risk_regime,
        score: quant.decision_score,
        p1w: quant.horizons.p_decline_1w,
        p2w: quant.horizons.p_decline_2w,
        p1m: quant.horizons.p_decline_1m,
        dd: quant.horizons.expected_drawdown_pct,
        driver: quant.dominant_feature,
      },
    ],
    sector: [
      {
        symbol: 'Ngân hàng',
        kind: 'Nhạy cảm thanh khoản',
        regime: 'very_high',
        score: Math.min(0.99, quant.decision_score + 0.09),
        p1w: Math.min(0.99, quant.horizons.p_decline_1w + 0.07),
        p2w: Math.min(0.99, quant.horizons.p_decline_2w + 0.08),
        p1m: Math.min(0.99, quant.horizons.p_decline_1m + 0.06),
        dd: quant.horizons.expected_drawdown_pct * 1.25,
        driver: 'usd_vnd_rate',
      },
      {
        symbol: 'Bất động sản',
        kind: 'Đòn bẩy cao',
        regime: 'high',
        score: Math.min(0.99, quant.decision_score + 0.05),
        p1w: Math.min(0.99, quant.horizons.p_decline_1w + 0.05),
        p2w: Math.min(0.99, quant.horizons.p_decline_2w + 0.06),
        p1m: Math.min(0.99, quant.horizons.p_decline_1m + 0.04),
        dd: quant.horizons.expected_drawdown_pct * 1.18,
        driver: 'sbv_interest_rate_pct',
      },
      {
        symbol: 'Xuất khẩu',
        kind: 'Phòng thủ',
        regime: 'neutral',
        score: Math.max(0.05, quant.decision_score - 0.12),
        p1w: Math.max(0.05, quant.horizons.p_decline_1w - 0.11),
        p2w: Math.max(0.05, quant.horizons.p_decline_2w - 0.09),
        p1m: Math.max(0.05, quant.horizons.p_decline_1m - 0.08),
        dd: quant.horizons.expected_drawdown_pct * 0.72,
        driver: 'breadth_volume_pressure',
      },
    ],
    ticker: [
      {
        symbol: 'VCB',
        kind: 'Banking proxy',
        regime: 'high',
        score: Math.min(0.99, quant.decision_score + 0.04),
        p1w: Math.min(0.99, quant.horizons.p_decline_1w + 0.03),
        p2w: Math.min(0.99, quant.horizons.p_decline_2w + 0.04),
        p1m: Math.min(0.99, quant.horizons.p_decline_1m + 0.03),
        dd: quant.horizons.expected_drawdown_pct * 1.08,
        driver: 'usd_vnd_rate',
      },
      {
        symbol: 'FPT',
        kind: 'Defensive growth',
        regime: 'neutral',
        score: Math.max(0.05, quant.decision_score - 0.1),
        p1w: Math.max(0.05, quant.horizons.p_decline_1w - 0.08),
        p2w: Math.max(0.05, quant.horizons.p_decline_2w - 0.09),
        p1m: Math.max(0.05, quant.horizons.p_decline_1m - 0.07),
        dd: quant.horizons.expected_drawdown_pct * 0.76,
        driver: 'breadth_advancers_pct',
      },
    ],
  }
}

function timeframeToSeconds(timeframe) {
  if (timeframe === '1w') return 7 * 24 * 60 * 60
  if (timeframe === '1m') return 30 * 24 * 60 * 60
  if (timeframe === '3m') return 90 * 24 * 60 * 60
  return 0
}

function formatApiError(payload, fallbackStatus) {
  const detail = payload?.detail ?? payload?.message ?? null

  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (detail && typeof detail === 'object') {
    return [detail.message, detail.error, detail.hint].filter(Boolean).join('\n')
  }

  return `Request failed: ${fallbackStatus}`
}

function formatLargeNumber(value) {
  if (!Number.isFinite(value)) return '--'
  return new Intl.NumberFormat('vi-VN', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}

function formatMetricValue(value, digits = 2) {
  if (!Number.isFinite(value)) return '--'
  return Number(value).toFixed(digits)
}

function hasLiveMetricChanged(previousData, nextData) {
  if (!previousData) return true

  return (
    previousData.value !== nextData.value ||
    previousData.risk_score !== nextData.risk_score ||
    previousData.regime !== nextData.regime ||
    previousData.stock_pct !== nextData.stock_pct ||
    previousData.cash_pct !== nextData.cash_pct ||
    previousData.lower_bound !== nextData.lower_bound ||
    previousData.upper_bound !== nextData.upper_bound
  )
}

function App() {
  const [activeView, setActiveView] = useState('view-overview')
  const [status, setStatus] = useState(DEFAULT_STATUS)
  const [asOf, setAsOf] = useState('')
  const [historyData, setHistoryData] = useState([])
  const [historyError, setHistoryError] = useState('')
  const [timeframe, setTimeframe] = useState('all')
  const [eodLoading, setEodLoading] = useState(false)
  const [quantData, setQuantData] = useState(null)
  const [scenarioData, setScenarioData] = useState(null)
  const [liveData, setLiveData] = useState(null)
  const [moneyFlow, setMoneyFlow] = useState(null)
  const [activeBoardTab, setActiveBoardTab] = useState('market')
  const [chatOpen, setChatOpen] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState(INITIAL_CHAT_MESSAGES)
  const [fxValue, setFxValue] = useState('25000')
  const [irValue, setIrValue] = useState('4.5')
  const [financialTicker, setFinancialTicker] = useState('FPT')
  const [financialLoading, setFinancialLoading] = useState(false)
  const [financialData, setFinancialData] = useState(null)
  const [financialError, setFinancialError] = useState('')
  const [financialStatus, setFinancialStatus] = useState(null)

  const chartContainerRef = useRef(null)
  const chartRef = useRef(null)
  const lineSeriesRef = useRef(null)
  const riskSeriesRef = useRef(null)
  const latestLiveRef = useRef(null)

  const viewInfo = VIEW_META[activeView]
  const boards = useMemo(() => buildBoards(quantData), [quantData])
  const boardRows = boards[activeBoardTab] || []

  const overviewScore = liveData?.risk_score ?? quantData?.decision_score
  const overviewRegime = liveData?.regime ?? quantData?.risk_regime
  const overviewAllocation =
    Number.isFinite(liveData?.stock_pct) && Number.isFinite(liveData?.cash_pct)
      ? {
          stockPct: Math.round(liveData.stock_pct),
          cashPct: Math.round(liveData.cash_pct),
        }
      : deriveAllocation(quantData?.decision_score)

  const fetchJson = useCallback(async (url, options) => {
    const response = await fetch(url, options)
    const payload = await response.json().catch(() => null)
    if (!response.ok) {
      throw new Error(formatApiError(payload, response.status))
    }
    return payload
  }, [])

  const fetchHistoryData = useCallback(async () => {
    try {
      setHistoryError('')
      const payload = await fetchJson('/dashboard/history')
      const normalized = (payload.data || [])
        .map(normalizeHistoryItem)
        .filter((item) => Number.isFinite(item.time))
        .sort((left, right) => left.time - right.time)

      setHistoryData(normalized)

      if (normalized.length === 0) {
        setHistoryError('Không có dữ liệu lịch sử')
      }
    } catch (error) {
      setHistoryData([])
      setHistoryError(error.message)
    }
  }, [fetchJson])

  const fetchLiveData = useCallback(async () => {
    try {
      const data = await fetchJson('/dashboard/live')
      if (!data?.time) return null
      if (!hasLiveMetricChanged(latestLiveRef.current, data)) {
        return latestLiveRef.current
      }
      latestLiveRef.current = data
      setLiveData(data)
      return data
    } catch {
      return null
    }
  }, [fetchJson])

  const fetchMoneyFlowData = useCallback(async () => {
    try {
      const data = await fetchJson('/dashboard/money-flow')
      setMoneyFlow(data)
    } catch {
      setMoneyFlow(null)
    }
  }, [fetchJson])

  const fetchFinancialStatus = useCallback(async () => {
    try {
      const payload = await fetchJson('/financials/status')
      setFinancialStatus(payload)
    } catch {
      setFinancialStatus(null)
    }
  }, [fetchJson])

  useEffect(() => {
    if (!chartContainerRef.current || chartRef.current) return undefined

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#cbd5e1',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.05)' },
        horzLines: { color: 'rgba(255,255,255,0.05)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.1)',
      },
      leftPriceScale: {
        visible: false,
        scaleMargins: { top: 0.75, bottom: 0 },
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.1)',
        timeVisible: true,
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
    })

    const lineSeries = chart.addSeries(LineSeries, {
      color: '#3b82f6',
      lineWidth: 2,
    })

    const histogramSeries = chart.addSeries(HistogramSeries, {
      priceScaleId: 'left',
    })

    chartRef.current = chart
    lineSeriesRef.current = lineSeries
    riskSeriesRef.current = histogramSeries

    const resizeChart = () => {
      if (!chartContainerRef.current) return
      chart.resize(chartContainerRef.current.clientWidth, 280)
    }

    resizeChart()
    window.addEventListener('resize', resizeChart)

    return () => {
      window.removeEventListener('resize', resizeChart)
      chart.remove()
      chartRef.current = null
      lineSeriesRef.current = null
      riskSeriesRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!lineSeriesRef.current || !riskSeriesRef.current) return

    const lineData = historyData.map((item) => ({
      time: item.time,
      value: item.value,
    }))
    const riskBars = historyData.map((item) => ({
      time: item.time,
      value: item.risk_score,
      color: chartColorForRisk(item.risk_score),
    }))

    lineSeriesRef.current.setData(lineData)
    riskSeriesRef.current.setData(riskBars)
  }, [historyData])

  useEffect(() => {
    if (!lineSeriesRef.current || !riskSeriesRef.current || !liveData?.time) return

    lineSeriesRef.current.update({
      time: liveData.time,
      value: liveData.value,
    })
    riskSeriesRef.current.update({
      time: liveData.time,
      value: liveData.risk_score,
      color: chartColorForRisk(liveData.risk_score),
    })
  }, [liveData])

  useEffect(() => {
    if (!chartRef.current || historyData.length === 0) return

    const chart = chartRef.current
    const latestTimestamp = liveData?.time ?? historyData[historyData.length - 1]?.time

    if (timeframe === 'all' || !latestTimestamp) {
      chart.timeScale().fitContent()
      return
    }

    const seconds = timeframeToSeconds(timeframe)
    chart.timeScale().setVisibleRange({
      from: latestTimestamp - seconds,
      to: latestTimestamp,
    })
  }, [historyData, liveData, timeframe])

  useEffect(() => {
    let cancelled = false
    let liveIntervalId
    let moneyFlowIntervalId

    const bootSystem = async () => {
      try {
        const state = await fetchJson('/dashboard/state')
        if (cancelled) return

        if (state.loaded) {
          setAsOf(state.end_date || '')
          setStatus({
            tone: 'good',
            headline: 'Kết nối thành công',
            details: [
              `Database: ${state.rows} rows`,
              `As Of Date: ${state.end_date}`,
            ],
          })

          await fetchHistoryData()
          await fetchLiveData()
          liveIntervalId = window.setInterval(fetchLiveData, 30000)
        } else {
          setStatus({
            tone: 'warn',
            headline: 'Chưa nạp panel dữ liệu',
            details: [state.error, state.hint].filter(Boolean),
          })
        }
      } catch {
        if (cancelled) return
        setStatus({
          tone: 'bad',
          headline: 'Mất kết nối backend',
          details: [],
        })
      }
    }

    bootSystem()
    fetchMoneyFlowData()
    fetchFinancialStatus()
    moneyFlowIntervalId = window.setInterval(fetchMoneyFlowData, 60000)

    return () => {
      cancelled = true
      window.clearInterval(liveIntervalId)
      window.clearInterval(moneyFlowIntervalId)
    }
  }, [fetchFinancialStatus, fetchHistoryData, fetchJson, fetchLiveData, fetchMoneyFlowData])

  const loadFinancialAnalysis = useCallback(
    async (refresh = false) => {
      const ticker = financialTicker.trim().toUpperCase()
      if (!ticker) {
        window.alert('Nhập mã cổ phiếu để phân tích.')
        return
      }

      setFinancialLoading(true)
      setFinancialError('')

      try {
        const payload = await fetchJson(
          `/financials/${encodeURIComponent(ticker)}/analysis${refresh ? '?refresh=true' : ''}`,
        )
        setFinancialData(payload)
      } catch (error) {
        setFinancialData(null)
        setFinancialError(error.message)
      } finally {
        setFinancialLoading(false)
      }
    },
    [fetchJson, financialTicker],
  )

  useEffect(() => {
    if (activeView === 'view-financials' && !financialData && !financialLoading && !financialError) {
      loadFinancialAnalysis(false)
    }
  }, [activeView, financialData, financialError, financialLoading, loadFinancialAnalysis])

  const runEod = async () => {
    if (!asOf) {
      window.alert('Vui lòng chọn ngày As Of Date.')
      return
    }

    setEodLoading(true)
    setStatus({
      tone: 'warn',
      headline: 'Đang xử lý Quant Models...',
      details: [],
    })

    try {
      const payload = await fetchJson('/eod/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ as_of: asOf }),
      })

      setQuantData(payload.quant ?? payload)
      setScenarioData(null)
      setStatus({
        tone: 'good',
        headline: 'Hoàn tất EOD',
        details: [`Date: ${asOf}`],
      })
    } catch (error) {
      setStatus({
        tone: 'bad',
        headline: 'EOD thất bại',
        details: [error.message],
      })
      window.alert(`Lỗi gọi EOD API: ${error.message}`)
    } finally {
      setEodLoading(false)
    }
  }

  const runScenario = async () => {
    if (!asOf) {
      window.alert('Vui lòng chạy EOD hoặc chọn ngày trước khi giả lập kịch bản.')
      return
    }

    try {
      const payload = await fetchJson('/scenario/rerun', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          as_of: asOf,
          usd_vnd_rate: Number(fxValue),
          sbv_interest_rate_pct: Number(irValue),
        }),
      })

      setScenarioData(payload.quant ?? payload)
    } catch (error) {
      window.alert(`Lỗi gọi Scenario API: ${error.message}`)
    }
  }

  const sendChat = async (message) => {
    const trimmed = message.trim()
    if (!trimmed) return
    if (!asOf) {
      window.alert('Chọn ngày lập lưới dữ liệu trước.')
      return
    }

    const typingId = `typing-${Date.now()}`
    setChatMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: 'user', text: trimmed },
      { id: typingId, role: 'assistant', typing: true },
    ])
    setChatInput('')

    try {
      const payload = await fetchJson('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ as_of: asOf, message: trimmed }),
      })

      setChatMessages((current) =>
        current.map((item) =>
          item.id === typingId
            ? {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                text: payload.text || 'Lỗi nội dung.',
                provenance: payload.provenance,
              }
            : item,
        ),
      )
    } catch {
      setChatMessages((current) =>
        current.map((item) =>
          item.id === typingId
            ? {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                text: 'Network Error.',
                error: true,
              }
            : item,
        ),
      )
    }
  }

  const moneyFlowSummary = useMemo(() => {
    if (!moneyFlow) {
      return {
        label: 'Khối ngoại: Đang tải...',
        positive: false,
      }
    }

    if (moneyFlow.foreign_net_val > 0) {
      return {
        label: `Khối ngoại: Mua ròng +${moneyFlow.foreign_net_val} tỷ`,
        positive: true,
      }
    }

    return {
      label: `Khối ngoại: Bán ròng ${moneyFlow.foreign_net_val} tỷ`,
      positive: false,
    }
  }, [moneyFlow])

  const shapItems = quantData?.shap_top || []
  const scenarioRegime = scenarioData?.risk_regime
  const financialFlags = financialData?.flags || []
  const financialNotes = financialData?.provider_notes || financialStatus?.notes || []

  return (
    <div className="app-shell">
      <div className="app-container">
        <aside className="sidebar">
          <div className="brand">
            <div className="brand-logo">DQ</div>
            <div className="brand-name">DeepQuant</div>
          </div>

          <nav className="nav-menu">
            {Object.entries(VIEW_META).map(([key, item]) => (
              <button
                key={key}
                className={`nav-item ${activeView === key ? 'active' : ''}`}
                type="button"
                onClick={() => setActiveView(key)}
              >
                <span className="icon">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          <div className="system-status">
            <span className="eyebrow">Trạng thái Hệ thống</span>
            <div className={`value status-value ${status.tone}`}>
              <div className="status-headline">
                <span className={`live-dot ${status.tone}`} />
                <span>{status.headline}</span>
              </div>
              {status.details.map((detail) => (
                <div key={detail}>{detail}</div>
              ))}
            </div>
          </div>
        </aside>

        <main className="main-content">
          <div className="top-bar">
            <div className="page-title">
              <h1>{viewInfo.title}</h1>
              <p>{viewInfo.sub}</p>
            </div>

            {activeView === 'view-financials' ? (
              <div className="global-controls financial-toolbar">
                <div className="control-group">
                  <label htmlFor="financialTickerInput">Ticker</label>
                  <input
                    id="financialTickerInput"
                    type="text"
                    value={financialTicker}
                    onChange={(event) => setFinancialTicker(event.target.value.toUpperCase())}
                  />
                </div>
                <button
                  className={`btn btn-primary ${financialLoading ? 'loading' : ''}`}
                  type="button"
                  onClick={() => loadFinancialAnalysis(false)}
                >
                  <span className="btn-text">
                    {financialLoading ? 'Đang phân tích...' : 'Phân tích BCTC'}
                  </span>
                  {financialLoading ? (
                    <span className="btn-spinner">
                      <span className="spinner" />
                    </span>
                  ) : null}
                </button>
                <button className="btn btn-ghost" type="button" onClick={() => loadFinancialAnalysis(true)}>
                  Làm mới nguồn
                </button>
              </div>
            ) : (
              <div className="global-controls">
                <div className="control-group">
                  <label htmlFor="asOfInput">As Of Date</label>
                  <input
                    id="asOfInput"
                    type="date"
                    value={asOf}
                    onChange={(event) => setAsOf(event.target.value)}
                  />
                </div>
                <button
                  className={`btn btn-primary ${eodLoading ? 'loading' : ''}`}
                  type="button"
                  onClick={runEod}
                >
                  <span className="btn-text">
                    {eodLoading ? 'Đang tính toán...' : 'Chạy Phân tích EOD'}
                  </span>
                  {eodLoading ? (
                    <span className="btn-spinner">
                      <span className="spinner" />
                    </span>
                  ) : null}
                </button>
              </div>
            )}
          </div>

          <section className={`view ${activeView === 'view-overview' ? 'active' : ''}`}>
            <div className="macro-trackers">
              {quantData?.narrative_inputs ? (
                <>
                  <div className="macro-chip">
                    Đóng cửa VN-INDEX:
                    <span className="macro-chip-value">
                      {quantData.narrative_inputs.vn_index || 'N/A'}
                    </span>
                  </div>
                  <div className="macro-chip">
                    Biến động Tỷ giá:
                    <span className="macro-chip-value text-warn">
                      {quantData.narrative_inputs.usd_vnd_rate || 'N/A'} đ
                    </span>
                  </div>
                  <div className="macro-chip">
                    Điểm mù (Driver):
                    <span className="macro-chip-value text-warn">
                      {humanize(quantData.dominant_feature)}
                    </span>
                  </div>
                </>
              ) : null}
            </div>

            <div className="glass-card chart-card">
              <div className="chart-card-header">
                <h3>Lịch sử Risk Score &amp; VN-INDEX</h3>
                <div className="chart-actions">
                  <div className="timeframe-group">
                    {['1w', '1m', '3m', 'all'].map((item) => (
                      <button
                        key={item}
                        className={`btn btn-ghost tf-btn ${timeframe === item ? 'active' : ''}`}
                        type="button"
                        onClick={() => setTimeframe(item)}
                      >
                        {item.toUpperCase()}
                      </button>
                    ))}
                  </div>
                  <button
                    className="btn btn-ghost export-btn"
                    type="button"
                    onClick={() => window.print()}
                  >
                    🖨️ Xuất Báo Cáo
                  </button>
                </div>
              </div>
              <div className="chart-wrapper">
                <div ref={chartContainerRef} className="chart-surface" />
                {historyError ? <div className="chart-overlay">{historyError}</div> : null}
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{ marginBottom: 12 }}>
                Đề xuất Phân bổ Tài sản Cốt lõi (Asset Allocation)
              </h3>
              <div className="allocation-meta">
                <span className="cash-label">
                  Tỷ trọng Tiền mặt: <span>{overviewAllocation.cashPct}%</span>
                </span>
                <span className="stock-label">
                  Tỷ trọng Cổ phiếu Risk: <span>{overviewAllocation.stockPct}%</span>
                </span>
              </div>
              <div className="allocation-bar-wrap">
                <div
                  className="allocation-bar-cash"
                  style={{ width: `${overviewAllocation.cashPct}%` }}
                />
              </div>
            </div>

            <div className="stats-grid">
              <div className="glass-card stat-card">
                <div
                  className="stat-label has-tooltip"
                  data-tooltip="Xác suất giảm điểm kết hợp từ XGBoost, HMM, GARCH"
                >
                  Composite Risk Score
                </div>
                <div className="stat-value">{pct(overviewScore)}</div>
                <div className="stat-sub">
                  Độ tin cậy: <span>{quantData?.backtest?.last_auc?.toFixed(2) || '--'}</span>
                </div>
              </div>

              <div className="glass-card stat-card">
                <div
                  className="stat-label has-tooltip"
                  data-tooltip="Trạng thái thị trường phát hiện bởi Hidden Markov Model (HMM)"
                >
                  Risk Regime
                </div>
                <div className="stat-value stat-badge-slot">
                  <span className={`badge ${riskClass(overviewRegime)}`}>
                    {formatRegimeLabel(overviewRegime)}
                  </span>
                </div>
              </div>

              <div className="glass-card stat-card">
                <div
                  className="stat-label has-tooltip"
                  data-tooltip="Mức sụt giảm tối đa kỳ vọng dựa trên Monte Carlo VaR"
                >
                  Expected Drawdown
                </div>
                <div className="stat-value">
                  {fixedPct(quantData?.horizons?.expected_drawdown_pct)}
                </div>
                <div className="stat-sub">Max drawdown kỳ vọng</div>
              </div>

              <div className="glass-card stat-card">
                <div
                  className="stat-label has-tooltip"
                  data-tooltip="Biến số có SHAP importance cao nhất đẩy rủi ro tăng"
                >
                  Dominant Driver
                </div>
                <div className="stat-value driver-value">{humanize(quantData?.dominant_feature)}</div>
                <div className="stat-sub text-danger">Yếu tố tác động chính</div>
              </div>
            </div>

            <div className="grid-2">
              <div className="glass-card narrative-card">
                <h3>Bản tin Định lượng (AI Narrative)</h3>
                <p className="section-subtitle">
                  Được sinh tự động từ kết quả Quant Models.
                </p>
                <div className="narrative-body">
                  {quantData?.narrative?.body ||
                    'Chưa có dữ liệu dự báo. Vui lòng chọn ngày và chạy EOD.'}
                </div>
                <ul className="narrative-bullets">
                  {(quantData?.narrative?.bullet_highlights || []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="glass-card">
                <h3>Xác suất Giảm Điểm (Risk Horizons)</h3>
                <div className="bar-chart mt-4">
                  {quantData?.horizons ? (
                    <>
                      <div className="bar-item">
                        <div className="bar-meta">
                          <span>Xác suất 1 Tuần (1W)</span>
                          <span className="val">{pct(quantData.horizons.p_decline_1w)}</span>
                        </div>
                        <div className="bar-track">
                          <div
                            className="bar-fill danger"
                            style={{ width: `${Math.max(5, quantData.horizons.p_decline_1w * 100)}%` }}
                          />
                        </div>
                      </div>
                      <div className="bar-item">
                        <div className="bar-meta">
                          <span>Xác suất 2 Tuần (2W)</span>
                          <span className="val">{pct(quantData.horizons.p_decline_2w)}</span>
                        </div>
                        <div className="bar-track">
                          <div
                            className="bar-fill danger"
                            style={{ width: `${Math.max(5, quantData.horizons.p_decline_2w * 100)}%` }}
                          />
                        </div>
                      </div>
                      <div className="bar-item">
                        <div className="bar-meta">
                          <span>Xác suất 1 Tháng (1M)</span>
                          <span className="val">{pct(quantData.horizons.p_decline_1m)}</span>
                        </div>
                        <div className="bar-track">
                          <div
                            className="bar-fill danger"
                            style={{ width: `${Math.max(5, quantData.horizons.p_decline_1m * 100)}%` }}
                          />
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="muted">Đang tải...</div>
                  )}
                </div>
              </div>
            </div>
          </section>

          <section className={`view ${activeView === 'view-explain' ? 'active' : ''}`}>
            <div className="glass-card">
              <h3>Phân rã Rủi ro (SHAP Explainer)</h3>
              <p className="section-subtitle">
                Biểu đồ thể hiện mức độ đóng góp của các biến số kinh tế vĩ mô và kỹ thuật vào
                tỷ lệ rủi ro chung.
              </p>

              <div className="bar-chart">
                {shapItems.length > 0 ? (
                  shapItems.map((item) => {
                    const isDanger = item.direction === 'increases_risk'
                    return (
                      <div key={item.feature_name} className="bar-item">
                        <div className="bar-meta">
                          <span>{humanize(item.feature_name)}</span>
                          <span className="val">{pct(item.share)}</span>
                        </div>
                        <div className="bar-track">
                          <div
                            className={`bar-fill ${isDanger ? 'danger' : 'success'}`}
                            style={{ width: `${Math.max(5, item.share * 100)}%` }}
                          />
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="empty-state">
                    <div className="empty-icon">🔬</div>
                    <h4>Chưa có dữ liệu SHAP</h4>
                    <p>
                      Chạy &quot;Phân tích EOD&quot; để hệ thống tính toán Feature Attribution cho
                      phiên giao dịch mới nhất.
                    </p>
                    <div className="empty-skeleton">
                      <div className="skeleton skeleton-line long" />
                      <div className="skeleton skeleton-line medium" />
                      <div className="skeleton skeleton-line short" />
                      <div className="skeleton skeleton-line custom-45" />
                      <div className="skeleton skeleton-line custom-30" />
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="glass-card">
              <h3>Metadata &amp; Provenance</h3>
              <pre className="provenance-block">
                {quantData
                  ? JSON.stringify(
                      {
                        run_id: quantData.run_id,
                        model_info: quantData.provenance || {},
                      },
                      null,
                      2,
                    )
                  : 'Không có thông tin Model.'}
              </pre>
            </div>
          </section>

          <section className={`view ${activeView === 'view-scenario' ? 'active' : ''}`}>
            <div className="grid-half">
              <div className="glass-card">
                <h3>Thiết lập Kịch bản Vĩ mô</h3>
                <p className="section-subtitle">
                  Điều chỉnh các yếu tố vĩ mô để đánh giá tác động lên VN-INDEX.
                </p>

                <div className="scenario-controls">
                  <div className="slider-container">
                    <div className="slider-meta">
                      <span>Tỷ giá USD/VND</span>
                      <span>{fxValue}</span>
                    </div>
                    <input
                      type="range"
                      min="23000"
                      max="27000"
                      step="50"
                      value={fxValue}
                      onChange={(event) => setFxValue(event.target.value)}
                    />
                    <input
                      type="number"
                      value={fxValue}
                      onChange={(event) => setFxValue(event.target.value)}
                    />
                  </div>

                  <div className="slider-container">
                    <div className="slider-meta">
                      <span>Lãi suất NHNN (%)</span>
                      <span>{irValue}</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      step="0.1"
                      value={irValue}
                      onChange={(event) => setIrValue(event.target.value)}
                    />
                    <input
                      type="number"
                      value={irValue}
                      onChange={(event) => setIrValue(event.target.value)}
                    />
                  </div>
                </div>

                <button className="btn btn-primary scenario-btn" type="button" onClick={runScenario}>
                  ▶ Chạy Mô phỏng Kịch bản
                </button>
              </div>

              <div className="glass-card">
                <h3>Kết quả Mô phỏng</h3>
                <div className="scenario-result-list">
                  <div className="scenario-result-row">
                    <span>Risk Score Mới</span>
                    <span className="stat-value scenario-value">
                      {pct(scenarioData?.decision_score)}
                    </span>
                  </div>
                  <div className="scenario-result-row">
                    <span>Drawdown Mới</span>
                    <span className="stat-value scenario-value">
                      {fixedPct(scenarioData?.horizons?.expected_drawdown_pct)}
                    </span>
                  </div>
                  <div className="scenario-result-row no-border">
                    <span>Risk Regime Mới</span>
                    <span className={`badge ${riskClass(scenarioRegime)}`}>
                      {formatRegimeLabel(scenarioRegime)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className={`view ${activeView === 'view-sectors' ? 'active' : ''}`}>
            <div className="glass-card">
              <h3 style={{ marginBottom: 12 }}>Bản đồ Dòng tiền (Sector Rotation Matrix)</h3>
              <div className="money-flow-header">
                <span>Luân chuyển nhóm ngành hằng ngày</span>
                <span className={moneyFlowSummary.positive ? 'text-success' : 'text-danger'}>
                  {moneyFlowSummary.label}
                </span>
              </div>
              <div className="heatmap-container">
                {moneyFlow?.sectors?.length ? (
                  moneyFlow.sectors.map((sector) => {
                    const totalWeight = moneyFlow.sectors.reduce(
                      (sum, item) => sum + item.weight,
                      0,
                    )
                    const width = Math.max(8, (sector.weight / totalWeight) * 100 - 1)
                    const isPositive = sector.flow > 0

                    return (
                      <div
                        key={sector.name}
                        className={`heatmap-item ${isPositive ? 'positive' : 'negative'}`}
                        style={{
                          width: `calc(${width}%)`,
                          flexGrow: sector.weight * 10,
                        }}
                      >
                        <div className="heatmap-name">{sector.name}</div>
                        <div className="heatmap-value">
                          {isPositive ? '+' : ''}
                          {Math.abs(sector.flow)} Tỷ
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="muted">Đang tải dữ liệu luân chuyển dòng tiền...</div>
                )}
              </div>
            </div>

            <div className="glass-card">
              <h3>Screener Ngành &amp; Cổ phiếu Đại diện</h3>
              <p className="section-subtitle">
                Dữ liệu mock cho ứng dụng. Phân bổ rủi ro theo từng nhóm ngành và cổ phiếu.
              </p>

              <div className="board-tabs">
                {BOARD_TABS.map((tab) => (
                  <button
                    key={tab.key}
                    className={`board-tab ${activeBoardTab === tab.key ? 'active' : ''}`}
                    type="button"
                    onClick={() => setActiveBoardTab(tab.key)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Thực thể</th>
                      <th>Risk Score</th>
                      <th>Regime</th>
                      <th>1W</th>
                      <th>2W</th>
                      <th>1M</th>
                      <th>Drawdown</th>
                      <th>Driver Chính</th>
                    </tr>
                  </thead>
                  <tbody>
                    {boardRows.length > 0 ? (
                      boardRows.map((row) => (
                        <tr key={row.symbol}>
                          <td>
                            <div className="entity-name">{row.symbol}</div>
                            <div className="entity-sub">{row.kind}</div>
                          </td>
                          <td className={row.score > 0.6 ? 'high-risk-cell' : ''}>{pct(row.score)}</td>
                          <td>
                            <span className={`badge ${riskClass(row.regime)}`}>
                              {String(row.regime).replaceAll('_', ' ')}
                            </span>
                          </td>
                          <td>{pct(row.p1w)}</td>
                          <td>{pct(row.p2w)}</td>
                          <td>{pct(row.p1m)}</td>
                          <td>{fixedPct(row.dd)}</td>
                          <td className="table-muted">{humanize(row.driver)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="8" className="empty-table">
                          Chưa có dữ liệu
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <section className={`view ${activeView === 'view-financials' ? 'active' : ''}`}>
            <div className="glass-card">
              <div className="financial-header-row">
                <div>
                  <h3>Financial Snapshot</h3>
                  <p className="section-subtitle">
                    Tập trung vào tăng trưởng, biên lợi nhuận, dòng tiền, thanh khoản và đòn bẩy.
                  </p>
                </div>
                {financialData?.latest_period ? (
                  <span className="badge neutral">{financialData.latest_period}</span>
                ) : null}
              </div>

              {financialError ? <div className="financial-error">{financialError}</div> : null}

              {financialData ? (
                <>
                  <div className="financial-company-meta">
                    <span className="financial-company-name">
                      {financialData.company_name || financialData.ticker}
                    </span>
                    <span>{financialData.exchange || 'VN'}</span>
                    <span>{financialData.industry || 'Chưa rõ ngành'}</span>
                    <span>Nguồn: {financialData.source}</span>
                  </div>

                  <div className="stats-grid financial-stats-grid">
                    <div className="glass-card stat-card">
                      <div className="stat-label">Doanh thu</div>
                      <div className="stat-value">{formatLargeNumber(financialData.summary.revenue)}</div>
                      <div className="stat-sub">
                        YoY: {formatMetricValue(financialData.summary.revenue_growth_yoy_pct, 1)}%
                      </div>
                    </div>
                    <div className="glass-card stat-card">
                      <div className="stat-label">Lợi nhuận ròng</div>
                      <div className="stat-value">{formatLargeNumber(financialData.summary.net_income)}</div>
                      <div className="stat-sub">
                        YoY: {formatMetricValue(financialData.summary.net_income_growth_yoy_pct, 1)}%
                      </div>
                    </div>
                    <div className="glass-card stat-card">
                      <div className="stat-label">Biên lợi nhuận ròng</div>
                      <div className="stat-value">{formatMetricValue(financialData.summary.net_margin_pct, 1)}%</div>
                      <div className="stat-sub">
                        Biên gộp: {formatMetricValue(financialData.summary.gross_margin_pct, 1)}%
                      </div>
                    </div>
                    <div className="glass-card stat-card">
                      <div className="stat-label">Đòn bẩy / Thanh khoản</div>
                      <div className="stat-value">{formatMetricValue(financialData.summary.debt_to_equity)}</div>
                      <div className="stat-sub">
                        Current ratio: {formatMetricValue(financialData.summary.current_ratio)}
                      </div>
                    </div>
                  </div>

                  <div className="grid-half">
                    <div className="glass-card">
                      <h3>Highlights</h3>
                      <ul className="narrative-bullets financial-bullets">
                        {financialData.highlights.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="glass-card">
                      <h3>Risk Flags</h3>
                      {financialFlags.length > 0 ? (
                        <div className="financial-flag-list">
                          {financialFlags.map((flag) => (
                            <div key={`${flag.level}-${flag.title}`} className={`financial-flag ${flag.level}`}>
                              <div className="financial-flag-title">{flag.title}</div>
                              <div className="financial-flag-detail">{flag.detail}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="muted">Chưa phát hiện cảnh báo trọng yếu từ dữ liệu hiện có.</div>
                      )}
                    </div>
                  </div>

                  <div className="glass-card">
                    <h3>Provider Notes</h3>
                    <div className="financial-notes">
                      {financialNotes.length > 0 ? (
                        financialNotes.map((note) => <div key={note}>• {note}</div>)
                      ) : (
                        <div className="muted">Không có ghi chú thêm.</div>
                      )}
                    </div>
                  </div>

                  <div className="glass-card">
                    <h3>Xu hướng các kỳ gần nhất</h3>
                    <div className="table-container">
                      <table>
                        <thead>
                          <tr>
                            <th>Kỳ</th>
                            <th>Doanh thu</th>
                            <th>Lợi nhuận ròng</th>
                            <th>OCF</th>
                            <th>Gross Margin</th>
                            <th>Net Margin</th>
                            <th>D/E</th>
                            <th>Current Ratio</th>
                          </tr>
                        </thead>
                        <tbody>
                          {financialData.trends.map((trend) => (
                            <tr key={trend.period}>
                              <td>{trend.period}</td>
                              <td>{formatLargeNumber(trend.revenue)}</td>
                              <td>{formatLargeNumber(trend.net_income)}</td>
                              <td>{formatLargeNumber(trend.operating_cash_flow)}</td>
                              <td>{formatMetricValue(trend.gross_margin_pct, 1)}%</td>
                              <td>{formatMetricValue(trend.net_margin_pct, 1)}%</td>
                              <td>{formatMetricValue(trend.debt_to_equity)}</td>
                              <td>{formatMetricValue(trend.current_ratio)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              ) : (
                <div className="muted">
                  Nhập ticker và bấm `Phân tích BCTC`. Nếu provider live lỗi, bạn vẫn có thể dùng cache/import
                  dataset JSON qua API backend.
                </div>
              )}
            </div>
          </section>
        </main>
      </div>

      <button
        className="floating-chat-btn"
        type="button"
        title="Chat với Quant AI"
        onClick={() => setChatOpen((open) => !open)}
      >
        💬
      </button>

      <div className={`floating-chat-popup ${chatOpen ? 'open' : ''}`}>
        <div className="floating-chat-header">
          <span className="chat-title">
            <span className="chat-title-icon">🤖</span> Quant Assistant
          </span>
          <button className="floating-chat-close" type="button" onClick={() => setChatOpen(false)}>
            &times;
          </button>
        </div>

        <div className="chat-interface popup-chat-interface">
          <div className="chat-history">
            {chatMessages.map((message) => (
              <div key={message.id} className={`chat-msg ${message.role}`}>
                <div className={`msg-bubble ${message.error ? 'msg-error' : ''}`}>
                  {message.typing ? (
                    <div className="typing-indicator">
                      <span />
                      <span />
                      <span />
                    </div>
                  ) : (
                    message.text
                  )}
                </div>
                {message.provenance ? (
                  <div className="msg-meta">
                    Model: {message.provenance.model_version} | ID: {message.provenance.run_id}
                  </div>
                ) : null}
              </div>
            ))}
          </div>

          <div className="chat-input-area">
            <div className="chat-prompts">
              {CHAT_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  className="prompt-chip"
                  type="button"
                  onClick={() => sendChat(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>

            <div className="chat-form">
              <input
                type="text"
                placeholder="Hỏi phân tích rủi ro, stress test, vĩ mô..."
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    sendChat(chatInput)
                  }
                }}
              />
              <button className="btn btn-primary" type="button" onClick={() => sendChat(chatInput)}>
                ↗
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
