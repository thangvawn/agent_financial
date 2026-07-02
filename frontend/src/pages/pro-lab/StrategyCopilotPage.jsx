import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { aiHealth, aiStrategyCopilot } from '../../modules/pro-lab'

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
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 15 }}
      className="w-full min-h-screen bg-transparent text-[#c8d6d2] font-sans px-6 md:px-10 py-6 md:py-8 flex flex-col gap-6 max-w-[1720px] mx-auto"
    >
      <header className="flex justify-between items-center pb-4 border-b border-[#88aab8]/15">
        <nav className="flex items-center gap-1.5 text-xs text-[#5e7a72]">
          <button type="button" className="p-0 border-none bg-transparent text-[#4fd1b4] font-semibold cursor-pointer hover:text-[#6ee0c8] transition !bg-transparent !border-none !shadow-none !h-auto !p-0" onClick={onBack}>Pro Lab</button>
          <span className="text-[#2a3f3a] text-xs">›</span>
          <span className="text-[#5e7a72] font-semibold">Strategy Copilot</span>
        </nav>
        <div className="flex gap-2 items-center flex-shrink-0">
          <button type="button" className="text-xs font-bold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-full transition cursor-pointer active:scale-95 !h-auto !py-1.5">▷ How it works</button>
          <button type="button" className="text-xs font-semibold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-lg transition cursor-pointer active:scale-95 !h-auto !py-1.5">✧ Examples</button>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">
            {health?.openai_configured ? `Live · ${health.model}` : 'OpenAI offline'}
          </span>
        </div>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <article className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <div className="flex justify-between items-start gap-4 flex-wrap pb-2">
            <div className="flex-1">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Strategy Prompter</h2>
              <p className="text-xs text-[#5e7a72] mt-0.5">Describe your strategy idea, rules, and parameters to refine them.</p>
            </div>
          </div>

          <div className="relative flex flex-col">
            <textarea
              className="w-full p-4 rounded-xl border border-[#88aab8]/20 bg-[#0c1720]/80 text-[#edf7f5] text-xs outline-none focus:border-[#4fd1b4] transition leading-relaxed resize-none"
              value={idea}
              onChange={(e) => setIdea(e.target.value.slice(0, ideaLimit))}
              rows={7}
              placeholder="Build a mean-reversion strategy using sector z-scores..."
            />
            <span className="absolute bottom-3 right-3 text-[10px] text-[#5e7a72] font-semibold">{idea.length} / {ideaLimit}</span>
          </div>

          <div className="flex flex-wrap gap-2">
            <button type="button" className="px-3 py-1 rounded-full text-[10px] font-bold border border-[#88aab8]/15 bg-[#0c1720]/40 text-[#a0b8b0] hover:border-[#4fd1b4]/30 hover:text-white transition cursor-pointer active:scale-95 !h-auto !py-1">＋ Add context</button>
            {['Macro regime', 'Rates outlook', 'Volatility regime', 'Market breadth'].map((label) => (
              <button
                key={label}
                type="button"
                className="px-3 py-1 rounded-full text-[10px] font-bold border border-[#88aab8]/15 bg-[#0c1720]/40 text-[#a0b8b0] hover:border-[#4fd1b4]/30 hover:text-white transition cursor-pointer active:scale-95 !h-auto !py-1"
              >
                {label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-end gap-4 p-4 rounded-xl bg-[#0c1720]/50 border border-[#88aab8]/10">
            <label className="flex flex-col gap-1.5 flex-1 min-w-[140px]">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Model</span>
              <select
                className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition"
                value={market}
                onChange={(e) => setMarket(e.target.value)}
              >
                {MARKETS.map((m) => (
                  <option key={m.id} value={m.label}>{m.label}</option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1.5 flex-1 min-w-[140px]">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Cadence</span>
              <select
                className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition"
                value={horizon}
                onChange={(e) => setHorizon(e.target.value)}
              >
                {HORIZONS.map((h) => (
                  <option key={h.id} value={h.id}>{h.label}</option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1.5 flex-1 min-w-[140px]">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Risk Budget</span>
              <input
                type="number"
                step="0.5"
                min="0.1"
                max="20"
                className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition"
                value={riskBudget}
                onChange={(e) => setRiskBudget(parseFloat(e.target.value) || 2)}
              />
            </label>

            <button
              type="button"
              className="bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] px-4 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer active:scale-95 flex items-center justify-center gap-1 shrink-0 !h-auto !py-2.5"
              onClick={handleGenerate}
              disabled={loading || !health?.openai_configured}
            >
              ✣ {loading ? 'Generating…' : 'Generate Draft'}
            </button>
          </div>

          {error && <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-900/30 text-rose-400 text-xs font-semibold">{error}</div>}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <MiniCard title="Input Signals" badge="3" rows={INPUT_SIGNAL_ROWS} action="Add Signal" />
            <MiniCard title="Universe & Benchmark" rows={SUMMARY_CARDS} action="Add Universe / Benchmark" />
            <MiniCard title="Risk Budget" rows={RISK_ROWS} action="Adjust Risk" />
            <MiniCard title="Validation Queue" rows={VALIDATION_ROWS.map((item, index) => [item, index < 3 ? '✓' : '□'])} action="Add Validation" />
          </div>
        </article>

        <article className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <header className="flex justify-between items-start gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-1.5">Strategy Draft <span className="text-xs text-[#5e7a72] lowercase">(v0.1)</span></h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">DRAFT</span>
            </div>
            <div className="flex gap-2">
              <button type="button" className="text-xs font-semibold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-lg transition cursor-pointer active:scale-95 !h-auto !py-1.5">⊙ View Blueprint</button>
              <button type="button" className="text-white bg-[#0c1720]/60 border border-[#88aab8]/10 hover:border-[#4fd1b4]/30 flex items-center justify-center p-0 rounded-lg !w-7 !h-7 !h-auto">⋮</button>
            </div>
          </header>

          {loading ? (
            <div className="flex flex-col items-center justify-center p-8 gap-4">
              <div className="w-full h-1.5 bg-[#0c1720]/80 rounded-full overflow-hidden">
                <div className="block h-full bg-[#4fd1b4] w-[40%] animate-pulse" />
              </div>
              <p className="text-xs text-[#88aab8]">OpenAI đang phân tích ý tưởng và xây blueprint…</p>
            </div>
          ) : (
            <div className="flex flex-col">
              <DraftRow icon="⚑" label="Strategy Name">{displayDraft.strategy_name}</DraftRow>
              <DraftRow icon="◎" label="Objective">{displayDraft.rationale}</DraftRow>
              <DraftRow icon="⌘" label="Asset Universe">{displayDraft.market}</DraftRow>
              <DraftRow icon="⇄" label="Signal Stack">
                {displayDraft.signal_stack.map((item) => <span key={item} className="px-2 py-0.5 rounded bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5] text-[10px] font-semibold">{item}</span>)}
              </DraftRow>
              <DraftRow icon="◴" label="Risk Budget">
                {displayDraft.risk_rules.map((item) => <span key={item} className="px-2 py-0.5 rounded bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5] text-[10px] font-semibold">{item}</span>)}
              </DraftRow>
              <DraftRow icon="⏱" label="Cadence">
                <span className="px-2 py-0.5 rounded bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5] text-[10px] font-semibold">{displayDraft.horizon}</span>
                <span className="px-2 py-0.5 rounded bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5] text-[10px] font-semibold">Hold: 5 trading days</span>
              </DraftRow>
              <DraftRow icon="⊕" label="Validation Queue">
                {displayDraft.validation_queue.map((item) => <span key={item} className="px-2 py-0.5 rounded bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5] text-[10px] font-semibold">{item}</span>)}
                <span className="px-2 py-0.5 rounded bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5] text-[10px] font-semibold">+1</span>
              </DraftRow>
              <DraftRow icon="≈" label="Key Assumptions">
                <ul className="list-disc pl-4 space-y-1 text-[#88aab8]">
                  <li>Mean reversion persists at sector level over short horizon</li>
                  <li>Transaction costs &lt; 15 bps round trip</li>
                  <li>Liquidity sufficient for target universe</li>
                </ul>
              </DraftRow>
              <DraftRow icon="☷" label="Status">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/20">Draft Generated</span>
                <span className="text-[10px] text-[#5e7a72] font-semibold mt-0.5">{displayDraft.last_run_time || 'May 16, 2025 10:22 AM'}</span>
              </DraftRow>
            </div>
          )}

          <footer className="flex justify-between items-center gap-4 border-t border-[#88aab8]/15 pt-3 mt-1">
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] text-[#5e7a72] uppercase font-bold">Draft Confidence</span>
              <strong className="text-sm font-extrabold text-[#4fd1b4]">Medium</strong>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] text-[#5e7a72] uppercase font-bold">Est. Sharpe (Backtest)</span>
              <strong className="text-sm font-extrabold text-[#4fd1b4]">1.15 – 1.45</strong>
            </div>
          </footer>
        </article>
      </section>

      <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-6">
        <header className="flex justify-between items-start gap-4 flex-wrap pb-4 border-b border-[#88aab8]/15">
          <div>
            <h2 className="text-base font-extrabold text-white flex items-center gap-1.5"><span>②</span> Strategy Blueprint <em className="text-xs text-[#5e7a72] not-italic font-normal">(Editable)</em></h2>
            <p className="text-xs text-[#88aab8] mt-0.5">Review and refine the generated components.</p>
          </div>
          <div className="flex gap-2">
            <button type="button" className="text-xs font-semibold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-lg transition cursor-pointer active:scale-95 !h-auto !py-1.5">⛶ Expand All</button>
            <button type="button" className="text-xs font-semibold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-lg transition cursor-pointer active:scale-95 !h-auto !py-1.5">⇲ Collapse All</button>
          </div>
        </header>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {BLUEPRINT_CARDS.map(([icon, title, rows]) => (
            <article key={title} className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-3">
              <header className="flex justify-between items-start gap-2">
                <h3 className="text-xs font-bold text-white flex items-center gap-1.5"><span>{icon}</span>{title}</h3>
                <button type="button" className="text-[10px] font-semibold text-[#4fd1b4] hover:underline cursor-pointer !border-none !bg-transparent !shadow-none !h-auto !p-0">Edit</button>
              </header>
              <ul className="list-disc pl-4 space-y-1.5 text-[11px] text-[#88aab8] flex-1">
                {rows.map((row) => <li key={row}>{row}</li>)}
              </ul>
              <footer className="text-[9px] text-[#5e7a72] font-semibold border-t border-[#88aab8]/10 pt-2">⊙ Status: <strong>Generated</strong></footer>
            </article>
          ))}
        </div>
        <footer className="flex flex-wrap gap-3 items-center border-t border-[#88aab8]/15 pt-4 mt-2">
          <button type="button" className="text-xs font-semibold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-lg transition cursor-pointer active:scale-95 !h-auto !py-1.5">☷ Refine Draft</button>
          <button type="button" className="text-xs font-semibold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-lg transition cursor-pointer active:scale-95 !h-auto !py-1.5">⟳ Regenerate</button>
          <button type="button" className="text-xs font-semibold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-lg transition cursor-pointer active:scale-95 !h-auto !py-1.5">⇔ Compare Variants</button>
          <span className="flex-1" />
          <button type="button" className="text-xs font-semibold text-[#4fd1b4] bg-[#4fd1b4]/10 hover:bg-[#4fd1b4]/20 border border-[#4fd1b4]/20 px-3.5 py-1.5 rounded-lg transition cursor-pointer active:scale-95 !h-auto !py-1.5">▣ Save Blueprint</button>
          <button type="button" className="bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] px-4 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer active:scale-95 !h-auto !py-2.5">♙ Send to Committee</button>
        </footer>
      </section>
    </motion.div>
  )
}

function MiniCard({ title, badge, rows, action }) {
  return (
    <article className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-3">
      <header className="flex justify-between items-center">
        <h3 className="text-xs font-bold text-white">{title}</h3>
        {badge ? <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">{badge}</span> : <button type="button" className="text-[10px] font-semibold text-[#4fd1b4] hover:underline cursor-pointer !border-none !bg-transparent !shadow-none !h-auto !p-0">Edit</button>}
      </header>
      <div className="flex flex-col gap-1.5">
        {rows.map(([label, value]) => (
          <p key={`${title}-${label}`} className="flex justify-between text-xs">
            <span className="text-[#88aab8]">{label}</span>
            <strong className={value === 'Risk' ? 'text-amber-400 font-semibold' : 'font-semibold text-white'}>{value}</strong>
          </p>
        ))}
      </div>
      <button type="button" className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] text-left mt-1 !border-none !bg-transparent !shadow-none !h-auto !p-0">＋ {action}</button>
    </article>
  )
}

function DraftRow({ icon, label, children }) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-[#88aab8]/10 text-xs">
      <span className="text-[#4fd1b4] text-xs shrink-0 w-4 text-center mt-0.5">{icon}</span>
      <span className="text-[#88aab8] w-28 shrink-0">{label}</span>
      <div className="flex-1 text-[#edf7f5] flex flex-wrap gap-1.5">{children}</div>
    </div>
  )
}
