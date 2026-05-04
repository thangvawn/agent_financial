import { useState } from 'react'
import './auto-copy-paper.css'

const RISK_CONTROLS = [
  { control: 'Max Gross Exposure', threshold: '100.00%' },
  { control: 'Max Net Exposure', threshold: '50.00%' },
  { control: 'Max Position Size', threshold: '2.00%' },
  { control: 'Daily Loss Limit', threshold: '3.00%' },
  { control: 'Drawdown Limit', threshold: '10.00%' },
  { control: 'Concentration (Top 5)', threshold: '25.00%' },
  { control: 'Leverage', threshold: '1.50x' },
  { control: 'Volatility', threshold: '20.00%' },
]

const PRE_LAUNCH_ITEMS = [
  'Strategy source validated',
  'Paper account configured',
  'Risk limits set',
  'Kill switches enabled',
  'Manual review rules defined',
  'Schedule configured',
]

const APPROVAL_STEPS = [
  { name: 'Plan Creator', status: 'Completed', done: true },
  { name: 'Risk Review', status: 'Pending', done: false },
  { name: 'Final Approval', status: 'Pending', done: false },
]

const KILL_SWITCHES = [
  { id: 'exposure', label: 'Exposure Breach' },
  { id: 'loss', label: 'Loss Threshold' },
  { id: 'data', label: 'Data / Feed Issues' },
]

const REVIEW_RULES = [
  { id: 'newPos', label: 'New Position Opens', checked: true },
  { id: 'sizeExc', label: 'Position Size > 1.50%', checked: true },
  { id: 'watchlist', label: 'Watchlist Changes', checked: true },
]

const SPARKLINE_POINTS = [12, 18, 14, 20, 16, 22, 15, 19, 13, 17, 14, 16]

