import React, { useState } from "react"
import { motion } from "framer-motion"

const JOURNAL_ENTRIES = [
  {
    action: "Long NVDA @ 945.30",
    details: { Buy: "5.35", R: "1.8", Thesis: "Breakout above resistance on volume" },
    tag: "Plan Followed",
    tagColor: "green",
    dot: "",
  },
  {
    action: "Added NVDA @ 951.10",
    details: { Size: "+2 contracts", Note: "Scaled in after confirmation candle" },
    tag: "Oversize",
    tagColor: "yellow",
    dot: "warn",
  },
  {
    action: "Short TSLA @ 178.40",
    details: { Sell: "3.20", R: "1.2", Thesis: "Breakdown below 180 support" },
    tag: "Rule Break",
    tagColor: "red",
    dot: "danger",
  },
  {
    action: "Closed NVDA @ 961.75",
    details: { P_L: "+$1,645", Duration: "2h 15m" },
    tag: "Plan Followed",
    tagColor: "green",
    dot: "",
  },
  {
    action: "Closed TSLA @ 175.90",
    details: { P_L: "+$529", Duration: "45m" },
    tag: "Rule Break",
    tagColor: "red",
    dot: "danger",
  },
]

const DETECTED_ISSUES = [
  { name: "FOMO Entry", count: 14, icon: "✗", severity: "red" },
  { name: "Oversize Position", count: 9, icon: "⚠", severity: "yellow" },
  { name: "Early Exit", count: 7, icon: "✗", severity: "red" },
  { name: "Revenge Trade", count: 4, icon: "⚠", severity: "yellow" },
]

const OUTLINE_SECTIONS = [
  { num: 1, title: "Hypothesis" },
  { num: 2, title: "Experiment Setup" },
  { num: 3, title: "Results" },
  { num: 4, title: "Caveats" },
  { num: 5, title: "Next Steps" },
]

const REPORT_CONTENT = [
  {
    title: "1. Hypothesis",
    text: "Mean reversion strategies should outperform momentum strategies during elevated volatility regimes (VIX > 25). The hypothesis rests on the observation that during high-volatility periods, overreactions create larger dislocations from fair value, which subsequently revert faster than during low-volatility environments.",
  },
  {
    title: "2. Experiment Setup",
    text: "Universe: S&P 500 constituents. Period: 2018–2025. Signal: 5-day z-score of returns. Entry: z-score < −2.0 (long) or > 2.0 (short). Exit: z-score returns to ±0.5 band or 10-day holding cap. Risk: max 2% per position, 15% gross exposure. Regime filter: VIX > 25 = active, VIX ≤ 25 = inactive (flat).",
  },
  {
    title: "3. Results",
    text: "Annualized return: 14.2% (vs. 9.8% for momentum baseline). Sharpe ratio: 1.42 (vs. 0.87). Max drawdown: −8.7% (vs. −16.3%). Win rate: 62.4%. The strategy was active for approximately 28% of trading days, concentrated in Q4 2018, Q1 2020, and Q2–Q3 2022.",
  },
  {
    title: "4. Caveats",
    text: "Backtest uses close-to-close returns, not intraday. Transaction costs modeled at 5 bps, which may understate slippage during high-vol periods. Survivorship bias partially mitigated via point-in-time constituent lists but not fully eliminated. Regime classification is binary and may miss transition periods.",
  },
  {
    title: "5. Next Steps",
    text: "Run walk-forward analysis on 2023–2025 out-of-sample data. Test non-binary regime filters (e.g., VIX percentile buckets). Explore sector-level mean reversion for higher granularity. Paper trade for 30 days before any capital allocation.",
  },
]

const SOURCE_ATTACHMENTS = [
  { name: "mean_reversion_backtest.csv", size: "241 KB", icon: "📊" },
  { name: "volatility_regime_analysis.pdf", size: "1.8 MB", icon: "📄" },
  { name: "sp500_constituents_pit.xlsx", size: "512 KB", icon: "📋" },
  { name: "strategy_comparison_chart.png", size: "89 KB", icon: "🖼" },
]

const DISCIPLINE_CHART_POINTS = [
  65, 68, 62, 70, 72, 69, 74, 71, 75, 73,
  70, 68, 72, 76, 74, 71, 78, 75, 73, 77,
  72, 74, 70, 68, 73, 76, 80, 78, 74, 72,
]

