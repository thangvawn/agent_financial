import { useEffect, useState } from 'react'

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
import BacktestValidationPage from './BacktestValidationPage'
import BlueprintSwarmPage from './BlueprintSwarmPage'
import DataRouterExportPage from './DataRouterExportPage'
import JournalReportPage from './JournalReportPage'
import OptimizerScenarioPage from './OptimizerScenarioPage'
import ProLabBlueprintsPage from './ProLabBlueprintsPage'
import ProLabExperimentsPage from './ProLabExperimentsPage'
import ProLabOverviewPage from './ProLabOverviewPage'
import ProLabSessionsPage from './ProLabSessionsPage'
import StrategyCopilotPage from './StrategyCopilotPage'
import './pro-lab.css'
import './pro-lab-cockpit.css'

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
  { id: 'backtest-validation', label: 'Backtest / Validation' },
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
        let tokenToUse = accessToken
        if (teaserPayload.enabled && teaserPayload.pro_eligible && !tokenToUse) {
          const accessPayload = await issueProLabAccessToken(sessionId)
          if (cancelled) return
          tokenToUse = accessPayload.access_token
          setAccessToken(tokenToUse)
        }
        if (teaserPayload.enabled && teaserPayload.pro_eligible) {
          const [workspacePayload, catalogPayload, statePayload] = await Promise.all([
            fetchProLabWorkspace(sessionId, tokenToUse),
            fetchProLabCatalog(tokenToUse),
            fetchProLabWorkspaceState(sessionId, tokenToUse),
          ])
          if (cancelled) return
          setWorkspace(workspacePayload)
          setCatalog(catalogPayload)
          setWorkspaceState(statePayload)
          if (statePayload.active_page) setSubpage(statePayload.active_page)
          hydrateSelection(workspacePayload)
          const sessions = await fetchProLabSessions(sessionId, accessToken)
          if (cancelled) return
          setSessionsPayload(sessions)
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [sessionId, accessToken])

  function hydrateSelection(workspacePayload) {
    const firstBlueprint = workspacePayload.blueprints[0]
    setSelectedBlueprintId((current) => current || firstBlueprint?.blueprint_id || '')
    setCompareRightId((current) => current || workspacePayload.blueprints[1]?.blueprint_id || '')
    if (firstBlueprint) {
      setForm({
        name: firstBlueprint.name,
        objective: firstBlueprint.objective,
        asset_universe: firstBlueprint.asset_universe.join(','),
        benchmark: firstBlueprint.benchmark,
        rebalance_frequency: firstBlueprint.rebalance_frequency,
        risk_constraints: firstBlueprint.risk_constraints,
        assumptions_note: firstBlueprint.assumptions_note || '',
      })
    }
  }

  async function loadWorkspace(tokenOverride = accessToken) {
    setError('')
    const [payload, catalogPayload, statePayload] = await Promise.all([
      fetchProLabWorkspace(sessionId, tokenOverride),
      fetchProLabCatalog(tokenOverride),
      fetchProLabWorkspaceState(sessionId, tokenOverride),
    ])
    setWorkspace(payload)
    setCatalog(catalogPayload)
    setWorkspaceState(statePayload)
    hydrateSelection(payload)
    const sessions = await fetchProLabSessions(sessionId, tokenOverride)
    setSessionsPayload(sessions)
    return payload
  }

  async function loadSessions(tokenOverride = accessToken) {
    setError('')
    const payload = await fetchProLabSessions(sessionId, tokenOverride)
    setSessionsPayload(payload)
    return payload
  }

  async function handleIssueAccessToken() {
    setError('')
    try {
      const payload = await issueProLabAccessToken(sessionId)
      setAccessToken(payload.access_token)
      await loadWorkspace(payload.access_token)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleSaveBlueprint() {
    setError('')
    try {
      const payload = await createProLabBlueprint(
        {
          user_id: sessionId,
          name: form.name,
          objective: form.objective,
          asset_universe: form.asset_universe.split(',').map((item) => item.trim()).filter(Boolean),
          benchmark: form.benchmark,
          rebalance_frequency: form.rebalance_frequency,
          risk_constraints: form.risk_constraints,
          assumptions_note: form.assumptions_note,
        },
        accessToken,
      )
      setResult({ type: 'blueprint_created', payload })
      await loadWorkspace()
      setSelectedBlueprintId(payload.blueprint_id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleUpdateBlueprint() {
    if (!selectedBlueprintId) return
    setError('')
    try {
      const payload = await updateProLabBlueprint(
        selectedBlueprintId,
        {
          user_id: sessionId,
          name: form.name,
          objective: form.objective,
          asset_universe: form.asset_universe.split(',').map((item) => item.trim()).filter(Boolean),
          benchmark: form.benchmark,
          rebalance_frequency: form.rebalance_frequency,
          risk_constraints: form.risk_constraints,
          assumptions_note: form.assumptions_note,
        },
        accessToken,
      )
      setResult({ type: 'blueprint_updated', payload })
      await loadWorkspace()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleArchiveBlueprint() {
    if (!selectedBlueprintId) return
    setError('')
    try {
      const payload = await archiveProLabBlueprint(selectedBlueprintId, sessionId, accessToken)
      setResult({ type: 'blueprint_archived', payload })
      await loadWorkspace()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleCompareBlueprints() {
    if (!selectedBlueprintId || !compareRightId) return
    setError('')
    try {
      const payload = await compareProLabBlueprints(sessionId, selectedBlueprintId, compareRightId, accessToken)
      setCompareResult(payload)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleScenarioRun() {
    if (!selectedBlueprintId) return
    setError('')
    try {
      const payload = await runProLabScenario(
        {
          user_id: sessionId,
          blueprint_id: selectedBlueprintId,
          scenario_preset: 'fx_stress',
          usd_vnd_rate: 25850,
          sbv_interest_rate_pct: 4.5,
        },
        accessToken,
      )
      setResult({ type: 'scenario', payload })
      await loadWorkspace()
      setSubpage('experiments')
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleBacktestRun() {
    if (!selectedBlueprintId) return
    setError('')
    try {
      const payload = await runProLabBacktest(
        {
          user_id: sessionId,
          blueprint_id: selectedBlueprintId,
          start_date: '2023-01-01',
          end_date: '2025-12-31',
          initial_capital: 100000000,
        },
        accessToken,
      )
      setResult({ type: 'backtest', payload })
      await loadWorkspace()
      setSubpage('experiments')
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleProviderCommand(providerId, commandId, inputPayload = {}) {
    setError('')
    try {
      const payload = await runProLabCommand(
        {
          user_id: sessionId,
          blueprint_id: selectedBlueprintId || null,
          provider_id: providerId,
          command_id: commandId,
          input_payload: inputPayload,
        },
        accessToken,
      )
      setLastRun(payload)
      setResult({ type: 'provider_run', payload })
      await loadWorkspace()
      setSubpage('experiments')
    } catch (err) {
      setError(err.message)
    }
  }

  async function persistWorkspaceState(nextSubpage = subpage) {
    if (!accessToken) return
    try {
      const payload = await saveProLabWorkspaceState(
        {
          user_id: sessionId,
          active_page: nextSubpage,
          open_panels: ['catalog', 'experiments'],
          selected_blueprint_id: selectedBlueprintId || null,
          selected_experiment_id: workspace?.experiments?.[0]?.experiment_id || null,
          layout: { density: 'comfortable', right_panel: 'run_details' },
          notes: workspaceState?.notes || '',
        },
        accessToken,
      )
      setWorkspaceState(payload)
    } catch {
      // Workspace autosave must not block research actions.
    }
  }

  function handleSubpageChange(nextSubpage) {
    if (nextSubpage === 'backtest-studio') {
      onOpenBacktestStudio?.()
      return
    }
    setSubpage(nextSubpage)
    persistWorkspaceState(nextSubpage)
  }

  async function handleExportReport(experimentId) {
    setError('')
    try {
      const payload = await exportProLabReport(sessionId, experimentId, accessToken)
      setReportExport(payload)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRevokeSession(tokenId) {
    setError('')
    try {
      const payload = await revokeProLabSession(sessionId, tokenId, accessToken)
      setResult({ type: 'session_revoked', payload })
      if (payload.token_id === accessToken) {
        setAccessToken('')
        setWorkspace(null)
        setSessionsPayload(null)
        setCompareResult(null)
        setReportExport(null)
        return
      }
      await loadSessions()
    } catch (err) {
      setError(err.message)
    }
  }

  const blueprintCount = workspace?.blueprints?.length || 0
  const experimentCount = workspace?.experiments?.length || 0
  const isModulePage = ['strategy-copilot', 'blueprint-swarm', 'optimizer-scenario', 'backtest-validation', 'data-router-export', 'journal-report', 'auto-copy'].includes(subpage)
  const showTopHero = !isModulePage && subpage !== 'overview'

  return (
    <section className={`pl ${isModulePage ? 'pl--module-page' : ''}`}>
      {showTopHero ? <ProLabHero onBack={onBack} /> : null}

      {!isModulePage && (
        <nav className="pl-tabs" aria-label="Pro Lab sections">
          {PAGES.map(([id, label]) => (
            <button
              key={id}
              className={subpage === id ? 'pl-tab pl-tab--active' : 'pl-tab'}
              type="button"
              onClick={() => handleSubpageChange(id)}
            >
              {label}
            </button>
          ))}
        </nav>
      )}

      {loading && <p className="pl-state">Đang tải Pro Lab...</p>}
      {error && <p className="pl-state pl-state--error">{error}</p>}

      {isModulePage && (
        <>
          <nav className="pl-module-nav">
            <button
              type="button"
              className="pl-module-nav__back"
              onClick={() => setSubpage('overview')}
            >
              ← Overview
            </button>
            <div className="pl-module-nav__breadcrumb">
              <a onClick={() => setSubpage('overview')} role="button" tabIndex={0}>Pro Lab</a>
              <span aria-hidden>/</span>
              <span>{MODULE_LIST.find((m) => m.id === subpage)?.label || subpage}</span>
            </div>
          </nav>

          <div className="pl-module-switcher">
            {MODULE_LIST.map((mod) => (
              <button
                key={mod.id}
                type="button"
                className={`pl-module-switcher__btn ${subpage === mod.id ? 'pl-module-switcher__btn--active' : ''}`}
                onClick={() => setSubpage(mod.id)}
              >
                {mod.label}
              </button>
            ))}
          </div>
        </>
      )}

      {subpage === 'strategy-copilot' && (
        <StrategyCopilotPage onBack={() => setSubpage('overview')} />
      )}
      {subpage === 'blueprint-swarm' && (
        <BlueprintSwarmPage onBack={() => setSubpage('overview')} />
      )}
      {subpage === 'optimizer-scenario' && (
        <OptimizerScenarioPage onBack={() => setSubpage('overview')} />
      )}
      {subpage === 'backtest-validation' && (
        <BacktestValidationPage onBack={() => setSubpage('overview')} />
      )}
      {subpage === 'data-router-export' && (
        <DataRouterExportPage onBack={() => setSubpage('overview')} />
      )}
      {subpage === 'journal-report' && (
        <JournalReportPage onBack={() => setSubpage('overview')} />
      )}
      {subpage === 'auto-copy' && (
        <AutoCopyPaperPage onBack={() => setSubpage('overview')} />
      )}

      {!['strategy-copilot', 'blueprint-swarm', 'optimizer-scenario', 'backtest-validation', 'data-router-export', 'journal-report', 'auto-copy'].includes(subpage) && (
        <div className="pl-main-layout">
          <div className="pl-main-content">
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
            <aside className="pl-sidebar">
              <RiskControlsPanel />
              <QuickControlsPanel />
            </aside>
          )}
        </div>
      )}

      {result && (
        <section className="pl-result-dock">
          <h2>Kết quả gần nhất</h2>
          <p>Type: {result.type}</p>
          <p>ID: {result.payload.blueprint_id || result.payload.experiment_id || result.payload.run_id || result.payload.token_id}</p>
          <ProLabRunSummary payload={result.payload} />
        </section>
      )}
    </section>
  )
}

function ProLabHero({ onBack }) {
  return (
    <header className="pl-hero">
      <button type="button" className="pl-hero__home" onClick={onBack}>Home</button>
      <div className="pl-hero__left">
        <h1 className="pl-hero__title">Pro Lab</h1>
        <p className="pl-hero__subtitle">Personal Trading Research Cockpit</p>
        <p className="pl-hero__description">
          Your private workspace to design, test, critique, and manage
          trading strategies. From hypothesis to live research with
          rigor, control risk, and build repeatable edge.
        </p>
      </div>
      <div className="pl-hero__pipeline">
        <div className="pl-pipeline">
          {WORKFLOW_STEPS.map((step, index) => (
            <div key={step.id} className="pl-pipeline__step">
              <span className="pl-pipeline__label">{step.label}</span>
              {index < WORKFLOW_STEPS.length - 1 && (
                <span className="pl-pipeline__connector">
                  <span className="pl-pipeline__line" />
                  <span className="pl-pipeline__arrow-head">›</span>
                </span>
              )}
            </div>
          ))}
        </div>
        <div className="pl-pipeline__icons">
          {WORKFLOW_STEPS.map((step, index) => (
            <div key={step.id} className="pl-pipeline__icon-group">
              <div className={`pl-pipeline__circle pl-pipeline__circle--${step.id}`}>
                {step.id === 'idea' && <IdeaIcon />}
                {step.id === 'build' && <BuildIcon />}
                {step.id === 'validate' && <ValidateIcon />}
                {step.id === 'operate' && <OperateIcon />}
              </div>
              {index < WORKFLOW_STEPS.length - 1 && <span className="pl-pipeline__icon-line" />}
            </div>
          ))}
        </div>
        <div className="pl-pipeline__descs">
          {WORKFLOW_STEPS.map((step) => (
            <span key={step.id} className="pl-pipeline__desc">{step.description}</span>
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
    <section className="pl-risk-panel">
      <div className="pl-risk-panel__header">
        <div className="pl-risk-panel__title">
          <span className="pl-risk-dot" />
          <strong>Risk & Controls</strong>
        </div>
        <span className="pl-risk-panel__scope">This Workspace</span>
      </div>

      <div className="pl-risk-gauge">
        <div className="pl-risk-gauge__label">Current Risk</div>
        <div className="pl-risk-gauge__score">
          <span className="pl-risk-gauge__value">{riskScore}</span>
          <span className="pl-risk-gauge__max">/ 1.00</span>
        </div>
        <span className="pl-risk-gauge__level pl-risk-gauge__level--moderate">Moderate</span>
        <div className="pl-risk-sparkline">
          <svg viewBox="0 0 200 40" className="pl-risk-sparkline__svg">
            <polyline
              fill="none"
              stroke="#4fd1b4"
              strokeWidth="2"
              points="0,30 20,28 40,32 60,25 80,20 100,22 120,18 140,15 160,12 180,14 200,10"
            />
          </svg>
          <div className="pl-risk-sparkline__labels">
            <span>May 2</span><span>May 9</span><span>May 16</span>
          </div>
        </div>
      </div>

      <div className="pl-risk-metrics">
        {metrics.map((m) => (
          <div key={m.label} className="pl-risk-metric">
            <span className="pl-risk-metric__label">{m.label}</span>
            <span className="pl-risk-metric__value">{m.value}</span>
          </div>
        ))}
      </div>

      <button type="button" className="pl-risk-cta">View Risk Dashboard →</button>
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
    <section className="pl-quick-controls">
      <h3>Quick Controls</h3>
      <div className="pl-quick-controls__grid">
        {controls.map((c) => (
          <button key={c.label} type="button" className="pl-quick-control-btn">
            <span className="pl-quick-control-btn__icon">{c.icon}</span>
            <span className="pl-quick-control-btn__label">{c.label}</span>
          </button>
        ))}
      </div>
    </section>
  )
}

function RecentExperimentsTable({ experiments, onExportReport }) {
  const demoExperiments = [
    { id: 'E-1247', strategy: 'Mean Reversion v3', status: 'Completed', statusColor: 'green', lastRun: 'May 16, 2025 10:22 AM', sharpe: '1.38', returnOOS: '18.42%', returnVal: '-8.21%', maxDD: '', hasPlay: true },
    { id: 'E-1246', strategy: 'Trend Following v2', status: 'Completed', statusColor: 'green', lastRun: 'May 16, 2025 9:41 AM', sharpe: '1.12', returnOOS: '14.37%', returnVal: '-7.14%', maxDD: '', hasPlay: true },
    { id: 'E-1245', strategy: 'Cross-Sectional Value', status: 'Running', statusColor: 'yellow', lastRun: 'May 16, 2025 9:12 AM', sharpe: '—', returnOOS: '—', returnVal: '—', maxDD: '', hasPlay: false },
    { id: 'E-1244', strategy: 'Options Vol Harvest', status: 'Completed', statusColor: 'green', lastRun: 'May 15, 2025 4:03 PM', sharpe: '0.87', returnOOS: '9.21%', returnVal: '-6.09%', maxDD: '', hasPlay: true },
    { id: 'E-1243', strategy: 'Macro Regime Rotation', status: 'Draft', statusColor: 'gray', lastRun: 'May 15, 2025 2:18 PM', sharpe: '', returnOOS: '', returnVal: '', maxDD: '', hasPlay: false },
  ]

  const items = demoExperiments

  return (
    <section className="pl-experiments-table">
      <div className="pl-experiments-table__header">
        <div className="pl-experiments-table__title">
          <span className="pl-experiments-table__icon">🔬</span>
          <h3>Recent Experiments</h3>
        </div>
        <button type="button" className="pl-link-btn">View All Experiments →</button>
      </div>
      <table className="pl-table">
        <thead>
          <tr>
            <th></th>
            <th>Experiment</th>
            <th>Strategy / Blueprint</th>
            <th>Status</th>
            <th>Last Run</th>
            <th>Sharpe (OOS)</th>
            <th>Return (OOS)</th>
            <th>Max DD</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((exp) => (
            <tr key={exp.id}>
              <td><span className="pl-table__star">☆</span></td>
              <td className="pl-table__id">{exp.id}</td>
              <td>{exp.strategy}</td>
              <td>
                <span className={`pl-status pl-status--${exp.statusColor}`}>
                  {exp.status} {exp.statusColor === 'green' ? '✓' : exp.statusColor === 'yellow' ? '⟳' : '✎'}
                </span>
              </td>
              <td className="pl-table__muted">{exp.lastRun}</td>
              <td>{exp.sharpe || '—'}</td>
              <td className="pl-table__positive">{exp.returnOOS || '—'}</td>
              <td className="pl-table__negative">{exp.returnVal || '—'}</td>
              <td>
                <div className="pl-table__actions">
                  {exp.hasPlay && <button type="button" className="pl-table__action-btn">▶</button>}
                  <button type="button" className="pl-table__action-btn">⋯</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
    <div className="pl-result-summary">
      {sections.map(([title, lines]) => (
        <article key={title}>
          <strong>{title}</strong>
          {lines.slice(0, 4).map((line) => <span key={line}>{line}</span>)}
        </article>
      ))}
    </div>
  )
}
