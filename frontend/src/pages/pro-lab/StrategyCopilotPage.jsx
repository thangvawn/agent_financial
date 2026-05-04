import { useEffect, useState } from 'react'
import { aiHealth, aiStrategyCopilot } from '../../modules/pro-lab'
import './strategy-copilot.css'

const DEMO_IDEA = 'Tìm chiến lược cho cổ phiếu VN ưu tiên doanh nghiệp chất lượng (ROE cao, nợ thấp), momentum 60-90 ngày xác nhận, kiểm soát drawdown bằng vol target. Rebalance hàng tháng.'

const MARKETS = [
  { id: 'vietnam_equities', label: 'Vietnam equities (HOSE/HNX)' },
  { id: 'us_equities', label: 'US equities (S&P 500)' },
  { id: 'hk_equities', label: 'HK equities (Hang Seng)' },
  { id: 'crypto', label: 'Crypto (BTC/ETH/Top 50)' },
  { id: 'global_macro', label: 'Global macro / FX' },
]

const HORIZONS = [
  { id: 'daily', label: 'Daily' },
  { id: 'weekly', label: 'Weekly' },
  { id: 'monthly', label: 'Monthly' },
  { id: 'quarterly', label: 'Quarterly' },
]

const EXAMPLE_IDEAS = [
  'Long-only momentum trên VN30 với volatility filter, exit khi RSI quá mua.',
  'Mean reversion BTC-USDT khi giá lệch >2 sigma so với SMA(20), TP/SL 3%.',
  'Multi-factor (value + quality + momentum) trên S&P 500, top 30 equal-weight, monthly rebalance.',
  'Sector rotation theo macro regime: cyclical khi PMI > 50, defensive khi PMI < 48.',
]

const DEMO_DRAFT = {
  strategy_name: 'Sector Mean-Reversion (Z-Score)',
  rationale: 'Capture short-term mean reversion in S&P 500 sectors using return z-scores.',
  market: 'S&P 500 Sectors (11)',
  horizon: 'Signal: Daily (EOD)',
  universe: ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU'],
  signal_stack: ['Return Z-Score (20d)', 'Volatility Filter', 'Crowding Filter'],
  risk_rules: ['2% daily risk budget', '~10% gross exposure', 'Max 3% per sector'],
  validation_queue: ['Backtest', 'Cross-Sectional Robustness', 'Stress Test'],
  confidence: 'medium',
}

const INPUT_SIGNAL_ROWS = [
  ['Return Z-Score (20d)', 'Primary'],
  ['Volatility Filter (20d)', 'Risk'],
  ['Crowding/Positioning', 'Risk'],
]

const SUMMARY_CARDS = [
  ['Universe', 'S&P 500 Sectors (11)'],
  ['Benchmark', 'S&P 500 Index (SPX)'],
  ['Coverage', '100%'],
  ['Rebalance', 'Daily'],
]

const RISK_ROWS = [
  ['Daily Risk Budget', '2.0%'],
  ['Gross Exposure Target', '~10%'],
  ['Net Exposure Target', '~0%'],
  ['Max Position (Per Sector)', '3%'],
]

const VALIDATION_ROWS = ['Backtest (In-Sample)', 'Cross-Sectional Robustness', 'Stress Test (Regimes)', 'Walk-Forward Analysis']

const BLUEPRINT_CARDS = [
  ['∑', 'Signal Logic', ['Long if Z-Score(20d) < -1.5', 'Short if Z-Score(20d) > +1.5', 'Ranked cross-sectionally.']],
  ['▽', 'Filters', ['20d Volatility < 75th percentile', 'ADV (20d) > $25M', 'Crowding Score < 70th percentile']],
  ['♙', 'Positioning', ['Equal weight within selected legs', 'Max 3% per sector', 'Target gross ~10%, net ~0%']],
  ['✈', 'Execution', ['Enter on close', 'Exit after 5 trading days', 'Market-on-Close']],
  ['◈', 'Risk Controls', ['Daily stop: 2.0% of NAV', 'Max drawdown stop: 15%', 'Vol spike guard: VIX > 30 pause']],
]

