import { useState } from 'react'
import { motion } from 'framer-motion'

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
    <svg className="block" width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
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
      <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" className="fill-white text-[10px] font-bold">
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
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 15 }}
      className="w-full min-h-screen bg-transparent text-[#c8d6d2] font-sans px-6 md:px-10 py-6 md:py-8 flex flex-col gap-6 max-w-[1720px] mx-auto"
    >
      {/* ── Header ──────────────────────────────────────── */}
      <header className="flex flex-col gap-4 pb-4 border-b border-[#88aab8]/15">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <nav className="flex items-center gap-1.5 text-xs text-[#5e7a72]">
              <button className="p-0 border-none bg-transparent text-[#4fd1b4] font-semibold cursor-pointer hover:text-[#6ee0c8] transition !bg-transparent !border-none !shadow-none !h-auto !p-0" onClick={onBack}>Pro Lab</button>
              <span className="text-[#2a3f3a] text-xs">›</span>
              <span className="text-[#5e7a72] font-semibold">Auto / Copy Paper Plan</span>
            </nav>
            <div className="flex items-center gap-3 mt-1">
              <h1 className="text-lg font-extrabold text-[#ecf4f0] tracking-tight leading-tight">Auto / Copy Paper Plan</h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/20">Paper Only</span>
            </div>
            <p className="text-xs text-[#5e7a72] mt-0.5">Design a controlled paper automation plan with built-in risk, review, and governance.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="px-3.5 py-1.5 rounded-full text-xs font-bold transition-all border cursor-pointer active:scale-95 flex items-center gap-2 bg-[#f59e0b]/10 border-[#f59e0b]/20 text-[#f59e0b] !h-auto">
              <span className="w-1.5 h-1.5 rounded-full bg-current" />Paper Only
            </button>
            <button className="px-3.5 py-1.5 rounded-full text-xs font-bold transition-all border cursor-pointer active:scale-95 flex items-center gap-2 bg-[#4fd1b4]/10 border-[#4fd1b4]/20 text-[#4fd1b4] !h-auto">
              <span className="w-1.5 h-1.5 rounded-full bg-current" />Manual Review Required
            </button>
            <button className="px-3.5 py-1.5 rounded-full text-xs font-bold transition-all border cursor-pointer active:scale-95 flex items-center gap-2 bg-[#3b82f6]/10 border-[#3b82f6]/20 text-[#3b82f6] !h-auto">
              <span className="w-1.5 h-1.5 rounded-full bg-current" />Limits Active
            </button>
          </div>
        </div>
      </header>

      {/* ── Warning Banner ──────────────────────────────── */}
      <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-900/30 text-xs flex items-start gap-2.5 leading-relaxed">
        <span className="text-amber-400 font-bold shrink-0 mt-0.5">⚠</span>
        <div>
          <span className="font-extrabold text-amber-400">PAPER MODE ONLY — NO LIVE ORDERS. </span>
          <span className="text-[#88aab8]">
            This plan runs entirely in paper (shadow). No orders will be sent to any broker or exchange.
          </span>
        </div>
      </div>

      {/* ── Action Buttons ──────────────────────────────── */}
      <div className="flex gap-2 flex-wrap">
        <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 border border-[#88aab8]/20 hover:border-[#88aab8]/45 text-[#edf7f5] !h-auto !py-2.5">Save Plan</button>
        <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] !h-auto !py-2.5">Run Dry Test</button>
        <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] !h-auto !py-2.5">Submit for Review</button>
      </div>

      {/* ── Main Layout ─────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-6 items-start">
        {/* Left — Plan Builder */}
        <div>
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Plan Builder</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* 1. Strategy Source */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">1</span>
                  <span className="text-xs font-bold text-white">Strategy Source</span>
                </div>
                <p className="text-[10px] text-[#5e7a72] font-semibold">Select the strategy to copy</p>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  <select className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition" defaultValue="csv">
                    <option value="csv">Cross-Sectional Value</option>
                    <option value="mom">Momentum</option>
                  </select>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20 self-start">Live Source</span>
                </div>
              </div>

              {/* 2. Paper Account */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">2</span>
                  <span className="text-xs font-bold text-white">Paper Account / Shadow Account</span>
                </div>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  <select className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition" defaultValue="shadow">
                    <option value="shadow">Shadow Account – CV Copy</option>
                  </select>
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Buying Power:</span>
                    <span className="font-bold text-white">$1,000,000.00</span>
                  </div>
                </div>
              </div>

              {/* 3. Position Limits */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">3</span>
                  <span className="text-xs font-bold text-white">Position Limits</span>
                </div>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Max Position Size:</span>
                    <span className="font-bold text-white">2.00 %</span>
                  </div>
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Max Positions:</span>
                    <span className="font-bold text-white">50</span>
                  </div>
                </div>
              </div>

              {/* 4. Max Gross Exposure */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">4</span>
                  <span className="text-xs font-bold text-white">Max Gross Exposure</span>
                </div>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Max Gross Exposure:</span>
                    <span className="font-bold text-white">100.00 %</span>
                  </div>
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Current (Est.):</span>
                    <span className="font-bold text-white flex items-center gap-1.5">
                      18.42%
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20" style={{ fontSize: '0.68rem' }}>Good</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* 5. Kill Switch */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">5</span>
                  <span className="text-xs font-bold text-white">Kill Switch</span>
                </div>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  {KILL_SWITCHES.map((ks) => (
                    <div key={ks.id} className="flex justify-between items-center gap-4 py-1">
                      <span className="text-xs text-[#88aab8]">{ks.label}</span>
                      <div
                        role="button"
                        tabIndex={0}
                        className={`w-9 h-5 rounded-full bg-[#0c1720] border border-[#88aab8]/25 p-0.5 relative transition-all duration-200 cursor-pointer ${killSwitches[ks.id] ? 'bg-[#4fd1b4]/20 border-[#4fd1b4]/40' : ''}`}
                        onClick={() => toggleKill(ks.id)}
                        onKeyDown={(e) => e.key === 'Enter' && toggleKill(ks.id)}
                      >
                        <span className={`w-3.5 h-3.5 rounded-full bg-[#88aab8] block transition-transform duration-200 ${killSwitches[ks.id] ? 'translate-x-4 bg-[#4fd1b4]' : ''}`} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 6. Manual Review Rules */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">6</span>
                  <span className="text-xs font-bold text-white">Manual Review Rules</span>
                </div>
                <p className="text-[10px] text-[#5e7a72] font-semibold">Events requiring manual approval.</p>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  {REVIEW_RULES.map((r) => (
                    <div key={r.id} className="flex items-center gap-2.5 text-xs text-[#edf7f5] py-1">
                      <span className={`w-4 h-4 rounded border flex items-center justify-center text-[10px] font-bold ${r.checked ? 'bg-[#4fd1b4]/10 border-[#4fd1b4]/30 text-[#4fd1b4]' : 'border-[#88aab8]/25 text-transparent'}`}>
                        {r.checked ? '✓' : ''}
                      </span>
                      {r.label}
                    </div>
                  ))}
                  <button className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer text-left mt-1 border-none bg-transparent p-0 !border-none !bg-transparent !shadow-none !h-auto !p-0">Other Edit rules ✎</button>
                </div>
              </div>

              {/* 7. Copy Ratio */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">7</span>
                  <span className="text-xs font-bold text-white">Copy Ratio</span>
                </div>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Copy Ratio:</span>
                    <input className="bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-1.5 text-xs outline-none focus:border-[#4fd1b4] transition" type="text" defaultValue="100 %" style={{ width: '80px', textAlign: 'right' }} />
                  </div>
                  <div className="flex justify-between items-center gap-4 py-1">
                    <span className="text-xs text-[#88aab8]">Allow fractional shares</span>
                    <div
                      role="button"
                      tabIndex={0}
                      className={`w-9 h-5 rounded-full bg-[#0c1720] border border-[#88aab8]/25 p-0.5 relative transition-all duration-200 cursor-pointer ${fractional ? 'bg-[#4fd1b4]/20 border-[#4fd1b4]/40' : ''}`}
                      onClick={() => setFractional(!fractional)}
                      onKeyDown={(e) => e.key === 'Enter' && setFractional(!fractional)}
                    >
                      <span className={`w-3.5 h-3.5 rounded-full bg-[#88aab8] block transition-transform duration-200 ${fractional ? 'translate-x-4 bg-[#4fd1b4]' : ''}`} />
                    </div>
                  </div>
                </div>
              </div>

              {/* 8. Allowed Instruments */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">8</span>
                  <span className="text-xs font-bold text-white">Allowed Instruments</span>
                </div>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  <div className="flex flex-wrap gap-1.5">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0c1720] border border-[#88aab8]/15 text-[#edf7f5] text-[10px] font-semibold">US Equities <span className="text-[#5e7a72] hover:text-[#edf7f5] ml-1 cursor-pointer font-bold">✕</span></span>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0c1720] border border-[#88aab8]/15 text-[#edf7f5] text-[10px] font-semibold">ETFs <span className="text-[#5e7a72] hover:text-[#edf7f5] ml-1 cursor-pointer font-bold">✕</span></span>
                    <button className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer text-left mt-1 border-none bg-transparent p-0 !border-none !bg-transparent !shadow-none !h-auto !p-0">+ Add Instrument Type</button>
                  </div>
                  <p className="text-[10px] text-[#5e7a72] font-semibold mt-1">Excluded: Options, Futures, Crypto</p>
                </div>
              </div>

              {/* 9. Schedule */}
              <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 border-b border-[#88aab8]/10 pb-2 mb-1">
                  <span className="w-5 h-5 rounded-lg bg-[#4fd1b4]/10 text-[#4fd1b4] font-extrabold text-[10px] flex items-center justify-center">9</span>
                  <span className="text-xs font-bold text-white">Schedule</span>
                </div>
                <div className="flex flex-col gap-2.5 mt-1.5">
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Rebalance Frequency:</span>
                    <select className="bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition w-auto" defaultValue="daily">
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                    </select>
                  </div>
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Time (ET):</span>
                    <span className="font-bold text-white">16:00</span>
                  </div>
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Update Window:</span>
                    <span className="font-bold text-white">15m</span>
                  </div>
                  <div className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                    <span className="text-[#88aab8]">Start Date:</span>
                    <span className="font-bold text-white">May 20, 2025</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right — Sidebar */}
        <div className="grid gap-4">
          {/* Risk & Controls */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Risk &amp; Controls</h3>
            <div className="overflow-x-auto [scrollbar-width:thin]">
              <table className="w-full text-left border-collapse text-xs min-w-[320px]">
                <thead>
                  <tr>
                    <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Control</th>
                    <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Threshold</th>
                    <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {RISK_CONTROLS.map((rc) => (
                    <tr key={rc.control}>
                      <td className="py-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{rc.control}</td>
                      <td className="py-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{rc.threshold}</td>
                      <td className="py-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/15 text-[#4fd1b4] border border-[#4fd1b4]/20">Active</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer border-none bg-transparent p-0 text-left mt-2 !border-none !bg-transparent !shadow-none !h-auto !p-0">Edit Risk Settings ›</button>
          </div>

          {/* Pre-Launch Checklist */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <div className="flex justify-between items-center pb-2 border-b border-[#88aab8]/15 mb-1">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider" style={{ margin: 0 }}>Pre-Launch Checklist</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">6/6</span>
            </div>
            <div className="flex flex-col gap-2">
              {PRE_LAUNCH_ITEMS.map((item) => (
                <div key={item} className="flex items-center gap-2.5 text-xs text-[#edf7f5] py-1">
                  <span className="w-4 h-4 rounded border flex items-center justify-center text-[10px] font-bold bg-[#4fd1b4]/10 border-[#4fd1b4]/30 text-[#4fd1b4]">✓</span>
                  {item}
                </div>
              ))}
            </div>
          </div>

          {/* Approval Flow */}
          <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Approval Flow</h3>
            <div className="flex flex-col gap-4 relative pl-4 border-l border-[#88aab8]/15 ml-2 mt-2">
              {APPROVAL_STEPS.map((step, i) => (
                <div key={step.name} className="relative flex items-center gap-3">
                  <span className={`absolute -left-[21px] w-5 h-5 rounded-full border border-[#101d26] text-[10px] font-extrabold flex items-center justify-center ${step.done ? 'bg-[#4fd1b4] text-[#071016]' : 'bg-[#0c1720] border-[#88aab8]/20 text-[#5e7a72]'}`}>
                    {step.done ? '✓' : i + 1}
                  </span>
                  <div className="flex flex-col gap-0.5">
                    <div className="text-xs font-bold text-white">{step.name}</div>
                    <div className={`text-[10px] font-semibold ${step.done ? 'text-emerald-400' : 'text-[#5e7a72]'}`}>
                      {step.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-[#5e7a72] font-semibold italic mt-2">Plan will be activated in Paper Mode only.</p>
          </div>
        </div>
      </div>

      {/* ── Bottom — Paper Monitoring ───────────────────── */}
      <div className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4 mt-6">
        <h2 className="text-sm font-extrabold text-white uppercase tracking-wider">Paper Monitoring (After Dry Test)</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Copy Drift */}
          <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-3 justify-between min-h-[140px]">
            <div className="flex justify-between items-center">
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Copy Drift (Est.)</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">Good</span>
            </div>
            <div className="text-lg font-extrabold text-white">0.48%</div>
            <MiniSparkline points={SPARKLINE_POINTS} />
          </div>

          {/* Pending Review */}
          <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-3 justify-between min-h-[140px]">
            <div className="flex justify-between items-center">
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Pending Review</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950/20 text-rose-400 border border-rose-900/30">3 Items</span>
            </div>
            <div className="text-lg font-extrabold text-white">3 Items</div>
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between text-[11px] text-[#88aab8]">
                <span>New Positions:</span><span>2</span>
              </div>
              <div className="flex justify-between text-[11px] text-[#88aab8]">
                <span>Size Exceptions:</span><span>1</span>
              </div>
            </div>
            <button className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer border-none bg-transparent p-0 text-left mt-auto pt-2 !border-none !bg-transparent !shadow-none !h-auto !p-0">View Items →</button>
          </div>

          {/* Breach Alerts */}
          <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-3 justify-between min-h-[140px]">
            <div className="flex justify-between items-center">
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Breach Alerts</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">0 Active</span>
            </div>
            <div className="text-lg font-extrabold text-white">0 Active</div>
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between text-[11px] text-[#88aab8]">
                <span>Last 7 Days:</span><span>0</span>
              </div>
              <div className="flex justify-between text-[11px] text-[#88aab8]">
                <span>Last 30 Days:</span><span>0</span>
              </div>
            </div>
            <button className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer border-none bg-transparent p-0 text-left mt-auto pt-2 !border-none !bg-transparent !shadow-none !h-auto !p-0">View Alerts →</button>
          </div>

          {/* Plan Health */}
          <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-3 justify-between min-h-[140px]">
            <div className="flex justify-between items-center">
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Plan Health</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">Healthy</span>
            </div>
            <div className="flex items-center gap-4 mt-1">
              <MiniDonut pct={92} />
              <div className="flex flex-col gap-1 text-[10px] text-[#88aab8]">
                <span className="flex items-center gap-1.5"><span className="text-emerald-400 font-bold">✓</span> Data Feeds</span>
                <span className="flex items-center gap-1.5"><span className="text-emerald-400 font-bold">✓</span> Risk Controls</span>
                <span className="flex items-center gap-1.5"><span className="text-emerald-400 font-bold">✓</span> Account Sync</span>
                <span className="flex items-center gap-1.5"><span className="text-emerald-400 font-bold">✓</span> Rule Engine</span>
              </div>
            </div>
            <button className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer border-none bg-transparent p-0 text-left mt-auto pt-2 !border-none !bg-transparent !shadow-none !h-auto !p-0">View Diagnostics →</button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
