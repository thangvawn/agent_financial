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

import { fetchInstrumentHistory } from '../../modules/data-hub'

const DEFAULT_STRATEGY = `Strategy idea:
- Buy when price closes above 20-day moving average.
- Exit when price closes below 20-day moving average.
- Risk rule: no leverage, paper mode only.`

const DEFAULT_FORM = {
  symbol: 'BTC',
  period: '1y',
  initialCapital: 100000,
  commissionPct: 0.1,
  slippagePct: 0.05,
  strategyText: DEFAULT_STRATEGY,
  chartType: 'candles',
  showMa20: true,
  showMa50: true,
  showEquity: true,
}

export default function ProLabBacktestStudioPage({ selectedBlueprintId, workspace, onBack, onOpenBlueprints }) {
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
  const signalSeriesRef = useRef(null)
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
          interval: '1d',
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
  }, [form.symbol, form.period])

  useEffect(() => {
    if (!chartContainerRef.current || chartRef.current) return undefined

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
      height: 620,
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
    const signalSeries = chart.addSeries(HistogramSeries, {
      priceScaleId: 'left',
      lastValueVisible: false,
      priceLineVisible: false,
    })

    chartRef.current = chart
    priceSeriesRef.current = null
    ma20SeriesRef.current = ma20Series
    ma50SeriesRef.current = ma50Series
    signalSeriesRef.current = signalSeries
    equitySeriesRef.current = equitySeries

    const resizeChart = () => {
      if (!chartContainerRef.current || !chartRef.current) return
      chartRef.current.applyOptions({
        width: chartContainerRef.current.clientWidth,
        height: isExpanded ? Math.max(520, window.innerHeight - 260) : 620,
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
      signalSeriesRef.current = null
      equitySeriesRef.current = null
    }
  }, [isExpanded])

  useEffect(() => {
    if (!chartContainerRef.current || !chartRef.current) return
    chartRef.current.applyOptions({
      width: chartContainerRef.current.clientWidth,
      height: isExpanded ? Math.max(520, window.innerHeight - 260) : 620,
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
    signalSeriesRef.current?.setData(
      visiblePoints.map((item) => ({
        time: item.time,
        value: item.signal || 0,
        color: item.signal > 0 ? 'rgba(79, 209, 180, 0.45)' : item.signal < 0 ? 'rgba(255, 99, 99, 0.45)' : 'rgba(0,0,0,0)',
      })),
    )
    if (form.showEquity && result?.equityCurve?.length) {
      equitySeriesRef.current?.setData(result.equityCurve.slice(0, visiblePoints.length))
    } else {
      equitySeriesRef.current?.setData([])
    }
    chartRef.current?.timeScale().fitContent()
  }, [visiblePoints, result, form.chartType, form.showMa20, form.showMa50, form.showEquity])

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
    setForm((current) => ({ ...current, [key]: value }))
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

  function runBacktest() {
    if (points.length < 40) {
      setError('Cần ít nhất khoảng 40 điểm dữ liệu để chạy backtest sandbox.')
      return
    }
    setError('')
    const output = simulateMovingAverageStrategy(points, {
      initialCapital: Number(form.initialCapital || 100000),
      commissionPct: Number(form.commissionPct || 0),
      slippagePct: Number(form.slippagePct || 0),
    })
    setResult(output)
    setReplayIndex(points.length)
  }

  return (
    <section className={isExpanded ? 'pro-lab-section backtest-studio backtest-studio--expanded' : 'pro-lab-section backtest-studio'}>
      <section className="backtest-studio__hero">
        <div>
          <p className="pro-lab-eyebrow">TradingView-style Sandbox</p>
          <h2>Backtest Studio</h2>
          <p>
            Replay biểu đồ lịch sử, nhập chiến lược bằng ngôn ngữ tự nhiên, tạo LLM draft và chạy sandbox backtest.
            MVP hiện dùng moving-average parser đơn giản, chưa phải engine execution thật.
          </p>
        </div>
        <div className="pro-lab-badges">
          {onBack ? <button type="button" onClick={onBack}>Về Pro Lab</button> : null}
          <span className="pro-lab-badge pro-lab-badge--warn">Paper only</span>
          <span className="pro-lab-badge">Not investment advice</span>
          <span className="pro-lab-badge">{selectedBlueprint ? selectedBlueprint.name : 'No blueprint selected'}</span>
          <button type="button" onClick={() => setIsExpanded((current) => !current)}>
            {isExpanded ? 'Compact' : 'Full screen'}
          </button>
        </div>
      </section>

      <div className="backtest-studio__full-layout">
        <main className="backtest-studio__chart-shell backtest-studio__chart-shell--full">
          <div className="backtest-studio__chart-head">
            <div>
              <p className="pro-lab-eyebrow">Historical Replay</p>
              <h3>{history?.symbol || form.symbol.toUpperCase()} · {history?.name || 'History feed'}</h3>
            </div>
            <div className="backtest-studio__toolbar">
              <select value={form.chartType} onChange={(event) => updateForm('chartType', event.target.value)}>
                <option value="candles">Candles</option>
                <option value="bars">Bars</option>
                <option value="line">Line</option>
                <option value="area">Area</option>
                <option value="baseline">Baseline</option>
              </select>
              <label><input type="checkbox" checked={form.showMa20} onChange={(event) => updateForm('showMa20', event.target.checked)} /> MA20</label>
              <label><input type="checkbox" checked={form.showMa50} onChange={(event) => updateForm('showMa50', event.target.checked)} /> MA50</label>
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
            <span>{history?.freshness || 'degraded'} · {history?.source || 'data-hub'}</span>
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
                  {['3mo', '6mo', '1y', '2y'].map((item) => <option key={item} value={item}>{item}</option>)}
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
              <button type="button" onClick={runBacktest} disabled={loading || !points.length}>Run backtest</button>
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
              </div>
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
            <p>Chưa chạy backtest. Nhập chiến lược hoặc dùng LLM draft rồi bấm Run backtest.</p>
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
        time: date,
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

function buildTechnicalSnapshot(points) {
  const last = points[points.length - 1]
  const ma20 = points.length ? movingAverage(points, points.length - 1, 20) : null
  const ma50 = points.length ? movingAverage(points, points.length - 1, 50) : null
  const rsi = calculateRsi(points, 14)
  const volatilityPct = calculateVolatility(points, 20)
  let trend = 'Neutral'
  if (ma20 && ma50 && last?.price > ma20 && ma20 > ma50) trend = 'Bullish'
  if (ma20 && ma50 && last?.price < ma20 && ma20 < ma50) trend = 'Bearish'
  return {
    lastPrice: last?.price || 0,
    ma20,
    ma50,
    rsi,
    volatilityPct,
    trend,
  }
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
  return Math.sqrt(variance) * Math.sqrt(252) * 100
}

function simulateMovingAverageStrategy(points, config) {
  const initialCapital = config.initialCapital
  let cash = initialCapital
  let units = 0
  let inPosition = false
  let entryPrice = 0
  let winningTrades = 0
  const trades = []
  const equityCurve = []
  const enriched = points.map((item, index) => {
    const ma20 = movingAverage(points, index, 20)
    const ma50 = movingAverage(points, index, 50)
    return { ...item, ma20, ma50, signal: 0 }
  })

  for (let index = 1; index < enriched.length; index += 1) {
    const previous = enriched[index - 1]
    const current = enriched[index]
    const canUseCross = previous.ma20 && previous.ma50 && current.ma20 && current.ma50
    const buy = canUseCross && previous.ma20 <= previous.ma50 && current.ma20 > current.ma50
    const sell = canUseCross && previous.ma20 >= previous.ma50 && current.ma20 < current.ma50
    const costRate = (config.commissionPct + config.slippagePct) / 100

    if (buy && !inPosition) {
      const executionPrice = current.price * (1 + costRate)
      units = cash / executionPrice
      cash = 0
      inPosition = true
      entryPrice = executionPrice
      current.signal = 1
      trades.push({ side: 'BUY', date: current.date, price: executionPrice })
    } else if (sell && inPosition) {
      const executionPrice = current.price * (1 - costRate)
      cash = units * executionPrice
      units = 0
      inPosition = false
      current.signal = -1
      if (executionPrice > entryPrice) winningTrades += 1
      trades.push({ side: 'SELL', date: current.date, price: executionPrice })
    }

    const equity = cash + units * current.price
    equityCurve.push({ time: current.time, value: equity })
  }

  const lastPrice = enriched[enriched.length - 1].price
  const finalEquity = cash + units * lastPrice
  const totalReturnPct = ((finalEquity - initialCapital) / initialCapital) * 100
  const maxDrawdownPct = calculateMaxDrawdown(equityCurve.map((item) => item.value))
  const sellTrades = trades.filter((item) => item.side === 'SELL').length

  return {
    metrics: {
      finalEquity,
      totalReturnPct,
      maxDrawdownPct,
      trades: trades.length,
      winRatePct: sellTrades ? (winningTrades / sellTrades) * 100 : 0,
    },
    trades,
    equityCurve,
    caveats: [
      'MVP strategy parser đang dùng MA20/MA50 cross mặc định, chưa parse đầy đủ mọi prompt.',
      'Kết quả là paper sandbox, không phải tín hiệu mua/bán hoặc khuyến nghị cá nhân hóa.',
      'Chưa mô phỏng đầy đủ thanh khoản, thuế, partial fills, corporate actions hoặc survivorship bias.',
    ],
  }
}

function movingAverage(points, index, windowSize) {
  if (index < windowSize - 1) return null
  const slice = points.slice(index - windowSize + 1, index + 1)
  return slice.reduce((sum, item) => sum + item.price, 0) / windowSize
}

function calculateMaxDrawdown(values) {
  let peak = values[0] || 0
  let maxDrawdown = 0
  for (const value of values) {
    peak = Math.max(peak, value)
    if (peak > 0) {
      maxDrawdown = Math.min(maxDrawdown, ((value - peak) / peak) * 100)
    }
  }
  return maxDrawdown
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })
}
