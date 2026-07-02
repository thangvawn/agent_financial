import { useState, useMemo } from 'react'
import { formatCompactNumber, formatPercent, formatMaybeNumber, formatSignedPercent, growthPercent, formatRatioPercent } from './BctcTables'
import BctcUploadPanel from './BctcUploadPanel'

function firstNumber(...args) {
  for (const val of args) {
    if (val !== null && val !== undefined && val !== '') {
      const num = Number(val)
      if (Number.isFinite(num)) return num
    }
  }
  return null
}

function ratioPercent(value, total) {
  const numeric = Math.abs(Number(value))
  const denominator = Math.abs(Number(total))
  if (!Number.isFinite(numeric) || !Number.isFinite(denominator) || denominator <= 0) return 0
  return Math.max(4, Math.min(100, (numeric / denominator) * 100))
}

function scoreLabel(tone) {
  if (tone === 'good') return 'Tốt'
  if (tone === 'warn') return 'Cảnh báo'
  return 'Trung bình'
}

function sanitizeScore(value) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? Math.max(10, Math.min(100, numeric)) : 50
}

function shortPeriodLabel(label) {
  return String(label || '')
    .replace(/^20(\d{2}) Q/i, 'Q')
    .replace(/^20(\d{2})$/, "'$1")
}

function chartNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

