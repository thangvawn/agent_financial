import React, { useState } from "react";

/* ── Static Data ─────────────────────────────────────────────── */

const RECENT_TRADES = [
  { date: "2025-05-14", ticker: "NVDA", side: "Buy", size: 4.2, price: 131.28, frn: 1.1, pnl: 1842, hold: "3d" },
  { date: "2025-05-13", ticker: "MSFT", side: "Sell", size: 3.8, price: 449.12, frn: 0.9, pnl: -624, hold: "7d" },
  { date: "2025-05-12", ticker: "AAPL", side: "Buy", size: 5.1, price: 198.56, frn: 1.3, pnl: 2105, hold: "5d" },
  { date: "2025-05-10", ticker: "GOOGL", side: "Sell", size: 2.9, price: 174.33, frn: 0.8, pnl: 967, hold: "4d" },
  { date: "2025-05-09", ticker: "AMZN", side: "Buy", size: 3.5, price: 186.74, frn: 1.2, pnl: -312, hold: "6d" },
  { date: "2025-05-07", ticker: "META", side: "Sell", size: 4.0, price: 512.08, frn: 1.0, pnl: 1478, hold: "8d" },
  { date: "2025-05-05", ticker: "TSLA", side: "Buy", size: 2.6, price: 178.92, frn: 1.5, pnl: -891, hold: "2d" },
];

const METRICS = [
  { label: "CAGR", value: "15.27%", spy: "10.16%", color: "#4fd1b4" },
  { label: "Sharpe Ratio", value: "1.38", spy: "0.92", color: "#c8d6d2" },
  { label: "Max Drawdown", value: "-18.42%", spy: "-33.74%", color: "#e85d75" },
  { label: "Win Rate", value: "58.6%", spy: "54.1%", color: "#c8d6d2" },
  { label: "Turnover Ann.", value: "92.4%", spy: "20.1%", color: "#c8d6d2" },
  { label: "Avg Net Exposure", value: "78.3%", spy: "97.5%", color: "#c8d6d2" },
];

const COST_SENSITIVITY = [
  { cost: 0, cagr: "16.12%", sharpe: "1.46" },
  { cost: 2.5, cagr: "15.27%", sharpe: "1.38", base: true },
  { cost: 5, cagr: "14.41%", sharpe: "1.30" },
  { cost: 10, cagr: "12.68%", sharpe: "1.14" },
  { cost: 20, cagr: "9.19%", sharpe: "0.82" },
];

const FAIL_CONDITIONS = [
  { label: "Max Drawdown Limit", value: "18.42%", pass: true },
  { label: "Consecutive Losses", value: "5", pass: true },
  { label: "Leverage Limit", value: "1.42x", pass: true },
  { label: "Liquidity Stress", value: "24%", pass: true },
];

const OOS_CHECKS = [
  { label: "OOS Period", value: "2023-01 → 2025-05" },
  { label: "OOS CAGR", value: "12.81%" },
  { label: "OOS Sharpe", value: "1.05" },
  { label: "OOS vs Benchmark", value: "+3.92%" },
  { label: "Rank vs Universe", value: "Top 18%" },
];

const VALIDATION_SUMMARY = [
  { check: "Overfit Risk", detail: "Low", status: "Pass" },
  { check: "Benchmark Gap", detail: "+3.92%", status: "Pass" },
  { check: "Capacity", detail: "$2.10M", status: "Watch" },
  { check: "Cost Sensitivity", detail: "Moderate", status: "Watch" },
];

const CAVEATS = [
  { caveat: "Survivorship Bias", impact: "Medium", confidence: 3, notes: "Universe re-constituted quarterly; delisted names excluded" },
  { caveat: "Look-Ahead Bias", impact: "Low", confidence: 4, notes: "All signals use point-in-time data with 1-day lag" },
  { caveat: "Regime Dependence", impact: "High", confidence: 2, notes: "Strategy underperforms in low-volatility grind-up regimes" },
  { caveat: "Liquidity Assumptions", impact: "Medium", confidence: 3, notes: "Slippage model assumes mid-cap+ liquidity profiles" },
  { caveat: "Benchmark Selection", impact: "Low", confidence: 4, notes: "SPY TR used; sector-neutral benchmark may differ" },
];

