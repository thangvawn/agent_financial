import { useEffect, useState } from 'react'
import { aiHealth, aiSwarmCommittee } from '../../modules/pro-lab'

const EXPERTS = [
  {
    id: 'strategist',
    role: 'Strategist',
    title: 'Market Structure Expert',
    icon: '♟',
    stance: 'Positive',
    stanceColor: '#34d399',
    confidence: 82,
    vote: 'approve',
    bullets: [
      'Quality-momentum blend is well-suited for current macro regime with rotating sector leadership.',
      'Global large/mid cap universe provides sufficient liquidity depth for institutional-scale execution.',
      'Monthly rebalance cadence balances signal decay against transaction cost drag effectively.',
    ],
  },
  {
    id: 'quant',
    role: 'Quant',
    title: 'Model & Signal Expert',
    icon: '∑',
    stance: 'Cautious',
    stanceColor: '#fbbf24',
    confidence: 68,
    vote: 'revise',
    bullets: [
      'Factor crowding risk in quality-momentum space has increased 23% YoY — consider orthogonalization.',
      'Recommend adding decay-weighted momentum (6/12 blend) instead of pure 12M momentum lookback.',
      'Sharpe target may overfit to recent low-vol regime. Suggest Sortino or Calmar as secondary objective.',
    ],
  },
  {
    id: 'risk',
    role: 'Risk',
    title: 'Risk & Compliance Expert',
    icon: '⛨',
    stance: 'Cautious',
    stanceColor: '#fbbf24',
    confidence: 71,
    vote: 'revise',
    bullets: [
      'Sector exclusions (financials, commodities) create unintended beta tilt — hedge or document residual.',
      'Max drawdown constraint missing. Recommend ≤15% from peak to align with institutional mandates.',
      'Currency exposure unhedged across 24 markets. FX vol could contribute 30%+ of total portfolio risk.',
    ],
  },
  {
    id: 'execution',
    role: 'Execution',
    title: 'Trading & Implementation Expert',
    icon: '⚡',
    stance: 'Positive',
    stanceColor: '#34d399',
    confidence: 79,
    vote: 'approve',
    bullets: [
      'Monthly rebalance with 6,412-asset universe is executable within 2-day trading window at target AUM.',
      'Estimated implementation shortfall: 8–12 bps per rebalance, within acceptable range for strategy alpha.',
      'Recommend pre-trade compliance checks for ADV limits in emerging market mid-cap names.',
    ],
  },
]

const VERDICT_METRICS = [
  {
    label: 'Overfit Risk',
    value: 'Moderate',
    color: '#fbbf24',
    sub: 'Risk Score: 44/100',
    spark: [30, 38, 42, 44, 41, 44],
  },
  {
    label: 'Liquidity Check',
    value: 'Good',
    color: '#34d399',
    sub: 'Avg ADV: $12.4M',
    spark: [60, 65, 70, 72, 68, 74],
  },
  {
    label: 'Benchmark Gap',
    value: 'Favorable',
    color: '#34d399',
    sub: 'Tracking Error: 3.2%',
    spark: [20, 24, 28, 32, 30, 32],
  },
  {
    label: 'Cost Impact',
    value: 'Manageable',
    color: '#60a5fa',
    sub: 'Est. Drag: 18 bps/yr',
    spark: [10, 14, 16, 18, 17, 18],
  },
  {
    label: 'Final Recommendation',
    value: 'Approve for Validation',
    color: '#34d399',
    sub: 'Committee Score: 75/100',
    spark: [55, 62, 68, 72, 74, 75],
  },
]

function MiniSparkline({ data, color }) {
  if (!data || data.length < 2) return null
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const h = 20
  const w = 48
  const step = w / (data.length - 1)
  const points = data.map((v, i) => `${i * step},${h - ((v - min) / range) * h}`).join(' ')
  return (
    <svg width={w} height={h} className="bs-spark" viewBox={`0 0 ${w} ${h}`}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  )
}

function ConfidenceBar({ value, color }) {
  return (
    <div className="bs-conf">
      <div className="bs-conf__track">
        <div className="bs-conf__fill" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="bs-conf__label" style={{ color }}>{value}%</span>
    </div>
  )
}

const ROLE_ICONS = {
  'Bull Researcher': '♟',
  'Bear Risk Analyst': '⛨',
  'Quant Engineer': '∑',
  'Portfolio Manager': '⚡',
}

const STANCE_COLOR = {
  supportive: '#10b981',
  cautious: '#f59e0b',
  opposed: '#ef4444',
}