function roundSvg(val) {
  return Math.round(val * 10) / 10
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

export function MetricTrendChart({ rows, metrics, formatValue, height = 288, showEndpointLabels = false }) {
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
    return <p className="text-xs text-slate-400 italic py-4">Chưa đủ dữ liệu để vẽ chart cho chế độ này.</p>
  }

  return (
    <div className="flex flex-col gap-3" onMouseLeave={() => setActiveIndex(fallbackIndex)}>
      <div className="flex flex-wrap gap-3.5 text-[11px] font-semibold text-slate-550 dark:text-zinc-400">
        {metrics.map((metric) => (
          <span key={metric.key} className="flex items-center gap-1.5">
            <i className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: metric.color }} />
            {metric.label}
          </span>
        ))}
      </div>
      <svg
        className="w-full h-auto bg-slate-50 dark:bg-zinc-950/40 rounded-xl border border-slate-200 dark:border-zinc-800"
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
            <line x1={chart.left} x2={chart.right} y1={line.y} y2={line.y} className="stroke-slate-200 dark:stroke-zinc-800/80 stroke-1" />
            <text x={chart.left - 10} y={line.y + 4} textAnchor="end" className="fill-slate-550 dark:fill-zinc-400 text-[10px] font-semibold">{line.leftLabel}</text>
            {chart.hasRightScale && <text x={chart.right + 10} y={line.y + 4} className="fill-slate-550 dark:fill-zinc-400 text-[10px] font-semibold">{line.rightLabel}</text>}
          </g>
        ))}
        <line x1={chart.left} x2={chart.right} y1={chart.bottom} y2={chart.bottom} className="stroke-slate-300 dark:stroke-zinc-700 stroke-1" />
        {chart.barShapes.map((bar) => (
          <rect
            key={`${bar.key}-${bar.index}`}
            x={bar.x}
            y={bar.y}
            width={bar.width}
            height={bar.height}
            rx="3"
            className="transition-opacity duration-150"
            fill={bar.key === 'net_income' ? 'url(#bctcBarIncome)' : 'url(#bctcBarRevenue)'}
          />
        ))}
        {chart.lines.map((line) => (
          <g key={line.key} filter="url(#bctcLineGlow)">
            <polyline points={line.points} fill="none" stroke={line.color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            {line.nodes.map((node) => (
              <circle key={`${line.key}-${node.index}`} cx={node.x} cy={node.y} r={node.index === activeIndex ? 5 : 3.5} fill="#ffffff" stroke={line.color} strokeWidth="2.5" />
            ))}
          </g>
        ))}
        {chart.xLabels.map((label) => (
          <text key={`${label.text}-${label.x}`} x={label.x} y={chart.height - 12} textAnchor="middle" className="fill-slate-500 dark:fill-zinc-450 text-[10px] font-bold">
            {label.text}
          </text>
        ))}
        {chart.xByIndex[activeIndex] && (
          <line x1={chart.xByIndex[activeIndex]} x2={chart.xByIndex[activeIndex]} y1={chart.top} y2={chart.bottom} className="stroke-teal-500/30 stroke-1 stroke-dasharray-[4_4]" />
        )}
      </svg>
      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200 dark:border-zinc-800 text-xs">
        {activePoint ? (
          <div className="flex flex-col gap-1.5">
            <strong className="font-bold text-slate-805 dark:text-white">{activePoint.label}</strong>
            <div className="flex flex-wrap gap-4 text-slate-655 dark:text-zinc-350">
              {metrics.map((item) => (
                <span key={item.key}>
                  {item.label}: <strong className="font-semibold text-slate-900 dark:text-white">{(item.formatValue || formatValue)(activePoint[item.key])}</strong>
                </span>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-slate-400 italic">Di chuột lên chart để xem chi tiết kỳ.</p>
        )}
      </div>
    </div>
  )
}

export function HealthScoreGauge({ score, tone }) {
  return (
    <div className="relative w-32 h-32 rounded-full flex flex-col items-center justify-center border-8 border-slate-100 dark:border-zinc-850 shrink-0">
      <div className="absolute inset-0 rounded-full border-8 border-teal-500 border-t-transparent animate-pulse" style={{ clipPath: `polygon(50% 50%, -50% -50%, 150% -50%)` }} />
      <strong className="text-3xl font-extrabold text-slate-900 dark:text-white leading-none">{score}</strong>
      <span className="text-[10px] text-slate-500 mt-1 uppercase tracking-wider font-bold">/ 100</span>
      <em className={`text-[10px] font-bold uppercase tracking-wide mt-2 ${
        tone === 'good' ? 'text-emerald-500' :
        tone === 'warn' ? 'text-red-500' : 'text-amber-500'
      }`}>{scoreLabel(tone)}</em>
    </div>
  )
}

export function HealthRadar({ rows }) {
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
    <svg className="w-36 h-36 border border-slate-200 dark:border-zinc-800 rounded-xl bg-slate-50 dark:bg-zinc-950/20" viewBox="0 0 144 144" aria-hidden="true">
      {rings.map((ring, idx) => <polygon key={idx} points={ring} className="fill-none stroke-slate-200 dark:stroke-zinc-800/60 stroke-1" />)}
      {points.map((point) => (
        <g key={point.label}>
          <line x1={center} y1={center} x2={point.axisX} y2={point.axisY} className="stroke-slate-200 dark:stroke-zinc-800/60 stroke-1" />
          <circle cx={point.x} cy={point.y} r="3" className="fill-teal-500 stroke-white dark:stroke-zinc-900 stroke-1" />
        </g>
      ))}
      <polygon points={polygon} className="fill-teal-500/10 stroke-teal-500 stroke-2" />
    </svg>
  )
}

export function BalanceSheetSummaryCard({ data, fallbackItems, fallbackTotal }) {
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
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200 dark:border-zinc-850">
        <div className="flex flex-col shrink-0">
          <span className="text-[10px] text-slate-455 font-bold uppercase tracking-wider">Nợ / nguồn vốn</span>
          <strong className="text-lg font-extrabold text-slate-900 dark:text-white mt-1">{formatRatioPercent(liabilityRatio)}</strong>
        </div>
        <div className="flex-1 grid grid-cols-3 gap-3 text-xs border-l border-slate-200 dark:border-zinc-800 pl-4 font-semibold text-slate-655 dark:text-zinc-350">
          <div>
            <span className="block text-[9px] text-slate-450 uppercase">Tổng tài sản</span>
            <strong className="block text-slate-900 dark:text-white mt-0.5">{formatCompactNumber(totalAssets)}</strong>
          </div>
          <div>
            <span className="block text-[9px] text-slate-450 uppercase">Vốn chủ</span>
            <strong className="block text-slate-900 dark:text-white mt-0.5">{formatCompactNumber(equity)}</strong>
          </div>
          <div>
            <span className="block text-[9px] text-slate-450 uppercase">Tiền mặt</span>
            <strong className="block text-slate-900 dark:text-white mt-0.5">{formatCompactNumber(cash)}</strong>
          </div>
        </div>
      </div>
      {estimatedCount > 0 && <em className="text-[10px] text-amber-600 dark:text-amber-450">{estimatedCount} trường dữ liệu đang được ước tính.</em>}
    </div>
  )
}