function MiniSparkline({ points, width = 120, height = 28, color = '#4fd1b4' }) {
  const max = Math.max(...points)
  const min = Math.min(...points)
  const range = max - min || 1
  const step = width / (points.length - 1)

  const d = points
    .map((p, i) => {
      const x = i * step
      const y = height - ((p - min) / range) * (height - 4) - 2
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')

  return (
    <svg className="ac-sparkline" width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <path d={d} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function MiniDonut({ pct, size = 56, color = '#22c55e' }) {
  const r = (size - 8) / 2
  const cx = size / 2
  const cy = size / 2
  const circ = 2 * Math.PI * r
  const filled = (pct / 100) * circ
  const gap = circ - filled

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(79,209,180,0.1)" strokeWidth={5} />
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={5}
        strokeDasharray={`${filled} ${gap}`}
        strokeDashoffset={circ / 4}
        strokeLinecap="round"
      />
      <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" className="ac-donut-center">
        {pct}%
      </text>
    </svg>
  )
}

export default function AutoCopyPaperPage({ onBack }) {
  const [killSwitches, setKillSwitches] = useState({ exposure: true, loss: true, data: true })
  const [fractional, setFractional] = useState(true)

  const toggleKill = (id) => setKillSwitches((prev) => ({ ...prev, [id]: !prev[id] }))

  return (
    <div className="ac">
      {/* ── Header ──────────────────────────────────────── */}
      <header className="ac-header">
        <div className="ac-header__top">
          <div>
            <nav className="ac-breadcrumb">
              <button className="ac-breadcrumb__link" onClick={onBack}>Pro Lab</button>
              <span className="ac-breadcrumb__sep">›</span>
              <span className="ac-breadcrumb__current">Auto / Copy Paper Plan</span>
            </nav>
            <div className="ac-title-row">
              <h1 className="ac-title">Auto / Copy Paper Plan</h1>
              <span className="ac-badge ac-badge--paper">Paper Only</span>
            </div>
            <p className="ac-subtitle">Design a controlled paper automation plan with built-in risk, review, and governance.</p>
          </div>
          <div className="ac-toggles">
            <button className="ac-toggle-btn ac-toggle-btn--active">
              <span className="ac-toggle-dot" />Paper Only
            </button>
            <button className="ac-toggle-btn ac-toggle-btn--green">
              <span className="ac-toggle-dot" />Manual Review Required
            </button>
            <button className="ac-toggle-btn ac-toggle-btn--blue">
              <span className="ac-toggle-dot" />Limits Active
            </button>
          </div>
        </div>
      </header>

      {/* ── Warning Banner ──────────────────────────────── */}
      <div className="ac-warning">
        <span className="ac-warning__icon">⚠</span>
        <div>
          <span className="ac-warning__title">PAPER MODE ONLY — NO LIVE ORDERS. </span>
          <span className="ac-warning__text">
            This plan runs entirely in paper (shadow). No orders will be sent to any broker or exchange.
          </span>
        </div>
      </div>

      {/* ── Action Buttons ──────────────────────────────── */}
      <div className="ac-actions">
        <button className="ac-btn">Save Plan</button>
        <button className="ac-btn ac-btn--green">Run Dry Test</button>
        <button className="ac-btn ac-btn--green">Submit for Review</button>
      </div>

      {/* ── Main Layout ─────────────────────────────────── */}
      <div className="ac-layout">
        {/* Left — Plan Builder */}
        <div>
          <div className="ac-card">
            <h2 className="ac-card__title">Plan Builder</h2>
            <div className="ac-plan-grid">
              {/* 1. Strategy Source */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">1</span>
                  <span className="ac-plan-item__label">Strategy Source</span>
                </div>
                <p className="ac-plan-item__desc">Select the strategy to copy</p>
                <div className="ac-plan-item__body">
                  <select className="ac-select" defaultValue="csv">
                    <option value="csv">Cross-Sectional Value</option>
                    <option value="mom">Momentum</option>
                  </select>
                  <span className="ac-badge ac-badge--green">Live Source</span>
                </div>
              </div>

              {/* 2. Paper Account */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">2</span>
                  <span className="ac-plan-item__label">Paper Account / Shadow Account</span>
                </div>
                <div className="ac-plan-item__body">
                  <select className="ac-select" defaultValue="shadow">
                    <option value="shadow">Shadow Account – CV Copy</option>
                  </select>
                  <div className="ac-kv">
                    <span className="ac-kv__key">Buying Power:</span>
                    <span className="ac-kv__val">$1,000,000.00</span>
                  </div>
                </div>
              </div>

              {/* 3. Position Limits */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">3</span>
                  <span className="ac-plan-item__label">Position Limits</span>
                </div>
                <div className="ac-plan-item__body">
                  <div className="ac-kv">
                    <span className="ac-kv__key">Max Position Size:</span>
                    <span className="ac-kv__val">2.00 %</span>
                  </div>
                  <div className="ac-kv">
                    <span className="ac-kv__key">Max Positions:</span>
                    <span className="ac-kv__val">50</span>
                  </div>
                </div>
              </div>

              {/* 4. Max Gross Exposure */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">4</span>
                  <span className="ac-plan-item__label">Max Gross Exposure</span>
                </div>
                <div className="ac-plan-item__body">
                  <div className="ac-kv">
                    <span className="ac-kv__key">Max Gross Exposure:</span>
                    <span className="ac-kv__val">100.00 %</span>
                  </div>
                  <div className="ac-kv">
                    <span className="ac-kv__key">Current (Est.):</span>
                    <span className="ac-kv__val" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      18.42%
                      <span className="ac-badge ac-badge--green" style={{ fontSize: '0.68rem' }}>Good</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* 5. Kill Switch */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">5</span>
                  <span className="ac-plan-item__label">Kill Switch</span>
                </div>
                <div className="ac-plan-item__body">
                  {KILL_SWITCHES.map((ks) => (
                    <div key={ks.id} className="ac-toggle-row">
                      <span className="ac-toggle-row__label">{ks.label}</span>
                      <button
                        className={`ac-switch ${killSwitches[ks.id] ? 'ac-switch--on' : ''}`}
                        onClick={() => toggleKill(ks.id)}
                      >
                        <span className="ac-switch__knob" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* 6. Manual Review Rules */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">6</span>
                  <span className="ac-plan-item__label">Manual Review Rules</span>
                </div>
                <p className="ac-plan-item__desc">Events requiring manual approval.</p>
                <div className="ac-plan-item__body">
                  {REVIEW_RULES.map((r) => (
                    <div key={r.id} className="ac-check-row">
                      <span className={`ac-check-icon ${r.checked ? 'ac-check-icon--on' : 'ac-check-icon--off'}`}>
                        {r.checked ? '✓' : ''}
                      </span>
                      {r.label}
                    </div>
                  ))}
                  <button className="ac-add-btn">Other Edit rules ✎</button>
                </div>
              </div>

              {/* 7. Copy Ratio */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">7</span>
                  <span className="ac-plan-item__label">Copy Ratio</span>
                </div>
                <div className="ac-plan-item__body">
                  <div className="ac-kv">
                    <span className="ac-kv__key">Copy Ratio:</span>
                    <input className="ac-input" type="text" defaultValue="100 %" style={{ width: '80px', textAlign: 'right' }} />
                  </div>
                  <div className="ac-toggle-row">
                    <span className="ac-toggle-row__label">Allow fractional shares</span>
                    <button
                      className={`ac-switch ${fractional ? 'ac-switch--on' : ''}`}
                      onClick={() => setFractional(!fractional)}
                    >
                      <span className="ac-switch__knob" />
                    </button>
                  </div>
                </div>
              </div>

              {/* 8. Allowed Instruments */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">8</span>
                  <span className="ac-plan-item__label">Allowed Instruments</span>
                </div>
                <div className="ac-plan-item__body">
                  <div className="ac-tags">
                    <span className="ac-tag">US Equities <span className="ac-tag__x">✕</span></span>
                    <span className="ac-tag">ETFs <span className="ac-tag__x">✕</span></span>
                    <button className="ac-add-btn">+ Add Instrument Type</button>
                  </div>
                  <p className="ac-excluded">Excluded: Options, Futures, Crypto</p>
                </div>
              </div>

              {/* 9. Schedule */}
              <div className="ac-plan-item">
                <div className="ac-plan-item__head">
                  <span className="ac-plan-item__num">9</span>
                  <span className="ac-plan-item__label">Schedule</span>
                </div>
                <div className="ac-plan-item__body">
                  <div className="ac-kv">
                    <span className="ac-kv__key">Rebalance Frequency:</span>
                    <select className="ac-select" defaultValue="daily" style={{ width: 'auto' }}>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                    </select>
                  </div>
                  <div className="ac-kv">
                    <span className="ac-kv__key">Time (ET):</span>
                    <span className="ac-kv__val">16:00</span>
                  </div>
                  <div className="ac-kv">
                    <span className="ac-kv__key">Update Window:</span>
                    <span className="ac-kv__val">15m</span>
                  </div>
                  <div className="ac-kv">
                    <span className="ac-kv__key">Start Date:</span>
                    <span className="ac-kv__val">May 20, 2025</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right — Sidebar */}
        <div className="ac-sidebar">
          {/* Risk & Controls */}
          <div className="ac-card">
            <h3 className="ac-card__title ac-card__title--sm">Risk &amp; Controls</h3>
            <table className="ac-risk-table">
              <thead>
                <tr>
                  <th>Control</th>
                  <th>Threshold</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {RISK_CONTROLS.map((rc) => (
                  <tr key={rc.control}>
                    <td>{rc.control}</td>
                    <td>{rc.threshold}</td>
                    <td><span className="ac-badge ac-badge--teal">Active</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button className="ac-edit-link">Edit Risk Settings ›</button>
          </div>

          {/* Pre-Launch Checklist */}
          <div className="ac-card">
            <div className="ac-checklist__head">
              <h3 className="ac-card__title ac-card__title--sm" style={{ margin: 0 }}>Pre-Launch Checklist</h3>
              <span className="ac-checklist__counter">6/6</span>
            </div>
            <div className="ac-checklist">
              {PRE_LAUNCH_ITEMS.map((item) => (
                <div key={item} className="ac-check-row">
                  <span className="ac-check-icon ac-check-icon--on">✓</span>
                  {item}
                </div>
              ))}
            </div>
          </div>

          {/* Approval Flow */}
          <div className="ac-card">
            <h3 className="ac-card__title ac-card__title--sm">Approval Flow</h3>
            <div className="ac-approval-steps">
              {APPROVAL_STEPS.map((step, i) => (
                <div key={step.name} className="ac-approval-step">
                  <span className={`ac-step-dot ${step.done ? 'ac-step-dot--done' : 'ac-step-dot--pending'}`}>
                    {step.done ? '✓' : i + 1}
                  </span>
                  <div className="ac-step-info">
                    <div className="ac-step-info__name">{step.name}</div>
                    <div className={`ac-step-info__status ${step.done ? 'ac-step-info__status--done' : 'ac-step-info__status--pending'}`}>
                      {step.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <p className="ac-plan-note">Plan will be activated in Paper Mode only.</p>
          </div>
        </div>
      </div>

      {/* ── Bottom — Paper Monitoring ───────────────────── */}
      <div className="ac-monitoring">
        <h2 className="ac-monitoring__title">Paper Monitoring (After Dry Test)</h2>
        <div className="ac-monitor-grid">
          {/* Copy Drift */}
          <div className="ac-monitor-card">
            <div className="ac-monitor-card__head">
              <span className="ac-monitor-card__label">Copy Drift (Est.)</span>
              <span className="ac-badge ac-badge--green">Good</span>
            </div>
            <div className="ac-monitor-card__value">0.48%</div>
            <MiniSparkline points={SPARKLINE_POINTS} />
          </div>

          {/* Pending Review */}
          <div className="ac-monitor-card">
            <div className="ac-monitor-card__head">
              <span className="ac-monitor-card__label">Pending Review</span>
              <span className="ac-badge ac-badge--red">3 Items</span>
            </div>
            <div className="ac-monitor-card__value">3 Items</div>
            <div className="ac-monitor-card__details">
              <div className="ac-monitor-card__detail">
                <span>New Positions:</span><span>2</span>
              </div>
              <div className="ac-monitor-card__detail">
                <span>Size Exceptions:</span><span>1</span>
              </div>
            </div>
            <button className="ac-view-link">View Items →</button>
          </div>

          {/* Breach Alerts */}
          <div className="ac-monitor-card">
            <div className="ac-monitor-card__head">
              <span className="ac-monitor-card__label">Breach Alerts</span>
              <span className="ac-badge ac-badge--green">0 Active</span>
            </div>
            <div className="ac-monitor-card__value">0 Active</div>
            <div className="ac-monitor-card__details">
              <div className="ac-monitor-card__detail">
                <span>Last 7 Days:</span><span>0</span>
              </div>
              <div className="ac-monitor-card__detail">
                <span>Last 30 Days:</span><span>0</span>
              </div>
            </div>
            <button className="ac-view-link">View Alerts →</button>
          </div>

          {/* Plan Health */}
          <div className="ac-monitor-card">
            <div className="ac-monitor-card__head">
              <span className="ac-monitor-card__label">Plan Health</span>
              <span className="ac-badge ac-badge--green">Healthy</span>
            </div>
            <div className="ac-donut-wrap">
              <MiniDonut pct={92} />
              <div className="ac-health-checks">
                <span className="ac-health-check"><span className="ac-health-check__icon">✓</span> Data Feeds</span>
                <span className="ac-health-check"><span className="ac-health-check__icon">✓</span> Risk Controls</span>
                <span className="ac-health-check"><span className="ac-health-check__icon">✓</span> Account Sync</span>
                <span className="ac-health-check"><span className="ac-health-check__icon">✓</span> Rule Engine</span>
              </div>
            </div>
            <button className="ac-view-link">View Diagnostics →</button>
          </div>
        </div>
      </div>
    </div>
  )
}
