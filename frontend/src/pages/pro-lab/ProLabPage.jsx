import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

import {
  archiveProLabBlueprint,
  compareProLabBlueprints,
  createProLabBlueprint,
  fetchProLabCatalog,
  exportProLabReport,
  fetchProLabSessions,
  fetchProLabTeaser,
  fetchProLabWorkspaceState,
  fetchProLabWorkspace,
  issueProLabAccessToken,
  revokeProLabSession,
  runProLabCommand,
  runProLabBacktest,
  runProLabScenario,
  saveProLabWorkspaceState,
  updateProLabBlueprint,
} from '../../modules/pro-lab'
import AutoCopyPaperPage from './AutoCopyPaperPage'
import BlueprintSwarmPage from './BlueprintSwarmPage'
import DataRouterExportPage from './DataRouterExportPage'
import JournalReportPage from './JournalReportPage'
import OptimizerScenarioPage from './OptimizerScenarioPage'
import ProLabBacktestStudioPage from './ProLabBacktestStudioPage'
import ProLabBlueprintsPage from './ProLabBlueprintsPage'
import ProLabExperimentsPage from './ProLabExperimentsPage'
import ProLabOverviewPage from './ProLabOverviewPage'
import ProLabSessionsPage from './ProLabSessionsPage'
import StrategyCopilotPage from './StrategyCopilotPage'

const DEFAULT_BLUEPRINT = {
  name: 'VN Quality Rotation',
  objective: 'Tao mot sandbox de so benchmark va doc scenario theo cach co cau truc, khong bien no thanh tin hieu mua ban.',
  asset_universe: 'FPT,VCB,MWG',
  benchmark: 'VNINDEX',
  rebalance_frequency: 'monthly',
  risk_constraints: 'Max concentration 35%, avoid single-theme overload',
  assumptions_note: 'Dung cho premium/internal research workspace, khong dung de marketing public.',
}

const WORKFLOW_STEPS = [
  { id: 'idea', label: 'IDEA', description: 'Generate ideas\nand hypotheses' },
  { id: 'build', label: 'BUILD', description: 'Design strategies\nand assemble data' },
  { id: 'validate', label: 'VALIDATE', description: 'Backtest, stress test\nand validate edge' },
  { id: 'operate', label: 'OPERATE', description: 'Deploy, monitor and\niterate in production' },
]

const PAGES = [
  ['overview', 'Overview', 'Dashboard'],
  ['blueprints', 'Design', 'Hypothesis and constraints'],
  ['backtest-studio', 'Backtest Studio', 'Open full-screen workspace'],
  ['experiments', 'Run & Review', 'Scenario, backtest, memo'],
  ['sessions', 'Access', 'Tokens and active sessions'],
]

const MODULE_LIST = [
  { id: 'strategy-copilot', label: 'Strategy Copilot' },
  { id: 'blueprint-swarm', label: 'Blueprint / Swarm' },
  { id: 'optimizer-scenario', label: 'Optimizer / Scenario' },
  { id: 'backtest-validation', label: 'Chart / Backtest Studio' },
  { id: 'data-router-export', label: 'Data Router / Export' },
  { id: 'journal-report', label: 'Journal / Report' },
  { id: 'auto-copy', label: 'Auto / Copy Paper' },
]