export default function BlueprintSwarmPage({ onBack }) {
  const [strategyName, setStrategyName] = useState('Global Quality Momentum (GQM)')
  const [objective] = useState('sharpe')
  const [notes, setNotes] = useState('Long-only quality + momentum trên VN30. Exit khi RSI > 80 hoặc drawdown > 10%. Rebalance hàng tháng, max 30 mã.')
  const [aiResult, setAiResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [health, setHealth] = useState(null)

  useEffect(() => {
    aiHealth().then(setHealth).catch(() => setHealth({ openai_configured: false }))
  }, [])

  async function runCommittee() {
    if (!notes.trim()) {
      setError('Nhập strategy brief để committee review.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await aiSwarmCommittee({
        strategy_brief: `Strategy name: ${strategyName}\n\nObjective: ${objective}\n\nDetail: ${notes}`,
        review_focus: 'overfit, liquidity, benchmark gap, execution assumptions, FX exposure',
        market: 'Vietnam equities',
      })
      setAiResult(result)
    } catch (err) {
      setError(err.message || 'Lỗi gọi OpenAI')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bs-page">
      {/* ── Header ──────────────────────────────────────────── */}
      <header className="bs-header">
        <nav className="bs-breadcrumb">
          <button type="button" className="bs-breadcrumb__link" onClick={onBack}>Pro Lab</button>
          <span className="bs-breadcrumb__sep">›</span>
          <span className="bs-breadcrumb__link">Swarm Committee</span>
          <span className="bs-breadcrumb__sep">›</span>
          <span className="bs-breadcrumb__current">Blueprint Designer</span>
        </nav>
        <div className="bs-header__actions">
          <button type="button" className="bs-btn bs-btn--primary">Save Blueprint</button>
          <button type="button" className="bs-btn bs-btn--outline">Export Blueprint</button>
          <span className="bs-version-badge">
            {health?.openai_configured ? `Live · ${health.model}` : 'OpenAI offline'}
          </span>
        </div>
      </header>

      {/* ── Two-column body ─────────────────────────────────── */}
      <div className="bs-body">
        {/* LEFT — Blueprint Designer */}
        <section className="bs-card bs-designer">
          <div className="bs-section-head">
            <span className="bs-section-icon">✦</span>
            <div>
              <h2 className="bs-section-title">Blueprint Designer</h2>
              <p className="bs-section-sub">Design and configure your strategy using no-code blocks.</p>
            </div>
          </div>

          <div className="bs-form">
            <label className="bs-field">
              <span className="bs-field__label">Strategy Name</span>
              <div className="bs-field__wrap">
                <input
                  className="bs-input"
                  type="text"
                  maxLength={80}
                  value={strategyName}
                  onChange={(e) => setStrategyName(e.target.value)}
                />
                <span className="bs-field__count">{strategyName.length}/80</span>
              </div>
            </label>

            <label className="bs-field">
              <span className="bs-field__label">Objective</span>
              <div className="bs-field__wrap">
                <select className="bs-select" defaultValue={objective}>
                  <option value="sharpe">Maximize risk-adjusted returns (Sharpe)</option>
                  <option value="sortino">Maximize downside-adjusted returns (Sortino)</option>
                  <option value="cagr">Maximize CAGR</option>
                </select>
              </div>
            </label>

            <div className="bs-field">
              <span className="bs-field__label">Asset Universe</span>
              <div className="bs-field__wrap bs-field__wrap--row">
                <span className="bs-input bs-input--readonly">Global Equities (Large &amp; Mid Cap)</span>
                <span className="bs-pill">6,412 assets</span>
              </div>
            </div>

            <label className="bs-field">
              <span className="bs-field__label">Benchmark</span>
              <div className="bs-field__wrap">
                <select className="bs-select" defaultValue="msci-acwi">
                  <option value="msci-acwi">MSCI ACWI Net Total Return</option>
                  <option value="sp500">S&amp;P 500 Total Return</option>
                  <option value="ftse">FTSE All-World</option>
                </select>
              </div>
            </label>

            <label className="bs-field">
              <span className="bs-field__label">Rebalance Frequency</span>
              <div className="bs-field__wrap">
                <select className="bs-select" defaultValue="monthly">
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                </select>
              </div>
            </label>

            <div className="bs-field">
              <span className="bs-field__label">Risk Constraints</span>
              <button type="button" className="bs-expand-row">
                <span>4 Constraints</span>
                <span className="bs-expand-arrow">▸</span>
              </button>
            </div>

            <div className="bs-field">
              <span className="bs-field__label">Assumptions</span>
              <button type="button" className="bs-expand-row">
                <span>3 Assumptions</span>
                <span className="bs-expand-arrow">▸</span>
              </button>
            </div>

            <label className="bs-field">
              <span className="bs-field__label">Notes</span>
              <div className="bs-field__wrap">
                <textarea
                  className="bs-textarea"
                  maxLength={500}
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
                <span className="bs-field__count">{notes.length}/500</span>
              </div>
            </label>
          </div>

          <footer className="bs-designer-footer">
            <span>Blueprint ID: BP-2025-05-16-0013</span>
            <span className="bs-designer-footer__sep">|</span>
            <button type="button" className="bs-link-btn">Duplicate</button>
            <span className="bs-designer-footer__sep">|</span>
            <span>Last saved: May 16, 2025 10:22 AM</span>
            <span className="bs-designer-footer__sep">|</span>
            <span className="bs-saved-check">Saved ✓</span>
          </footer>
        </section>

        {/* RIGHT — Swarm Committee */}
        <section className="bs-card bs-swarm">
          <div className="bs-section-head">
            <div>
              <h2 className="bs-section-title">Swarm Committee</h2>
              <p className="bs-section-sub">
                {aiResult ? 'Multi-agent experts đã hoàn thành review.' : 'Bấm "Run Committee" để OpenAI mô phỏng investment committee debate.'}
              </p>
            </div>
            <button
              type="button"
              className="bs-btn bs-btn--primary bs-btn--sm"
              onClick={runCommittee}
              disabled={loading || !health?.openai_configured}
            >
              {loading ? 'Đang debate…' : aiResult ? 'Re-run Committee' : 'Run Committee'}
            </button>
          </div>

          {error && (
            <div className="bs-error-bar">{error}</div>
          )}

          {!aiResult && !loading && (
            <div className="bs-empty">
              <span className="bs-empty__icon">⌥</span>
              <p>Committee chưa chạy. Khi bấm Run, AI sẽ mô phỏng 4 vai trò debate (Bull · Bear · Quant · PM) và đưa ra final call.</p>
            </div>
          )}

          {loading && (
            <div className="bs-loading">
              <div className="bs-loading__bar"><span /></div>
              <p>Bull, Bear, Quant và PM đang debate strategy của bạn…</p>
            </div>
          )}

          {aiResult && (
            <div className="bs-experts-grid">
              {aiResult.memos.map((memo, idx) => {
                const stanceKey = memo.stance.toLowerCase()
                const color = STANCE_COLOR[stanceKey] || '#6366f1'
                return (
                  <article key={idx} className="bs-expert-card">
                    <div className="bs-expert-head">
                      <span className="bs-expert-icon">{ROLE_ICONS[memo.role] || '◯'}</span>
                      <div>
                        <h3 className="bs-expert-role">{memo.role}</h3>
                        <p className="bs-expert-title">{memo.stance}</p>
                      </div>
                      <span className="bs-stance" style={{ color, borderColor: color }}>
                        {memo.stance}
                      </span>
                    </div>
                    <p className="bs-expert-memo">{memo.memo}</p>
                    {memo.key_concerns.length > 0 && (
                      <ul className="bs-expert-bullets">
                        {memo.key_concerns.map((c, i) => <li key={i}>{c}</li>)}
                      </ul>
                    )}
                  </article>
                )
              })}
            </div>
          )}
        </section>
      </div>

      {/* ── Bottom — Committee Verdict ──────────────────────── */}
      {aiResult && (
        <section className="bs-card bs-verdict">
          <h2 className="bs-section-title">Committee Verdict — AI synthesis</h2>

          <div className="bs-verdict-grid">
            <article className="bs-metric-card">
              <span className="bs-metric-label">Consensus</span>
              <span className="bs-metric-value" style={{ color: aiResult.consensus === 'buy' ? '#10b981' : aiResult.consensus === 'reject_or_revise' ? '#ef4444' : '#f59e0b' }}>
                {aiResult.consensus}
              </span>
              <span className="bs-metric-sub">Confidence: {aiResult.confidence}</span>
            </article>
            <article className="bs-metric-card" style={{ gridColumn: 'span 2' }}>
              <span className="bs-metric-label">PM Decision Summary</span>
              <p style={{ margin: '6px 0 0', fontSize: '0.92rem', lineHeight: 1.6 }}>{aiResult.decision_summary}</p>
            </article>
          </div>

          <div className="bs-next-step">
            <strong>Recommended Next Steps:</strong>
            <ol style={{ margin: '8px 0 0', paddingLeft: 22, lineHeight: 1.7 }}>
              {aiResult.next_actions.map((a, i) => <li key={i}>{a}</li>)}
            </ol>
          </div>

          <div className="bs-verdict-actions">
            <button type="button" className="bs-btn bs-btn--outline" onClick={runCommittee}>Run Committee Again</button>
            <button type="button" className="bs-btn bs-btn--primary">Send to Backtest</button>
          </div>
        </section>
      )}

      <style>{`
        /* ═══════════════════════════════════════════════════════
           Blueprint + Swarm — bs- prefix (LIGHT sparkle theme)
           ═══════════════════════════════════════════════════════ */

        .bs-page {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
          min-height: 100vh;
          padding: clamp(1.2rem, 2.5vw, 2rem) clamp(1rem, 2vw, 1.6rem);
          color: #252b3b;
          background: #ffffff;
          font-family: Montserrat, Inter, system-ui, sans-serif;
        }

        .bs-empty,
        .bs-loading {
          display: grid;
          place-items: center;
          gap: 12px;
          padding: 40px 24px;
          text-align: center;
          color: rgba(37, 43, 59, 0.55);
        }

        .bs-empty__icon {
          font-size: 2.2rem;
          opacity: 0.5;
        }

        .bs-empty p,
        .bs-loading p {
          margin: 0;
          font-size: 0.92rem;
          max-width: 440px;
        }

        .bs-loading__bar {
          width: 100%;
          max-width: 320px;
          height: 6px;
          border-radius: 999px;
          background: rgba(37, 43, 59, 0.08);
          overflow: hidden;
        }

        .bs-loading__bar span {
          display: block;
          height: 100%;
          width: 30%;
          border-radius: inherit;
          background: linear-gradient(90deg, #3b82f6, #6366f1);
          animation: bs-loading-slide 1.4s ease-in-out infinite;
        }

        @keyframes bs-loading-slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(330%); }
        }

        .bs-error-bar {
          padding: 10px 14px;
          border-radius: 8px;
          background: rgba(220, 38, 38, 0.06);
          border: 1px solid rgba(220, 38, 38, 0.18);
          color: #b91c1c;
          font-size: 0.86rem;
          font-weight: 600;
        }

        .bs-expert-memo {
          margin: 8px 0 12px;
          padding: 12px;
          background: #f8fbff;
          border-radius: 8px;
          font-size: 0.88rem;
          line-height: 1.55;
          color: #252b3b;
          border-left: 3px solid #3b82f6;
        }

        /* ── Header ─────────────────────────────────────────── */
        .bs-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 0.75rem;
          max-width: 1720px;
          margin-inline: auto;
          width: 100%;
        }

        .bs-breadcrumb {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.85rem;
          color: #7a9b92;
        }

        .bs-breadcrumb__link {
          background: none;
          border: none;
          color: #7a9b92;
          cursor: pointer;
          font: inherit;
          padding: 0;
          transition: color .15s;
        }

        .bs-breadcrumb__link:hover { color: #4fd1b4; }
        .bs-breadcrumb__sep { opacity: .45; }
        .bs-breadcrumb__current { color: #dceae5; font-weight: 600; }

        .bs-header__actions {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .bs-version-badge {
          font-size: 0.75rem;
          color: #7a9b92;
          border: 1px solid rgba(79,209,180,.12);
          border-radius: 6px;
          padding: 0.25rem 0.65rem;
          white-space: nowrap;
        }

        /* ── Buttons ────────────────────────────────────────── */
        .bs-btn {
          font: inherit;
          font-size: 0.82rem;
          font-weight: 600;
          padding: 0.45rem 1rem;
          border-radius: 7px;
          border: 1px solid transparent;
          cursor: pointer;
          transition: background .15s, border-color .15s, opacity .15s;
          white-space: nowrap;
        }

        .bs-btn--primary {
          background: #4fd1b4;
          color: #091210;
        }

        .bs-btn--primary:hover { background: #38bfa2; }

        .bs-btn--outline {
          background: transparent;
          border-color: rgba(79,209,180,.25);
          color: #4fd1b4;
        }

        .bs-btn--outline:hover { border-color: #4fd1b4; background: rgba(79,209,180,.06); }

        .bs-btn--sm { padding: 0.3rem 0.75rem; font-size: 0.78rem; }

        .bs-btn--danger {
          background: rgba(239,68,68,.15);
          border-color: rgba(239,68,68,.35);
          color: #f87171;
        }

        .bs-btn--danger:hover { background: rgba(239,68,68,.25); }

        .bs-btn--success {
          background: #22c55e;
          color: #091210;
        }

        .bs-btn--success:hover { background: #16a34a; }

        .bs-link-btn {
          background: none;
          border: none;
          color: #4fd1b4;
          cursor: pointer;
          font: inherit;
          font-size: 0.78rem;
          padding: 0;
          text-decoration: underline;
          text-underline-offset: 2px;
        }

        .bs-link-btn:hover { color: #38bfa2; }

        /* ── Cards ──────────────────────────────────────────── */
        .bs-card {
          background: rgba(12,22,18,.7);
          border: 1px solid rgba(79,209,180,.08);
          border-radius: 14px;
          padding: 1.5rem;
          max-width: 1720px;
          margin-inline: auto;
          width: 100%;
        }

        /* ── Body two-col ──────────────────────────────────── */
        .bs-body {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.25rem;
          max-width: 1720px;
          margin-inline: auto;
          width: 100%;
        }

        @media (max-width: 1100px) {
          .bs-body { grid-template-columns: 1fr; }
        }

        /* ── Section headings ──────────────────────────────── */
        .bs-section-head {
          display: flex;
          align-items: flex-start;
          gap: 0.65rem;
          margin-bottom: 1.25rem;
        }

        .bs-section-icon {
          font-size: 1.35rem;
          color: #4fd1b4;
          line-height: 1;
          margin-top: 0.1rem;
        }

        .bs-section-title {
          margin: 0;
          font-size: 1.15rem;
          font-weight: 700;
          color: #dceae5;
        }

        .bs-section-sub {
          margin: 0.15rem 0 0;
          font-size: 0.8rem;
          color: #7a9b92;
        }

        /* ── Form ──────────────────────────────────────────── */
        .bs-form {
          display: flex;
          flex-direction: column;
          gap: 0.85rem;
        }

        .bs-field {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
        }

        .bs-field__label {
          font-size: 0.78rem;
          font-weight: 600;
          color: #9bb5ad;
          text-transform: uppercase;
          letter-spacing: 0.04em;
        }

        .bs-field__wrap {
          position: relative;
          display: flex;
          flex-direction: column;
        }

        .bs-field__wrap--row {
          flex-direction: row;
          align-items: center;
          gap: 0.5rem;
        }

        .bs-field__count {
          position: absolute;
          right: 10px;
          bottom: 7px;
          font-size: 0.7rem;
          color: #5a7a72;
          pointer-events: none;
        }

        .bs-input,
        .bs-select,
        .bs-textarea {
          width: 100%;
          padding: 0.55rem 0.75rem;
          font: inherit;
          font-size: 0.88rem;
          color: #dceae5;
          background: rgba(6,14,12,.6);
          border: 1px solid rgba(79,209,180,.1);
          border-radius: 8px;
          outline: none;
          transition: border-color .15s;
          box-sizing: border-box;
        }

        .bs-input:focus,
        .bs-select:focus,
        .bs-textarea:focus {
          border-color: rgba(79,209,180,.35);
        }

        .bs-input--readonly {
          cursor: default;
          opacity: .85;
          flex: 1;
        }

        .bs-select { appearance: none; cursor: pointer; }

        .bs-textarea { resize: vertical; min-height: 3.2rem; }

        .bs-pill {
          font-size: 0.72rem;
          font-weight: 600;
          color: #4fd1b4;
          background: rgba(79,209,180,.1);
          border-radius: 20px;
          padding: 0.2rem 0.6rem;
          white-space: nowrap;
        }

        .bs-expand-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          width: 100%;
          padding: 0.55rem 0.75rem;
          font: inherit;
          font-size: 0.88rem;
          color: #b0c8c0;
          background: rgba(6,14,12,.6);
          border: 1px solid rgba(79,209,180,.1);
          border-radius: 8px;
          cursor: pointer;
          transition: border-color .15s;
        }

        .bs-expand-row:hover { border-color: rgba(79,209,180,.25); }

        .bs-expand-arrow {
          color: #4fd1b4;
          font-size: 0.85rem;
          transition: transform .2s;
        }

        /* ── Designer footer ───────────────────────────────── */
        .bs-designer-footer {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 0.35rem;
          margin-top: 1.25rem;
          padding-top: 0.85rem;
          border-top: 1px solid rgba(79,209,180,.06);
          font-size: 0.74rem;
          color: #5a7a72;
        }

        .bs-designer-footer__sep { opacity: .35; }

        .bs-saved-check { color: #34d399; }

        /* ── Expert cards ──────────────────────────────────── */
        .bs-experts-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.85rem;
        }

        @media (max-width: 700px) {
          .bs-experts-grid { grid-template-columns: 1fr; }
        }

        .bs-expert-card {
          background: rgba(6,14,12,.55);
          border: 1px solid rgba(79,209,180,.07);
          border-radius: 10px;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.65rem;
        }

        .bs-expert-head {
          display: flex;
          align-items: flex-start;
          gap: 0.5rem;
        }

        .bs-expert-icon {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          background: rgba(79,209,180,.08);
          color: #4fd1b4;
          font-size: 1rem;
          flex-shrink: 0;
        }

        .bs-expert-role {
          margin: 0;
          font-size: 0.92rem;
          font-weight: 700;
          color: #dceae5;
        }

        .bs-expert-title {
          margin: 0;
          font-size: 0.72rem;
          color: #7a9b92;
        }

        .bs-stance {
          margin-left: auto;
          font-size: 0.7rem;
          font-weight: 600;
          border: 1px solid;
          border-radius: 20px;
          padding: 0.15rem 0.55rem;
          white-space: nowrap;
          flex-shrink: 0;
        }

        .bs-expert-bullets {
          margin: 0;
          padding-left: 1.1rem;
          font-size: 0.78rem;
          line-height: 1.55;
          color: #a8c4bb;
        }

        .bs-expert-bullets li + li { margin-top: 0.3rem; }

        /* ── Confidence bar ────────────────────────────────── */
        .bs-conf {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .bs-conf__track {
          flex: 1;
          height: 5px;
          background: rgba(79,209,180,.08);
          border-radius: 3px;
          overflow: hidden;
        }

        .bs-conf__fill {
          height: 100%;
          border-radius: 3px;
          transition: width .4s ease;
        }

        .bs-conf__label {
          font-size: 0.78rem;
          font-weight: 700;
          min-width: 2.5rem;
          text-align: right;
        }

        /* ── Vote buttons ──────────────────────────────────── */
        .bs-expert-vote { margin-top: auto; }

        .bs-vote-btn {
          font: inherit;
          font-size: 0.78rem;
          font-weight: 600;
          padding: 0.35rem 0.85rem;
          border-radius: 6px;
          border: none;
          cursor: pointer;
          transition: opacity .15s;
        }

        .bs-vote-btn:hover { opacity: .85; }

        .bs-vote-btn--approve {
          background: rgba(34,197,94,.15);
          color: #34d399;
          border: 1px solid rgba(34,197,94,.3);
        }

        .bs-vote-btn--revise {
          background: rgba(239,68,68,.12);
          color: #f87171;
          border: 1px solid rgba(239,68,68,.25);
        }

        /* ── Verdict ───────────────────────────────────────── */
        .bs-verdict-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 0.75rem;
          margin-bottom: 1.25rem;
        }

        @media (max-width: 900px) {
          .bs-verdict-grid { grid-template-columns: repeat(3, 1fr); }
        }

        @media (max-width: 600px) {
          .bs-verdict-grid { grid-template-columns: 1fr 1fr; }
        }

        .bs-metric-card {
          background: rgba(6,14,12,.5);
          border: 1px solid rgba(79,209,180,.06);
          border-radius: 9px;
          padding: 0.85rem;
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
        }

        .bs-metric-label {
          font-size: 0.72rem;
          font-weight: 600;
          color: #7a9b92;
          text-transform: uppercase;
          letter-spacing: 0.03em;
        }

        .bs-metric-value {
          font-size: 1.05rem;
          font-weight: 700;
        }

        .bs-metric-sub-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 0.4rem;
        }

        .bs-metric-sub {
          font-size: 0.72rem;
          color: #5a7a72;
        }

        .bs-spark { display: block; }

        .bs-next-step {
          font-size: 0.82rem;
          line-height: 1.6;
          color: #9bb5ad;
          margin: 0 0 1.15rem;
          padding: 0.75rem;
          background: rgba(79,209,180,.04);
          border-radius: 8px;
          border-left: 3px solid rgba(79,209,180,.25);
        }

        .bs-next-step strong { color: #dceae5; }

        .bs-verdict-actions {
          display: flex;
          gap: 0.65rem;
          flex-wrap: wrap;
        }
      `}</style>
    </div>
  )
}
