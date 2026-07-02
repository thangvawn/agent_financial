import { formatCompactNumber, formatPercent, formatMaybeNumber } from './BctcTables'

function firstNumber(...args) {
  for (const val of args) {
    if (val !== null && val !== undefined && val !== '') {
      const num = Number(val)
      if (Number.isFinite(num)) return num
    }
  }
  return null
}

function ratioPct(value, total) {
  const numeric = Number(value)
  const denominator = Number(total)
  if (!Number.isFinite(numeric) || !Number.isFinite(denominator) || denominator <= 0) return 0
  return Math.max(0, Math.min(100, (numeric / denominator) * 100))
}

function shortPeriodLabel(label) {
  return String(label || '')
    .replace(/^20(\d{2}) Q/i, 'Q')
    .replace(/^20(\d{2})$/, "'$1")
}

function roundSvg(val) {
  return Math.round(val * 10) / 10
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

function scoreLabel(tone) {
  if (tone === 'good') return 'Tốt'
  if (tone === 'warn') return 'Cảnh báo'
  return 'Trung bình'
}

export function BalanceAssetStackChart({ rows }) {
  const cleanRows = rows.slice(-5)
  const maxTotal = Math.max(...cleanRows.map((row) => Number(row.totalAssets) || 0), 1)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3.5 text-[11px] font-semibold text-slate-550 dark:text-zinc-400">
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-emerald-500" />Tiền mặt</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-amber-500" />Phải thu</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-orange-500" />Hàng tồn kho</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-teal-650" />Tài sản cố định</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-slate-400" />Tài sản khác</span>
      </div>
      <div className="flex justify-between items-end gap-2 h-44 border-b border-slate-200 dark:border-zinc-800 pb-2">
        {cleanRows.map((row) => {
          const total = Math.max(Number(row.totalAssets) || 0, 1)
          const other = Math.max(0, total - row.cash - row.receivables - row.inventory - row.fixedAssets)
          const height = Math.max(20, (total / maxTotal) * 100)
          return (
            <div key={row.period} className="flex-1 flex flex-col items-center gap-1.5">
              <div className="w-8 rounded flex flex-col-reverse overflow-hidden" style={{ height: `${height * 1.3}px` }}>
                <i className="bg-emerald-505" style={{ height: `${ratioPct(row.cash, total)}%` }} />
                <i className="bg-amber-550" style={{ height: `${ratioPct(row.receivables, total)}%` }} />
                <i className="bg-orange-550" style={{ height: `${ratioPct(row.inventory, total)}%` }} />
                <i className="bg-teal-650" style={{ height: `${ratioPct(row.fixedAssets, total)}%` }} />
                <i className="bg-slate-450" style={{ height: `${Math.max(4, ratioPct(other, total))}%` }} />
              </div>
              <span className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold">{shortPeriodLabel(row.period)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function BalanceFundingDonut({ rows, latest }) {
  const row = rows.at(-1) || {}
  const shortDebt = firstNumber(latest.short_term_debt, row.shortTermDebt, row.totalLiabilities * 0.58)
  const longDebt = firstNumber(latest.long_term_debt, row.longTermDebt, row.totalLiabilities - shortDebt)
  const equity = firstNumber(row.equity, latest.equity)
  const total = Math.max(firstNumber(shortDebt, 0) + firstNumber(longDebt, 0) + firstNumber(equity, 0), 1)
  const shortPct = ratioPct(shortDebt, total)
  const longPct = ratioPct(longDebt, total)
  const equityPct = ratioPct(equity, total)

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6 p-4 bg-slate-50 dark:bg-zinc-950/20 rounded-2xl border border-slate-150 dark:border-zinc-850">
      <div className="relative w-32 h-32 rounded-full flex flex-col items-center justify-center border-8 border-slate-200 dark:border-zinc-800 shrink-0">
        <strong className="text-sm font-extrabold text-slate-900 dark:text-white leading-none">{formatCompactNumber(row.totalAssets)}</strong>
        <span className="text-[9px] text-slate-500 dark:text-zinc-550 mt-1 uppercase tracking-wider font-bold">Tổng tài sản</span>
      </div>
      <div className="flex-1 flex flex-col gap-2.5 text-xs text-slate-655 dark:text-zinc-350 w-full">
        <p className="flex items-center gap-2 font-semibold">
          <i className="w-2.5 h-2.5 rounded-full bg-red-500 shrink-0" />
          <span>Nợ ngắn hạn:</span>
          <strong className="text-slate-900 dark:text-white ml-auto">{formatPercent(shortPct)}</strong>
        </p>
        <p className="flex items-center gap-2 font-semibold">
          <i className="w-2.5 h-2.5 rounded-full bg-orange-505 shrink-0" />
          <span>Nợ dài hạn:</span>
          <strong className="text-slate-900 dark:text-white ml-auto">{formatPercent(longPct)}</strong>
        </p>
        <p className="flex items-center gap-2 font-semibold">
          <i className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
          <span>Vốn chủ sở hữu:</span>
          <strong className="text-slate-900 dark:text-white ml-auto">{formatPercent(equityPct)}</strong>
        </p>
        <em className="text-[10px] text-slate-450 mt-1 block">Tại {row.period || 'kỳ mới nhất'}</em>
      </div>
    </div>
  )
}

export function BalanceLiquidityChart({ rows }) {
  const cleanRows = rows.slice(-6)
  const workingCapitalValues = cleanRows.map((row) => row.workingCapital).filter(Number.isFinite)
  const maxWorking = Math.max(...workingCapitalValues.map(Math.abs), 1)
  const currentPoints = chartPolyline(cleanRows.map((row) => row.currentRatio), 0, 3)
  const quickPoints = chartPolyline(cleanRows.map((row) => row.quickRatio), 0, 3)
  const workingPoints = chartPolyline(cleanRows.map((row) => row.workingCapital / maxWorking), 0, 1)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3.5 text-[11px] font-semibold text-slate-550 dark:text-zinc-400">
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-blue-500" />Vốn lưu động</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-indigo-500" />Current Ratio</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-purple-550" />Quick Ratio</span>
      </div>
      <div className="w-full">
        <svg viewBox="0 0 520 220" className="w-full h-auto bg-slate-50 dark:bg-zinc-950/40 rounded-xl border border-slate-200 dark:border-zinc-800">
          {[40, 80, 120, 160].map((y) => <line key={y} x1="42" x2="500" y1={y} y2={y} className="stroke-slate-200 dark:stroke-zinc-800/80 stroke-1 stroke-dasharray-[4_4]" />)}
          <polyline points={workingPoints} className="fill-none stroke-blue-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          <polyline points={currentPoints} className="fill-none stroke-indigo-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          <polyline points={quickPoints} className="fill-none stroke-purple-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          {cleanRows.map((row, index) => (
            <text key={row.period} x={52 + index * (438 / Math.max(1, cleanRows.length - 1))} y="204" textAnchor="middle" className="fill-slate-500 dark:fill-zinc-400 text-[10px] font-bold">
              {shortPeriodLabel(row.period)}
            </text>
          ))}
        </svg>
      </div>
    </div>
  )
}

