import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
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
    <svg width={w} height={h} className="block" viewBox={`0 0 ${w} ${h}`}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
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
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 15 }}
      className="w-full min-h-screen bg-transparent text-[#c8d6d2] font-sans px-6 md:px-10 py-6 md:py-8 flex flex-col gap-6 max-w-[1720px] mx-auto"
    >
      {/* ── Header ──────────────────────────────────────────── */}
      <header className="flex justify-between items-center pb-4 border-b border-[#88aab8]/15">
        <nav className="flex items-center gap-1.5 text-xs text-[#5e7a72]">
          <button type="button" className="p-0 border-none bg-transparent text-[#4fd1b4] font-semibold cursor-pointer hover:text-[#6ee0c8] transition" onClick={onBack}>Pro Lab</button>
          <span className="text-[#2a3f3a] text-xs">›</span>
          <span className="p-0 border-none bg-transparent text-[#4fd1b4] font-semibold cursor-pointer hover:text-[#6ee0c8] transition">Swarm Committee</span>
          <span className="text-[#2a3f3a] text-xs">›</span>
          <span className="text-[#5e7a72] font-semibold">Blueprint Designer</span>
        </nav>
        <div className="flex gap-2 items-center flex-shrink-0">
          <button type="button" className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] !h-auto !py-1.5">Save Blueprint</button>
          <button type="button" className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 text-[#a0b8b0] bg-transparent border border-[#4fd1b4]/10 hover:border-[#4fd1b4]/25 !h-auto !py-1.5">Export Blueprint</button>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">
            {health?.openai_configured ? `Live · ${health.model}` : 'OpenAI offline'}
          </span>
        </div>
      </header>

      {/* ── Two-column body ─────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* LEFT — Blueprint Designer */}
        <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <div className="flex justify-between items-start gap-4 flex-wrap pb-2">
            <span className="w-[38px] h-[38px] min-w-[38px] flex items-center justify-center rounded-xl text-lg flex-shrink-0 bg-[#4fd1b4]/10 border border-[#4fd1b4]/20 text-[#4fd1b4]">✦</span>
            <div className="flex-1">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Blueprint Designer</h2>
              <p className="text-xs text-[#5e7a72] mt-0.5">Design and configure your strategy using no-code blocks.</p>
            </div>
          </div>

          <div className="grid gap-4">
            <label className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Strategy Name</span>
              <div className="relative flex flex-col">
                <input
                  className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition"
                  type="text"
                  maxLength={80}
                  value={strategyName}
                  onChange={(e) => setStrategyName(e.target.value)}
                />
                <span className="absolute bottom-3 right-3 text-[10px] text-[#5e7a72] font-semibold">{strategyName.length}/80</span>
              </div>
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Objective</span>
              <div className="relative flex flex-col">
                <select className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition" defaultValue={objective}>
                  <option value="sharpe">Maximize risk-adjusted returns (Sharpe)</option>
                  <option value="sortino">Maximize downside-adjusted returns (Sortino)</option>
                  <option value="cagr">Maximize CAGR</option>
                </select>
              </div>
            </label>

            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Asset Universe</span>
              <div className="flex items-center gap-2">
                <span className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs select-all flex-1">Global Equities (Large &amp; Mid Cap)</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">6,412 assets</span>
              </div>
            </div>

            <label className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Benchmark</span>
              <div className="relative flex flex-col">
                <select className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition" defaultValue="msci-acwi">
                  <option value="msci-acwi">MSCI ACWI Net Total Return</option>
                  <option value="sp500">S&amp;P 500 Total Return</option>
                  <option value="ftse">FTSE All-World</option>
                </select>
              </div>
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Rebalance Frequency</span>
              <div className="relative flex flex-col">
                <select className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition" defaultValue="monthly">
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                </select>
              </div>
            </label>

            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Risk Constraints</span>
              <div
                role="button"
                tabIndex={0}
                className="flex justify-between items-center text-xs p-2.5 rounded-xl border border-[#88aab8]/10 bg-[#0c1720]/30 hover:border-[#4fd1b4]/20 cursor-pointer transition-all"
              >
                <span>4 Constraints</span>
                <span className="text-[#4fd1b4] font-bold">▸</span>
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Assumptions</span>
              <div
                role="button"
                tabIndex={0}
                className="flex justify-between items-center text-xs p-2.5 rounded-xl border border-[#88aab8]/10 bg-[#0c1720]/30 hover:border-[#4fd1b4]/20 cursor-pointer transition-all"
              >
                <span>3 Assumptions</span>
                <span className="text-[#4fd1b4] font-bold">▸</span>
              </div>
            </div>

            <label className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Notes</span>
              <div className="relative flex flex-col">
                <textarea
                  className="w-full p-4 rounded-xl border border-[#88aab8]/20 bg-[#0c1720]/80 text-[#edf7f5] text-xs outline-none focus:border-[#4fd1b4] transition leading-relaxed resize-none"
                  maxLength={500}
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
                <span className="absolute bottom-3 right-3 text-[10px] text-[#5e7a72] font-semibold">{notes.length}/500</span>
              </div>
            </label>
          </div>

          <footer className="flex flex-wrap gap-2 items-center border-t border-[#88aab8]/15 pt-3 mt-1 text-[10px] text-[#5e7a72] font-semibold">
            <span>Blueprint ID: BP-2025-05-16-0013</span>
            <span className="text-[#2a3f3a] mx-1">|</span>
            <button type="button" className="text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer hover:underline border-none bg-transparent p-0">Duplicate</button>
            <span className="text-[#2a3f3a] mx-1">|</span>
            <span>Last saved: May 16, 2025 10:22 AM</span>
            <span className="text-[#2a3f3a] mx-1">|</span>
            <span className="text-emerald-400">Saved ✓</span>
          </footer>
        </section>

        {/* RIGHT — Swarm Committee */}
        <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <div className="flex justify-between items-start gap-4 flex-wrap pb-2">
            <div className="flex-1">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Swarm Committee</h2>
              <p className="text-xs text-[#5e7a72] mt-0.5">
                {aiResult ? 'Multi-agent experts đã hoàn thành review.' : 'Bấm "Run Committee" để OpenAI mô phỏng investment committee debate.'}
              </p>
            </div>
            <button
              type="button"
              className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] !h-auto !py-1.5"
              onClick={runCommittee}
              disabled={loading || !health?.openai_configured}
            >
              {loading ? 'Đang debate…' : aiResult ? 'Re-run Committee' : 'Run Committee'}
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-900/30 text-rose-400 text-xs font-semibold">{error}</div>
          )}

          {!aiResult && !loading && (
            <div className="flex flex-col items-center justify-center p-8 gap-4 text-center">
              <span className="text-2xl text-[#5e7a72]">⌥</span>
              <p className="text-xs text-[#88aab8] max-w-sm">Committee chưa chạy. Khi bấm Run, AI sẽ mô phỏng 4 vai trò debate (Bull · Bear · Quant · PM) và đưa ra final call.</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center p-8 gap-4 text-center">
              <div className="w-full h-1.5 bg-[#0c1720]/80 rounded-full overflow-hidden">
                <div className="block h-full bg-[#4fd1b4] w-[40%] animate-pulse" />
              </div>
              <p className="text-xs text-[#88aab8]">Bull, Bear, Quant và PM đang debate strategy của bạn…</p>
            </div>
          )}

          {aiResult && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {aiResult.memos.map((memo, idx) => {
                const stanceKey = memo.stance.toLowerCase()
                const color = STANCE_COLOR[stanceKey] || '#6366f1'
                return (
                  <article key={idx} className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-3">
                    <div className="flex justify-between items-start gap-2">
                      <span className="w-7 h-7 rounded-lg flex items-center justify-center bg-[#4fd1b4]/10 text-[#4fd1b4] text-xs font-bold">{ROLE_ICONS[memo.role] || '◯'}</span>
                      <div className="flex-1">
                        <h3 className="text-xs font-bold text-white">{memo.role}</h3>
                        <p className="text-[10px] text-[#5e7a72] font-semibold">{memo.stance}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border" style={{ color, borderColor: color }}>
                        {memo.stance}
                      </span>
                    </div>
                    <p className="text-xs text-[#88aab8] leading-relaxed p-3 bg-[#0c1720]/40 rounded-lg border-l-2 border-[#4fd1b4]">{memo.memo}</p>
                    {memo.key_concerns.length > 0 && (
                      <ul className="list-disc pl-4 space-y-1.5 text-[11px] text-[#5e7a72]">
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
        <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4 mt-6">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Committee Verdict — AI synthesis</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <article className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Consensus</span>
              <span className="text-lg font-extrabold" style={{ color: aiResult.consensus === 'buy' ? '#10b981' : aiResult.consensus === 'reject_or_revise' ? '#ef4444' : '#f59e0b' }}>
                {aiResult.consensus}
              </span>
              <span className="text-[10px] text-[#5e7a72] font-semibold">Confidence: {aiResult.confidence}</span>
            </article>
            <article className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1 md:col-span-2">
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">PM Decision Summary</span>
              <p style={{ margin: '6px 0 0', fontSize: '0.85rem', lineHeight: 1.6 }} className="text-[#88aab8]">{aiResult.decision_summary}</p>
            </article>
          </div>

          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-900/30 text-xs text-[#88aab8] leading-relaxed">
            <strong className="text-white">Recommended Next Steps:</strong>
            <ol style={{ margin: '8px 0 0', paddingLeft: 22, lineHeight: 1.7 }} className="list-decimal">
              {aiResult.next_actions.map((a, i) => <li key={i}>{a}</li>)}
            </ol>
          </div>

          <div className="flex gap-2">
            <button type="button" className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 text-[#a0b8b0] bg-transparent border border-[#4fd1b4]/10 hover:border-[#4fd1b4]/25" onClick={runCommittee}>Run Committee Again</button>
            <button type="button" className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016]">Send to Backtest</button>
          </div>
        </section>
      )}
    </motion.div>
  )
}
