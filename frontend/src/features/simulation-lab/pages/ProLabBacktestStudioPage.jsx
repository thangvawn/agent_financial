import { useEffect, useMemo, useRef, useState } from 'react'
import {
  AreaSeries,
  BarSeries,
  BaselineSeries,
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  LineSeries,
  createChart,
} from 'lightweight-charts'

import { fetchInstrumentHistory } from '../../market-portfolio/services'
import { runProLabBacktest } from '../services/proLabApi'

const DEFAULT_STRATEGY = `Strategy idea:
- Buy when price closes above 20-day moving average.
- Exit when price closes below 20-day moving average.
- Risk rule: no leverage, paper mode only.`

function toFiniteNumber(value, fallback) {
  if (value === '' || value === null || value === undefined) return fallback
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

const DEFAULT_FORM = {
  symbol: 'BTC',
  period: '5d',
  timeframe: '5m',
  initialCapital: 100000,
  commissionPct: 0.1,
  slippagePct: 0.05,
  strategyText: DEFAULT_STRATEGY,
  chartType: 'candles',
  showMa20: true,
  showMa50: true,
  showMa200: true,
  showVolume: true,
  showEquity: true,
}

const TIMEFRAME_PRESETS = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1h' },
  { value: '4h', label: '4h' },
  { value: '1d', label: '1D' },
  { value: '1wk', label: '1W' },
  { value: '1mo', label: '1M' },
  { value: '1y', label: '1Y' },
]

