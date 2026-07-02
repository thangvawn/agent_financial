import { useState } from 'react'
import { motion } from 'framer-motion'

const SOURCES = [
  { id: 'polygon', name: 'Polygon', domain: 'Prices', status: 'healthy', primary: 'Polygon WebSocket', fallback: 'Alpha Vantage', latency: '89ms', freshness: '< 1s', cache: '82%', errorRate: '0.02%' },
  { id: 'fmp', name: 'FinancialModelingPro', domain: 'Fundamentals', status: 'healthy', primary: 'FMP REST', fallback: 'SEC Edgar', latency: '340ms', freshness: '6h', cache: '91%', errorRate: '0.05%' },
  { id: 'alpha', name: 'Alpha Vantage', domain: 'News', status: 'fallback', primary: 'Alpha Vantage', fallback: 'NewsAPI', latency: '720ms', freshness: '45s', cache: '56%', errorRate: '0.31%' },
  { id: 'worldbank', name: 'World Bank', domain: 'Macro', status: 'healthy', primary: 'World Bank API', fallback: 'FRED', latency: '510ms', freshness: '24h', cache: '95%', errorRate: '0.01%' },
  { id: 'quandl', name: 'Quandl', domain: 'Alternative', status: 'degraded', primary: 'Quandl v3', fallback: 'Tiingo', latency: '1.2s', freshness: '4h', cache: '48%', errorRate: '0.89%' },
]

const ROUTED_TO = [
  { label: 'Prices', detail: 'Real-time & EOD' },
  { label: 'Financial Statements', detail: 'Daily' },
  { label: 'News', detail: 'Near Real-time' },
  { label: 'Macro', detail: 'Daily' },
  { label: 'Alternative Data', detail: 'EOD/Intraday' },
]

const EXPORT_FORMATS = [
  { id: 'markdown', label: 'Markdown Blueprint', ext: '.md', icon: '📄' },
  { id: 'python', label: 'Python Strategy Skeleton', ext: '.py', icon: '🐍' },
  { id: 'pine', label: 'Pine Script Skeleton', ext: '.pine', icon: '🌲' },
  { id: 'runbook', label: 'Runbook/Checklist', ext: '.md', icon: '📋' },
  { id: 'csv-json', label: 'CSV/JSON Package', ext: '.zip', icon: '📦' },
  { id: 'full', label: 'Full Export Bundle', ext: '.zip', icon: '🗂️' },
]

const CONFIG_ITEMS = [
  { id: 'params', label: 'Include Strategy Parameters', checked: true },
  { id: 'risk', label: 'Include Risk & Position Sizing', checked: true },
  { id: 'backtest', label: 'Include Backtest Results', checked: true },
  { id: 'visuals', label: 'Include Visuals & Charts', checked: true },
  { id: 'schema', label: 'Include Data Schema', checked: true },
  { id: 'citations', label: 'Include Citations & Links', checked: true },
]

const FILE_PREVIEW = [
  { name: 'strategy_blueprint.md', size: '21 KB' },
  { name: 'parameters.yaml', size: '8 KB' },
  { name: 'backtest_summary.md', size: '34 KB' },
  { name: 'equity_curve.png', size: '156 KB' },
]