function DisciplineChart() {
  const pts = DISCIPLINE_CHART_POINTS
  const max = Math.max(...pts)
  const min = Math.min(...pts)
  const range = max - min || 1
  const w = 100
  const h = 100
  const pad = 4

  const polyline = pts
    .map((v, i) => {
      const x = pad + (i / (pts.length - 1)) * (w - 2 * pad)
      const y = h - pad - ((v - min) / range) * (h - 2 * pad)
      return `${x},${y}`
    })
    .join(" ")

  const areaPath =
    `M ${pad},${h - pad} ` +
    pts
      .map((v, i) => {
        const x = pad + (i / (pts.length - 1)) * (w - 2 * pad)
        const y = h - pad - ((v - min) / range) * (h - 2 * pad)
        return `L ${x},${y}`
      })
      .join(" ") +
    ` L ${w - pad},${h - pad} Z`

  return (
    <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
      <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Discipline Score Over Time (30D)</h4>
      <div className="w-full h-28 bg-[#0c1720]/40 border border-[#88aab8]/10 rounded-xl overflow-hidden">
        <svg className="w-full h-full" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
          <defs>
            <linearGradient id="jr-area-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(79,209,180,0.25)" />
              <stop offset="100%" stopColor="rgba(79,209,180,0.02)" />
            </linearGradient>
          </defs>
          {[0, 25, 50, 75, 100].map((pct) => {
            const y = h - pad - (pct / 100) * (h - 2 * pad) * (range / (max - min + range * 0.1))
            return (
              <line
                key={pct}
                x1={pad}
                x2={w - pad}
                y1={y}
                y2={y}
                stroke="rgba(79,209,180,0.06)"
                strokeWidth="0.3"
              />
            )
          })}
          <path d={areaPath} fill="url(#jr-area-grad)" />
          <polyline
            points={polyline}
            fill="none"
            stroke="#4fd1b4"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>
      <div className="flex justify-between text-[10px] text-[#5e7a72] font-semibold mt-1">
        <span>Apr 3</span>
        <span>Apr 17</span>
        <span>May 2</span>
      </div>
    </div>
  )
}

