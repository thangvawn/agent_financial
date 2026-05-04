import { useState, useMemo } from 'react'
import './optimizer-scenario.css'

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
        stroke="#091210"
        strokeWidth={2}
      />
    )
  })

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {arcs}
      <circle cx={cx} cy={cy} r={r * 0.52} fill="#091210" />
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
    <div className="os">
      {/* Breadcrumb */}
      <nav className="os-breadcrumb">
        <button className="os-breadcrumb__link" onClick={onBack}>Research</button>
        <span className="os-breadcrumb__sep">/</span>
        <button className="os-breadcrumb__link" onClick={onBack}>Pro Lab</button>
        <span className="os-breadcrumb__sep">/</span>
        <span className="os-breadcrumb__current">Optimizer &amp; Scenario Lab</span>
      </nav>

      {/* Two-column layout */}
      <div className="os-columns">
        {/* ── Left: Optimizer Lab ──────────────────────── */}
        <div className="os-col">
          <header className="os-section-header">
            <div className="os-section-header__left">
              <span className="os-section-icon os-section-icon--green">⚙️</span>
              <div>
                <h2 className="os-section-title">Optimizer Lab</h2>
                <p className="os-section-subtitle">Build risk-aware portfolios that respect your constraints.</p>
              </div>
            </div>
            <div className="os-section-header__actions">
              <button className="os-pill os-pill--draft">Draft</button>
              <button className="os-pill os-pill--outline" onClick={() => setValues(DEFAULT_VALUES)}>Reset</button>
            </div>
          </header>

          {/* Optimization Controls */}
          <div className="os-card">
            <h3 className="os-card__title">Optimization Controls</h3>
            <div className="os-controls">
              {SLIDER_CONTROLS.map((ctrl) => (
                <label key={ctrl.id} className="os-control-field">
                  <div className="os-control-field__head">
                    <label className="os-slider-group__label">{ctrl.label}</label>
                  </div>
                  <div className="os-compact-input">
                    <input
                      type="number"
                      className="os-num-input"
                      value={values[ctrl.id]}
                      min={ctrl.min}
                      max={ctrl.max}
                      step={ctrl.step}
                      onChange={(e) => set(ctrl.id, parseFloat(e.target.value) || 0)}
                    />
                    <span className="os-slider-group__suffix">{ctrl.suffix}</span>
                  </div>
                </label>
              ))}

              <div className="os-control-divider" />
              <h4 className="os-control-subtitle">Exposure Constraints</h4>

              {RANGE_CONTROLS.map((ctrl) => (
                <div key={ctrl.id} className="os-constraint-row">
                  <span className="os-slider-group__label">{ctrl.label}</span>
                  <div className="os-range-inputs">
                    <label>
                      <span>Min</span>
                      <div className="os-compact-input os-compact-input--sm">
                        <input
                          type="number"
                          className="os-num-input"
                          value={values[ctrl.id][0]}
                          min={ctrl.min}
                          max={ctrl.max}
                          step={ctrl.step}
                          onChange={(e) => setRange(ctrl.id, 0, parseFloat(e.target.value) || 0)}
                        />
                        <span className="os-slider-group__suffix">{ctrl.suffix}</span>
                      </div>
                    </label>
                    <label>
                      <span>Max</span>
                      <div className="os-compact-input os-compact-input--sm">
                        <input
                          type="number"
                          className="os-num-input"
                          value={values[ctrl.id][1]}
                          min={ctrl.min}
                          max={ctrl.max}
                          step={ctrl.step}
                          onChange={(e) => setRange(ctrl.id, 1, parseFloat(e.target.value) || 0)}
                        />
                        <span className="os-slider-group__suffix">{ctrl.suffix}</span>
                      </div>
                    </label>
                    <span className="os-checkmark">✓</span>
                  </div>
                </div>
              ))}

              {/* Allocation Method */}
              <div className="os-slider-group">
                <label className="os-slider-group__label">Allocation Method</label>
                <select
                  className="os-select"
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

            <div className="os-run-row">
              <button className="os-btn os-btn--run">Run Optimization ▶</button>
              <span className="os-run-row__ts">Last run: May 16, 2025 10:22 AM</span>
            </div>
          </div>

          {/* Portfolio Allocation (Draft) */}
          <div className="os-card">
            <h3 className="os-card__title">Portfolio Allocation (Draft)</h3>
            <div className="os-alloc-layout">
              <DonutChart data={ALLOCATION_CHART} size={190} />
              <div className="os-alloc-legend">
                {ALLOCATION_CHART.map((d) => (
                  <div key={d.label} className="os-alloc-legend__row">
                    <span className="os-alloc-legend__dot" style={{ background: d.color }} />
                    <span className="os-alloc-legend__label">{d.label}</span>
                    <span className="os-alloc-legend__pct">{d.pct}%</span>
                  </div>
                ))}
                <div className="os-alloc-legend__total">
                  <span>Total</span>
                  <strong>{totalPct.toFixed(1)}%</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Constraint Check */}
          <div className="os-card">
            <h3 className="os-card__title">Constraint Check</h3>
            <table className="os-table">
              <thead>
                <tr>
                  <th>Constraint</th>
                  <th>Status</th>
                  <th>Utilization</th>
                </tr>
              </thead>
              <tbody>
                {CONSTRAINT_ROWS.map((row) => (
                  <tr key={row.name}>
                    <td>{row.name}</td>
                    <td><span className="os-badge os-badge--pass">✓ {row.status}</span></td>
                    <td>{row.util}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Draft Weights */}
          <div className="os-card">
            <h3 className="os-card__title">Draft Weights</h3>
            <table className="os-table">
              <thead>
                <tr>
                  <th>Asset / ETF</th>
                  <th>Asset Class</th>
                  <th>Weight%</th>
                  <th>Δ vs Current</th>
                  <th>Marginal Risk</th>
                </tr>
              </thead>
              <tbody>
                {DRAFT_WEIGHTS.map((row) => (
                  <tr key={row.asset}>
                    <td className="os-table__bold">{row.asset}</td>
                    <td className="os-table__muted">{row.cls}</td>
                    <td>{row.weight}%</td>
                    <td className={row.delta.startsWith('+') ? 'os-table__up' : 'os-table__down'}>{row.delta}%</td>
                    <td>{row.risk}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Right: Scenario Lab ─────────────────────── */}
        <div className="os-col">
          <header className="os-section-header">
            <div className="os-section-header__left">
              <span className="os-section-icon os-section-icon--amber">🌐</span>
              <div>
                <h2 className="os-section-title">Scenario Lab</h2>
                <p className="os-section-subtitle">Model macro shocks and stress-test your portfolio.</p>
              </div>
            </div>
            <div className="os-section-header__actions">
              <button className="os-pill os-pill--outline">Manage Scenarios</button>
              <button className="os-pill os-pill--icon">⋯</button>
            </div>
          </header>

          {/* Macro & Stress Scenarios */}
          <div className="os-card">
            <h3 className="os-card__title">Macro &amp; Stress Scenarios</h3>
            <div className="os-scenario-cards">
              {SCENARIOS.map((s) => (
                <button
                  key={s.id}
                  className={`os-scenario-card ${activeScenario === s.id ? 'os-scenario-card--active' : ''}`}
                  onClick={() => setActiveScenario(s.id)}
                  style={{ '--sc-color': s.color }}
                >
                  <span className="os-scenario-card__name">{s.name}</span>
                  <div className="os-scenario-card__meta">
                    <span className="os-scenario-card__dots">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <span
                          key={i}
                          className={`os-dot ${i < s.severity ? 'os-dot--filled' : ''}`}
                          style={i < s.severity ? { background: s.color } : undefined}
                        />
                      ))}
                    </span>
                    <span className="os-scenario-card__horizon">{s.horizon}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Impact Heatmap */}
          <div className="os-card">
            <h3 className="os-card__title">Impact Heatmap</h3>
            <div className="os-heatmap-wrap">
              <table className="os-table os-table--heatmap">
                <thead>
                  <tr>
                    <th>Asset / Sector</th>
                    <th>FX Shock</th>
                    <th>Rate Shock</th>
                    <th>Inflation</th>
                    <th>Growth</th>
                  </tr>
                </thead>
                <tbody>
                  {HEATMAP_ROWS.map((row) => (
                    <tr key={row.asset}>
                      <td className="os-table__bold">{row.asset}</td>
                      {[row.fx, row.rate, row.inflation, row.growth].map((val, i) => (
                        <td key={i} style={{ background: heatColor(val) }}>
                          <span className={val >= 0 ? 'os-table__up' : 'os-table__down'}>
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
          <div className="os-card">
            <h3 className="os-card__title">Scenario Assumptions</h3>
            <div className="os-kv-grid">
              {SCENARIO_ASSUMPTIONS.map((a) => (
                <div key={a.key} className="os-kv">
                  <span className="os-kv__key">{a.key}</span>
                  <span className="os-kv__val">{a.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Portfolio Stress Results */}
          <div className="os-card">
            <h3 className="os-card__title">Portfolio Stress Results</h3>
            <div className="os-metrics-grid">
              {STRESS_RESULTS.map((m) => (
                <div key={m.label} className="os-metric-card">
                  <span className="os-metric-card__label">{m.label}</span>
                  <strong
                    className={`os-metric-card__value ${m.negative ? 'os-metric-card__value--neg' : ''}`}
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
      <div className="os-action-bar">
        <button className="os-btn os-btn--run">Apply Scenario ▶</button>
        <button className="os-btn os-btn--blue">Re-optimize ▶</button>
        <button className="os-btn os-btn--outline">Save Scenario Pack</button>
      </div>
    </div>
  )
}