/* ── SVG Chart Helpers ───────────────────────────────────────── */

function CumulativeReturnChart() {
  const strategyPoints = [
    [0, 0], [60, 12], [120, 8], [180, 28], [240, 22], [300, 45],
    [360, 38], [420, 62], [480, 55], [540, 78], [600, 72], [660, 95],
    [720, 110], [780, 105], [840, 128], [900, 135], [960, 148],
    [1020, 158], [1080, 165], [1140, 172], [1200, 178.6],
  ];
  const benchmarkPoints = [
    [0, 0], [60, 8], [120, 5], [180, 18], [240, 14], [300, 30],
    [360, 25], [420, 42], [480, 38], [540, 52], [600, 48], [660, 60],
    [720, 68], [780, 55], [840, 72], [900, 78], [960, 85],
    [1020, 92], [1080, 98], [1140, 105], [1200, 112.4],
  ];

  const toPath = (pts) =>
    pts.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${200 - y}`).join(" ");

  return (
    <svg viewBox="0 0 1200 220" className="bv-chart-svg">
      {[0, 50, 100, 150, 200].map((y) => (
        <line key={y} x1="0" y1={200 - y} x2="1200" y2={200 - y} stroke="#1a2e28" strokeWidth="1" />
      ))}
      {[0, 200, 400, 600, 800, 1000, 1200].map((x) => (
        <line key={x} x1={x} y1="0" x2={x} y2="220" stroke="#1a2e28" strokeWidth="1" />
      ))}
      <path d={toPath(benchmarkPoints)} fill="none" stroke="#5e7a72" strokeWidth="2" opacity="0.7" />
      <path d={toPath(strategyPoints)} fill="none" stroke="#4fd1b4" strokeWidth="2.5" />
    </svg>
  );
}

function MonteCarloChart() {
  const bars = [
    2, 4, 7, 12, 18, 28, 42, 55, 65, 72, 78, 72, 65, 55, 42, 28, 18, 12, 7, 4, 2,
  ];
  const maxH = Math.max(...bars);
  const barW = 24;

  return (
    <svg viewBox="0 0 540 120" className="bv-chart-svg bv-chart-svg--sm">
      {bars.map((h, i) => {
        const norm = (h / maxH) * 100;
        const is5th = i === 3;
        const is95th = i === 17;
        const isMed = i === 10;
        return (
          <g key={i}>
            <rect
              x={i * (barW + 2)}
              y={110 - norm}
              width={barW}
              height={norm}
              rx="2"
              fill={isMed ? "#4fd1b4" : is5th || is95th ? "#e8b84d" : "#1e3a32"}
              opacity={isMed ? 1 : 0.7}
            />
            {(is5th || is95th || isMed) && (
              <text
                x={i * (barW + 2) + barW / 2}
                y={106 - norm}
                textAnchor="middle"
                fill="#c8d6d2"
                fontSize="8"
              >
                {is5th ? "5th" : is95th ? "95th" : "Med"}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

/* ── Dot Indicator ───────────────────────────────────────────── */

function ConfidenceDots({ level }) {
  return (
    <span className="bv-dots">
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={`bv-dot ${i <= level ? "bv-dot--filled" : ""}`}
        />
      ))}
    </span>
  );
}

/* ── Main Component ──────────────────────────────────────────── */

export default function BacktestValidationPage({ onBack }) {
  const [timePeriod, setTimePeriod] = useState("All");
  const [logScale, setLogScale] = useState(false);
  const [activeValidation, setActiveValidation] = useState(1);

  return (
    <div className="bv">
      <style>{STYLES}</style>

      {/* Header */}
      <header className="bv-header">
        <nav className="bv-breadcrumb">
          <button className="bv-breadcrumb__link" onClick={onBack}>
            Pro Lab
          </button>
          <span className="bv-breadcrumb__sep">›</span>
          <span className="bv-breadcrumb__current">Backtest & Validation</span>
        </nav>
        <div className="bv-header__row">
          <div>
            <h1 className="bv-header__title">Backtest Lab + Validation Lab</h1>
            <p className="bv-header__sub">
              Run robust backtests and validate edge across market regimes and assumptions.
            </p>
          </div>
          <div className="bv-header__actions">
            <button className="bv-btn bv-btn--primary">▶ Run Backtest</button>
            <button className="bv-btn bv-btn--outline">Queue Validation</button>
          </div>
        </div>
      </header>

      {/* Two-Column Layout */}
      <div className="bv-layout">
        {/* ── Left: Backtest Lab ──────────────────────────────── */}
        <section className="bv-col bv-col--left">
          <h2 className="bv-section-title">Backtest Lab</h2>

          {/* Config Bar */}
          <div className="bv-config">
            <div className="bv-config__item">
              <span className="bv-config__label">Date Range</span>
              <span className="bv-config__value">2018-01-01 → 2025-05-16</span>
            </div>
            <div className="bv-config__item">
              <span className="bv-config__label">Benchmark</span>
              <select className="bv-select">
                <option>SPY TR</option>
                <option>QQQ TR</option>
                <option>IWM TR</option>
              </select>
            </div>
            <div className="bv-config__item">
              <span className="bv-config__label">Slippage</span>
              <span className="bv-config__value">1.0 bps</span>
            </div>
            <div className="bv-config__item">
              <span className="bv-config__label">Txn Cost</span>
              <span className="bv-config__value">2.5 bps</span>
            </div>
            <div className="bv-config__item">
              <span className="bv-config__label">Rebalance</span>
              <span className="bv-config__value">Weekly</span>
            </div>
          </div>

          {/* Cumulative Return Chart */}
          <div className="bv-card">
            <div className="bv-card__head">
              <h3 className="bv-card__title">Cumulative Return</h3>
              <div className="bv-card__controls">
                <div className="bv-period-btns">
                  {["1Y", "3Y", "5Y", "All"].map((p) => (
                    <button
                      key={p}
                      className={`bv-period-btn ${timePeriod === p ? "bv-period-btn--active" : ""}`}
                      onClick={() => setTimePeriod(p)}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <label className="bv-toggle-label">
                  <input
                    type="checkbox"
                    checked={logScale}
                    onChange={(e) => setLogScale(e.target.checked)}
                    className="bv-toggle-input"
                  />
                  <span className="bv-toggle-text">Log Scale</span>
                </label>
                <button className="bv-icon-btn" title="Expand">⛶</button>
              </div>
            </div>
            <div className="bv-chart-wrap">
              <CumulativeReturnChart />
              <div className="bv-chart-legend">
                <span className="bv-legend-item">
                  <span className="bv-legend-dot" style={{ background: "#4fd1b4" }} />
                  Strategy 178.6%
                </span>
                <span className="bv-legend-item">
                  <span className="bv-legend-dot" style={{ background: "#5e7a72" }} />
                  Benchmark SPY 112.4%
                </span>
              </div>
            </div>
          </div>

          {/* Performance Overview */}
          <div className="bv-card">
            <h3 className="bv-card__title">Performance Overview</h3>
            <div className="bv-metrics-grid">
              {METRICS.map((m) => (
                <div key={m.label} className="bv-metric">
                  <span className="bv-metric__label">{m.label}</span>
                  <span className="bv-metric__value" style={{ color: m.color }}>
                    {m.value}
                  </span>
                  <span className="bv-metric__spy">SPY {m.spy}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Trades */}
          <div className="bv-card">
            <h3 className="bv-card__title">Recent Trades</h3>
            <div className="bv-table-wrap">
              <table className="bv-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Ticker</th>
                    <th>Side</th>
                    <th>Size%</th>
                    <th>Price</th>
                    <th>Frn(bps)</th>
                    <th>PnL($)</th>
                    <th>Hold</th>
                  </tr>
                </thead>
                <tbody>
                  {RECENT_TRADES.map((t, i) => (
                    <tr key={i}>
                      <td>{t.date}</td>
                      <td className="bv-mono">{t.ticker}</td>
                      <td>
                        <span className={`bv-side ${t.side === "Buy" ? "bv-side--buy" : "bv-side--sell"}`}>
                          {t.side}
                        </span>
                      </td>
                      <td>{t.size}%</td>
                      <td className="bv-mono">${t.price.toFixed(2)}</td>
                      <td>{t.frn}</td>
                      <td className={t.pnl >= 0 ? "bv-pnl--pos" : "bv-pnl--neg"}>
                        {t.pnl >= 0 ? "+" : ""}${t.pnl.toLocaleString()}
                      </td>
                      <td>{t.hold}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* ── Right: Validation Lab ───────────────────────────── */}
        <section className="bv-col bv-col--right">
          <h2 className="bv-section-title">Validation Lab</h2>

          {/* Validation Tabs */}
          <div className="bv-vtabs">
            {[
              { id: 1, label: "Walk-Forward" },
              { id: 2, label: "Monte Carlo" },
              { id: 3, label: "Cost Sensitivity" },
            ].map((tab) => (
              <button
                key={tab.id}
                className={`bv-vtab ${activeValidation === tab.id ? "bv-vtab--active" : ""}`}
                onClick={() => setActiveValidation(tab.id)}
              >
                <span className="bv-vtab__num">{tab.id}</span>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Walk-Forward */}
          {activeValidation === 1 && (
            <div className="bv-card">
              <div className="bv-card__head">
                <h3 className="bv-card__title">Walk-Forward Analysis</h3>
                <span className="bv-badge bv-badge--pass">Pass</span>
              </div>
              <div className="bv-wf-grid">
                <div className="bv-wf-item">
                  <span className="bv-wf-item__label">Windows</span>
                  <span className="bv-wf-item__value">24</span>
                </div>
                <div className="bv-wf-item">
                  <span className="bv-wf-item__label">Avg OOS Sharpe</span>
                  <span className="bv-wf-item__value">1.12</span>
                </div>
                <div className="bv-wf-item">
                  <span className="bv-wf-item__label">Hit Rate</span>
                  <span className="bv-wf-item__value">66.7%</span>
                </div>
                <div className="bv-wf-item">
                  <span className="bv-wf-item__label">Stability</span>
                  <span className="bv-wf-item__value">
                    <span className="bv-badge bv-badge--good">Good</span>
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Monte Carlo */}
          {activeValidation === 2 && (
            <div className="bv-card">
              <div className="bv-card__head">
                <h3 className="bv-card__title">Monte Carlo Simulation</h3>
                <span className="bv-badge bv-badge--pass">Pass</span>
              </div>
              <div className="bv-mc-grid">
                <div className="bv-wf-item">
                  <span className="bv-wf-item__label">Median CAGR</span>
                  <span className="bv-wf-item__value">15.0%</span>
                </div>
                <div className="bv-wf-item">
                  <span className="bv-wf-item__label">5th–95th %ile</span>
                  <span className="bv-wf-item__value">6.6% – 24.9%</span>
                </div>
                <div className="bv-wf-item">
                  <span className="bv-wf-item__label">Prob &gt;0% CAGR</span>
                  <span className="bv-wf-item__value bv-wf-item__value--green">94.2%</span>
                </div>
                <div className="bv-wf-item">
                  <span className="bv-wf-item__label">Prob &gt; Benchmark</span>
                  <span className="bv-wf-item__value bv-wf-item__value--green">81.3%</span>
                </div>
              </div>
              <div className="bv-mc-chart">
                <MonteCarloChart />
              </div>
            </div>
          )}

          {/* Cost Sensitivity */}
          {activeValidation === 3 && (
            <div className="bv-card">
              <h3 className="bv-card__title">Transaction Cost Sensitivity</h3>
              <div className="bv-table-wrap">
                <table className="bv-table bv-table--compact">
                  <thead>
                    <tr>
                      <th>Cost (bps)</th>
                      <th>CAGR</th>
                      <th>Sharpe</th>
                    </tr>
                  </thead>
                  <tbody>
                    {COST_SENSITIVITY.map((row) => (
                      <tr key={row.cost} className={row.base ? "bv-row--highlight" : ""}>
                        <td>{row.cost}{row.base && <span className="bv-tag-base">Base</span>}</td>
                        <td>{row.cagr}</td>
                        <td>{row.sharpe}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Fail Conditions */}
          <div className="bv-card">
            <h3 className="bv-card__title">Fail Conditions</h3>
            <div className="bv-fail-grid">
              {FAIL_CONDITIONS.map((fc) => (
                <div key={fc.label} className="bv-fail-item">
                  <span className="bv-fail-item__icon">{fc.pass ? "✓" : "✗"}</span>
                  <div className="bv-fail-item__body">
                    <span className="bv-fail-item__label">{fc.label}</span>
                    <span className="bv-fail-item__value">{fc.value}</span>
                  </div>
                  <span className={`bv-badge ${fc.pass ? "bv-badge--pass" : "bv-badge--fail"}`}>
                    {fc.pass ? "Pass" : "Fail"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* OOS Checks */}
          <div className="bv-card">
            <h3 className="bv-card__title">Out-of-Sample Checks</h3>
            <div className="bv-oos-grid">
              {OOS_CHECKS.map((oos) => (
                <div key={oos.label} className="bv-oos-item">
                  <span className="bv-oos-item__label">{oos.label}</span>
                  <span className="bv-oos-item__value">{oos.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Validation Summary */}
          <div className="bv-card bv-card--summary">
            <div className="bv-summary-hero">
              <span className="bv-summary-badge">✓ PASS</span>
              <p className="bv-summary-text">
                Strategy passes all critical validation checks. Two items flagged for monitoring.
              </p>
            </div>
            <div className="bv-table-wrap">
              <table className="bv-table bv-table--compact">
                <thead>
                  <tr>
                    <th>Check</th>
                    <th>Detail</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {VALIDATION_SUMMARY.map((row) => (
                    <tr key={row.check}>
                      <td>{row.check}</td>
                      <td>{row.detail}</td>
                      <td>
                        <span className={`bv-badge ${row.status === "Pass" ? "bv-badge--pass" : "bv-badge--watch"}`}>
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Validation Caveats */}
          <div className="bv-card">
            <h3 className="bv-card__title">Validation Caveats</h3>
            <div className="bv-table-wrap">
              <table className="bv-table bv-table--compact">
                <thead>
                  <tr>
                    <th>Caveat</th>
                    <th>Impact</th>
                    <th>Confidence</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {CAVEATS.map((c) => (
                    <tr key={c.caveat}>
                      <td className="bv-mono">{c.caveat}</td>
                      <td>
                        <span className={`bv-impact bv-impact--${c.impact.toLowerCase()}`}>
                          {c.impact}
                        </span>
                      </td>
                      <td><ConfidenceDots level={c.confidence} /></td>
                      <td className="bv-notes">{c.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

/* ── Styles ────────────────────────────────────────────────────── */

const STYLES = `
/* ── Base ─────────────────────────────────────────────────── */
.bv {
  display: grid;
  gap: 1.25rem;
  min-height: 100vh;
  padding: clamp(1.2rem, 2.5vw, 2rem) clamp(1rem, 2vw, 1.6rem);
  color: #c8d6d2;
  background:
    radial-gradient(ellipse at 15% 0%, rgba(16, 70, 60, 0.3), transparent 55%),
    radial-gradient(ellipse at 85% 100%, rgba(8, 35, 45, 0.25), transparent 55%),
    #091210;
  font-family: "Avenir Next", "Inter", system-ui, sans-serif;
}

.bv > * {
  width: min(1800px, 100%);
  margin-inline: auto;
}

/* ── Header ───────────────────────────────────────────────── */
.bv-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bv-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
}