export function CashWaterfallChart({ rows }) {
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
    <div className="flex justify-between items-end gap-2 h-48 border-b border-slate-200 dark:border-zinc-800 pb-2.5">
      {steps.map((item) => {
        const height = Math.max(20, (Math.abs(Number(item.value) || 0) / maxAbs) * 130)
        return (
          <div key={item.key} className="flex-1 flex flex-col items-center gap-1.5">
            <strong className="text-[10px] font-bold text-slate-805 dark:text-white truncate max-w-full text-center">{formatCompactNumber(item.value)}</strong>
            <i className={`w-8 rounded-sm ${
              item.tone === 'base' ? 'bg-slate-500' :
              item.tone === 'positive' ? 'bg-emerald-500 shadow-md shadow-emerald-500/10' :
              'bg-red-500 shadow-md shadow-red-500/10'
            }`} style={{ height: `${height}px` }} />
            <span className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold whitespace-nowrap">{item.label}</span>
          </div>
        )
      })}
    </div>
  )
}

export function CashFlowTrendChart({ rows }) {
  const cleanRows = rows.slice(-7)
  const maxAbs = Math.max(...cleanRows.flatMap((row) => [row.cfo, row.cfi, row.cff, row.fcf].map((value) => Math.abs(Number(value) || 0))), 1)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3.5 text-[11px] font-semibold text-slate-550 dark:text-zinc-400">
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-emerald-505" />CFO</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-amber-500" />CFI</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-red-500" />CFF</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-teal-500" />FCF</span>
      </div>
      <div className="flex justify-between items-end gap-4 h-40 border-b border-slate-200 dark:border-zinc-800 pb-2">
        {cleanRows.map((row) => (
          <div key={row.period} className="flex-1 flex flex-col items-center gap-1.5">
            <div className="flex gap-0.5 items-end justify-center h-28 w-full">
              {[
                ['cfo', row.cfo, 'bg-emerald-505'],
                ['cfi', row.cfi, 'bg-amber-500'],
                ['cff', row.cff, 'bg-red-500'],
                ['fcf', row.fcf, 'bg-teal-505'],
              ].map(([key, value, colorClass]) => (
                <i
                  key={key}
                  className={`w-1.5 rounded-sm ${colorClass} ${Number(value) < 0 ? 'brightness-75' : ''}`}
                  style={{ height: `${Math.max(6, (Math.abs(Number(value) || 0) / maxAbs) * 100)}%` }}
                  title={`${key.toUpperCase()}: ${formatCompactNumber(value)}`}
                />
              ))}
            </div>
            <span className="text-[10px] text-slate-550 dark:text-zinc-400 font-bold">{shortPeriodLabel(row.period)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function CashQualityLineChart({ rows }) {
  const cleanRows = rows.slice(-7)
  const ocfPoints = chartPolyline(cleanRows.map((row) => row.ocfToNetIncome), 0, 2)
  const capexPoints = chartPolyline(cleanRows.map((row) => row.capexRatio), 0, 60)
  const conversionPoints = chartPolyline(cleanRows.map((row) => row.cashConversion), 0, 120)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3.5 text-[11px] font-semibold text-slate-550 dark:text-zinc-400">
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-emerald-505" />OCF/LNST</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-teal-500" />Capex Ratio</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-amber-500" />Chuyển hóa tiền mặt</span>
      </div>
      <div className="w-full">
        <svg viewBox="0 0 520 220" className="w-full h-auto bg-slate-50 dark:bg-zinc-950/40 rounded-xl border border-slate-200 dark:border-zinc-800">
          {[40, 80, 120, 160].map((y) => <line key={y} x1="42" x2="500" y1={y} y2={y} className="stroke-slate-200 dark:stroke-zinc-800/80 stroke-1 stroke-dasharray-[4_4]" />)}
          <polyline points={ocfPoints} className="fill-none stroke-emerald-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          <polyline points={capexPoints} className="fill-none stroke-teal-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          <polyline points={conversionPoints} className="fill-none stroke-amber-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          {cleanRows.map((row, index) => (
            <text key={row.period} x={52 + index * (438 / Math.max(1, cleanRows.length - 1))} y="204" textAnchor="middle" className="fill-slate-500 dark:fill-zinc-400 text-[10px] font-bold">
              {shortPeriodLabel(row.period)}
            </text>
          ))}
        </svg>
      </div>
    </div>
  )
}

export function RatioGroupCard({ group }) {
  return (
    <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
      <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
        <h2 className="text-sm font-bold text-slate-805 dark:text-white flex items-center gap-2">
          <span>{group.icon}</span>
          {group.title}
        </h2>
      </header>
      <div className="flex flex-col gap-4">
        {group.items.map((item) => (
          <div key={item.label} className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-xs font-semibold">
              <strong className="text-slate-805 dark:text-white">{item.label}</strong>
              <div className="flex items-center gap-2 text-[10px] font-bold">
                <span className="text-slate-655 dark:text-zinc-300">{item.value}</span>
                <span className={`px-2 py-0.5 rounded border ${
                  item.tone === 'good' ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-100 text-emerald-600 dark:text-emerald-400' :
                  item.tone === 'warn' ? 'bg-red-50 dark:bg-red-950/20 border-red-100 text-red-650 dark:text-red-400' :
                  'bg-slate-50 dark:bg-zinc-800 border-slate-200 text-slate-500 dark:text-zinc-400'
                }`}>{scoreLabel(item.tone)}</span>
              </div>
            </div>
            <div className="relative w-full h-2 rounded-full bg-slate-100 dark:bg-zinc-800 overflow-hidden">
              <div className={`h-full transition-all duration-300 ${
                item.tone === 'good' ? 'bg-emerald-505' :
                item.tone === 'warn' ? 'bg-red-505' : 'bg-amber-505'
              }`} style={{ width: `${item.progress}%` }} />
              <b className="absolute top-0 w-0.5 h-full bg-slate-500 dark:bg-zinc-300" style={{ left: `${item.benchmark}%` }} />
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

export function RatioTrendChart({ rows }) {
  const cleanRows = rows.slice(-7)
  const roePoints = chartPolyline(cleanRows.map((row) => row.roe), 0, 35)
  const currentPoints = chartPolyline(cleanRows.map((row) => row.currentRatio), 0, 3)
  const debtPoints = chartPolyline(cleanRows.map((row) => row.debtToEquity), 0, 2)
  const netMarginPoints = chartPolyline(cleanRows.map((row) => row.netMargin), 0, 25)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3.5 text-[11px] font-semibold text-slate-550 dark:text-zinc-400">
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-pink-500" />ROE</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-indigo-500" />Current Ratio</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-red-500" />Debt/Equity</span>
        <span className="flex items-center gap-1.5"><i className="w-3 h-3 rounded-sm bg-purple-550" />Biên lợi nhuận ròng</span>
      </div>
      <div className="w-full">
        <svg viewBox="0 0 520 220" className="w-full h-auto bg-slate-50 dark:bg-zinc-950/40 rounded-xl border border-slate-200 dark:border-zinc-800">
          {[40, 80, 120, 160].map((y) => <line key={y} x1="42" x2="500" y1={y} y2={y} className="stroke-slate-200 dark:stroke-zinc-800/80 stroke-1 stroke-dasharray-[4_4]" />)}
          <polyline points={roePoints} className="fill-none stroke-pink-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          <polyline points={currentPoints} className="fill-none stroke-indigo-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          <polyline points={debtPoints} className="fill-none stroke-red-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          <polyline points={netMarginPoints} className="fill-none stroke-purple-505 stroke-[2] stroke-linecap-round stroke-linejoin-round" />
          {cleanRows.map((row, index) => (
            <text key={row.period} x={52 + index * (438 / Math.max(1, cleanRows.length - 1))} y="204" textAnchor="middle" className="fill-slate-500 dark:fill-zinc-400 text-[10px] font-bold">
              {shortPeriodLabel(row.period)}
            </text>
          ))}
        </svg>
      </div>
    </div>
  )
}
