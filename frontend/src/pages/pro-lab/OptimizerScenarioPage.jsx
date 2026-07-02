import { useState, useMemo } from 'react'

const SLIDER_CONTROLS = [
  { id: 'riskBudget', label: 'Risk Budget (Annual Vol Target)', min: 5, max: 30, step: 0.5, suffix: '%' },
  { id: 'maxWeight', label: 'Max Weight (Single Asset)', min: 1, max: 25, step: 0.5, suffix: '%' },
  { id: 'targetVol', label: 'Target Volatility (Annualized)', min: 5, max: 30, step: 0.5, suffix: '%' },
  { id: 'turnoverCap', label: 'Turnover Cap (vs. Current)', min: 5, max: 50, step: 1, suffix: '%' },
  { id: 'sectorMax', label: 'Sector Max', min: 10, max: 50, step: 1, suffix: '%' },
  { id: 'countryMax', label: 'Single Country Max', min: 10, max: 60, step: 1, suffix: '%' },
]

const RANGE_CONTROLS = [
  { id: 'grossExposure', label: 'Gross Exposure', min: 50, max: 200, step: 1, suffix: '%' },
  { id: 'factorBeta', label: 'Factor Beta (Market)', min: 0.0, max: 2.0, step: 0.05, suffix: '' },
]

const DEFAULT_VALUES = {
  riskBudget: 14.0,
  maxWeight: 12.5,
  targetVol: 14.0,
  turnoverCap: 25.0,
  sectorMax: 25,
  countryMax: 30,
  grossExposure: [80, 150],
  factorBeta: [0.8, 1.2],
  allocationMethod: 'mean-variance-rp',
}

const ALLOCATION_CHART = [
  { label: 'US Equities', pct: 32.4, color: '#4fd1b4' },
  { label: "Int'l Equities", pct: 18.7, color: '#3b82f6' },
  { label: 'Emerging Markets', pct: 8.6, color: '#8b5cf6' },
  { label: 'Fixed Income', pct: 16.2, color: '#f59e0b' },
  { label: 'Real Estate', pct: 7.8, color: '#ef4444' },
  { label: 'Commodities', pct: 5.5, color: '#06b6d4' },
  { label: 'Cash', pct: 10.8, color: '#6b7280' },
]

const CONSTRAINT_ROWS = [
  { name: 'Risk Budget ≤ 14%', status: 'Pass', util: '98.2%' },
  { name: 'Max Single Asset ≤ 12.5%', status: 'Pass', util: '91.0%' },
  { name: 'Turnover ≤ 25%', status: 'Pass', util: '72.4%' },
  { name: 'Gross Exposure 80–150%', status: 'Pass', util: '100.0%' },
  { name: 'Sector Max ≤ 25%', status: 'Pass', util: '88.6%' },
  { name: 'Country Max ≤ 30%', status: 'Pass', util: '76.3%' },
]

const DRAFT_WEIGHTS = [
  { asset: 'SPY', cls: 'US Equities', weight: 18.2, delta: '+2.1', risk: '4.8%' },
  { asset: 'QQQ', cls: 'US Equities', weight: 14.2, delta: '+0.8', risk: '5.2%' },
  { asset: 'VEA', cls: "Int'l Equities", weight: 10.4, delta: '-1.2', risk: '2.9%' },
  { asset: 'EFA', cls: "Int'l Equities", weight: 8.3, delta: '+0.4', risk: '2.1%' },
  { asset: 'VWO', cls: 'Emerging Mkts', weight: 8.6, delta: '+1.6', risk: '3.4%' },
  { asset: 'AGG', cls: 'Fixed Income', weight: 16.2, delta: '-0.9', risk: '1.1%' },
  { asset: 'VNQ', cls: 'Real Estate', weight: 7.8, delta: '+0.3', risk: '2.6%' },
  { asset: 'GLD', cls: 'Commodities', weight: 5.5, delta: '-0.5', risk: '1.8%' },
  { asset: 'BIL', cls: 'Cash', weight: 10.8, delta: '-2.6', risk: '0.1%' },
]

const SCENARIOS = [
  { id: 'fx', name: 'FX Shock (USD Strong)', severity: 3, horizon: '3M', color: '#3b82f6' },
  { id: 'rate', name: 'Rate Shock (Up 200bps)', severity: 4, horizon: '6M', color: '#ef4444' },
  { id: 'inflation', name: 'Inflation Surprise', severity: 3, horizon: '12M', color: '#f59e0b' },
  { id: 'growth', name: 'Growth Slowdown', severity: 2, horizon: '6M', color: '#8b5cf6' },
]