.bv-breadcrumb__link {
  background: none;
  border: none;
  color: #4fd1b4;
  cursor: pointer;
  font-size: inherit;
  padding: 0;
}
.bv-breadcrumb__link:hover { text-decoration: underline; }

.bv-breadcrumb__sep { color: #3a5a50; }
.bv-breadcrumb__current { color: #5e7a72; }

.bv-header__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.bv-header__title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 800;
  color: #ecf4f0;
  letter-spacing: -0.03em;
  line-height: 1.15;
}

.bv-header__sub {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: #5e7a72;
  line-height: 1.5;
}

.bv-header__actions {
  display: flex;
  gap: 0.6rem;
  flex-shrink: 0;
  padding-top: 0.2rem;
}

/* ── Buttons ──────────────────────────────────────────────── */
.bv-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1.2rem;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: all 180ms ease;
}

.bv-btn--primary {
  background: #22c55e;
  color: #091210;
}
.bv-btn--primary:hover { background: #16a34a; }

.bv-btn--outline {
  background: transparent;
  color: #c8d6d2;
  border: 1.5px solid #2a3f3a;
}
.bv-btn--outline:hover {
  border-color: #4fd1b4;
  color: #4fd1b4;
}

/* ── Layout ───────────────────────────────────────────────── */
.bv-layout {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 1.5rem;
  align-items: start;
}

.bv-section-title {
  margin: 0 0 0.75rem;
  font-size: 1.05rem;
  font-weight: 800;
  color: #ecf4f0;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

/* ── Config Bar ───────────────────────────────────────────── */
.bv-config {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.65rem 0.85rem;
  background: rgba(16, 50, 42, 0.4);
  border: 1px solid #1a2e28;
  border-radius: 10px;
  margin-bottom: 0.75rem;
}

.bv-config__item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.76rem;
}

.bv-config__label {
  color: #5e7a72;
  font-weight: 600;
}

.bv-config__value {
  color: #c8d6d2;
  font-weight: 500;
}

.bv-select {
  background: #0d1a16;
  border: 1px solid #1a2e28;
  color: #c8d6d2;
  border-radius: 5px;
  padding: 0.2rem 0.5rem;
  font-size: 0.76rem;
}

/* ── Cards ────────────────────────────────────────────────── */
.bv-card {
  background: rgba(12, 30, 24, 0.6);
  border: 1px solid #1a2e28;
  border-radius: 12px;
  padding: 1rem 1.1rem;
  margin-bottom: 0.75rem;
}

.bv-card--summary {
  border-color: rgba(79, 209, 180, 0.25);
  background: rgba(16, 50, 42, 0.35);
}

.bv-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.7rem;
}