export default function ProLabBacktestStudioPage({ sessionId, selectedBlueprintId, workspace, accessToken, onBack, onOpenBlueprints }) {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [replayIndex, setReplayIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [result, setResult] = useState(null)
  const [isExpanded, setIsExpanded] = useState(true)
  const chartContainerRef = useRef(null)
  const chartRef = useRef(null)
  const priceSeriesRef = useRef(null)
  const ma20SeriesRef = useRef(null)
  const ma50SeriesRef = useRef(null)
  const ma200SeriesRef = useRef(null)
  const volumeSeriesRef = useRef(null)
  const equitySeriesRef = useRef(null)

  const points = useMemo(() => normalizePoints(history?.points || []), [history])
  const visiblePoints = useMemo(() => points.slice(0, Math.max(1, replayIndex || points.length)), [points, replayIndex])
  const technicalSnapshot = useMemo(() => buildTechnicalSnapshot(visiblePoints), [visiblePoints])
  const selectedBlueprint = workspace?.blueprints?.find((item) => item.blueprint_id === selectedBlueprintId) || null

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError('')
      setResult(null)
      try {
        const payload = await fetchInstrumentHistory(form.symbol.trim().toUpperCase(), {
          period: form.period,
          interval: resolveHistoryInterval(form.timeframe),
        })
        if (cancelled) return
        setHistory(payload)
        setReplayIndex((payload.points || []).length)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Không tải được dữ liệu lịch sử.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [form.symbol, form.period, form.timeframe])

  useEffect(() => {
    if (!chartContainerRef.current || chartRef.current) return undefined

    const initialHeight = isExpanded ? Math.max(520, window.innerHeight - 260) : 620
    chartContainerRef.current.style.height = `${initialHeight}px`

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#dbe7e3',
      },
      grid: {
        vertLines: { color: 'rgba(219, 231, 227, 0.06)' },
        horzLines: { color: 'rgba(219, 231, 227, 0.06)' },
      },
      rightPriceScale: { borderColor: 'rgba(219, 231, 227, 0.12)' },
      leftPriceScale: {
        visible: true,
        borderColor: 'rgba(219, 231, 227, 0.12)',
      },
      timeScale: {
        borderColor: 'rgba(219, 231, 227, 0.12)',
        timeVisible: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: initialHeight,
    })
    const equitySeries = chart.addSeries(AreaSeries, {
      priceScaleId: 'left',
      lineColor: '#d8871f',
      topColor: 'rgba(216, 135, 31, 0.22)',
      bottomColor: 'rgba(216, 135, 31, 0.01)',
      priceLineVisible: false,
    })
    const ma20Series = chart.addSeries(LineSeries, {
      color: '#f6c15d',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    })
    const ma50Series = chart.addSeries(LineSeries, {
      color: '#75a7ff',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    })
    const ma200Series = chart.addSeries(LineSeries, {
      color: '#c084fc',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    })
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceScaleId: 'volume',
      lastValueVisible: false,
      priceLineVisible: false,
    })
    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.82,
        bottom: 0,
      },
    })

    chartRef.current = chart
    priceSeriesRef.current = null
    ma20SeriesRef.current = ma20Series
    ma50SeriesRef.current = ma50Series
    ma200SeriesRef.current = ma200Series
    volumeSeriesRef.current = volumeSeries
    equitySeriesRef.current = equitySeries

    const resizeChart = () => {
      if (!chartContainerRef.current || !chartRef.current) return
      const h = isExpanded ? Math.max(520, window.innerHeight - 260) : 620
      chartContainerRef.current.style.height = `${h}px`
      chartRef.current.applyOptions({
        width: chartContainerRef.current.clientWidth,
        height: h,
      })
    }
    window.addEventListener('resize', resizeChart)
    return () => {
      window.removeEventListener('resize', resizeChart)
      chart.remove()
      chartRef.current = null
      priceSeriesRef.current = null
      ma20SeriesRef.current = null
      ma50SeriesRef.current = null
      ma200SeriesRef.current = null
      volumeSeriesRef.current = null
      equitySeriesRef.current = null
    }
  }, [isExpanded])

  useEffect(() => {
    if (!chartContainerRef.current || !chartRef.current) return
    const h = isExpanded ? Math.max(520, window.innerHeight - 260) : 620
    chartContainerRef.current.style.height = `${h}px`
    chartRef.current.applyOptions({
      width: chartContainerRef.current.clientWidth,
      height: h,
    })
    chartRef.current.timeScale().fitContent()
  }, [isExpanded])

  useEffect(() => {
    if (!chartRef.current) return
    if (priceSeriesRef.current) {
      chartRef.current.removeSeries(priceSeriesRef.current)
      priceSeriesRef.current = null
    }
    priceSeriesRef.current = createPriceSeries(chartRef.current, form.chartType, visiblePoints)
  }, [form.chartType, visiblePoints])

  useEffect(() => {
    if (!priceSeriesRef.current) return
    priceSeriesRef.current.setData(formatPriceSeriesData(visiblePoints, form.chartType))
    ma20SeriesRef.current?.setData(
      form.showMa20 ? movingAverageSeries(visiblePoints, 20) : [],
    )
    ma50SeriesRef.current?.setData(
      form.showMa50 ? movingAverageSeries(visiblePoints, 50) : [],
    )
    ma200SeriesRef.current?.setData(
      form.showMa200 ? movingAverageSeries(visiblePoints, 200) : [],
    )
    volumeSeriesRef.current?.setData(
      form.showVolume ? volumeSeriesData(visiblePoints) : [],
    )
    if (form.showEquity && result?.equityCurve?.length) {
      equitySeriesRef.current?.setData(result.equityCurve.slice(0, visiblePoints.length))
    } else {
      equitySeriesRef.current?.setData([])
    }
    chartRef.current?.timeScale().fitContent()
  }, [visiblePoints, result, form.chartType, form.showMa20, form.showMa50, form.showMa200, form.showVolume, form.showEquity])

  useEffect(() => {
    if (!isPlaying || !points.length) return undefined
    const timer = window.setInterval(() => {
      setReplayIndex((current) => {
        if (current >= points.length) {
          setIsPlaying(false)
          return current
        }
        return current + Math.max(1, Math.floor(points.length / 90))
      })
    }, 180)
    return () => window.clearInterval(timer)
  }, [isPlaying, points.length])

  function updateForm(key, value) {
    setForm((current) => {
      if (key === 'timeframe') {
        const nextOptions = periodOptionsFor(value)
        return {
          ...current,
          timeframe: value,
          period: nextOptions.includes(current.period) ? current.period : nextOptions[0],
        }
      }
      return { ...current, [key]: value }
    })
  }

  function handleDraftWithLlm() {
    setForm((current) => ({
      ...current,
      strategyText: `LLM draft strategy:
- Detect trend with 20-day and 50-day moving averages.
- Enter paper long when MA20 crosses above MA50 and price is above MA20.
- Exit when MA20 crosses below MA50 or drawdown exceeds 8%.
- Do not use leverage. Treat this as research-only, not a trading recommendation.`,
    }))
  }

  async function runBacktest() {
    if (!selectedBlueprintId || !sessionId || !accessToken) {
      setError('Cần mở từ Pro Lab, chọn blueprint và có access token trước khi chạy backend backtest.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload = await runProLabBacktest({
        user_id: sessionId,
        blueprint_id: selectedBlueprintId,
        start_date: resolveStartDate(points, form.period),
        end_date: resolveEndDate(points),
        initial_capital: toFiniteNumber(form.initialCapital, 100000) || 100000,
        timeframe: form.timeframe,
        commission_pct: toFiniteNumber(form.commissionPct, 0),
        slippage_pct: toFiniteNumber(form.slippagePct, 0),
        strategy_text: form.strategyText,
      }, accessToken)
      setResult(adaptBackendBacktestResult(payload))
      setReplayIndex(points.length)
    } catch (err) {
      setError(err.message || 'Không chạy được backend backtest.')
    } finally {
      setLoading(false)
    }
  }  const STYLES = `
    .backtest-studio {
      display: flex;
      flex-direction: column;
      gap: 16px;
      width: 100%;
      color: #edf7f5;
    }
    
    .backtest-studio__hero {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding: 16px 20px;
      background: rgba(16, 29, 38, 0.6);
      border: 1px solid rgba(136, 170, 184, 0.15);
      border-radius: 16px;
    }
    
    .backtest-studio__hero h2 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 800;
      color: #ffffff;
    }
    
    .backtest-studio__hero p {
      margin: 2px 0 0;
      font-size: 0.78rem;
      color: #88aab8;
    }
    
    .backtest-studio-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    
    .backtest-studio__full-layout {
      display: flex;
      flex-direction: column;
      gap: 16px;
      width: 100%;
    }
    
    .backtest-studio__chart-shell {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 20px;
      background: rgba(16, 29, 38, 0.6);
      border: 1px solid rgba(136, 170, 184, 0.15);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.24);
    }
    
    .backtest-studio__chart-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      border-bottom: 1px solid rgba(136, 170, 184, 0.12);
      padding-bottom: 12px;
    }
    
    .backtest-studio__chart-head h3 {
      margin: 0;
      font-size: 1rem;
      font-weight: 700;
      color: #ffffff;
    }
    
    .backtest-studio__toolbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }
    
    .backtest-studio__toolbar select {
      background: #0c1720;
      border: 1px solid rgba(136, 170, 184, 0.2);
      border-radius: 8px;
      color: #edf7f5;
      padding: 6px 10px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
    }
    .backtest-studio__toolbar select:focus {
      outline: none;
      border-color: #4fd1b4;
    }
    
    .backtest-studio__toolbar label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      color: #88aab8;
      cursor: pointer;
      user-select: none;
      padding: 6px 10px;
      border-radius: 8px;
      background: rgba(12, 23, 32, 0.5);
      border: 1px solid rgba(136, 170, 184, 0.12);
      transition: all 0.2s;
    }
    .backtest-studio__toolbar label:hover {
      border-color: rgba(79, 209, 180, 0.3);
      color: #edf7f5;
    }
    .backtest-studio__toolbar label input[type="checkbox"] {
      width: 14px;
      height: 14px;
      accent-color: #4fd1b4;
      cursor: pointer;
      margin: 0;
    }
    
    .backtest-studio__toolbar button {
      padding: 6px 12px;
      background: rgba(12, 23, 32, 0.6) !important;
      border: 1px solid rgba(136, 170, 184, 0.2) !important;
      border-radius: 8px !important;
      color: #edf7f5 !important;
      font-size: 0.75rem !important;
      font-weight: 700 !important;
      cursor: pointer;
      box-shadow: none !important;
      min-height: auto !important;
      height: auto !important;
      transition: all 0.2s;
    }
    .backtest-studio__toolbar button:hover:not(:disabled) {
      background: rgba(79, 209, 180, 0.1) !important;
      border-color: #4fd1b4 !important;
      color: #4fd1b4 !important;
    }
    .backtest-studio__toolbar button:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
    
    .backtest-studio__timeframes {
      display: flex;
      background: #0c1720;
      border: 1px solid rgba(136, 170, 184, 0.2);
      border-radius: 8px;
      padding: 2px;
      gap: 2px;
    }
    .backtest-studio__timeframes button {
      background: transparent !important;
      border: none !important;
      border-radius: 6px !important;
      color: #88aab8 !important;
      font-size: 0.75rem !important;
      font-weight: 700 !important;
      padding: 4px 10px !important;
      cursor: pointer;
      height: auto !important;
      min-height: auto !important;
      box-shadow: none !important;
      transition: all 0.2s;
    }
    .backtest-studio__timeframes button:hover {
      color: #edf7f5 !important;
    }
    .backtest-studio__timeframes button.is-active {
      background: rgba(79, 209, 180, 0.15) !important;
      color: #4fd1b4 !important;
    }
    
    .backtest-studio__chart {
      min-height: 520px;
      width: 100%;
      border-radius: 10px;
      border: 1px solid rgba(136, 170, 184, 0.1);
      background: #0a0f15;
      position: relative;
    }
    
    .backtest-studio__replay {
      width: 100%;
      margin: 8px 0;
      accent-color: #4fd1b4;
      cursor: pointer;
    }
    
    .backtest-studio__foot {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.68rem;
      color: #5e7a72;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    
    .backtest-studio__analysis-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    @media (min-width: 640px) {
      .backtest-studio__analysis-grid {
        grid-template-columns: repeat(4, 1fr);
      }
    }
    @media (min-width: 1024px) {
      .backtest-studio__analysis-grid {
        grid-template-columns: repeat(8, 1fr);
      }
    }
    
    .backtest-studio__metric {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: 10px 8px;
      background: rgba(16, 29, 38, 0.6);
      border: 1px solid rgba(136, 170, 184, 0.15);
      border-radius: 12px;
    }
    .backtest-studio__metric span {
      font-size: 0.65rem;
      font-weight: 800;
      color: #5e7a72;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
    }
    .backtest-studio__metric strong {
      font-size: 1.1rem;
      font-weight: 800;
      color: #edf7f5;
    }
    .backtest-studio__metric.is-up strong {
      color: #4fd1b4;
    }
    .backtest-studio__metric.is-down strong {
      color: #ff6363;
    }
    
    .backtest-studio__bottom-layout {
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
    }
    @media (min-width: 768px) {
      .backtest-studio__bottom-layout {
        grid-template-columns: 1.2fr 1fr;
      }
    }
    
    .backtest-studio__panel {
      padding: 20px;
      background: rgba(16, 29, 38, 0.6) !important;
      border: 1px solid rgba(136, 170, 184, 0.15) !important;
      border-radius: 16px !important;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.24) !important;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .backtest-studio__panel h3 {
      margin: 0 0 4px;
      font-size: 1rem;
      font-weight: 800;
      color: #ffffff;
    }
    
    .backtest-studio__form-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }
    .backtest-studio__form-grid label {
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 0.72rem;
      font-weight: 850;
      color: #5e7a72;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .backtest-studio__panel label input,
    .backtest-studio__panel label select,
    .backtest-studio__panel label textarea {
      background: #0c1720 !important;
      border: 1px solid rgba(136, 170, 184, 0.2) !important;
      border-radius: 8px !important;
      color: #edf7f5 !important;
      padding: 8px 12px !important;
      font-size: 0.82rem !important;
      font-weight: 600 !important;
      font-family: inherit;
    }
    .backtest-studio__panel label input:focus,
    .backtest-studio__panel label select:focus,
    .backtest-studio__panel label textarea:focus {
      outline: none;
      border-color: #4fd1b4 !important;
      box-shadow: 0 0 0 2px rgba(79, 209, 180, 0.15);
    }
    .backtest-studio__panel label textarea {
      resize: vertical;
      font-family: monospace;
    }
    
    .backtest-studio__metrics {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    
    .backtest-studio__trades {
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid rgba(136, 170, 184, 0.15);
      border-radius: 8px;
      background: rgba(12, 23, 32, 0.4);
      scrollbar-width: thin;
    }
    .backtest-studio__trades table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.72rem;
    }
    .backtest-studio__trades th {
      position: sticky;
      top: 0;
      background: #0c1720;
      padding: 6px 8px;
      color: #5e7a72;
      font-weight: 700;
      text-transform: uppercase;
      text-align: left;
      border-bottom: 1px solid rgba(136, 170, 184, 0.15);
    }
    .backtest-studio__trades td {
      padding: 6px 8px;
      border-bottom: 1px solid rgba(136, 170, 184, 0.08);
      color: #edf7f5;
    }
    .backtest-studio__trades tr:hover {
      background: rgba(79, 209, 180, 0.05);
    }
    
    .backtest-studio__result-chart {
      border: 1px solid rgba(136, 170, 184, 0.15);
      border-radius: 8px;
      padding: 10px;
      background: rgba(12, 23, 32, 0.4);
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .backtest-studio__result-chart-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.68rem;
      color: #5e7a72;
      text-transform: uppercase;
      margin-bottom: 6px;
    }
    .backtest-studio__mini-chart {
      width: 100%;
      border-radius: 6px;
      overflow: hidden;
    }
    
    .backtest-studio__monthly {
      border: 1px solid rgba(136, 170, 184, 0.15);
      border-radius: 8px;
      padding: 10px;
      background: rgba(12, 23, 32, 0.4);
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .backtest-studio__monthly-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 4px;
      margin-top: 6px;
    }
    @media (min-width: 480px) {
      .backtest-studio__monthly-grid {
        grid-template-columns: repeat(6, 1fr);
      }
    }
    .backtest-studio__monthly-grid div {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 6px;
      border-radius: 6px;
      font-size: 0.7rem;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(136, 170, 184, 0.05);
    }
    .backtest-studio__monthly-grid div.is-positive {
      background: rgba(57, 217, 138, calc(var(--intensity, 0.5) * 0.15));
      border-color: rgba(57, 217, 138, calc(var(--intensity, 0.5) * 0.25));
    }
    .backtest-studio__monthly-grid div.is-negative {
      background: rgba(255, 99, 99, calc(var(--intensity, 0.5) * 0.15));
      border-color: rgba(255, 99, 99, calc(var(--intensity, 0.5) * 0.25));
    }
    .backtest-studio__monthly-grid div span {
      font-weight: 600;
      color: #5e7a72;
      font-size: 0.6rem;
      text-transform: uppercase;
    }
    .backtest-studio__monthly-grid div strong {
      font-weight: 700;
      color: #edf7f5;
    }
    
    .backtest-studio__hero button,
    .backtest-studio__panel button {
      padding: 8px 16px !important;
      background: linear-gradient(135deg, #0f8f7b, #116d64) !important;
      border: 1px solid rgba(85, 216, 189, 0.4) !important;
      border-radius: 8px !important;
      color: #ffffff !important;
      font-size: 0.8rem !important;
      font-weight: 700 !important;
      cursor: pointer;
      box-shadow: none !important;
      min-height: auto !important;
      height: auto !important;
      transition: all 0.2s;
    }
    .backtest-studio__hero button:hover:not(:disabled),
    .backtest-studio__panel button:hover:not(:disabled) {
      background: linear-gradient(135deg, #11a38c, #137e74) !important;
      border-color: #4fd1b4 !important;
    }
    .backtest-studio__hero button:disabled,
    .backtest-studio__panel button:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
    
    .backtest-studio__hero button {
      background: rgba(12, 23, 32, 0.6) !important;
      border-color: rgba(136, 170, 184, 0.2) !important;
      color: #edf7f5 !important;
    }
    .backtest-studio__hero button:hover {
      background: rgba(79, 209, 180, 0.1) !important;
      border-color: #4fd1b4 !important;
      color: #4fd1b4 !important;
    }
  `;

  return (
    <section className={isExpanded ? 'pro-lab-section backtest-studio backtest-studio--expanded' : 'pro-lab-section backtest-studio'}>
      <style>{STYLES}</style>
      <section className="backtest-studio__hero">
        <div>
          <p className="pro-lab-eyebrow">TradingView-style Sandbox</p>
          <h2>Backtest Studio</h2>
          <p>
            Xem nến OHLC đa khung thời gian từ phút, giờ, ngày, tuần, tháng đến năm; overlay MA, volume, RSI và chạy backtest theo cùng timeframe.
            Đây là paper lab để đọc xu hướng và giả thuyết kỹ thuật, không phải tín hiệu giao dịch.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 mt-2 md:mt-0">
          {onBack ? (
            <button 
              type="button" 
              onClick={onBack}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold !bg-zinc-800/80 hover:!bg-zinc-800 !text-white !border-zinc-700 hover:!border-zinc-600 transition cursor-pointer !h-auto !min-h-0"
            >
              Về Pro Lab
            </button>
          ) : null}
          <span className="px-2 py-1 rounded-md text-[10px] font-bold bg-amber-500/10 border border-amber-500/20 text-amber-400 select-none uppercase tracking-wider">
            Paper only
          </span>
          <span className="px-2 py-1 rounded-md text-[10px] font-bold bg-zinc-800/60 border border-zinc-700/50 text-zinc-400 select-none uppercase tracking-wider">
            Not investment advice
          </span>
          <span className="px-2 py-1 rounded-md text-[10px] font-bold bg-[#4fd1b4]/10 border border-[#4fd1b4]/20 text-[#4fd1b4] select-none">
            {selectedBlueprint ? selectedBlueprint.name : 'No blueprint selected'}
          </span>
          <button 
            type="button" 
            onClick={() => setIsExpanded((current) => !current)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold !bg-zinc-800/80 hover:!bg-zinc-800 !text-white !border-zinc-700 hover:!border-zinc-600 transition cursor-pointer !h-auto !min-h-0"
          >
            {isExpanded ? 'Compact' : 'Full screen'}
          </button>
        </div>
      </section>

      <div className="backtest-studio__full-layout">
        <main className="backtest-studio__chart-shell backtest-studio__chart-shell--full">
          <div className="backtest-studio__chart-head">
            <div>
              <p className="pro-lab-eyebrow">Time Skip / Bar Replay</p>
              <h3>{history?.symbol || form.symbol.toUpperCase()} · {history?.name || 'History feed'}</h3>
            </div>
            <div className="backtest-studio__toolbar">
              <div className="backtest-studio__timeframes" aria-label="Timeframe presets">
                {TIMEFRAME_PRESETS.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    className={form.timeframe === item.value ? 'is-active' : ''}
                    onClick={() => updateForm('timeframe', item.value)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <select value={form.chartType} onChange={(event) => updateForm('chartType', event.target.value)}>
                <option value="candles">Candles</option>
                <option value="bars">Bars</option>
                <option value="line">Line</option>
                <option value="area">Area</option>
                <option value="baseline">Baseline</option>
              </select>
              <label><input type="checkbox" checked={form.showMa20} onChange={(event) => updateForm('showMa20', event.target.checked)} /> MA20</label>
              <label><input type="checkbox" checked={form.showMa50} onChange={(event) => updateForm('showMa50', event.target.checked)} /> MA50</label>
              <label><input type="checkbox" checked={form.showMa200} onChange={(event) => updateForm('showMa200', event.target.checked)} /> MA200</label>
              <label><input type="checkbox" checked={form.showVolume} onChange={(event) => updateForm('showVolume', event.target.checked)} /> Volume</label>
              <label><input type="checkbox" checked={form.showEquity} onChange={(event) => updateForm('showEquity', event.target.checked)} /> Equity</label>
              <button type="button" onClick={() => setReplayIndex(1)} disabled={!points.length}>Reset</button>
              <button type="button" onClick={() => setIsPlaying((current) => !current)} disabled={!points.length}>
                {isPlaying ? 'Pause' : 'Play replay'}
              </button>
              <button type="button" onClick={() => setReplayIndex(points.length)} disabled={!points.length}>Jump latest</button>
              <button type="button" onClick={() => setIsExpanded((current) => !current)}>
                {isExpanded ? 'Exit full screen' : 'Full screen'}
              </button>
            </div>
          </div>
          {loading ? <p className="pro-lab-state">Đang tải dữ liệu lịch sử...</p> : null}
          {error ? <p className="pro-lab-state pro-lab-state--error">{error}</p> : null}
          <div className="backtest-studio__chart" ref={chartContainerRef} />
          <input
            className="backtest-studio__replay"
            type="range"
            min="1"
            max={Math.max(points.length, 1)}
            value={Math.max(1, replayIndex || points.length || 1)}
            onChange={(event) => {
              setIsPlaying(false)
              setReplayIndex(Number(event.target.value))
            }}
          />
          <div className="backtest-studio__foot">
            <span>{visiblePoints[0]?.date || '--'}</span>
            <span>{history?.freshness || 'degraded'} · {history?.source || 'data-hub'} · {form.timeframe}</span>
            <span>{visiblePoints[visiblePoints.length - 1]?.date || '--'}</span>
          </div>
        </main>

        <section className="backtest-studio__analysis-grid">
          <Metric label="Last price" value={formatMoney(technicalSnapshot.lastPrice)} />
          <Metric label="Trend" value={technicalSnapshot.trend} tone={technicalSnapshot.trend === 'Bullish' ? 'up' : technicalSnapshot.trend === 'Bearish' ? 'down' : ''} />
          <Metric label="RSI 14" value={technicalSnapshot.rsi ? technicalSnapshot.rsi.toFixed(1) : '--'} tone={technicalSnapshot.rsi > 70 ? 'down' : technicalSnapshot.rsi < 30 ? 'up' : ''} />
          <Metric label="Volatility" value={`${technicalSnapshot.volatilityPct.toFixed(2)}%`} />
          <Metric label="MA20" value={technicalSnapshot.ma20 ? formatMoney(technicalSnapshot.ma20) : '--'} />
          <Metric label="MA50" value={technicalSnapshot.ma50 ? formatMoney(technicalSnapshot.ma50) : '--'} />
          <Metric label="MA200" value={technicalSnapshot.ma200 ? formatMoney(technicalSnapshot.ma200) : '--'} />
          <Metric label="Structure" value={technicalSnapshot.structure} tone={technicalSnapshot.structure === 'Breakout' ? 'up' : technicalSnapshot.structure === 'Breakdown' ? 'down' : ''} />
        </section>

        <section className="backtest-studio__bottom-layout">
          <aside className="pro-lab-card backtest-studio__panel">
            <p className="pro-lab-eyebrow">Strategy Setup</p>
            <h3>Thiết kế chiến lược</h3>
            <div className="backtest-studio__form-grid">
              <label>
                Symbol
                <input value={form.symbol} onChange={(event) => updateForm('symbol', event.target.value)} />
              </label>
              <label>
                Period
                <select value={form.period} onChange={(event) => updateForm('period', event.target.value)}>
                  {periodOptionsFor(form.timeframe).map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label>
                Timeframe
                <select value={form.timeframe} onChange={(event) => updateForm('timeframe', event.target.value)}>
                  {TIMEFRAME_PRESETS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </label>
              <label>
                Initial capital
                <input type="number" value={form.initialCapital} onChange={(event) => updateForm('initialCapital', event.target.value)} />
              </label>
              <label>
                Commission %
                <input type="number" step="0.01" value={form.commissionPct} onChange={(event) => updateForm('commissionPct', event.target.value)} />
              </label>
              <label>
                Slippage %
                <input type="number" step="0.01" value={form.slippagePct} onChange={(event) => updateForm('slippagePct', event.target.value)} />
              </label>
            </div>
            <label>
              Strategy prompt
              <textarea value={form.strategyText} rows={9} onChange={(event) => updateForm('strategyText', event.target.value)} />
            </label>
            <div className="pro-lab-actions-row">
              <button type="button" onClick={handleDraftWithLlm}>LLM draft</button>
              <button type="button" onClick={runBacktest} disabled={loading || !points.length || !selectedBlueprintId}>Run backend backtest</button>
              {!selectedBlueprint ? <button type="button" onClick={onOpenBlueprints}>Create blueprint</button> : null}
            </div>
          </aside>

          <aside className="pro-lab-card backtest-studio__panel">
          <p className="pro-lab-eyebrow">Result</p>
          <h3>Backtest Summary</h3>
          {result ? (
            <>
              <div className="backtest-studio__metrics">
                <Metric label="Return" value={`${result.metrics.totalReturnPct.toFixed(2)}%`} tone={result.metrics.totalReturnPct >= 0 ? 'up' : 'down'} />
                <Metric label="Max DD" value={`${result.metrics.maxDrawdownPct.toFixed(2)}%`} tone="down" />
                <Metric label="Trades" value={String(result.metrics.trades)} />
                <Metric label="Win rate" value={`${result.metrics.winRatePct.toFixed(1)}%`} />
                <Metric label="Sharpe" value={formatMetric(result.metrics.sharpe)} />
                <Metric label="Vol annual" value={formatPercentMetric(result.metrics.volatilityAnnualPct)} />
              </div>
              {result.meta ? (
                <div className="pro-lab-log-list">
                  <div><strong>Feed</strong><span>{result.meta.source || 'n/a'}</span></div>
                  <div><strong>Timeframe</strong><span>{result.meta.interval || '--'}</span></div>
                  <div><strong>Range</strong><span>{result.meta.range || '--'}</span></div>
                  <div><strong>Cost</strong><span>{result.meta.cost || '--'}</span></div>
                </div>
              ) : null}
              <ResultSeriesChart
                title="Equity vs Benchmark"
                series={[
                  { label: 'Portfolio', color: '#4fd1b4', data: result.series.portfolio },
                  { label: result.meta?.benchmarkLabel || 'Benchmark', color: '#75a7ff', data: result.series.benchmark },
                ]}
                height={230}
                valueMode="money"
              />
              <ResultSeriesChart
                title="Drawdown"
                series={[{ label: 'Drawdown %', color: '#ff6b6b', data: result.series.drawdown }]}
                height={160}
                valueMode="percent"
              />
              <MonthlyReturnStrip months={result.monthlyReturns} />
              <div className="pro-lab-log-list">
                {result.caveats.map((item) => (
                  <div key={item}><strong>Caveat</strong><span>{item}</span></div>
                ))}
              </div>
              <h4>Trades</h4>
              <div className="backtest-studio__trades">
                {result.trades.slice(-8).map((trade, index) => (
                  <div key={`${trade.date}-${index}`}>
                    <strong>{trade.side}</strong>
                    <span>{trade.date}</span>
                    <span>{formatMoney(trade.price)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p>Chưa chạy backtest. Mở từ Pro Lab với một blueprint, sau đó bấm Run backend backtest để dùng dữ liệu lịch sử thật.</p>
          )}
          </aside>
        </section>
      </div>
    </section>
  )
}

function Metric({ label, value, tone = '' }) {
  return (
    <article className={`backtest-studio__metric ${tone ? `is-${tone}` : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}

function ResultSeriesChart({ title, series, height = 220, valueMode = 'money' }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRefs = useRef([])
  const cleanedSeries = useMemo(
    () => series.filter((item) => Array.isArray(item.data) && item.data.length),
    [series],
  )

  useEffect(() => {
    if (!containerRef.current) return undefined
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#dbe7e3',
      },
      grid: {
        vertLines: { color: 'rgba(219, 231, 227, 0.05)' },
        horzLines: { color: 'rgba(219, 231, 227, 0.07)' },
      },
      rightPriceScale: { borderColor: 'rgba(219, 231, 227, 0.12)' },
      timeScale: { borderColor: 'rgba(219, 231, 227, 0.12)', timeVisible: true },
      localization: {
        priceFormatter: (value) => (valueMode === 'percent' ? `${Number(value).toFixed(1)}%` : formatMoney(value)),
      },
      width: containerRef.current.clientWidth,
      height,
    })
    chartRef.current = chart
    const resizeChart = () => {
      if (!containerRef.current || !chartRef.current) return
      chartRef.current.applyOptions({ width: containerRef.current.clientWidth, height })
    }
    window.addEventListener('resize', resizeChart)
    return () => {
      window.removeEventListener('resize', resizeChart)
      chart.remove()
      chartRef.current = null
      seriesRefs.current = []
    }
  }, [height, valueMode])

  useEffect(() => {
    if (!chartRef.current) return
    for (const item of seriesRefs.current) {
      chartRef.current.removeSeries(item)
    }
    seriesRefs.current = cleanedSeries.map((item) => {
      const line = chartRef.current.addSeries(LineSeries, {
        color: item.color,
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: true,
      })
      line.setData(item.data)
      return line
    })
    chartRef.current.timeScale().fitContent()
  }, [cleanedSeries])

  return (
    <section className="backtest-studio__result-chart">
      <div className="backtest-studio__result-chart-head">
        <h4>{title}</h4>
        <div>
          {cleanedSeries.map((item) => (
            <span key={item.label} style={{ '--series-color': item.color }}>{item.label}</span>
          ))}
        </div>
      </div>
      <div className="backtest-studio__mini-chart" ref={containerRef} style={{ minHeight: height }} />
    </section>
  )
}

function MonthlyReturnStrip({ months }) {
  const items = Array.isArray(months) ? months.slice(-18) : []
  if (!items.length) return null
  return (
    <section className="backtest-studio__monthly">
      <h4>Monthly returns</h4>
      <div className="backtest-studio__monthly-grid">
        {items.map((item) => {
          const value = Number(item.return_pct || 0)
          const intensity = Math.min(Math.abs(value) / 12, 1)
          return (
            <div
              key={item.period || item.time}
              className={value >= 0 ? 'is-positive' : 'is-negative'}
              style={{ '--intensity': intensity }}
              title={`${item.period}: ${value.toFixed(2)}%`}
            >
              <span>{item.period}</span>
              <strong>{value.toFixed(1)}%</strong>
            </div>
          )
        })}
      </div>
    </section>
  )
}

function normalizePoints(points) {
  return points
    .map((item, index, array) => {
      const date = item.date || item.time
      const close = Number(item.price || item.close || item.value || 0)
      const previousClose = Number(array[index - 1]?.price || array[index - 1]?.close || array[index - 1]?.value || close)
      const syntheticRange = close * 0.006
      const open = Number(item.open || previousClose || close)
      const high = Number(item.high || Math.max(open, close) + syntheticRange)
      const low = Number(item.low || Math.min(open, close) - syntheticRange)
      const volume = Number(item.volume || 0)
      return {
        date,
        time: normalizeChartTime(date) || date,
        price: close,
        open,
        high,
        low,
        close,
        volume,
      }
    })
    .filter((item) => item.date && Number.isFinite(item.price) && item.price > 0)
}

function createPriceSeries(chart, chartType, points = []) {
  if (chartType === 'candles') {
    return chart.addSeries(CandlestickSeries, {
      upColor: '#4fd1b4',
      downColor: '#ff6363',
      borderUpColor: '#4fd1b4',
      borderDownColor: '#ff6363',
      wickUpColor: '#4fd1b4',
      wickDownColor: '#ff6363',
      priceLineVisible: false,
    })
  }
  if (chartType === 'bars') {
    return chart.addSeries(BarSeries, {
      upColor: '#4fd1b4',
      downColor: '#ff6363',
      priceLineVisible: false,
    })
  }
  if (chartType === 'area') {
    return chart.addSeries(AreaSeries, {
      lineColor: '#4fd1b4',
      topColor: 'rgba(79, 209, 180, 0.26)',
      bottomColor: 'rgba(79, 209, 180, 0.02)',
      priceLineVisible: false,
    })
  }
  if (chartType === 'baseline') {
    const basePrice = points[0]?.price || 0
    return chart.addSeries(BaselineSeries, {
      baseValue: { type: 'price', price: basePrice },
      topLineColor: '#4fd1b4',
      topFillColor1: 'rgba(79, 209, 180, 0.22)',
      topFillColor2: 'rgba(79, 209, 180, 0.02)',
      bottomLineColor: '#ff6363',
      bottomFillColor1: 'rgba(255, 99, 99, 0.2)',
      bottomFillColor2: 'rgba(255, 99, 99, 0.02)',
      priceLineVisible: false,
    })
  }
  return chart.addSeries(LineSeries, {
    color: '#4fd1b4',
    lineWidth: 2,
    priceLineVisible: false,
  })
}

function formatPriceSeriesData(points, chartType) {
  if (chartType === 'candles' || chartType === 'bars') {
    return points.map((item) => ({
      time: item.time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }))
  }
  return points.map((item) => ({ time: item.time, value: item.price }))
}

function movingAverageSeries(points, windowSize) {
  return points
    .map((item, index) => {
      const value = movingAverage(points, index, windowSize)
      return value ? { time: item.time, value } : null
    })
    .filter(Boolean)
}

function volumeSeriesData(points) {
  return points.map((item) => ({
    time: item.time,
    value: item.volume || 0,
    color: item.close >= item.open ? 'rgba(79, 209, 180, 0.24)' : 'rgba(255, 99, 99, 0.24)',
  }))
}

function buildTechnicalSnapshot(points) {
  const last = points[points.length - 1]
  const ma20 = points.length ? movingAverage(points, points.length - 1, 20) : null
  const ma50 = points.length ? movingAverage(points, points.length - 1, 50) : null
  const ma200 = points.length ? movingAverage(points, points.length - 1, 200) : null
  const rsi = calculateRsi(points, 14)
  const volatilityPct = calculateVolatility(points, 20)
  const structure = detectMarketStructure(points)
  let trend = 'Neutral'
  if (ma20 && ma50 && last?.price > ma20 && ma20 > ma50 && (!ma200 || ma50 > ma200)) trend = 'Bullish'
  if (ma20 && ma50 && last?.price < ma20 && ma20 < ma50 && (!ma200 || ma50 < ma200)) trend = 'Bearish'
  return {
    lastPrice: last?.price || 0,
    ma20,
    ma50,
    ma200,
    rsi,
    volatilityPct,
    structure,
    trend,
  }
}

function detectMarketStructure(points) {
  if (points.length < 22) return 'Building'
  const last = points.at(-1)
  const lookback = points.slice(-21, -1)
  const high = Math.max(...lookback.map((item) => item.high))
  const low = Math.min(...lookback.map((item) => item.low))
  if (last.close > high) return 'Breakout'
  if (last.close < low) return 'Breakdown'
  return 'Range'
}

function calculateRsi(points, windowSize) {
  if (points.length <= windowSize) return null
  const slice = points.slice(-windowSize - 1)
  let gains = 0
  let losses = 0
  for (let index = 1; index < slice.length; index += 1) {
    const change = slice[index].price - slice[index - 1].price
    if (change >= 0) gains += change
    else losses += Math.abs(change)
  }
  const averageGain = gains / windowSize
  const averageLoss = losses / windowSize
  if (averageLoss === 0) return 100
  const rs = averageGain / averageLoss
  return 100 - 100 / (1 + rs)
}

function calculateVolatility(points, windowSize) {
  if (points.length <= windowSize) return 0
  const returns = points.slice(-windowSize).map((item, index, slice) => {
    if (index === 0) return 0
    return (item.price - slice[index - 1].price) / slice[index - 1].price
  }).slice(1)
  const mean = returns.reduce((sum, item) => sum + item, 0) / returns.length
  const variance = returns.reduce((sum, item) => sum + (item - mean) ** 2, 0) / returns.length
  const periodsPerYear = inferPeriodsPerYear(points)
  return Math.sqrt(variance) * Math.sqrt(periodsPerYear) * 100
}

function adaptBackendBacktestResult(payload) {
  const engine = findEngineResult(payload)
  const metrics = engine.metrics || {}
  const rawSeries = engine.series || {}
  const portfolioSeries = normalizeBackendSeries(rawSeries.portfolio)
  const benchmarkSeries = normalizeBackendSeries(rawSeries.benchmark)
  const drawdownSeries = normalizeBackendSeries(rawSeries.drawdown_pct)
  const finalEquity = portfolioSeries.at(-1)?.value || Number(metrics.final_value || metrics.ending_value || 0)
  const strategyMetrics = engine.strategy?.metrics || {}
  return {
    metrics: {
      finalEquity,
      totalReturnPct: Number(metrics.total_return_pct || 0),
      maxDrawdownPct: Number(metrics.max_drawdown_pct || 0),
      trades: Number(strategyMetrics.trade_count || metrics.trade_count || metrics.trading_days || portfolioSeries.length || 0),
      winRatePct: Number(metrics.win_rate_pct || strategyMetrics.win_rate_pct || 0),
      sharpe: numericOrNull(metrics.sharpe || metrics.sharpe_ratio),
      volatilityAnnualPct: numericOrNull(metrics.volatility_annual_pct),
    },
    trades: buildTradeRows(engine),
    equityCurve: portfolioSeries,
    series: {
      portfolio: portfolioSeries,
      benchmark: benchmarkSeries,
      drawdown: drawdownSeries,
    },
    monthlyReturns: engine.monthly_returns || [],
    caveats: payload.caveats || [],
    meta: {
      interval: engine.interval || payload.engine_result?.interval || '',
      source: engine.source || payload.engine_result?.source || '',
      range: `${engine.start_date || '--'} -> ${engine.end_date || '--'}`,
      benchmarkLabel: engine.benchmark_label || '',
      cost: engine.execution_costs
        ? `${Number(engine.execution_costs.commission_pct || 0).toFixed(2)}% commission, ${Number(engine.execution_costs.slippage_pct || 0).toFixed(2)}% slippage`
        : '',
    },
  }
}

function normalizeBackendSeries(series) {
  if (!Array.isArray(series)) return []
  return series
    .map((item) => ({
      time: normalizeChartTime(item.time),
      value: Number(item.value),
    }))
    .filter((item) => item.time && Number.isFinite(item.value))
}

function normalizeChartTime(value) {
  if (typeof value === 'number') return value
  if (!value) return null
  const parsed = Date.parse(String(value))
  if (!Number.isFinite(parsed)) return String(value).slice(0, 10)
  return Math.floor(parsed / 1000)
}

function numericOrNull(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function findEngineResult(payload) {
  const sectionPayload = payload?.notebook_sections?.find((section) => section.engine_result)?.engine_result
  return payload?.engine_result || payload?.output_payload?.engine_result || sectionPayload || {}
}

function buildTradeRows(engine) {
  const strategyTrades = engine.strategy?.trades
  if (Array.isArray(strategyTrades) && strategyTrades.length) {
    return strategyTrades.map((trade) => ({
      side: trade.exit_reason === 'stop_loss' ? 'STOP' : 'TRADE',
      date: trade.exit_date || trade.entry_date || '--',
      price: trade.exit_price || trade.entry_price || 0,
    }))
  }
  const portfolio = engine.series?.portfolio || []
  if (!portfolio.length) return []
  return [
    { side: 'START', date: formatSeriesTime(portfolio[0].time), price: portfolio[0].value },
    { side: 'END', date: formatSeriesTime(portfolio.at(-1).time), price: portfolio.at(-1).value },
  ]
}

function resolveStartDate(points, period) {
  if (points[0]?.date) return normalizeDateOnly(points[0].date)
  const end = new Date(resolveEndDate(points))
  const months = period === '3mo' ? 3 : period === '6mo' ? 6 : period === '2y' ? 24 : 12
  end.setMonth(end.getMonth() - months)
  return end.toISOString().slice(0, 10)
}

function resolveEndDate(points) {
  const last = points.at(-1)?.date
  return last ? normalizeDateOnly(last) : new Date().toISOString().slice(0, 10)
}

function formatSeriesTime(unixSeconds) {
  if (!unixSeconds) return '--'
  const value = new Date(Number(unixSeconds) * 1000).toISOString()
  return value.includes('T') ? value.slice(0, 16).replace('T', ' ') : value.slice(0, 10)
}

function movingAverage(points, index, windowSize) {
  if (index < windowSize - 1) return null
  const slice = points.slice(index - windowSize + 1, index + 1)
  return slice.reduce((sum, item) => sum + item.price, 0) / windowSize
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })
}

function formatMetric(value) {
  return value === null || value === undefined ? '--' : Number(value).toFixed(2)
}

function formatPercentMetric(value) {
  return value === null || value === undefined ? '--' : `${Number(value).toFixed(2)}%`
}

function resolveHistoryInterval(timeframe) {
  return TIMEFRAME_PRESETS.some((item) => item.value === timeframe) ? timeframe : '1d'
}

function periodOptionsFor(timeframe) {
  if (timeframe === '1m') return ['1d', '5d']
  if (['5m', '15m', '30m'].includes(timeframe)) return ['1d', '5d', '1mo']
  if (['1h', '4h'].includes(timeframe)) return ['5d', '1mo', '3mo', '6mo', '1y']
  if (timeframe === '1d') return ['1mo', '3mo', '6mo', '1y', '2y', '5y']
  if (timeframe === '1wk') return ['6mo', '1y', '2y', '5y', '10y']
  if (timeframe === '1mo') return ['1y', '2y', '5y', '10y', 'max']
  if (timeframe === '1y') return ['5y', '10y', 'max']
  return ['3mo', '6mo', '1y', '2y']
}

function normalizeDateOnly(value) {
  const text = String(value || '')
  return text.includes('T') ? text.slice(0, 10) : text
}

function inferPeriodsPerYear(points) {
  if (points.length < 2) return 252
  const first = Date.parse(points[0].date || points[0].time || '')
  const second = Date.parse(points[1].date || points[1].time || '')
  const diffMs = Math.abs(second - first)
  if (!Number.isFinite(diffMs) || diffMs <= 0) return 252
  const hourMs = 60 * 60 * 1000
  if (diffMs <= 2 * 60 * 1000) return 365 * 24 * 60
  if (diffMs <= 7 * 60 * 1000) return 365 * 24 * 12
  if (diffMs <= 20 * 60 * 1000) return 365 * 24 * 4
  if (diffMs <= 45 * 60 * 1000) return 365 * 24 * 2
  if (diffMs <= 90 * 60 * 1000) return 252 * 6
  if (diffMs <= 4.5 * hourMs) return 252 * 2
  if (diffMs >= 330 * 24 * hourMs) return 1
  if (diffMs >= 26 * 24 * hourMs) return 12
  if (diffMs >= 5 * 24 * hourMs) return 52
  return 252
}