export default function JournalReportPage({ onBack }) {
  const [bookmarked, setBookmarked] = useState(false)
  const [activeOutline, setActiveOutline] = useState(0)
  const [notesContent] = useState(
    "Good day overall. Followed my plan on NVDA very well — entered at the right level, managed size properly on the add, and took profit at target. The TSLA short was more impulsive, entered before the setup fully confirmed. Need to be more disciplined on waiting for confirmation before pulling the trigger on counter-trend plays."
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 15 }}
      className="w-full min-h-screen bg-transparent text-[#c8d6d2] font-sans px-6 md:px-10 py-6 md:py-8 flex flex-col gap-6 max-w-[1720px] mx-auto"
    >
      {/* Header */}
      <header className="flex justify-between items-center pb-4 border-b border-[#88aab8]/15">
        <nav className="flex items-center gap-1.5 text-xs text-[#5e7a72]">
          <button className="p-0 border-none bg-transparent text-[#4fd1b4] font-semibold cursor-pointer hover:text-[#6ee0c8] transition" onClick={onBack}>
            Pro Lab
          </button>
          <span className="text-[#2a3f3a]">›</span>
          <span className="text-[#5e7a72] font-semibold">
            Journal Lab + Report Builder
          </span>
        </nav>
        <button
          className={`text-sm font-bold transition-all !bg-transparent !border-none !shadow-none !h-auto ${bookmarked ? "text-amber-400" : "text-[#88aab8] hover:text-amber-400"}`}
          onClick={() => setBookmarked((b) => !b)}
          title="Bookmark"
        >
          {bookmarked ? "★" : "☆"}
        </button>
      </header>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* ═══ LEFT — Journal Lab ═══ */}
        <div className="grid gap-4">
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            {/* Section header */}
            <div className="flex justify-between items-start gap-4 flex-wrap">
              <div className="flex gap-2.5 items-start">
                <span className="w-[38px] h-[38px] min-w-[38px] flex items-center justify-center rounded-xl text-lg flex-shrink-0 bg-[#4fd1b4]/10 border border-[#4fd1b4]/20 text-[#4fd1b4]">📓</span>
                <div>
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider">Journal Lab</h2>
                  <p className="text-xs text-[#5e7a72] mt-0.5">
                    Trade journal &amp; shadow account review
                  </p>
                </div>
              </div>
              <div className="flex gap-2 items-center flex-shrink-0">
                <select className="bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition">
                  <option>Shadow Account A</option>
                  <option>Shadow Account B</option>
                  <option>Shadow Account C</option>
                </select>
                <button className="text-white bg-[#0c1720]/60 border border-[#88aab8]/10 hover:border-[#4fd1b4]/30 flex items-center justify-center p-0 rounded-lg text-xs !w-7 !h-7 !h-auto" title="Filter">
                  🔍
                </button>
              </div>
            </div>

            {/* Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
                <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Discipline Score (30D)</p>
                <p className="text-lg font-extrabold text-white flex items-center">
                  72/100{" "}
                  <span
                    className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20 ml-2"
                    style={{ fontSize: "0.6rem" }}
                  >
                    Good
                  </span>
                </p>
                <p className="text-[10px] text-[#4fd1b4] font-semibold">
                  ↑ 8.4 vs prior 30D
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
                <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Tagged Events (30D)</p>
                <p className="text-lg font-extrabold text-white">42</p>
                <div className="flex flex-wrap gap-3 mt-1">
                  <span className="inline-flex items-center gap-1.5 text-[10px] text-[#88aab8] font-bold">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: "#10b981" }} />
                    12
                  </span>
                  <span className="inline-flex items-center gap-1.5 text-[10px] text-[#88aab8] font-bold">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: "#f59e0b" }} />
                    14
                  </span>
                  <span className="inline-flex items-center gap-1.5 text-[10px] text-[#88aab8] font-bold">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: "#f97316" }} />
                    3
                  </span>
                  <span className="inline-flex items-center gap-1.5 text-[10px] text-[#88aab8] font-bold">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: "#ef4444" }} />
                    9
                  </span>
                  <span className="inline-flex items-center gap-1.5 text-[10px] text-[#88aab8] font-bold">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: "#6b7280" }} />
                    7
                  </span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
                <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Best Day (P&amp;L)</p>
                <p className="text-lg font-extrabold text-white">$2,174</p>
                <p className="text-[10px] text-[#5e7a72] font-semibold">May 9, 2025</p>
              </div>

              <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
                <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Total Trades</p>
                <p className="text-lg font-extrabold text-white">87</p>
                <p className="text-[10px] text-[#5e7a72] font-semibold">Win Rate: 54.0%</p>
              </div>
            </div>
          </div>

          {/* Journal Timeline */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
              Journal Timeline
            </h3>
            <div className="flex flex-col gap-4 border-l border-[#88aab8]/15 pl-4 ml-2">
              {JOURNAL_ENTRIES.map((entry, i) => (
                <div key={i} className="relative flex flex-col gap-1">
                  <div
                    className={`absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full border-2 border-[#101d26] ${
                      entry.dot === 'warn' ? 'bg-[#f59e0b]' : entry.dot === 'danger' ? 'bg-[#ef4444]' : 'bg-[#4fd1b4]'
                    }`}
                  />
                  <p className="text-xs font-bold text-white leading-snug">{entry.action}</p>
                  <div className="flex flex-wrap gap-2 text-[10px] items-center">
                    {Object.entries(entry.details).map(([k, v]) => (
                      <span key={k} className="text-[#edf7f5]">
                        <span className="text-[#5e7a72]">{k.replace("_", "/")}:</span> {v}
                      </span>
                    ))}
                    <span
                      className={`px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5] ${
                        entry.tagColor === 'green'
                          ? 'text-emerald-400 bg-emerald-950/20 border-emerald-900/30'
                          : entry.tagColor === 'yellow'
                          ? 'text-amber-400 bg-amber-950/20 border-amber-900/30'
                          : 'text-rose-400 bg-rose-950/20 border-rose-900/30'
                      }`}
                    >
                      {entry.tag}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <button className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] text-left mt-2 cursor-pointer border-none bg-transparent p-0 !border-none !bg-transparent !shadow-none !h-auto !p-0">+ View full journal →</button>
          </div>

          {/* Discipline Chart */}
          <DisciplineChart />

          {/* Detected Issues */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <div className="flex justify-between items-center pb-2 border-b border-[#88aab8]/15">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Detected Issues (30D)</h3>
              <button className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer border-none bg-transparent p-0 !border-none !bg-transparent !shadow-none !h-auto !p-0">View all Issues →</button>
            </div>
            <div className="flex flex-col gap-2.5">
              {DETECTED_ISSUES.map((issue) => (
                <div key={issue.name} className="flex justify-between items-center text-xs py-1.5 border-b border-[#88aab8]/10">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`w-5 h-5 rounded-lg flex items-center justify-center text-[10px] font-bold shrink-0 ${
                        issue.severity === 'red' ? 'bg-rose-950/20 border border-rose-900/30 text-rose-400' : 'bg-amber-950/20 border border-amber-900/30 text-amber-400'
                      }`}
                    >
                      {issue.icon}
                    </span>
                    <span className="text-white font-bold">{issue.name}</span>
                  </div>
                  <span className="text-[#5e7a72] font-semibold">
                    {issue.count} occurrences
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Reflective Notes */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Reflective Notes</h3>
              <select className="bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition" style={{ fontSize: "0.72rem" }}>
                <option>Templates</option>
                <option>Daily Review</option>
                <option>Weekly Summary</option>
                <option>Trade Debrief</option>
              </select>
            </div>
            <div className="flex items-center gap-1 p-2 rounded-xl bg-[#0c1720]/50 border border-[#88aab8]/10">
              <button className="flex items-center justify-center rounded hover:bg-[#11222a]/50 text-xs text-[#88aab8] hover:text-white cursor-pointer border-none bg-transparent !bg-transparent !border-none !shadow-none !w-7 !h-7"><b>B</b></button>
              <button className="flex items-center justify-center rounded hover:bg-[#11222a]/50 text-xs text-[#88aab8] hover:text-white cursor-pointer border-none bg-transparent !bg-transparent !border-none !shadow-none !w-7 !h-7"><i>I</i></button>
              <button className="flex items-center justify-center rounded hover:bg-[#11222a]/50 text-xs text-[#88aab8] hover:text-white cursor-pointer border-none bg-transparent !bg-transparent !border-none !shadow-none !w-7 !h-7"><u>U</u></button>
              <span className="w-[1px] h-4 bg-[#88aab8]/10 mx-1" />
              <button className="flex items-center justify-center rounded hover:bg-[#11222a]/50 text-xs text-[#88aab8] hover:text-white cursor-pointer border-none bg-transparent !bg-transparent !border-none !shadow-none !w-7 !h-7">≡</button>
              <button className="flex items-center justify-center rounded hover:bg-[#11222a]/50 text-xs text-[#88aab8] hover:text-white cursor-pointer border-none bg-transparent !bg-transparent !border-none !shadow-none !w-7 !h-7">☰</button>
              <span className="w-[1px] h-4 bg-[#88aab8]/10 mx-1" />
              <button className="flex items-center justify-center rounded hover:bg-[#11222a]/50 text-xs text-[#88aab8] hover:text-white cursor-pointer border-none bg-transparent !bg-transparent !border-none !shadow-none !w-7 !h-7">🔗</button>
              <button className="flex items-center justify-center rounded hover:bg-[#11222a]/50 text-xs text-[#88aab8] hover:text-white cursor-pointer border-none bg-transparent !bg-transparent !border-none !shadow-none !w-7 !h-7">📎</button>
            </div>
            <div className="w-full p-4 min-h-[140px] rounded-xl border border-[#88aab8]/20 bg-[#0c1720]/80 text-[#edf7f5] text-xs outline-none focus:border-[#4fd1b4] transition leading-relaxed resize-none" contentEditable suppressContentEditableWarning>
              {notesContent}
            </div>
            <div className="flex justify-between text-[10px] text-[#5e7a72] font-semibold mt-1">
              <span>Auto-saved | 10:32 AM</span>
              <span>{notesContent.length} characters</span>
            </div>
          </div>
        </div>

        {/* ═══ RIGHT — Report Builder ═══ */}
        <div className="grid gap-4">
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            {/* Report Header */}
            <div className="flex justify-between items-start gap-4 flex-wrap">
              <div>
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">Report Builder</h2>
                <p className="text-xs text-[#5e7a72] mt-0.5">
                  Structured research memo builder
                </p>
              </div>
              <div className="flex gap-2 flex-wrap">
                <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 text-[#a0b8b0] bg-transparent border border-[#4fd1b4]/10 hover:border-[#4fd1b4]/25 !h-auto !py-1.5">
                  Save Memo
                </button>
                <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] !h-auto !py-1.5">
                  Generate Report
                </button>
                <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#8b5cf6] hover:bg-[#a78bfa] text-white !h-auto !py-1.5">
                  Publish Internal Note ▶
                </button>
              </div>
            </div>

            {/* Memo Title */}
            <div className="pb-2 border-b border-[#88aab8]/15 mb-2">
              <h3 className="text-sm font-bold text-white flex items-center">
                Memo: Mean Reversion in High Volatility Regimes
                <button className="text-white bg-[#0c1720]/60 border border-[#88aab8]/10 hover:border-[#4fd1b4]/30 flex items-center justify-center p-0 rounded-lg text-xs !w-7 !h-7 !h-auto" style={{ marginLeft: "0.4rem" }}>✏️</button>
              </h3>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "1rem" }}>
              <span className="text-[10px] text-[#5e7a72] font-semibold">Last saved: 10:32 AM</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/20">Draft</span>
            </div>

            {/* Outline + Content */}
            <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-4 mt-2">
              <div className="flex flex-col gap-1.5">
                {OUTLINE_SECTIONS.map((sec, i) => (
                  <div
                    key={sec.num}
                    className={`flex justify-between items-center text-xs p-2.5 rounded-xl border cursor-pointer transition-all ${
                      activeOutline === i
                        ? "border-[#4fd1b4]/30 bg-[#101d26]/80 text-white"
                        : "border-[#88aab8]/10 bg-[#0c1720]/30 hover:border-[#4fd1b4]/20"
                    }`}
                    onClick={() => setActiveOutline(i)}
                  >
                    <span>
                      <span className="text-[#4fd1b4] font-bold mr-1.5">{sec.num}.</span>
                      {sec.title}
                    </span>
                    <button className="text-[10px] font-semibold text-[#4fd1b4] hover:underline cursor-pointer border-none bg-transparent p-0 !border-none !bg-transparent !shadow-none !h-auto !p-0">Edit</button>
                  </div>
                ))}
              </div>

              <div className="flex flex-col gap-4 max-h-[360px] overflow-y-auto pr-2 [scrollbar-width:thin]">
                {REPORT_CONTENT.map((section) => (
                  <div key={section.title} className="flex flex-col gap-1">
                    <h4 className="text-xs font-bold text-white">
                      {section.title}
                    </h4>
                    <p className="text-xs text-[#88aab8] leading-relaxed">{section.text}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Source Attachments */}
            <div className="border-t border-[#88aab8]/15 pt-4 mt-2 flex flex-col gap-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-1">Source Attachments</h4>
              <div className="grid gap-2">
                {SOURCE_ATTACHMENTS.map((file) => (
                  <div key={file.name} className="flex justify-between items-center text-xs p-2.5 rounded-xl border border-[#88aab8]/10 bg-[#0c1720]/30 hover:border-[#4fd1b4]/20 cursor-pointer transition-all">
                    <div className="flex items-center gap-2.5">
                      <span className="text-sm">{file.icon}</span>
                      <span className="text-white font-bold">{file.name}</span>
                    </div>
                    <span className="text-[#5e7a72] font-semibold">{file.size}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Generated Executive Summary */}
            <div className="p-5 rounded-2xl bg-[#4fd1b4]/5 border border-[#4fd1b4]/15 shadow-sm flex flex-col gap-3 mt-4">
              <h4 className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">
                ✨ Generated Executive Summary
              </h4>
              <p className="text-xs text-[#88aab8] leading-relaxed">
                This memo examines the performance of mean reversion strategies during elevated
                volatility regimes (VIX &gt; 25) across S&amp;P 500 constituents from 2018 to 2025.
                The analysis demonstrates that mean reversion significantly outperforms momentum
                approaches during high-vol periods, achieving a 14.2% annualized return with a
                Sharpe ratio of 1.42 versus the momentum baseline of 9.8% and 0.87 respectively.
                The strategy was active for approximately 28% of all trading days, concentrated
                in known volatility events.
              </p>
              <ul className="list-disc pl-4 space-y-1 text-xs text-[#88aab8]">
                <li>Annualized return: 14.2% (vs. 9.8% momentum baseline)</li>
                <li>Sharpe ratio: 1.42 (vs. 0.87)</li>
                <li>Max drawdown: −8.7% (vs. −16.3%)</li>
                <li>Win rate: 62.4% across 847 round-trip trades</li>
                <li>Active 28% of trading days during VIX &gt; 25 regimes</li>
              </ul>
            </div>

            {/* Conclusion */}
            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-900/30 flex items-start gap-3 mt-4">
              <span className="text-emerald-400 font-bold text-xs mt-0.5 shrink-0">✓</span>
              <p className="text-xs text-[#88aab8] leading-relaxed">
                Mean reversion should be favored in elevated volatility regimes with strict
                risk controls. The strategy demonstrates statistically significant alpha during
                VIX &gt; 25 periods while maintaining manageable drawdown characteristics.
                Recommended for paper trading validation before live deployment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