.bv-card__title {
  margin: 0 0 0.5rem;
  font-size: 0.88rem;
  font-weight: 700;
  color: #ecf4f0;
}

.bv-card__head .bv-card__title { margin-bottom: 0; }

.bv-card__controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* ── Period Buttons ───────────────────────────────────────── */
.bv-period-btns {
  display: flex;
  gap: 2px;
  background: #0d1a16;
  border-radius: 6px;
  padding: 2px;
}

.bv-period-btn {
  padding: 0.2rem 0.6rem;
  border: none;
  border-radius: 5px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #5e7a72;
  background: transparent;
  cursor: pointer;
  transition: all 150ms ease;
}

.bv-period-btn--active {
  background: #1a2e28;
  color: #4fd1b4;
}

/* ── Toggle ───────────────────────────────────────────────── */
.bv-toggle-label {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  color: #5e7a72;
  cursor: pointer;
}

.bv-toggle-input {
  accent-color: #4fd1b4;
  width: 14px;
  height: 14px;
}

/* ── Icon Button ──────────────────────────────────────────── */
.bv-icon-btn {
  background: none;
  border: 1px solid #1a2e28;
  color: #5e7a72;
  border-radius: 6px;
  padding: 0.2rem 0.4rem;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 150ms ease;
}
.bv-icon-btn:hover { color: #4fd1b4; border-color: #4fd1b4; }

/* ── Chart ────────────────────────────────────────────────── */
.bv-chart-wrap {
  position: relative;
}

.bv-chart-svg {
  width: 100%;
  height: 180px;
  display: block;
}

.bv-chart-svg--sm {
  height: 100px;
}

.bv-chart-legend {
  display: flex;
  gap: 1.2rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
}

.bv-legend-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: #c8d6d2;
}