const HEATMAP_ROWS = [
  { asset: 'US Equities', fx: -3.2, rate: -5.8, inflation: -2.1, growth: -7.4 },
  { asset: "Int'l Equities", fx: -6.1, rate: -4.3, inflation: -1.8, growth: -5.9 },
  { asset: 'Emerging Mkts', fx: -8.4, rate: -6.7, inflation: +1.2, growth: -9.1 },
  { asset: 'Fixed Income', fx: -0.5, rate: -12.3, inflation: -4.6, growth: +2.8 },
  { asset: 'Real Estate', fx: -1.8, rate: -8.9, inflation: +0.6, growth: -6.2 },
  { asset: 'Commodities', fx: +2.4, rate: -1.2, inflation: +5.8, growth: -3.7 },
  { asset: 'Cash', fx: +0.1, rate: +0.4, inflation: -0.3, growth: +0.2 },
]

const SCENARIO_ASSUMPTIONS = [
  { key: 'DXY Change', value: '+8%' },
  { key: 'EUR/USD Change', value: '-7%' },
  { key: 'US 10Y Yield', value: '+200bps' },
  { key: 'CPI YoY', value: '+1.5%' },
  { key: 'GDP Growth', value: '-2.0%' },
  { key: 'VIX Level', value: '32' },
]

const STRESS_RESULTS = [
  { label: 'Max Drawdown', value: '-14.2%', negative: true },
  { label: 'VaR (95%)', value: '-8.6%', negative: true },
  { label: 'Expected Return Impact', value: '-3.4%', negative: true },
  { label: 'Tracking Error', value: '6.8%', neutral: true },
  { label: 'Sharpe Ratio', value: '0.42', neutral: true },
  { label: 'Beta', value: '0.91', neutral: true },
]

function DonutChart({ data, size = 180 }) {
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - 14
  const total = data.reduce((s, d) => s + d.pct, 0)
  let cumAngle = -90

  const arcs = data.map((d) => {
    const angle = (d.pct / total) * 360
    const startRad = (cumAngle * Math.PI) / 180
    const endRad = ((cumAngle + angle) * Math.PI) / 180
    cumAngle += angle
    const largeArc = angle > 180 ? 1 : 0
    const x1 = cx + r * Math.cos(startRad)
    const y1 = cy + r * Math.sin(startRad)
    const x2 = cx + r * Math.cos(endRad)
    const y2 = cy + r * Math.sin(endRad)
    return (
      <path
        key={d.label}
        d={`M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`}
        fill={d.color}
        opacity={0.85}
        stroke="#101d26"
        strokeWidth={2}
      />
    )
  })

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {arcs}
      <circle cx={cx} cy={cy} r={r * 0.52} fill="#101d26" />
    </svg>
  )
}

function heatColor(val) {
  if (val >= 3) return 'rgba(79, 209, 180, 0.35)'
  if (val > 0) return 'rgba(79, 209, 180, 0.18)'
  if (val > -3) return 'rgba(224, 96, 96, 0.12)'
  if (val > -7) return 'rgba(224, 96, 96, 0.25)'
  return 'rgba(224, 96, 96, 0.4)'
}

