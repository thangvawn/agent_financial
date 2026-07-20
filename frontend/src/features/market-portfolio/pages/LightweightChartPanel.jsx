import { useEffect, useRef } from 'react'
import { createChart, AreaSeries, CandlestickSeries, HistogramSeries, LineStyle, CrosshairMode } from 'lightweight-charts'

/**
 * React wrapper around TradingView Lightweight Charts.
 * Supports area/candle modes, dark/light auto from data-theme, wheel zoom,
 * drag pan, double-click reset, crosshair tooltip — TradingView-style interactions.
 *
 * Data shape: points = [{date: ISO string, open?, high?, low?, close?, price?, volume?}, ...]
 */
export default function LightweightChartPanel({ points, mode = 'area', height = 320, ariaLabel = 'Biểu đồ giá theo thời gian' }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRef = useRef(null)
  const volumeSeriesRef = useRef(null)
  const modeRef = useRef(mode)
  const pointsRef = useRef(points)

  const isDark = (() => {
    if (typeof document === 'undefined') return true
    return document.documentElement.dataset.theme === 'dark'
      || document.documentElement.closest('[data-theme="dark"]') != null
      || document.querySelector('[data-theme="dark"]') != null
  })()
  const initialOptionsRef = useRef({ isDark, height })

  useEffect(() => {
    pointsRef.current = points
  }, [points])

  // Build chart on mount; tear down on unmount.
  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, buildChartOptions(initialOptionsRef.current))
    chartRef.current = chart
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })

    const ro = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (!entry || !chart) return
      const { width } = entry.contentRect
      chart.applyOptions({ width: Math.max(280, Math.floor(width)) })
    })
    ro.observe(containerRef.current)

    return () => {
      ro.disconnect()
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
      volumeSeriesRef.current = null
    }
    // We intentionally create the chart ONCE — options updated separately.
  }, [])

  // Apply theme + height changes without recreating the chart.
  useEffect(() => {
    if (!chartRef.current) return
    chartRef.current.applyOptions(buildChartOptions({ isDark, height }))
  }, [isDark, height])

  // (Re)create series whenever mode flips OR shape of data demands it.
  useEffect(() => {
    if (!chartRef.current) return
    const chart = chartRef.current
    // Remove existing series if any
    if (seriesRef.current) {
      try { chart.removeSeries(seriesRef.current) } catch { /* ignore */ }
      seriesRef.current = null
    }
    if (volumeSeriesRef.current) {
      try { chart.removeSeries(volumeSeriesRef.current) } catch { /* ignore */ }
      volumeSeriesRef.current = null
    }
    if (mode === 'candle') {
      seriesRef.current = chart.addSeries(CandlestickSeries, candleSeriesOptions())
    } else {
      seriesRef.current = chart.addSeries(AreaSeries, areaSeriesOptions(isDark))
    }
    volumeSeriesRef.current = chart.addSeries(HistogramSeries, volumeSeriesOptions())
    modeRef.current = mode
    // Push current data right away
    pushData(seriesRef.current, pointsRef.current, mode)
    pushVolumeData(volumeSeriesRef.current, pointsRef.current)
    chart.timeScale().fitContent()
  }, [mode, isDark])

  // Push data updates when points change (mode unchanged).
  useEffect(() => {
    if (!seriesRef.current) return
    pushData(seriesRef.current, points, modeRef.current)
    pushVolumeData(volumeSeriesRef.current, points)
    if (chartRef.current) chartRef.current.timeScale().fitContent()
  }, [points])

  return (
    <div
      ref={containerRef}
      className="gt-lwchart"
      style={{ width: '100%', height: `${height}px` }}
      role="img"
      aria-label={ariaLabel}
    />
  )
}

function pushData(series, points, mode) {
  if (!series || !points || !points.length) return
  if (mode === 'candle') {
    const data = points.map((p) => ({
      time: toTimeValue(p.date),
      open: Number(p.open ?? p.close ?? p.price ?? 0),
      high: Number(p.high ?? p.close ?? p.price ?? 0),
      low: Number(p.low ?? p.close ?? p.price ?? 0),
      close: Number(p.close ?? p.price ?? 0),
    })).filter((d) => Number.isFinite(d.close) && d.time)
    series.setData(dedupeByTime(data))
  } else {
    const data = points.map((p) => ({
      time: toTimeValue(p.date),
      value: Number(p.close ?? p.price ?? 0),
    })).filter((d) => Number.isFinite(d.value) && d.time)
    series.setData(dedupeByTime(data))
  }
}

function pushVolumeData(series, points) {
  if (!series || !points?.length) return
  const data = points.map((p) => ({
    time: toTimeValue(p.date),
    value: Number(p.volume || 0),
    color: Number(p.close ?? p.price ?? 0) >= Number(p.open ?? p.close ?? p.price ?? 0)
      ? 'rgba(34, 197, 94, 0.45)'
      : 'rgba(248, 113, 113, 0.45)',
  })).filter((d) => Number.isFinite(d.value) && d.value > 0 && d.time)
  if (data.length) series.setData(dedupeByTime(data))
}