export function CashFlowQuality({ data }) {
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
    <div className="flex flex-col gap-4">
      <div className="flex justify-between items-end gap-2 h-32 border-b border-slate-200 dark:border-zinc-800 pb-2">
        {bars.map((item) => (
          <div key={item.label} className="flex-1 flex flex-col items-center gap-1.5">
            <i className={`w-6 rounded-sm ${
              item.tone === 'good' ? 'bg-emerald-500' :
              item.tone === 'warn' ? 'bg-red-500' : 'bg-amber-500'
            } ${Number(item.value) < 0 ? 'brightness-75' : ''}`} style={{ height: `${Math.max(10, (Math.abs(Number(item.value) || 0) / maxValue) * 100)}%` }} />
            <strong className="text-[10px] font-bold text-slate-805 dark:text-white">{formatCompactNumber(item.value)}</strong>
            <span className="text-[10px] text-slate-500 dark:text-zinc-450 font-bold">{item.label}</span>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-150 dark:border-zinc-850 text-xs">
        <div className="flex flex-col">
          <span className="text-[9px] text-slate-450 uppercase font-bold">CFO / LNST</span>
          <strong className="text-sm font-extrabold text-slate-900 dark:text-white mt-0.5">{formatMaybeNumber(firstNumber(latest.cfo_to_net_income, data.cfoToNetIncome))}x</strong>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
          Number(data.cfoToNetIncome) >= 1 ? 'bg-emerald-50 border-emerald-100 text-emerald-600' : 'bg-amber-50 border-amber-100 text-amber-600'
        }`}>{latest.quality_label || (Number(data.cfoToNetIncome) >= 1 ? 'Tốt' : 'Cần kiểm tra')}</span>
      </div>
    </div>
  )
}

export function MarginAnalysisDetails({ data }) {
  if (!data) return null
  const latest = data.latest || {}
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-4 gap-2 text-center text-xs">
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-zinc-950/20 border border-slate-200/50">
          <span className="block text-[9px] text-slate-450 uppercase">Gross</span>
          <strong className="block text-slate-900 dark:text-white font-bold mt-0.5">{formatPercent(latest.gross_margin_pct)}</strong>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-zinc-950/20 border border-slate-200/50">
          <span className="block text-[9px] text-slate-450 uppercase">Operating</span>
          <strong className="block text-slate-900 dark:text-white font-bold mt-0.5">{formatPercent(latest.operating_margin_pct)}</strong>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-zinc-950/20 border border-slate-200/50">
          <span className="block text-[9px] text-slate-450 uppercase">EBIT</span>
          <strong className="block text-slate-900 dark:text-white font-bold mt-0.5">{formatPercent(latest.ebit_margin_pct)}</strong>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-zinc-950/20 border border-slate-200/50">
          <span className="block text-[9px] text-slate-450 uppercase">Net</span>
          <strong className="block text-slate-900 dark:text-white font-bold mt-0.5">{formatPercent(latest.net_margin_pct)}</strong>
        </div>
      </div>
      {data.interpretation && <p className="text-xs text-slate-500 leading-relaxed">{data.interpretation}</p>}
    </div>
  )
}