export default function DataRouterExportPage({ onBack }) {
  const [selectedFormat, setSelectedFormat] = useState('markdown')
  const [configChecks, setConfigChecks] = useState(
    CONFIG_ITEMS.reduce((acc, item) => ({ ...acc, [item.id]: item.checked }), {})
  )

  const toggleConfig = (id) => {
    setConfigChecks((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const statusBadge = (status) => {
    const map = {
      healthy: { bg: 'rgba(16,185,129,0.15)', color: '#10b981', text: 'Healthy' },
      fallback: { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', text: 'Fallback' },
      degraded: { bg: 'rgba(239,68,68,0.15)', color: '#ef4444', text: 'Degraded' },
    }
    const s = map[status] || map.healthy
    return <span className="px-2 py-0.5 rounded text-[10px] font-bold" style={{ background: s.bg, color: s.color }}>{s.text}</span>
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 15 }}
      className="w-full min-h-screen bg-transparent text-[#c8d6d2] font-sans px-6 md:px-10 py-6 md:py-8 flex flex-col gap-6 max-w-[1720px] mx-auto"
    >
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-[#5e7a72]">
        <button className="p-0 border-none bg-transparent text-[#4fd1b4] font-semibold cursor-pointer hover:text-[#6ee0c8] transition" onClick={onBack}>Pro Lab</button>
        <span className="text-[#2a3f3a] text-xs">›</span>
        <span className="text-[#5e7a72] font-semibold">Data Router + Export Lab</span>
      </nav>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1.1fr] gap-6 items-start">
        {/* LEFT — Data Router */}
        <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <header className="flex justify-between items-start gap-4 flex-wrap pb-2">
            <div className="flex gap-2.5 items-start">
              <span className="w-[38px] h-[38px] min-w-[38px] flex items-center justify-center rounded-xl text-lg flex-shrink-0 bg-[#4fd1b4]/10 border border-[#4fd1b4]/20 text-[#4fd1b4]">⚡</span>
              <div className="flex-1">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">Data Router</h2>
                <p className="text-xs text-[#5e7a72] mt-0.5">Route, monitor, and validate your data pipeline across all domains.</p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/20 text-emerald-400 border border-emerald-900/30 flex items-center gap-1.5">● All Systems Operational</span>
          </header>

          {/* Routing Map */}
          <div className="grid grid-cols-3 gap-4 items-center p-4 bg-black/25 rounded-xl border border-[#88aab8]/10">
            <div className="flex flex-col gap-2">
              <div className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider mb-1">SOURCES</div>
              {SOURCES.map((s) => (
                <div key={s.id} className={`p-3 rounded-lg bg-[#0c1720]/40 border flex flex-col gap-0.5 ${s.status === 'healthy' ? 'border-emerald-500/30' : s.status === 'fallback' ? 'border-amber-500/30' : 'border-rose-500/30'}`}>
                  <span className="text-xs font-semibold text-white">{s.name}</span>
                  <span className="text-[10px] text-[#5e7a72]">{s.domain}</span>
                </div>
              ))}
            </div>

            <div className="flex flex-col items-center gap-2">
              <div className="p-3.5 rounded-xl bg-gradient-to-br from-[#4fd1b4]/10 to-[#3b82f6]/5 border border-[#4fd1b4]/20 text-center">
                <div className="text-xs font-bold text-[#4fd1b4]">Data Router</div>
                <div className="text-[10px] text-[#8fa8a0] mt-0.5">Smart Routing</div>
                <div className="text-[9px] text-[#5e7a72] mt-0.5">Health + Latency + Cost</div>
              </div>
              {/* Connection lines (visual) */}
              <div className="flex flex-col gap-1 w-12">
                {SOURCES.map((s, i) => (
                  <div key={i} className={`h-[2px] rounded-full ${s.status === 'healthy' ? 'bg-emerald-500' : s.status === 'fallback' ? 'bg-[#f59e0b]' : 'bg-rose-500'}`} />
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <div className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider mb-1">ROUTED TO</div>
              {ROUTED_TO.map((t, i) => (
                <div key={i} className="p-3 rounded-lg bg-[#0c1720]/40 border border-blue-500/20 flex flex-col gap-0.5">
                  <span className="text-xs font-semibold text-white">{t.label}</span>
                  <span className="text-[10px] text-[#5e7a72]">{t.detail}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="flex gap-4 flex-wrap text-[10px] text-[#5e7a72]">
            <span className="inline-flex items-center gap-1.5"><span className="w-5 h-[2px] rounded-full bg-emerald-500" /> Primary Route</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-5 h-[2px] rounded-full bg-[#f59e0b]" /> Fallback Route</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-indigo-500" /> Cache</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-500" /> Degraded</span>
          </div>

          {/* Source Status Table */}
          <div className="overflow-x-auto rounded-xl border border-[#88aab8]/10 [scrollbar-width:thin]">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Source</th>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Domain</th>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Status</th>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Primary</th>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Fallback</th>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Latency</th>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Freshness</th>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Cache</th>
                  <th className="p-2.5 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Error Rate</th>
                </tr>
              </thead>
              <tbody>
                {SOURCES.map((s) => (
                  <tr key={s.id}>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-white font-bold">{s.name}</td>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{s.domain}</td>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{statusBadge(s.status)}</td>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{s.primary}</td>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{s.fallback}</td>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{s.latency}</td>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{s.freshness}</td>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{s.cache}</td>
                    <td className="p-2.5 border-b border-[#88aab8]/10 text-[#edf7f5]">{s.errorRate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Bottom Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mt-2">
            <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
              <span className="text-lg font-extrabold text-white">98.6%</span>
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Routing Health</span>
            </div>
            <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
              <span className="text-lg font-extrabold text-white">412ms</span>
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Avg Latency</span>
            </div>
            <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
              <span className="text-lg font-extrabold text-white">12s</span>
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Data Freshness</span>
            </div>
            <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
              <span className="text-lg font-extrabold text-white">74%</span>
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Cache Hit Rate</span>
            </div>
            <div className="p-4 rounded-xl bg-[#0c1720]/60 border border-[#88aab8]/10 flex flex-col gap-1">
              <span className="text-lg font-extrabold text-white">0.15%</span>
              <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Error Rate</span>
            </div>
          </div>
        </section>

        {/* RIGHT — Export Lab */}
        <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <header className="flex justify-between items-start gap-4 flex-wrap pb-2">
            <div className="flex gap-2.5 items-start">
              <span className="w-[38px] h-[38px] min-w-[38px] flex items-center justify-center rounded-xl text-lg flex-shrink-0 bg-[#4fd1b4]/10 border border-[#4fd1b4]/20 text-[#4fd1b4]">📦</span>
              <div className="flex-1">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">Export Lab</h2>
                <p className="text-xs text-[#5e7a72] mt-0.5">Package strategies, blueprints, and data into portable formats.</p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950/20 text-purple-400 border border-purple-900/30">Template v2.4</span>
          </header>

          {/* Export Options */}
          <div className="flex flex-col gap-2">
            <div className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Export Format</div>
            <div className="grid grid-cols-2 gap-3">
              {EXPORT_FORMATS.map((f) => (
                <div
                  key={f.id}
                  role="button"
                  tabIndex={0}
                  className={`p-4 rounded-xl border text-left cursor-pointer transition-all duration-200 flex flex-col gap-2 ${selectedFormat === f.id ? 'bg-[#101d26]/90 border-[#4fd1b4]/40 shadow-md' : 'bg-[#0c1720]/40 border-[#88aab8]/10 hover:border-[#88aab8]/25'}`}
                  onClick={() => setSelectedFormat(f.id)}
                  onKeyDown={(e) => e.key === 'Enter' && setSelectedFormat(f.id)}
                >
                  <span className="text-lg">{f.icon}</span>
                  <span className="text-xs font-bold text-white leading-snug">{f.label}</span>
                  <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">{f.ext}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Export Configuration */}
          <div className="flex flex-col gap-2">
            <div className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">Export Configuration</div>
            <div className="grid grid-cols-2 gap-3 mt-1">
              {CONFIG_ITEMS.map((item) => (
                <label key={item.id} className="flex items-center gap-2.5 text-xs text-[#edf7f5] py-1 cursor-pointer select-none">
                  <span className={`w-4 h-4 rounded border flex items-center justify-center text-[10px] font-bold ${configChecks[item.id] ? 'bg-[#4fd1b4]/10 border-[#4fd1b4]/30 text-[#4fd1b4]' : 'border-[#88aab8]/25 text-transparent'}`}>
                    {configChecks[item.id] && '✓'}
                  </span>
                  <input
                    type="checkbox"
                    checked={configChecks[item.id]}
                    onChange={() => toggleConfig(item.id)}
                    className="hidden"
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Package Summary */}
          <div className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-3">
            <div className="text-xs font-bold text-white uppercase tracking-wider">Package Summary</div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex justify-between text-xs py-1 border-b border-[#88aab8]/5"><span className="text-[#88aab8]">Files</span><span className="font-bold text-white">12</span></div>
              <div className="flex justify-between text-xs py-1 border-b border-[#88aab8]/5"><span className="text-[#88aab8]">Size</span><span className="font-bold text-white">1.42 MB</span></div>
              <div className="flex justify-between text-xs py-1 border-b border-[#88aab8]/5"><span className="text-[#88aab8]">Format</span><span className="font-bold text-white">Markdown Blueprint</span></div>
              <div className="flex justify-between text-xs py-1 border-b border-[#88aab8]/5 col-span-2">
                <span className="text-[#88aab8]">Includes</span>
                <span className="font-bold text-[#4fd1b4]">
                  {Object.entries(configChecks).filter(([, v]) => v).length} of {CONFIG_ITEMS.length} modules
                </span>
              </div>
            </div>
          </div>

          {/* File Preview */}
          <div className="flex flex-col gap-2">
            <div className="text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">File Preview</div>
            <div className="flex flex-col gap-1.5">
              {FILE_PREVIEW.map((f, i) => (
                <div key={i} className="flex justify-between text-xs py-1.5 border-b border-[#88aab8]/10 items-center">
                  <div className="flex items-center gap-2">
                    <span>📄</span>
                    <span className="text-[#edf7f5] font-semibold">{f.name}</span>
                  </div>
                  <span className="text-[#5e7a72] font-semibold">{f.size}</span>
                </div>
              ))}
              <div className="flex justify-between text-xs py-1.5 items-center">
                <div className="flex items-center gap-2">
                  <span>＋</span>
                  <span className="text-[#5e7a72] font-semibold">8 more files</span>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2 mt-2">
            <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] flex items-center justify-center gap-1 !h-auto !py-2.5">
              <span>⬇</span>
              Export Package
            </button>
            <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 border border-[#88aab8]/20 hover:border-[#88aab8]/45 text-[#edf7f5] flex items-center justify-center gap-1 !h-auto !py-2.5">
              <span>📋</span>
              Copy Template
            </button>
            <button className="px-4 py-2.5 rounded-xl text-xs font-bold cursor-pointer transition active:scale-95 border border-[#88aab8]/20 hover:border-[#88aab8]/45 text-[#edf7f5] flex items-center justify-center gap-1 !h-auto !py-2.5">
              <span>🔗</span>
              Share to Report Builder
            </button>
          </div>
        </section>
      </div>
    </motion.div>
  )
}