export default function StrategyCopilotPage({ onBack }) {
  const [idea, setIdea] = useState(DEMO_IDEA)
  const [market, setMarket] = useState(MARKETS[0].label)
  const [horizon, setHorizon] = useState('monthly')
  const [riskBudget, setRiskBudget] = useState(2.0)
  const [draft, setDraft] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [health, setHealth] = useState(null)

  useEffect(() => {
    aiHealth().then(setHealth).catch(() => setHealth({ openai_configured: false }))
  }, [])

  async function handleGenerate() {
    if (!idea.trim()) {
      setError('Nhập ý tưởng chiến lược trước khi generate.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await aiStrategyCopilot({
        idea: idea.trim(),
        market,
        horizon,
        risk_budget_pct: riskBudget,
      })
      setDraft(result)
    } catch (err) {
      setError(err.message || 'Lỗi gọi OpenAI')
    } finally {
      setLoading(false)
    }
  }

  const displayDraft = draft || DEMO_DRAFT
  const ideaLimit = 2000

  return (
    <div className="sc sc-copilot">
      <div className="sc-copilot__topbar">
        <nav className="sc-copilot__crumb">
          <button type="button" onClick={onBack}>Pro Lab</button>
          <span>›</span>
          <strong>Strategy Copilot</strong>
        </nav>
        <button type="button" className="sc-copilot__how">▷ How it works</button>
      </div>

      <section className="sc-copilot__main">
        <article className="sc-panel sc-idea-panel">
          <header className="sc-panel__head">
            <div>
              <h2><span>💡</span> 1 Idea Input</h2>
              <p>Describe your investment idea in natural language.</p>
            </div>
            <button type="button" className="sc-ghost-btn">✧ Examples</button>
          </header>

          <div className="sc-copilot-textarea">
            <textarea
              className="sc-copilot-textarea__input"
              value={idea}
              onChange={(e) => setIdea(e.target.value.slice(0, ideaLimit))}
              rows={7}
              placeholder="Build a mean-reversion strategy using sector z-scores..."
            />
            <span>{idea.length} / {ideaLimit}</span>
          </div>

          <div className="sc-context-chips">
            <button type="button">＋ Add context</button>
            {['Macro regime', 'Rates outlook', 'Volatility regime', 'Market breadth'].map((label) => (
              <button
                key={label}
                type="button"
              >
                {label}
              </button>
            ))}
          </div>

          <div className="sc-control-strip">
            <label className="sc-field">
              <span className="sc-field__label">Model</span>
              <select
                className="sc-select"
                value={market}
                onChange={(e) => setMarket(e.target.value)}
              >
                {MARKETS.map((m) => (
                  <option key={m.id} value={m.label}>{m.label}</option>
                ))}
              </select>
            </label>

            <label className="sc-field">
              <span className="sc-field__label">Cadence</span>
              <select
                className="sc-select"
                value={horizon}
                onChange={(e) => setHorizon(e.target.value)}
              >
                {HORIZONS.map((h) => (
                  <option key={h.id} value={h.id}>{h.label}</option>
                ))}
              </select>
            </label>

            <label className="sc-field">
              <span className="sc-field__label">Risk Budget</span>
              <input
                type="number"
                step="0.5"
                min="0.1"
                max="20"
                className="sc-input"
                value={riskBudget}
                onChange={(e) => setRiskBudget(parseFloat(e.target.value) || 2)}
              />
            </label>

            <button
              type="button"
              className="sc-generate-btn"
              onClick={handleGenerate}
              disabled={loading || !health?.openai_configured}
            >
              ✣ {loading ? 'Generating…' : 'Generate Draft'}
            </button>
          </div>

          {error && <div className="sc-error">{error}</div>}

          <div className="sc-mini-grid">
            <MiniCard title="Input Signals" badge="3" rows={INPUT_SIGNAL_ROWS} action="Add Signal" />
            <MiniCard title="Universe & Benchmark" rows={SUMMARY_CARDS} action="Add Universe / Benchmark" />
            <MiniCard title="Risk Budget" rows={RISK_ROWS} action="Adjust Risk" />
            <MiniCard title="Validation Queue" rows={VALIDATION_ROWS.map((item, index) => [item, index < 3 ? '✓' : '□'])} action="Add Validation" />
          </div>
        </article>

        <article className="sc-panel sc-draft-panel">
          <header className="sc-panel__head">
            <div className="sc-draft-title-row">
              <h2>Strategy Draft <span>(v0.1)</span></h2>
              <span className="sc-status-chip">DRAFT</span>
            </div>
            <div className="sc-draft-actions">
              <button type="button" className="sc-ghost-btn">⊙ View Blueprint</button>
              <button type="button" className="sc-icon-btn">⋮</button>
            </div>
          </header>

          {loading ? (
            <div className="sc-loading sc-loading--compact">
              <div className="sc-loading__bar"><span /></div>
              <p>OpenAI đang phân tích ý tưởng và xây blueprint…</p>
            </div>
          ) : (
            <div className="sc-draft-table">
              <DraftRow icon="⚑" label="Strategy Name">{displayDraft.strategy_name}</DraftRow>
              <DraftRow icon="◎" label="Objective">{displayDraft.rationale}</DraftRow>
              <DraftRow icon="⌘" label="Asset Universe">{displayDraft.market}</DraftRow>
              <DraftRow icon="⇄" label="Signal Stack">
                {displayDraft.signal_stack.map((item) => <span key={item} className="sc-chip">{item}</span>)}
              </DraftRow>
              <DraftRow icon="◴" label="Risk Budget">
                {displayDraft.risk_rules.map((item) => <span key={item} className="sc-chip">{item}</span>)}
              </DraftRow>
              <DraftRow icon="⏱" label="Cadence">
                <span className="sc-chip">{displayDraft.horizon}</span>
                <span className="sc-chip">Hold: 5 trading days</span>
              </DraftRow>
              <DraftRow icon="⊕" label="Validation Queue">
                {displayDraft.validation_queue.map((item) => <span key={item} className="sc-chip">{item}</span>)}
                <span className="sc-chip">+1</span>
              </DraftRow>
              <DraftRow icon="≈" label="Key Assumptions">
                <ul className="sc-assumption-list">
                  <li>Mean reversion persists at sector level over short horizon</li>
                  <li>Transaction costs &lt; 15 bps round trip</li>
                  <li>Liquidity sufficient for target universe</li>
                </ul>
              </DraftRow>
              <DraftRow icon="☷" label="Status">
                <span className="sc-status-chip sc-status-chip--amber">Draft Generated</span>
                <span className="sc-draft-date">May 16, 2025 10:22 AM</span>
              </DraftRow>
            </div>
          )}

          <footer className="sc-draft-footer">
            <div><span>Draft Confidence</span><strong>Medium</strong></div>
            <div><span>Est. Sharpe (Backtest)</span><strong>1.15 – 1.45</strong></div>
          </footer>
        </article>
      </section>

      <section className="sc-blueprint-panel">
        <header className="sc-blueprint-panel__head">
          <div>
            <h2><span>②</span> Strategy Blueprint <em>(Editable)</em></h2>
            <p>Review and refine the generated components.</p>
          </div>
          <div>
            <button type="button" className="sc-ghost-btn">⛶ Expand All</button>
            <button type="button" className="sc-ghost-btn">⇲ Collapse All</button>
          </div>
        </header>
        <div className="sc-blueprint-grid">
          {BLUEPRINT_CARDS.map(([icon, title, rows]) => (
            <article key={title} className="sc-blueprint-card">
              <header>
                <h3><span>{icon}</span>{title}</h3>
                <button type="button">Edit</button>
              </header>
              <ul>
                {rows.map((row) => <li key={row}>{row}</li>)}
              </ul>
              <footer>⊙ Status: <strong>Generated</strong></footer>
            </article>
          ))}
        </div>
        <footer className="sc-blueprint-actions">
          <button type="button" className="sc-ghost-btn">☷ Refine Draft</button>
          <button type="button" className="sc-ghost-btn">⟳ Regenerate</button>
          <button type="button" className="sc-ghost-btn">⇔ Compare Variants</button>
          <span />
          <button type="button" className="sc-ghost-btn">▣ Save Blueprint</button>
          <button type="button" className="sc-generate-btn">♙ Send to Committee</button>
        </footer>
      </section>
    </div>
  )
}

function MiniCard({ title, badge, rows, action }) {
  return (
    <article className="sc-mini-card">
      <header>
        <h3>{title}</h3>
        {badge ? <span>{badge}</span> : <button type="button">Edit</button>}
      </header>
      <div>
        {rows.map(([label, value]) => (
          <p key={`${title}-${label}`}>
            <span>{label}</span>
            <strong className={value === 'Risk' ? 'is-risk' : ''}>{value}</strong>
          </p>
        ))}
      </div>
      <button type="button">＋ {action}</button>
    </article>
  )
}

function DraftRow({ icon, label, children }) {
  return (
    <div className="sc-draft-row">
      <span className="sc-draft-row__icon">{icon}</span>
      <span className="sc-draft-row__label">{label}</span>
      <div className="sc-draft-row__value">{children}</div>
    </div>
  )
}