export default function ProLabPage({ sessionId, onBack, onOpenAdmin, onOpenBacktestStudio }) {
  const [subpage, setSubpage] = useState('overview')
  const [accessToken, setAccessToken] = useState(() => window.localStorage.getItem('pro_lab.access_token') || '')
  const [teaser, setTeaser] = useState(null)
  const [workspace, setWorkspace] = useState(null)
  const [catalog, setCatalog] = useState(null)
  const [workspaceState, setWorkspaceState] = useState(null)
  const [sessionsPayload, setSessionsPayload] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(DEFAULT_BLUEPRINT)
  const [selectedBlueprintId, setSelectedBlueprintId] = useState('')
  const [compareRightId, setCompareRightId] = useState('')
  const [compareResult, setCompareResult] = useState(null)
  const [reportExport, setReportExport] = useState(null)
  const [lastRun, setLastRun] = useState(null)
  const [result, setResult] = useState(null)

  useEffect(() => {
    window.localStorage.setItem('pro_lab.access_token', accessToken)
  }, [accessToken])

  useEffect(() => {
    let cancelled = false

    async function run() {
      setLoading(true)
      setError('')
      try {
        const teaserPayload = await fetchProLabTeaser(sessionId)
        if (cancelled) return
        setTeaser(teaserPayload)

        const cat = await fetchProLabCatalog(sessionId)
        if (cancelled) return
        setCatalog(cat)

        if (accessToken) {
          const ws = await fetchProLabWorkspace(sessionId, accessToken)
          if (cancelled) return
          setWorkspace(ws)

          const state = await fetchProLabWorkspaceState(sessionId, accessToken)
          if (cancelled) return
          setWorkspaceState(state)
        }
      } catch (err) {
        setError(err.message || 'Lỗi tải workspace')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    run()

    return () => {
      cancelled = true
    }
  }, [sessionId, accessToken])

  async function loadWorkspace() {
    if (!accessToken) return
    try {
      setError('')
      const ws = await fetchProLabWorkspace(sessionId, accessToken)
      setWorkspace(ws)
    } catch (err) {
      setError(err.message || 'Lỗi tải workspace')
    }
  }

  async function loadSessions() {
    try {
      setError('')
      const res = await fetchProLabSessions(sessionId)
      setSessionsPayload(res)
    } catch (err) {
      setError(err.message || 'Lỗi tải active sessions')
    }
  }

  useEffect(() => {
    if (subpage === 'sessions') {
      loadSessions()
    }
  }, [subpage])

  async function handleIssueAccessToken() {
    setError('')
    try {
      const res = await issueProLabAccessToken(sessionId)
      setAccessToken(res.access_token)
    } catch (err) {
      setError(err.message || 'Lỗi cấp token mới')
    }
  }

  async function handleRevokeSession(tokenId) {
    setError('')
    try {
      await revokeProLabSession(sessionId, tokenId)
      await loadSessions()
    } catch (err) {
      setError(err.message || 'Lỗi thu hồi session')
    }
  }

  async function handleSaveBlueprint() {
    if (!accessToken) return
    setError('')
    try {
      const payload = await createProLabBlueprint(sessionId, accessToken, form)
      setResult({ type: 'create_blueprint', payload })
      await loadWorkspace()
      setForm(DEFAULT_BLUEPRINT)
    } catch (err) {
      setError(err.message || 'Lỗi lưu blueprint')
    }
  }

  async function handleUpdateBlueprint(blueprintId, patch) {
    if (!accessToken) return
    setError('')
    try {
      const payload = await updateProLabBlueprint(sessionId, accessToken, blueprintId, patch)
      setResult({ type: 'update_blueprint', payload })
      await loadWorkspace()
    } catch (err) {
      setError(err.message || 'Lỗi cập nhật blueprint')
    }
  }

  async function handleArchiveBlueprint(blueprintId) {
    if (!accessToken) return
    setError('')
    try {
      const payload = await archiveProLabBlueprint(sessionId, accessToken, blueprintId)
      setResult({ type: 'archive_blueprint', payload })
      await loadWorkspace()
    } catch (err) {
      setError(err.message || 'Lỗi lưu trữ blueprint')
    }
  }

  async function handleCompareBlueprints() {
    if (!accessToken || !selectedBlueprintId || !compareRightId) return
    setError('')
    try {
      const res = await compareProLabBlueprints(sessionId, accessToken, selectedBlueprintId, compareRightId)
      setCompareResult(res)
    } catch (err) {
      setError(err.message || 'Lỗi so sánh blueprints')
    }
  }

  async function handleScenarioRun(blueprintId, key, val) {
    if (!accessToken) return
    setError('')
    try {
      const payload = await runProLabScenario(sessionId, accessToken, blueprintId, key, val)
      setLastRun({ type: 'scenario', payload })
      await loadWorkspace()
    } catch (err) {
      setError(err.message || 'Lỗi chạy scenario')
    }
  }

  async function handleBacktestRun(blueprintId, start, end) {
    if (!accessToken) return
    setError('')
    try {
      const payload = await runProLabBacktest(sessionId, accessToken, blueprintId, start, end)
      setLastRun({ type: 'backtest', payload })
      await loadWorkspace()
    } catch (err) {
      setError(err.message || 'Lỗi chạy backtest')
    }
  }

  async function handleProviderCommand(providerId, commandId, bodyPayload) {
    if (!accessToken) return
    setError('')
    try {
      const payload = await runProLabCommand(sessionId, accessToken, providerId, commandId, bodyPayload)
      setResult({ type: 'run_command', payload })
      await loadWorkspace()
    } catch (err) {
      setError(err.message || 'Lỗi chạy command')
    }
  }

  async function handleExportReport(experimentId, fmt) {
    if (!accessToken) return
    setError('')
    try {
      const res = await exportProLabReport(sessionId, accessToken, experimentId, fmt)
      setReportExport(res)
    } catch (err) {
      setError(err.message || 'Lỗi xuất report')
    }
  }

  function handleSubpageChange(id) {
    if (id === 'backtest-studio') {
      if (onOpenBacktestStudio) {
        onOpenBacktestStudio()
      } else {
        setSubpage('backtest-validation')
      }
    } else {
      setSubpage(id)
    }
  }

  const isModulePage = ['strategy-copilot', 'blueprint-swarm', 'optimizer-scenario', 'backtest-validation', 'data-router-export', 'journal-report', 'auto-copy'].includes(subpage)
  const blueprintCount = workspace?.blueprints?.length
  const experimentCount = workspace?.experiments?.length

  return (
    <section className="w-full min-h-screen bg-transparent text-[#c8d6d2] font-sans px-6 md:px-10 py-6 md:py-8 flex flex-col gap-6 max-w-[1720px] mx-auto">
      {/* Tab Navigation */}
      {!isModulePage && (
        <nav className="flex gap-2 border-b border-[#88aab8]/15 pb-2">
          {PAGES.map(([id, label]) => (
            <button
              key={id}
              className={`px-4 py-2 text-xs font-semibold hover:!text-white transition cursor-pointer border-b-2 !bg-transparent !border-t-0 !border-l-0 !border-r-0 !shadow-none !h-auto ${subpage === id ? '!text-[#4fd1b4] border-[#4fd1b4]' : '!text-[#88aab8] border-transparent'}`}
              type="button"
              onClick={() => handleSubpageChange(id)}
            >
              {label}
            </button>
          ))}
        </nav>
      )}

      {loading && <p className="text-xs text-[#88aab8]">Đang tải Pro Lab...</p>}
      {error && <p className="p-3 rounded-xl bg-rose-950/20 border border-rose-900/30 text-rose-400 text-xs font-semibold">{error}</p>}

      {isModulePage && (
        <>
          <nav className="flex justify-between items-center pb-2 border-b border-[#88aab8]/15 text-xs">
            <button
              type="button"
              className="text-[#4fd1b4] hover:text-[#6ee0c8] transition font-bold cursor-pointer border-none bg-transparent !shadow-none !h-auto !p-0"
              onClick={() => setSubpage('overview')}
            >
              ← Overview
            </button>
            <div className="flex items-center gap-1 text-[#5e7a72]">
              <a onClick={() => setSubpage('overview')} role="button" tabIndex={0} className="hover:text-[#4fd1b4] cursor-pointer">Pro Lab</a>
              <span aria-hidden>/</span>
              <span className="text-white font-semibold">{MODULE_LIST.find((m) => m.id === subpage)?.label || subpage}</span>
            </div>
          </nav>

          <div className="flex flex-wrap gap-2 py-3 border-b border-[#88aab8]/10">
            {MODULE_LIST.map((mod) => (
              <button
                key={mod.id}
                type="button"
                className={`px-3 py-1.5 rounded-lg text-[10px] font-bold transition cursor-pointer border ${subpage === mod.id ? '!bg-[#4fd1b4]/10 !border-[#4fd1b4]/20 !text-[#4fd1b4]' : '!bg-[#0c1720]/40 !border-[#88aab8]/10 !text-[#a0b8b0] hover:!border-[#4fd1b4]/30'}`}
                onClick={() => setSubpage(mod.id)}
              >
                {mod.label}
              </button>
            ))}
          </div>
        </>
      )}

      <AnimatePresence mode="wait">
        {subpage === 'strategy-copilot' && (
          <StrategyCopilotPage key="strategy-copilot" onBack={() => setSubpage('overview')} />
        )}
        {subpage === 'blueprint-swarm' && (
          <BlueprintSwarmPage key="blueprint-swarm" onBack={() => setSubpage('overview')} />
        )}
        {subpage === 'optimizer-scenario' && (
          <OptimizerScenarioPage key="optimizer-scenario" onBack={() => setSubpage('overview')} />
        )}
        {subpage === 'backtest-validation' && (
          <ProLabBacktestStudioPage
            key="backtest-validation"
            sessionId={sessionId}
            selectedBlueprintId={selectedBlueprintId}
            workspace={workspace}
            accessToken={accessToken}
            onBack={() => setSubpage('overview')}
            onOpenBlueprints={() => setSubpage('blueprints')}
          />
        )}
        {subpage === 'data-router-export' && (
          <DataRouterExportPage key="data-router-export" onBack={() => setSubpage('overview')} />
        )}
        {subpage === 'journal-report' && (
          <JournalReportPage key="journal-report" onBack={() => setSubpage('overview')} />
        )}
        {subpage === 'auto-copy' && (
          <AutoCopyPaperPage key="auto-copy" onBack={() => setSubpage('overview')} />
        )}

        {!['strategy-copilot', 'blueprint-swarm', 'optimizer-scenario', 'backtest-validation', 'data-router-export', 'journal-report', 'auto-copy'].includes(subpage) && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.2 }}
            className={subpage === 'overview' ? "grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-6 items-start w-full" : "w-full flex flex-col gap-6"}
          >
            <div className={subpage === 'overview' ? "grid gap-6" : "w-full"}>
              {subpage === 'overview' && (
                <>
                  <ProLabHero onBack={onBack} />
                  <ProLabOverviewPage
                    teaser={teaser}
                    workspace={workspace}
                    catalog={catalog}
                    workspaceState={workspaceState}
                    accessToken={accessToken}
                    onIssueToken={handleIssueAccessToken}
                    onLoadWorkspace={() => loadWorkspace()}
                    onOpenAdmin={onOpenAdmin}
                    onRunCommand={handleProviderCommand}
                    onNavigateModule={(moduleId) => setSubpage(moduleId)}
                    blueprintCount={blueprintCount}
                    experimentCount={experimentCount}
                  />
                  {workspace ? (
                    <RecentExperimentsTable
                      experiments={workspace.experiments}
                      onExportReport={handleExportReport}
                    />
                  ) : null}
                </>
              )}
              {subpage === 'blueprints' && (
                <ProLabBlueprintsPage
                  form={form}
                  setForm={setForm}
                  selectedBlueprintId={selectedBlueprintId}
                  setSelectedBlueprintId={setSelectedBlueprintId}
                  compareRightId={compareRightId}
                  setCompareRightId={setCompareRightId}
                  compareResult={compareResult}
                  workspace={workspace}
                  onSaveBlueprint={handleSaveBlueprint}
                  onUpdateBlueprint={handleUpdateBlueprint}
                  onArchiveBlueprint={handleArchiveBlueprint}
                  onCompareBlueprints={handleCompareBlueprints}
                />
              )}
              {subpage === 'experiments' && (
                <ProLabExperimentsPage
                  workspace={workspace}
                  catalog={catalog}
                  lastRun={lastRun}
                  selectedBlueprintId={selectedBlueprintId}
                  onScenarioRun={handleScenarioRun}
                  onBacktestRun={handleBacktestRun}
                  onRunCommand={handleProviderCommand}
                  onExportReport={handleExportReport}
                  reportExport={reportExport}
                />
              )}
              {subpage === 'sessions' && (
                <ProLabSessionsPage
                  sessionsPayload={sessionsPayload}
                  onRefresh={() => loadSessions()}
                  onRevoke={handleRevokeSession}
                />
              )}
            </div>

            {subpage === 'overview' && (
              <aside className="grid gap-6">
                <RiskControlsPanel />
                <QuickControlsPanel />
              </aside>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {result && (
        <section className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-900/30 shadow-md flex flex-col gap-3 mt-6">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">Kết quả gần nhất</h2>
          <p className="text-xs text-[#88aab8]">Type: {result.type}</p>
          <p className="text-xs text-[#88aab8]">ID: {result.payload.blueprint_id || result.payload.experiment_id || result.payload.run_id || result.payload.token_id}</p>
          <ProLabRunSummary payload={result.payload} />
        </section>
      )}
    </section>
  )
}

function recentIsoDate(daysAgo) {
  const value = new Date()
  value.setDate(value.getDate() - daysAgo)
  return value.toISOString().slice(0, 10)
}

function ProLabHero({ onBack }) {
  return (
    <header className="p-6 rounded-2xl bg-gradient-to-r from-[#101d26]/80 to-[#0c1720]/50 border border-[#88aab8]/15 shadow-md flex flex-col md:flex-row gap-6 justify-between items-center relative w-full">
      <div 
        role="button" 
        tabIndex={0} 
        className="absolute top-4 right-4 text-xs font-semibold text-[#4fd1b4] hover:text-[#6ee0c8] hover:underline cursor-pointer transition duration-150" 
        onClick={onBack}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onBack() }}
      >
        Home
      </div>
      <div className="flex-1 flex flex-col gap-2">
        <h1 className="text-xl font-extrabold text-white">Pro Lab</h1>
        <p className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">Personal Trading Research Cockpit</p>
        <p className="text-xs text-[#88aab8] leading-relaxed max-w-lg">
          Your private workspace to design, test, critique, and manage
          trading strategies. From hypothesis to live research with
          rigor, control risk, and build repeatable edge.
        </p>
      </div>
      <div className="flex flex-col gap-3 shrink-0 w-full md:w-auto">
        <div className="flex justify-between items-center text-[10px] font-bold text-[#5e7a72] px-2">
          {WORKFLOW_STEPS.map((step, index) => (
            <div key={step.id} className="relative flex items-center">
              <span>{step.label}</span>
              {index < WORKFLOW_STEPS.length - 1 && (
                <span className="flex items-center mx-2">
                  <span className="w-8 h-[1px] bg-[#88aab8]/15" />
                  <span className="text-[#88aab8]/30 ml-0.5">›</span>
                </span>
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between items-center relative px-4">
          {WORKFLOW_STEPS.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`w-[42px] h-[42px] rounded-full flex items-center justify-center border bg-[#0c1720] transition-all ${
                step.id === 'idea' ? 'border-[#4fd1b4]/30 bg-[#4fd1b4]/5 text-[#4fd1b4]' :
                step.id === 'build' ? 'border-[#3b82f6]/30 bg-[#3b82f6]/5 text-[#3b82f6]' :
                step.id === 'validate' ? 'border-[#f59e0b]/30 bg-[#f59e0b]/5 text-[#f59e0b]' :
                'border-emerald-500/30 bg-emerald-500/5 text-emerald-500'
              }`}>
                {step.id === 'idea' && <IdeaIcon />}
                {step.id === 'build' && <BuildIcon />}
                {step.id === 'validate' && <ValidateIcon />}
                {step.id === 'operate' && <OperateIcon />}
              </div>
              {index < WORKFLOW_STEPS.length - 1 && <span className="flex-1 h-[2px] bg-[#88aab8]/10" />}
            </div>
          ))}
        </div>
        <div className="flex justify-between text-[8px] text-[#5e7a72] leading-snug text-center gap-2">
          {WORKFLOW_STEPS.map((step) => (
            <span key={step.id} className="flex-1">{step.description}</span>
          ))}
        </div>
      </div>
    </header>
  )
}

function RiskControlsPanel() {
  const riskScore = 0.74
  const metrics = [
    { label: 'Max Gross Exposure', value: '78%' },
    { label: 'Net Exposure', value: '18%' },
    { label: 'Leverage (Gross)', value: '1.42x' },
    { label: 'Volatility (Ann.)', value: '14.6%' },
    { label: 'Largest Position', value: '6.1%' },
    { label: 'Portfolio VaR (95%)', value: '2.35%' },
    { label: 'Expected Shortfall (95%)', value: '3.61%' },
    { label: 'Liquidity Score', value: 'High' },
    { label: 'Concentration (Top 5)', value: '24%' },
  ]

  return (
    <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
      <div className="flex justify-between items-center border-b border-[#88aab8]/10 pb-2.5">
        <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <strong>Risk & Controls</strong>
        </div>
        <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">This Workspace</span>
      </div>

      <div className="flex flex-col items-center p-4 bg-[#0c1720]/40 rounded-xl border border-[#88aab8]/10 relative overflow-hidden gap-1">
        <div className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Current Risk</div>
        <div className="text-2xl font-extrabold text-white">
          <span>{riskScore}</span>
          <span className="text-xs text-[#5e7a72] font-semibold">/ 1.00</span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/20">Moderate</span>
        <div className="w-full h-10 mt-2">
          <svg viewBox="0 0 200 40" className="w-full h-full">
            <polyline
              fill="none"
              stroke="#4fd1b4"
              strokeWidth="2"
              points="0,30 20,28 40,32 60,25 80,20 100,22 120,18 140,15 160,12 180,14 200,10"
            />
          </svg>
          <div className="flex justify-between text-[8px] text-[#5e7a72] font-semibold">
            <span>May 2</span><span>May 9</span><span>May 16</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {metrics.map((m) => (
          <div key={m.label} className="flex justify-between py-1.5 border-b border-[#88aab8]/10 text-xs">
            <span className="text-[#88aab8]">{m.label}</span>
            <span className="font-bold text-white">{m.value}</span>
          </div>
        ))}
      </div>

      <button type="button" className="text-[10px] font-bold text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer text-center mt-2 border-none bg-transparent">View Risk Dashboard →</button>
    </section>
  )
}

function QuickControlsPanel() {
  const controls = [
    { icon: '⏱', label: 'Risk Limits' },
    { icon: '⚡', label: 'Kill Switch' },
    { icon: '🛡', label: 'Trade Blocks' },
    { icon: '🔔', label: 'Alerts' },
  ]
  return (
    <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Quick Controls</h3>
      <div className="grid grid-cols-2 gap-3">
        {controls.map((c) => (
          <button key={c.label} type="button" className="p-3 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col items-center gap-1.5 hover:border-[#4fd1b4]/30 hover:bg-[#0c1720]/60 transition cursor-pointer active:scale-95 text-xs text-[#edf7f5]">
            <span className="text-base">{c.icon}</span>
            <span className="text-[10px] font-bold text-[#edf7f5]">{c.label}</span>
          </button>
        ))}
      </div>
    </section>
  )
}

function RecentExperimentsTable() {
  const demoExperiments = [
    { id: 'E-1247', strategy: 'Mean Reversion v3', status: 'Completed', statusColor: 'green', lastRun: 'May 16, 2025 10:22 AM', sharpe: '1.38', returnOOS: '18.42%', returnVal: '-8.21%', maxDD: '', hasPlay: true },
    { id: 'E-1246', strategy: 'Trend Following v2', status: 'Completed', statusColor: 'green', lastRun: 'May 16, 2025 9:41 AM', sharpe: '1.12', returnOOS: '14.37%', returnVal: '-7.14%', maxDD: '', hasPlay: true },
    { id: 'E-1245', strategy: 'Cross-Sectional Value', status: 'Running', statusColor: 'yellow', lastRun: 'May 16, 2025 9:12 AM', sharpe: '—', returnOOS: '—', returnVal: '—', maxDD: '', hasPlay: false },
    { id: 'E-1244', strategy: 'Options Vol Harvest', status: 'Completed', statusColor: 'green', lastRun: 'May 15, 2025 4:03 PM', sharpe: '0.87', returnOOS: '9.21%', returnVal: '-6.09%', maxDD: '', hasPlay: true },
    { id: 'E-1243', strategy: 'Macro Regime Rotation', status: 'Draft', statusColor: 'gray', lastRun: 'May 15, 2025 2:18 PM', sharpe: '', returnOOS: '', returnVal: '', maxDD: '', hasPlay: false },
  ]

  const items = demoExperiments

  return (
    <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
      <div className="flex justify-between items-center pb-2 border-b border-[#88aab8]/15">
        <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
          <span className="text-xs">🔬</span>
          <h3>Recent Experiments</h3>
        </div>
        <button type="button" className="text-[#4fd1b4] hover:text-[#6ee0c8] cursor-pointer hover:underline border-none bg-transparent p-0">View All Experiments →</button>
      </div>
      <div className="overflow-x-auto [scrollbar-width:thin]">
        <table className="w-full text-left border-collapse text-xs min-w-[800px]">
          <thead>
            <tr>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15"></th>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Experiment</th>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Strategy / Blueprint</th>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Status</th>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Last Run</th>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Sharpe (OOS)</th>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Return (OOS)</th>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Max DD</th>
            <th className="pb-2 text-[#5e7a72] font-bold uppercase tracking-wider text-[10px] border-b border-[#88aab8]/15">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((exp) => (
            <tr key={exp.id}>
              <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]"><span className="text-[#5e7a72] hover:text-amber-400 cursor-pointer">☆</span></td>
              <td className="py-3 border-b border-[#88aab8]/10 font-bold text-white">{exp.id}</td>
              <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">{exp.strategy}</td>
              <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  exp.statusColor === 'green' ? 'bg-emerald-950/20 text-emerald-400 border border-emerald-900/30' :
                  exp.statusColor === 'yellow' ? 'bg-amber-950/20 text-amber-400 border border-amber-900/30' :
                  'bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5]'
                }`}>
                  {exp.status} {exp.statusColor === 'green' ? '✓' : exp.statusColor === 'yellow' ? '⟳' : '✎'}
                </span>
              </td>
              <td className="py-3 border-b border-[#88aab8]/10 text-[#5e7a72]">{exp.lastRun}</td>
              <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">{exp.sharpe || '—'}</td>
              <td className="py-3 border-b border-[#88aab8]/10 text-emerald-400 font-bold">{exp.returnOOS || '—'}</td>
              <td className="py-3 border-b border-[#88aab8]/10 text-rose-400 font-bold">{exp.returnVal || '—'}</td>
              <td className="py-3 border-b border-[#88aab8]/10 text-[#edf7f5]">
                <div className="flex gap-2">
                  {exp.hasPlay && <button type="button" className="text-white bg-[#0c1720]/60 border border-[#88aab8]/10 hover:border-[#4fd1b4]/30 w-6 h-6 flex items-center justify-center p-0 rounded-lg text-xs">▶</button>}
                  <button type="button" className="text-white bg-[#0c1720]/60 border border-[#88aab8]/10 hover:border-[#4fd1b4]/30 w-6 h-6 flex items-center justify-center p-0 rounded-lg text-xs">⋯</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </section>
  )
}

function IdeaIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
    </svg>
  )
}

function BuildIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  )
}

function ValidateIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  )
}

function OperateIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  )
}

function ProLabRunSummary({ payload }) {
  const output = payload?.output_payload || {}
  const sections = []
  if (output.strategy_draft) {
    sections.push(['Strategy draft', [
      `Market: ${output.strategy_draft.market}`,
      `Universe: ${(output.strategy_draft.universe || []).join(', ')}`,
      `Signals: ${(output.strategy_draft.signal_stack || []).join(' / ')}`,
    ]])
  }
  if (output.role_memos) {
    sections.push(['Swarm memos', output.role_memos.map((item) => `${item.role}: ${item.memo}`)])
  }
  if (output.allocation) {
    sections.push(['Allocation', output.allocation.map((item) => `${item.ticker}: ${item.target_weight_pct}% (${item.role})`)])
  }
  if (output.validation_suite) {
    sections.push(['Validation', output.validation_suite.map((item) => `${item.check}: ${item.setting}`)])
  }
  if (output.source_map) {
    sections.push(['Data router', output.source_map.map((item) => `${item.domain}: ${item.primary} → ${item.fallback} (${item.status})`)])
  }
  if (output.files) {
    sections.push(['Export files', output.files.map((item) => `${item.filename} · ${item.language}`)])
  }
  if (output.discipline_score != null) {
    sections.push(['Journal', [`Score: ${output.discipline_score}/100`, ...((output.rule_breaks || []).length ? output.rule_breaks : ['No obvious rule break detected'])]])
  }
  if (!sections.length) return null
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-2">
      {sections.map(([title, lines]) => (
        <article key={title} className="flex flex-col gap-1">
          <strong className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">{title}</strong>
          {lines.slice(0, 4).map((line) => <span key={line} className="text-xs text-[#88aab8]">{line}</span>)}
        </article>
      ))}
    </div>
  )
}