export default function OptimizerScenarioPage({ onBack }) {
  const [values, setValues] = useState(DEFAULT_VALUES)
  const [activeScenario, setActiveScenario] = useState('fx')

  const set = (key, val) => setValues((prev) => ({ ...prev, [key]: val }))
  const setRange = (key, idx, val) =>
    setValues((prev) => {
      const arr = [...prev[key]]
      arr[idx] = val
      return { ...prev, [key]: arr }
    })

  const totalPct = useMemo(() => ALLOCATION_CHART.reduce((s, d) => s + d.pct, 0), [])

  return (
    <div className="w-full min-h-screen bg-transparent text-[#c8d6d2] font-sans px-6 md:px-10 py-6 md:py-8 flex flex-col gap-6 max-w-[1720px] mx-auto">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-[#5e7a72]">
        <button className="p-0 border-none bg-transparent text-[#4fd1b4] font-semibold cursor-pointer hover:text-[#6ee0c8] transition" onClick={onBack}>Research</button>
        <span className="text-[#2a3f3a]">/</span>
        <button className="p-0 border-none bg-transparent text-[#4fd1b4] font-semibold cursor-pointer hover:text-[#6ee0c8] transition" onClick={onBack}>Pro Lab</button>
        <span className="text-[#2a3f3a]">/</span>
        <span className="text-[#5e7a72] font-semibold">Optimizer &amp; Scenario Lab</span>
      </nav>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-5 items-start">
        {/* ── Left: Optimizer Lab ──────────────────────── */}
        <div className="grid gap-4">
          <header className="flex justify-between items-start gap-4 flex-wrap">
            <div className="flex gap-2.5 items-start">
              <span className="w-[38px] h-[38px] min-w-[38px] flex items-center justify-center rounded-xl text-lg flex-shrink-0 bg-[#4fd1b4]/10 border border-[#4fd1b4]/20 text-[#4fd1b4]">⚙️</span>
              <div>
                <h2 className="margin-0 text-lg font-extrabold text-[#ecf4f0] tracking-tight leading-tight">Optimizer Lab</h2>
                <p className="margin-0 mt-0.5 text-xs text-[#5e7a72] leading-normal">Build risk-aware portfolios that respect your constraints.</p>
              </div>
            </div>
            <div className="flex gap-2 items-center flex-shrink-0">
              <button className="px-3 py-1 rounded-lg text-[10px] font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">Draft</button>
              <button className="px-3 py-1 rounded-lg text-[10px] font-bold cursor-pointer transition active:scale-95 text-[#a0b8b0] bg-transparent border border-[#4fd1b4]/10 hover:border-[#4fd1b4]/25" onClick={() => setValues(DEFAULT_VALUES)}>Reset</button>
            </div>
          </header>

          {/* Optimization Controls */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Optimization Controls</h3>
            <div className="grid gap-4">
              {SLIDER_CONTROLS.map((ctrl) => (
                <label key={ctrl.id} className="flex flex-col gap-1">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold text-[#88aab8]">{ctrl.label}</span>
                  </div>
                  <div className="flex items-center bg-[#0c1720]/80 border border-[#88aab8]/20 rounded-lg px-2 py-1">
                    <input
                      type="number"
                      className="bg-transparent border-none text-[#edf7f5] text-xs font-semibold w-16 outline-none text-right"
                      value={values[ctrl.id]}
                      min={ctrl.min}
                      max={ctrl.max}
                      step={ctrl.step}
                      onChange={(e) => set(ctrl.id, parseFloat(e.target.value) || 0)}
                    />
                    <span className="text-xs font-bold text-[#88aab8] select-none ml-1">{ctrl.suffix}</span>
                  </div>
                </label>
              ))}

              <div className="h-[1px] bg-[#88aab8]/10 my-1" />
              <h4 className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">Exposure Constraints</h4>

              {RANGE_CONTROLS.map((ctrl) => (
                <div key={ctrl.id} className="flex flex-wrap items-center justify-between gap-2.5 py-1">
                  <span className="text-xs font-semibold text-[#88aab8]">{ctrl.label}</span>
                  <div className="flex items-center gap-3 text-xs">
                    <label className="flex items-center gap-1.5">
                      <span className="text-[#5e7a72]">Min</span>
                      <div className="flex items-center bg-[#0c1720]/80 border border-[#88aab8]/20 rounded-lg px-2 py-1 max-w-[100px]">
                        <input
                          type="number"
                          className="bg-transparent border-none text-[#edf7f5] text-xs font-semibold w-12 outline-none text-right"
                          value={values[ctrl.id][0]}
                          min={ctrl.min}
                          max={ctrl.max}
                          step={ctrl.step}
                          onChange={(e) => setRange(ctrl.id, 0, parseFloat(e.target.value) || 0)}
                        />
                        <span className="text-xs font-bold text-[#88aab8] select-none ml-1">{ctrl.suffix}</span>
                      </div>
                    </label>
                    <label className="flex items-center gap-1.5">
                      <span className="text-[#5e7a72]">Max</span>
                      <div className="flex items-center bg-[#0c1720]/80 border border-[#88aab8]/20 rounded-lg px-2 py-1 max-w-[100px]">
                        <input
                          type="number"
                          className="bg-transparent border-none text-[#edf7f5] text-xs font-semibold w-12 outline-none text-right"
                          value={values[ctrl.id][1]}
                          min={ctrl.min}
                          max={ctrl.max}
                          step={ctrl.step}
                          onChange={(e) => setRange(ctrl.id, 1, parseFloat(e.target.value) || 0)}
                        />
                        <span className="text-xs font-bold text-[#88aab8] select-none ml-1">{ctrl.suffix}</span>
                      </div>
                    </label>
                    <span className="text-emerald-500 font-bold text-xs">✓</span>
                  </div>
                </div>
              ))}

              {/* Allocation Method */}
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-[#88aab8]">Allocation Method</label>
                <select
                  className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition"
                  value={values.allocationMethod}
                  onChange={(e) => set('allocationMethod', e.target.value)}
                >
                  <option value="mean-variance-rp">Mean-Variance (Risk Parity Hybrid)</option>
                  <option value="black-litterman">Black-Litterman</option>
                  <option value="min-variance">Minimum Variance</option>
                  <option value="max-sharpe">Maximum Sharpe</option>
                  <option value="equal-weight">Equal Weight</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between gap-4 mt-2">
              <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] !h-auto !py-2.5">Run Optimization ▶</button>
              <span className="text-[10px] text-[#5e7a72] font-semibold">Last run: May 16, 2025 10:22 AM</span>
            </div>
          </div>

          {/* Portfolio Allocation (Draft) */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Portfolio Allocation (Draft)</h3>
            <div className="flex flex-col sm:flex-row items-center gap-6 justify-center">
              <DonutChart data={ALLOCATION_CHART} size={190} />
              <div className="flex-1 w-full flex flex-col gap-2">
                {ALLOCATION_CHART.map((d) => (
                  <div key={d.label} className="flex items-center gap-2 text-xs">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: d.color }} />
                    <span className="flex-1 text-[#88aab8]">{d.label}</span>
                    <span className="font-bold text-white">{d.pct}%</span>
                  </div>
                ))}
                <div className="flex justify-between border-t border-[#88aab8]/15 pt-2 mt-1 text-xs font-bold text-white">
                  <span>Total</span>
                  <strong>{totalPct.toFixed(1)}%</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Constraint Check */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Constraint Check</h3>
            <div className="overflow-x-auto [scrollbar-width:thin]">
              <table className="w-full text-left border-collapse text-xs min-w-[500px]">
                <thead>
                  <tr>
                    <th className="pb-2.5 border-b border-[#88aab8]/15 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px]">Constraint</th>
                    <th className="pb-2.5 border-b border-[#88aab8]/15 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px]">Status</th>
                    <th className="pb-2.5 border-b border-[#88aab8]/15 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px]">Utilization</th>
                  </tr>
                </thead>
                <tbody>
                  {CONSTRAINT_ROWS.map((row) => (
                    <tr key={row.name}>
                      <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">{row.name}</td>
                      <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">✓ {row.status}</span>
                      </td>
                      <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">{row.util}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Draft Weights */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Draft Weights</h3>
            <div className="overflow-x-auto [scrollbar-width:thin]">
              <table className="w-full text-left border-collapse text-xs min-w-[600px]">
                <thead>
                  <tr>
                    <th className="pb-2.5 border-b border-[#88aab8]/15 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px]">Asset / ETF</th>
                    <th className="pb-2.5 border-b border-[#88aab8]/15 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px]">Asset Class</th>
                    <th className="pb-2.5 border-b border-[#88aab8]/15 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px]">Weight%</th>
                    <th className="pb-2.5 border-b border-[#88aab8]/15 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px]">Δ vs Current</th>
                    <th className="pb-2.5 border-b border-[#88aab8]/15 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px]">Marginal Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {DRAFT_WEIGHTS.map((row) => (
                    <tr key={row.asset}>
                      <td className="py-3 border-b border-[#88aab8]/10 text-white font-bold">{row.asset}</td>
                      <td className="py-3 border-b border-[#88aab8]/10 text-[#5e7a72]">{row.cls}</td>
                      <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">{row.weight}%</td>
                      <td className={`py-3 border-b border-[#88aab8]/10 ${row.delta.startsWith('+') ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}`}>{row.delta}%</td>
                      <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">{row.risk}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ── Right: Scenario Lab ─────────────────────── */}
        <div className="grid gap-4">
          <header className="flex justify-between items-start gap-4 flex-wrap">
            <div className="flex gap-2.5 items-start">
              <span className="w-[38px] h-[38px] min-w-[38px] flex items-center justify-center rounded-xl text-lg flex-shrink-0 bg-[#f59e0b]/10 border border-[#f59e0b]/20 text-[#f59e0b]">🌐</span>
              <div>
                <h2 className="margin-0 text-lg font-extrabold text-[#ecf4f0] tracking-tight leading-tight">Scenario Lab</h2>
                <p className="margin-0 mt-0.5 text-xs text-[#5e7a72] leading-normal">Model macro shocks and stress-test your portfolio.</p>
              </div>
            </div>
            <div className="flex gap-2 items-center flex-shrink-0">
              <button className="px-3 py-1 rounded-lg text-[10px] font-bold cursor-pointer transition active:scale-95 text-[#a0b8b0] bg-transparent border border-[#4fd1b4]/10 hover:border-[#4fd1b4]/25">Manage Scenarios</button>
              <button className="px-3 py-1 rounded-lg text-[10px] font-bold cursor-pointer transition active:scale-95 text-[#a0b8b0] bg-[#11222a]/50 border border-[#4fd1b4]/10 hover:border-[#4fd1b4]/25 w-7 h-7 flex items-center justify-center p-0">⋯</button>
            </div>
          </header>

          {/* Macro & Stress Scenarios */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Macro &amp; Stress Scenarios</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {SCENARIOS.map((s) => {
                const isActive = activeScenario === s.id
                return (
                  <div
                    key={s.id}
                    role="button"
                    tabIndex={0}
                    className={`flex flex-col gap-3 p-4 rounded-xl border text-left cursor-pointer transition-all duration-200 ${
                      isActive
                        ? 'bg-[#101d26]/90 shadow-md'
                        : 'bg-[#0c1720]/40 border-[#88aab8]/10 hover:border-[#88aab8]/25'
                    }`}
                    style={{ borderColor: isActive ? s.color : undefined }}
                    onClick={() => setActiveScenario(s.id)}
                    onKeyDown={(e) => e.key === 'Enter' && setActiveScenario(s.id)}
                  >
                    <span className="text-xs font-bold text-white leading-snug">{s.name}</span>
                    <div className="flex justify-between items-center mt-1">
                      <span className="flex gap-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <span
                            key={i}
                            className={`w-1.5 h-1.5 rounded-full ${i < s.severity ? '' : 'bg-[#11222a]/80'}`}
                            style={i < s.severity ? { background: s.color } : undefined}
                          />
                        ))}
                      </span>
                      <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">{s.horizon}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Impact Heatmap */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Impact Heatmap</h3>
            <div className="overflow-x-auto [scrollbar-width:thin]">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr>
                    <th className="pb-2.5 border border-[#88aab8]/10 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] p-2">Asset / Sector</th>
                    <th className="pb-2.5 border border-[#88aab8]/10 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] p-2 text-center">FX Shock</th>
                    <th className="pb-2.5 border border-[#88aab8]/10 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] p-2 text-center">Rate Shock</th>
                    <th className="pb-2.5 border border-[#88aab8]/10 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] p-2 text-center">Inflation</th>
                    <th className="pb-2.5 border border-[#88aab8]/10 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] p-2 text-center">Growth</th>
                  </tr>
                </thead>
                <tbody>
                  {HEATMAP_ROWS.map((row) => (
                    <tr key={row.asset}>
                      <td className="p-2 border border-[#88aab8]/10 text-white font-bold">{row.asset}</td>
                      {[row.fx, row.rate, row.inflation, row.growth].map((val, i) => (
                        <td key={i} className="text-center border border-[#88aab8]/10 p-2" style={{ background: heatColor(val) }}>
                          <span className={val >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {val >= 0 ? '+' : ''}{val.toFixed(1)}%
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Scenario Assumptions */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Scenario Assumptions</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {SCENARIO_ASSUMPTIONS.map((a) => (
                <div key={a.key} className="flex justify-between py-1.5 border-b border-[#88aab8]/10 text-xs">
                  <span className="text-[#88aab8]">{a.key}</span>
                  <span className="font-bold text-white">{a.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Portfolio Stress Results */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Portfolio Stress Results</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {STRESS_RESULTS.map((m) => (
                <div key={m.label} className="p-3.5 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
                  <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">{m.label}</span>
                  <strong
                    className={`text-sm font-extrabold ${m.negative ? 'text-rose-400' : 'text-white'}`}
                  >
                    {m.value}
                  </strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom action bar */}
      <div className="flex flex-wrap gap-3 pt-4 border-t border-[#88aab8]/15 mt-4">
        <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] !h-auto !py-2.5">Apply Scenario ▶</button>
        <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 bg-[#3b82f6] hover:bg-[#60a5fa] text-white !h-auto !py-2.5">Re-optimize ▶</button>
        <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 border border-[#88aab8]/20 hover:border-[#88aab8]/45 text-[#edf7f5] !h-auto !py-2.5">Save Scenario Pack</button>
      </div>
    </div>
  )
}
