import { useEffect, useMemo, useRef, useState } from 'react'
import {
  AreaSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  createChart,
} from 'lightweight-charts'

import { fetchMarketOverviewCrossAsset, fetchMarketOverviewHistory } from '../../modules/home-onboarding'
import { trackAnalyticsEvent } from '../../shared/analytics/trackEvent'

const TIMEFRAMES = [
  ['1m', '1M'],
  ['3m', '3M'],
  ['all', 'Toàn bộ'],
]

const shellClass = 'flex flex-col gap-4'
const heroClass = 'grid gap-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-5 xl:grid-cols-[1.3fr_1fr]'
const cardClass = 'rounded-2xl border border-slate-200 bg-white p-4'
const sectionClass = 'rounded-2xl border border-slate-200 bg-slate-50/80 p-4'
const buttonPrimaryClass = 'inline-flex items-center rounded-full bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-55'
const buttonSecondaryClass = 'inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100'

export default function MarketOverviewPage({
  sessionId,
  embedded = false,
  minimal = false,
  hasInteracted: externalHasInteracted = false,
  onInteracted,
  onContinue,
  onResetOnboarding,
}) {
  const [historyData, setHistoryData] = useState([])
  const [crossAsset, setCrossAsset] = useState(null)
  const [activeTimeframe, setActiveTimeframe] = useState('3m')
  const [activeAssetId, setActiveAssetId] = useState('gold')
  const [localHasInteracted, setLocalHasInteracted] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const mainChartContainerRef = useRef(null)
  const mainChartRef = useRef(null)
  const mainLineSeriesRef = useRef(null)
  const mainRiskSeriesRef = useRef(null)
  const crossChartContainerRef = useRef(null)
  const crossChartRef = useRef(null)
  const crossSeriesRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError('')
      try {
        const [historyPayload, crossAssetPayload] = await Promise.all([
          fetchMarketOverviewHistory(),
          fetchMarketOverviewCrossAsset(180),
        ])
        if (cancelled) return
        setHistoryData(
          (historyPayload.data || [])
            .map(normalizeHistoryItem)
            .filter((item) => Number.isFinite(item.time) && Number.isFinite(item.value))
            .sort((left, right) => left.time - right.time),
        )
        setCrossAsset(crossAssetPayload)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Không tải được market overview.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  const filteredHistory = useMemo(() => applyTimeframe(historyData, activeTimeframe), [historyData, activeTimeframe])
  const activeAsset = useMemo(() => {
    const assets = crossAsset?.assets || []
    return assets.find((asset) => asset.id === activeAssetId) || assets[0] || null
  }, [activeAssetId, crossAsset])
  const hasInteracted = embedded ? externalHasInteracted : localHasInteracted

  useEffect(() => {
    if (!mainChartContainerRef.current || mainChartRef.current) return undefined

    const chart = createChart(mainChartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#254640',
      },
      grid: {
        vertLines: { color: 'rgba(37, 70, 64, 0.06)' },
        horzLines: { color: 'rgba(37, 70, 64, 0.06)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(37, 70, 64, 0.14)',
      },
      leftPriceScale: {
        visible: false,
        scaleMargins: { top: 0.76, bottom: 0.05 },
      },
      timeScale: {
        borderColor: 'rgba(37, 70, 64, 0.14)',
        timeVisible: true,
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      width: mainChartContainerRef.current.clientWidth,
      height: 340,
    })

    const lineSeries = chart.addSeries(LineSeries, {
      color: '#1f6b5f',
      lineWidth: 3,
      lastValueVisible: true,
      priceLineVisible: false,
    })

    const riskSeries = chart.addSeries(HistogramSeries, {
      priceScaleId: 'left',
      lastValueVisible: false,
      priceLineVisible: false,
    })

    mainChartRef.current = chart
    mainLineSeriesRef.current = lineSeries
    mainRiskSeriesRef.current = riskSeries

    const resizeChart = () => {
      if (!mainChartContainerRef.current || !mainChartRef.current) return
      mainChartRef.current.applyOptions({
        width: mainChartContainerRef.current.clientWidth,
        height: 340,
      })
    }

    window.addEventListener('resize', resizeChart)
    return () => {
      window.removeEventListener('resize', resizeChart)
      chart.remove()
      mainChartRef.current = null
      mainLineSeriesRef.current = null
      mainRiskSeriesRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!mainLineSeriesRef.current || !mainRiskSeriesRef.current) return
    mainLineSeriesRef.current.setData(filteredHistory.map((item) => ({ time: item.time, value: item.value })))
    mainRiskSeriesRef.current.setData(
      filteredHistory.map((item) => ({
        time: item.time,
        value: item.risk_score,
        color: chartColorForRisk(item.risk_score),
      })),
    )
    mainChartRef.current?.timeScale().fitContent()
  }, [filteredHistory])

  useEffect(() => {
    if (!crossChartContainerRef.current || crossChartRef.current) return undefined

    const chart = createChart(crossChartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#254640',
      },
      grid: {
        vertLines: { color: 'rgba(37, 70, 64, 0.05)' },
        horzLines: { color: 'rgba(37, 70, 64, 0.05)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(37, 70, 64, 0.14)',
      },
      timeScale: {
        borderColor: 'rgba(37, 70, 64, 0.14)',
        timeVisible: true,
      },
      width: crossChartContainerRef.current.clientWidth,
      height: 260,
    })

    const series = chart.addSeries(AreaSeries, {
      lineColor: '#c9773f',
      topColor: 'rgba(201, 119, 63, 0.28)',
      bottomColor: 'rgba(201, 119, 63, 0.02)',
      priceLineVisible: false,
    })

    crossChartRef.current = chart
    crossSeriesRef.current = series

    const resizeChart = () => {
      if (!crossChartContainerRef.current || !crossChartRef.current) return
      crossChartRef.current.applyOptions({
        width: crossChartContainerRef.current.clientWidth,
        height: 260,
      })
    }

    window.addEventListener('resize', resizeChart)
    return () => {
      window.removeEventListener('resize', resizeChart)
      chart.remove()
      crossChartRef.current = null
      crossSeriesRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!crossSeriesRef.current || !activeAsset?.bars?.length) return
    crossSeriesRef.current.setData(activeAsset.bars)
    crossChartRef.current?.timeScale().fitContent()
  }, [activeAsset])

  function registerInteraction(kind, value) {
    if (!embedded) setLocalHasInteracted(true)
    if (embedded && !externalHasInteracted) onInteracted?.()
    trackAnalyticsEvent({
      event_name: 'market_overview_interacted',
      module: 'home_onboarding',
      surface: embedded ? 'home_market_overview' : 'market_overview',
      session_id: sessionId,
      properties: { interaction_kind: kind, interaction_value: value },
    })
  }

  function handleContinue() {
    trackAnalyticsEvent({
      event_name: 'market_overview_completed',
      module: 'home_onboarding',
      surface: 'market_overview',
      session_id: sessionId,
      properties: {
        timeframe: activeTimeframe,
        cross_asset_id: activeAsset?.id || '',
        interacted: hasInteracted,
      },
    })
    onContinue?.()
  }

  return (
    <section className={shellClass}>
      {!minimal ? (
      <div className={heroClass}>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700">{embedded ? 'Market context' : 'Bối cảnh trước khi lập kế hoạch'}</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">
            {embedded ? 'Đọc thị trường bằng biểu đồ tương tác' : 'Đọc nhịp thị trường bằng biểu đồ tương tác'}
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Trước khi đi sâu vào Health, Goals hay Guided Investing, hãy nhìn bối cảnh vận động thật của thị trường.
            Cách này giúp các phần kế hoạch không bị tách rời khỏi dữ liệu nền.
          </p>
        </div>
        <aside className={cardClass}>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Experience path</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Cách đọc an toàn</h2>
          <div className="mt-3 grid gap-2">
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">1. Onboarding</div>
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">2. Market context</div>
            <div className={hasInteracted
              ? 'rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700'
              : 'rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600'}
            >
              {embedded ? '3. Nối với Health và Goals' : '3. Mở Home và các module'}
            </div>
          </div>
          <p className="mt-3 text-xs text-slate-500">
            {hasInteracted
              ? 'Bạn đã tương tác với chart. Có thể đọc tiếp phần giải thích và kế hoạch.'
              : 'Hãy đổi timeframe hoặc xem một cross-asset để có thêm bối cảnh.'}
          </p>
          {!embedded ? (
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" className={buttonPrimaryClass} onClick={handleContinue} disabled={!hasInteracted}>
                Mở Home và các module kế hoạch
              </button>
              {onResetOnboarding ? (
                <button type="button" className={buttonSecondaryClass} onClick={onResetOnboarding}>
                  Sửa lại onboarding
                </button>
              ) : null}
            </div>
          ) : null}
        </aside>
      </div>
      ) : null}

      <section className={sectionClass}>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Interactive chart 01</p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">VN-Index và Risk Score chạy cùng nhau</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {TIMEFRAMES.map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={activeTimeframe === value ? buttonPrimaryClass : buttonSecondaryClass}
                onClick={() => {
                  setActiveTimeframe(value)
                  registerInteraction('timeframe', value)
                }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {loading ? <p className="text-sm text-slate-600">Đang tải chart thị trường...</p> : null}
        {error ? <p className="rounded-xl border border-rose-200 bg-rose-50 p-2 text-sm text-rose-700">{error}</p> : null}

        <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-white p-2" ref={mainChartContainerRef} />

        {filteredHistory.length ? (
          <div className="mt-3 grid gap-2 md:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <span className="text-xs uppercase tracking-wide text-slate-500">Phiên gần nhất</span>
              <strong className="mt-1 block text-base font-semibold text-slate-900">{filteredHistory.at(-1)?.value?.toLocaleString('vi-VN')}</strong>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <span className="text-xs uppercase tracking-wide text-slate-500">Risk score gần nhất</span>
              <strong className="mt-1 block text-base font-semibold text-slate-900">{formatPct(filteredHistory.at(-1)?.risk_score)}</strong>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <span className="text-xs uppercase tracking-wide text-slate-500">Cách đọc</span>
              <strong className="mt-1 block text-base font-semibold text-slate-900">{riskNarrative(filteredHistory.at(-1)?.risk_score)}</strong>
            </div>
          </div>
        ) : null}
      </section>

      <section className={sectionClass}>
        <div className="mb-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Interactive chart 02</p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Cross-asset context để nhìn risk-on / risk-off</h2>
          </div>
        </div>

        <div className="mb-3 flex flex-wrap gap-2">
          {(crossAsset?.assets || []).map((asset) => (
            <button
              key={asset.id}
              type="button"
              className={activeAsset?.id === asset.id ? buttonPrimaryClass : buttonSecondaryClass}
              onClick={() => {
                setActiveAssetId(asset.id)
                registerInteraction('cross_asset', asset.id)
              }}
            >
              {asset.label}
            </button>
          ))}
        </div>

        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white p-2" ref={crossChartContainerRef} />

        {activeAsset ? (
          <div className="mt-3 grid gap-2 md:grid-cols-4">
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <span className="text-xs uppercase tracking-wide text-slate-500">Tài sản</span>
              <strong className="mt-1 block text-base font-semibold text-slate-900">{activeAsset.label}</strong>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <span className="text-xs uppercase tracking-wide text-slate-500">1W</span>
              <strong className="mt-1 block text-base font-semibold text-slate-900">{formatChange(activeAsset.change_1w_pct)}</strong>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <span className="text-xs uppercase tracking-wide text-slate-500">1M</span>
              <strong className="mt-1 block text-base font-semibold text-slate-900">{formatChange(activeAsset.change_1m_pct)}</strong>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <span className="text-xs uppercase tracking-wide text-slate-500">So what</span>
              <strong className="mt-1 block text-base font-semibold text-slate-900">{activeAsset.decision_hint}</strong>
            </div>
          </div>
        ) : null}
      </section>

      {!minimal ? (
      <section className="grid gap-3">
        <div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Kế hoạch tiếp theo</p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Các module nên nối với bối cảnh thị trường</h2>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {[
            ['Financial Health', 'Đặt baseline tài chính cá nhân sau khi đã thấy môi trường chung.'],
            ['Goals', 'Biến mong muốn thành kế hoạch có khoảng cách, không bị tách khỏi bối cảnh thị trường.'],
            ['Learn Hub', 'Học đúng phần đang cần, thay vì đọc lý thuyết rời rạc.'],
            ['Guided Investing', 'Đi vào watchlist, company health, scenario sau khi đã có góc nhìn nền.'],
          ].map(([title, description]) => (
            <article key={title} className={hasInteracted
              ? 'rounded-xl border border-emerald-200 bg-emerald-50 p-4'
              : 'rounded-xl border border-slate-200 bg-slate-100 p-4'}
            >
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{hasInteracted ? 'Sẵn sàng' : 'Nên xem chart trước'}</p>
              <h3 className="mt-1 text-lg font-semibold text-slate-900">{title}</h3>
              <p className="mt-2 text-sm text-slate-600">{description}</p>
            </article>
          ))}
        </div>
      </section>
      ) : null}
    </section>
  )
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

function applyTimeframe(historyData, timeframe) {
  if (!historyData.length || timeframe === 'all') return historyData
  const latest = historyData.at(-1)?.time
  if (!latest) return historyData
  const seconds = timeframe === '1m' ? 30 * 24 * 60 * 60 : 90 * 24 * 60 * 60
  return historyData.filter((item) => item.time >= latest - seconds)
}

function chartColorForRisk(score) {
  if (score > 0.75) return 'rgba(164, 71, 60, 0.72)'
  if (score > 0.55) return 'rgba(201, 119, 63, 0.68)'
  return 'rgba(31, 107, 95, 0.45)'
}

function formatPct(value) {
  if (!Number.isFinite(value)) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function formatChange(value) {
  if (!Number.isFinite(value)) return '--'
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}

function riskNarrative(value) {
  if (!Number.isFinite(value)) return 'Chưa rõ'
  if (value > 0.75) return 'Risk cao'
  if (value > 0.55) return 'Risk nhạy'
  return 'Risk tương đối bình ổn'
}