.bv-legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

/* ── Metrics Grid ─────────────────────────────────────────── */
.bv-metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.5rem;
}

.bv-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0.6rem 0.4rem;
  background: rgba(16, 50, 42, 0.35);
  border: 1px solid #1a2e28;
  border-radius: 8px;
}

.bv-metric__label {
  font-size: 0.68rem;
  font-weight: 600;
  color: #5e7a72;
  margin-bottom: 0.3rem;
}

.bv-metric__value {
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.bv-metric__spy {
  font-size: 0.66rem;
  color: #4a665e;
  margin-top: 0.15rem;
}

/* ── Tables ───────────────────────────────────────────────── */
.bv-table-wrap {
  overflow-x: auto;
}

.bv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

.bv-table th {
  text-align: left;
  padding: 0.5rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 700;
  color: #5e7a72;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid #1a2e28;
  white-space: nowrap;
}

.bv-table td {
  padding: 0.45rem 0.6rem;
  border-bottom: 1px solid rgba(26, 46, 40, 0.5);
  color: #c8d6d2;
  white-space: nowrap;
}

.bv-table--compact td,
.bv-table--compact th {
  padding: 0.35rem 0.5rem;
}

.bv-table tbody tr:hover {
  background: rgba(79, 209, 180, 0.04);
}

.bv-mono {
  font-family: "SF Mono", "Fira Code", monospace;
  font-weight: 500;
}

.bv-side {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 700;
}

.bv-side--buy {
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}

.bv-side--sell {
  background: rgba(232, 93, 117, 0.12);
  color: #e85d75;
}

.bv-pnl--pos { color: #22c55e; font-weight: 600; }
.bv-pnl--neg { color: #e85d75; font-weight: 600; }

.bv-row--highlight {
  background: rgba(79, 209, 180, 0.08) !important;
}

.bv-tag-base {
  display: inline-block;
  margin-left: 0.4rem;
  padding: 0.05rem 0.35rem;
  border-radius: 4px;
  font-size: 0.64rem;
  font-weight: 700;
  background: rgba(79, 209, 180, 0.15);
  color: #4fd1b4;
}

/* ── Validation Tabs ──────────────────────────────────────── */
.bv-vtabs {
  display: flex;
  gap: 0.35rem;
  margin-bottom: 0.75rem;
}

.bv-vtab {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.9rem;
  border-radius: 8px;
  border: 1px solid #1a2e28;
  background: transparent;
  color: #5e7a72;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 180ms ease;
}

.bv-vtab--active {
  background: rgba(79, 209, 180, 0.1);
  border-color: rgba(79, 209, 180, 0.3);
  color: #4fd1b4;
}

.bv-vtab__num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(79, 209, 180, 0.12);
  color: #4fd1b4;
  font-size: 0.68rem;
  font-weight: 800;
}

.bv-vtab--active .bv-vtab__num {
  background: #4fd1b4;
  color: #091210;
}

/* ── Walk-Forward / Monte Carlo Grid ──────────────────────── */
.bv-wf-grid,
.bv-mc-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.bv-wf-item {
  display: flex;
  flex-direction: column;
  padding: 0.55rem 0.7rem;
  background: rgba(16, 50, 42, 0.35);
  border: 1px solid #1a2e28;
  border-radius: 8px;
}

.bv-wf-item__label {
  font-size: 0.68rem;
  font-weight: 600;
  color: #5e7a72;
  margin-bottom: 0.2rem;
}

.bv-wf-item__value {
  font-size: 1.05rem;
  font-weight: 700;
  color: #ecf4f0;
}

.bv-wf-item__value--green { color: #4fd1b4; }

.bv-mc-chart {
  margin-top: 0.6rem;
  padding: 0.5rem;
  background: rgba(16, 50, 42, 0.2);
  border-radius: 8px;
}

/* ── Fail Conditions ──────────────────────────────────────── */
.bv-fail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.bv-fail-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.7rem;
  background: rgba(16, 50, 42, 0.3);
  border: 1px solid #1a2e28;
  border-radius: 8px;
}

.bv-fail-item__icon {
  font-size: 1rem;
  color: #22c55e;
  flex-shrink: 0;
}

.bv-fail-item__body {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.bv-fail-item__label {
  font-size: 0.7rem;
  color: #5e7a72;
  font-weight: 600;
}

.bv-fail-item__value {
  font-size: 0.88rem;
  color: #ecf4f0;
  font-weight: 700;
}

/* ── OOS Checks ───────────────────────────────────────────── */
.bv-oos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.5rem;
}

.bv-oos-item {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.65rem;
  background: rgba(16, 50, 42, 0.35);
  border: 1px solid #1a2e28;
  border-radius: 8px;
}

.bv-oos-item__label {
  font-size: 0.68rem;
  color: #5e7a72;
  font-weight: 600;
  margin-bottom: 0.15rem;
}

.bv-oos-item__value {
  font-size: 0.92rem;
  color: #ecf4f0;
  font-weight: 700;
}

/* ── Badges ───────────────────────────────────────────────── */
.bv-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.bv-badge--pass {
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}

.bv-badge--fail {
  background: rgba(232, 93, 117, 0.12);
  color: #e85d75;
}

.bv-badge--watch {
  background: rgba(232, 184, 77, 0.12);
  color: #e8b84d;
}

.bv-badge--good {
  background: rgba(79, 209, 180, 0.12);
  color: #4fd1b4;
}

/* ── Summary Hero ─────────────────────────────────────────── */
.bv-summary-hero {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.8rem;
  padding: 0.75rem;
  background: rgba(34, 197, 94, 0.06);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 10px;
}

.bv-summary-badge {
  font-size: 1.5rem;
  font-weight: 900;
  color: #22c55e;
  flex-shrink: 0;
  letter-spacing: 0.02em;
}

.bv-summary-text {
  margin: 0;
  font-size: 0.82rem;
  color: #c8d6d2;
  line-height: 1.5;
}

/* ── Impact Tags ──────────────────────────────────────────── */
.bv-impact {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 700;
}

.bv-impact--high {
  background: rgba(232, 93, 117, 0.12);
  color: #e85d75;
}

.bv-impact--medium {
  background: rgba(232, 184, 77, 0.12);
  color: #e8b84d;
}

.bv-impact--low {
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}

/* ── Confidence Dots ──────────────────────────────────────── */
.bv-dots {
  display: inline-flex;
  gap: 3px;
}

.bv-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1a2e28;
  display: inline-block;
}

.bv-dot--filled {
  background: #4fd1b4;
}

/* ── Notes Column ─────────────────────────────────────────── */
.bv-notes {
  white-space: normal !important;
  max-width: 260px;
  font-size: 0.74rem;
  line-height: 1.4;
  color: #8a9e98;
}

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 1100px) {
  .bv-layout {
    grid-template-columns: 1fr;
  }
  .bv-metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .bv-metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .bv-fail-grid {
    grid-template-columns: 1fr;
  }
  .bv-header__row {
    flex-direction: column;
  }
}
`;