function dedupeByTime(arr) {
  // lightweight-charts requires strictly ascending unique time values
  const seen = new Set()
  const out = []
  for (const item of arr) {
    const t = item.time
    if (seen.has(t)) continue
    seen.add(t)
    out.push(item)
  }
  out.sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0))
  return out
}

function toTimeValue(iso) {
  if (!iso) return null
  // lightweight-charts expects either Unix timestamp (seconds) for intraday
  // or YYYY-MM-DD string for daily. Use timestamp universally for intraday support.
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return Math.floor(d.getTime() / 1000)
}

function buildChartOptions({ isDark, height }) {
  const palette = themePalette(isDark)
  return {
    height,
    autoSize: true,
    layout: {
      background: { type: 'solid', color: palette.bg },
      textColor: palette.text,
      fontFamily: 'Inter, "SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif',
      fontSize: 11,
      attributionLogo: false,
    },
    grid: {
      vertLines: { color: palette.gridSubtle, style: LineStyle.Dotted },
      horzLines: { color: palette.gridSubtle, style: LineStyle.Dotted },
    },
    rightPriceScale: {
      borderColor: palette.line,
      textColor: palette.textMuted,
      entireTextOnly: true,
    },
    timeScale: {
      borderColor: palette.line,
      timeVisible: true,
      secondsVisible: false,
      rightOffset: 4,
      barSpacing: 6,
    },
    crosshair: {
      mode: CrosshairMode.Magnet,
      vertLine: {
        color: palette.crosshair,
        width: 1,
        style: LineStyle.Dashed,
        labelBackgroundColor: palette.tooltipBg,
      },
      horzLine: {
        color: palette.crosshair,
        width: 1,
        style: LineStyle.Dashed,
        labelBackgroundColor: palette.tooltipBg,
      },
    },
    handleScroll: {
      mouseWheel: true,
      pressedMouseMove: true,
      horzTouchDrag: true,
      vertTouchDrag: false,
    },
    handleScale: {
      mouseWheel: true,
      pinch: true,
      axisPressedMouseMove: { time: true, price: true },
      axisDoubleClickReset: { time: true, price: true },
    },
    kineticScroll: { touch: true, mouse: false },
    localization: {
      locale: 'en-GB',
      priceFormatter: (price) => formatLwPrice(price),
    },
  }
}

function areaSeriesOptions(isDark) {
  const p = themePalette(isDark)
  return {
    lineColor: p.accent,
    topColor: hexWithAlpha(p.accent, 0.28),
    bottomColor: hexWithAlpha(p.accent, 0.0),
    lineWidth: 2,
    priceLineVisible: true,
    priceLineColor: p.accent,
    priceLineStyle: LineStyle.Dashed,
    crosshairMarkerVisible: true,
    crosshairMarkerRadius: 4,
    crosshairMarkerBorderColor: p.bg,
    crosshairMarkerBackgroundColor: p.accent,
    lastValueVisible: true,
  }
}

function candleSeriesOptions() {
  return {
    upColor: '#16a34a',
    downColor: '#dc2626',
    borderUpColor: '#16a34a',
    borderDownColor: '#dc2626',
    wickUpColor: '#16a34a',
    wickDownColor: '#dc2626',
    borderVisible: true,
    priceLineVisible: true,
    priceLineColor: '#71717a',
    priceLineStyle: LineStyle.Dashed,
    lastValueVisible: true,
  }
}

function volumeSeriesOptions() {
  return {
    priceScaleId: 'volume',
    priceFormat: { type: 'volume' },
    lastValueVisible: false,
    priceLineVisible: false,
  }
}

function themePalette(isDark) {
  return isDark
    ? {
        bg: 'transparent',
        text: '#a1a1aa',
        textMuted: '#71717a',
        line: '#27272a',
        gridSubtle: 'rgba(63, 63, 70, 0.4)',
        accent: '#3b82f6',
        crosshair: '#71717a',
        tooltipBg: '#27272a',
      }
    : {
        bg: 'transparent',
        text: '#52525b',
        textMuted: '#71717a',
        line: '#e4e4e7',
        gridSubtle: 'rgba(228, 228, 231, 0.6)',
        accent: '#2563eb',
        crosshair: '#a1a1aa',
        tooltipBg: '#f4f4f5',
      }
}

function hexWithAlpha(hex, alpha) {
  // Accept #rrggbb (light/dark accent) — return rgba string
  const m = /^#([0-9a-fA-F]{6})$/.exec(hex)
  if (!m) return hex
  const r = parseInt(m[1].slice(0, 2), 16)
  const g = parseInt(m[1].slice(2, 4), 16)
  const b = parseInt(m[1].slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function formatLwPrice(value) {
  if (!Number.isFinite(value)) return ''
  if (Math.abs(value) >= 1000) return value.toLocaleString('en-US', { maximumFractionDigits: 2 })
  return value.toLocaleString('en-US', { maximumFractionDigits: 4 })
}
