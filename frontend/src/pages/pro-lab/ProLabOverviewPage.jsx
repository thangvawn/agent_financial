export default function ProLabOverviewPage({
  teaser,
  workspace,
  catalog,
  workspaceState,
  accessToken,
  onIssueToken,
  onLoadWorkspace,
  onOpenAdmin,
  onRunCommand,
  onNavigateModule,
  blueprintCount,
  experimentCount,
}) {
  const privateProvider = catalog?.providers?.find((item) => item.provider_id === 'private_auto_copy_trading')

  const moduleCards = [
    {
      id: 'strategy-copilot',
      color: '#3b82f6',
      title: 'Strategy Copilot',
      description: 'AI copilots to ideate, refine and critique strategies.',
      status: 'Active',
      statusType: 'active',
      providerId: 'strategy_copilot',
      commandId: 'natural_language_strategy',
    },
    {
      id: 'swarm',
      color: '#8b5cf6',
      title: 'Swarm Committee',
      description: 'Multi-agent debates and research referee.',
      status: '3 Active',
      statusType: 'info',
      icon: 'swarm',
      providerId: 'swarm_committee',
      commandId: 'quant_strategy_review',
    },
    {
      id: 'blueprint',
      color: '#6366f1',
      title: 'Blueprint Designer',
      description: 'Visual strategy builder with no-code blocks.',
      status: 'Open →',
      statusType: 'link',
      providerId: null,
      commandId: null,
    },
    {
      id: 'optimizer',
      color: '#10b981',
      title: 'Optimizer Lab',
      description: 'Parameter search and robust optimization.',
      status: 'Ready',
      statusType: 'ready',
      providerId: 'optimizer_lab',
      commandId: 'risk_budget_optimizer',
    },
    {
      id: 'scenario',
      color: '#f59e0b',
      title: 'Scenario Lab',
      description: 'Macro & market scenario modeling and shocks.',
      status: `${experimentCount || 6} Scenarios`,
      statusType: 'info',
      providerId: 'scenario_lab',
      commandId: 'fx_rate_stress',
    },
    {
      id: 'backtest',
      color: '#ef4444',
      title: 'Backtest Lab',
      description: 'High-fidelity backtests with costs and slippage.',
      status: 'Last run: 2h ago',
      statusType: 'info',
      providerId: 'backtest_lab',
      commandId: 'benchmark_sandbox',
    },
    {
      id: 'validation',
      color: '#22c55e',
      title: 'Validation Lab',
      description: 'Walk-forward, OOS and model diagnostics.',
      status: 'Pass',
      statusType: 'pass',
      providerId: 'validation_lab',
      commandId: 'walk_forward_monte_carlo',
    },
    {
      id: 'data-router',
      color: '#06b6d4',
      title: 'Data Router',
      description: 'Connect, clean and route data to your workflows.',
      status: 'All Good',
      statusType: 'good',
      providerId: 'data_router',
      commandId: 'source_health_check',
    },
    {
      id: 'export',
      color: '#84cc16',
      title: 'Export Lab',
      description: 'Export strategies, signals and results.',
      status: 'CSV / JSON',
      statusType: 'info',
      providerId: 'export_lab',
      commandId: 'strategy_code_export',
    },
    {
      id: 'journal',
      color: '#a855f7',
      title: 'Journal Lab',
      description: 'Research journal and experiment notes.',
      status: '+ 12 New',
      statusType: 'new',
      providerId: 'journal_lab',
      commandId: 'shadow_account_review',
    },
    {
      id: 'report',
      color: '#0ea5e9',
      title: 'Report Builder',
      description: 'Build and schedule research reports.',
      status: '3 Reports',
      statusType: 'info',
      providerId: 'report_builder',
      commandId: 'research_memo',
    },
    {
      id: 'auto-copy',
      color: '#f97316',
      title: 'Auto / Copy Paper Plan',
      description: 'Auto-generate copy paper plans from research.',
      status: `Drafts: ${blueprintCount || 2}`,
      statusType: 'info',
      providerId: 'private_auto_copy_trading',
      commandId: 'paper_auto_trading_plan',
    },
  ]

  const MODULE_ROUTES = {
    'strategy-copilot': 'strategy-copilot',
    'swarm': 'blueprint-swarm',
    'blueprint': 'blueprint-swarm',
    'optimizer': 'optimizer-scenario',
    'scenario': 'optimizer-scenario',
    'backtest': 'backtest-validation',
    'validation': 'backtest-validation',
    'data-router': 'data-router-export',
    'export': 'data-router-export',
    'journal': 'journal-report',
    'report': 'journal-report',
    'auto-copy': 'auto-copy',
  }

  function handleCardClick(card) {
    const route = MODULE_ROUTES[card.id]
    if (route && onNavigateModule) {
      onNavigateModule(route)
      return
    }
    if (!card.providerId || !card.commandId) return
    const isPrivate = card.providerId === 'private_auto_copy_trading'
    if (isPrivate && !privateProvider) return
    onRunCommand(card.providerId, card.commandId, defaultPayloadFor(card.providerId, card.commandId))
  }

  return (
    <section className="pl-overview">
      <div className="pl-module-grid">
        {moduleCards.map((card) => {
          const isPrivate = card.providerId === 'private_auto_copy_trading'
          const isHidden = isPrivate && !privateProvider
          return (
            <article
              key={card.id}
              className={`pl-module-card ${isHidden ? 'pl-module-card--disabled' : ''}`}
              onClick={() => handleCardClick(card)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleCardClick(card)}
            >
              <div className="pl-module-card__top">
                <div className="pl-module-card__icon" style={{ background: `${card.color}18`, borderColor: `${card.color}30` }}>
                  <CardIcon id={card.id} color={card.color} />
                </div>
                <div className="pl-module-card__text">
                  <h3 className="pl-module-card__title">{card.title}</h3>
                  <p className="pl-module-card__desc">{card.description}</p>
                </div>
              </div>
              <div className="pl-module-card__footer">
                <ModuleStatus status={card.status} type={card.statusType} />
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}

function CardIcon({ id, color }) {
  const style = { color }
  const props = { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round', style }

  switch (id) {
    case 'strategy-copilot':
      return <svg {...props}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
    case 'swarm':
      return <svg {...props}><circle cx="12" cy="12" r="3" /><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41" /></svg>
    case 'blueprint':
      return <svg {...props}><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18M9 21V9" /></svg>
    case 'optimizer':
      return <svg {...props}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
    case 'scenario':
      return <svg {...props}><circle cx="12" cy="12" r="10" /><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>
    case 'backtest':
      return <svg {...props}><path d="M18 20V10M12 20V4M6 20v-6" /></svg>
    case 'validation':
      return <svg {...props}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="M22 4L12 14.01l-3-3" /></svg>
    case 'data-router':
      return <svg {...props}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" /></svg>
    case 'export':
      return <svg {...props}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
    case 'journal':
      return <svg {...props}><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /></svg>
    case 'report':
      return <svg {...props}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
    case 'auto-copy':
      return <svg {...props}><rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" /></svg>
    default:
      return <svg {...props}><circle cx="12" cy="12" r="10" /></svg>
  }
}

function ModuleStatus({ status, type }) {
  const classMap = {
    active: 'pl-module-status--active',
    ready: 'pl-module-status--ready',
    pass: 'pl-module-status--pass',
    good: 'pl-module-status--good',
    info: 'pl-module-status--info',
    link: 'pl-module-status--link',
    new: 'pl-module-status--new',
  }
  return (
    <span className={`pl-module-status ${classMap[type] || ''}`}>
      {type === 'active' && <span className="pl-module-status__dot" />}
      {type === 'pass' && '✓ '}
      {type === 'good' && '✓ '}
      {status}
    </span>
  )
}

function defaultPayloadFor(providerId, commandId) {
  if (providerId === 'strategy_copilot') {
    return { idea: 'Tìm strategy VN equities ưu tiên doanh nghiệp chất lượng, momentum xác nhận và drawdown được kiểm soát.', market: 'Vietnam equities', horizon: 'monthly', risk_budget_pct: 2 }
  }
  if (providerId === 'swarm_committee') {
    return { review_focus: 'overfit, liquidity, benchmark gap, execution assumptions', validation_depth: 'standard' }
  }
  if (providerId === 'optimizer_lab') {
    return { method: 'risk_parity', max_weight_pct: 35, target_volatility_pct: 18 }
  }
  if (providerId === 'validation_lab') {
    return { window_months: 6, cost_bps: 20, simulations: 1000 }
  }
  if (providerId === 'data_router') {
    return { sources: ['prices', 'financials', 'news', 'macro'], required_fields: ['price', 'volume', 'financials', 'news', 'macro'] }
  }
  if (providerId === 'export_lab') {
    return { target: 'python', include_alerts: true }
  }
  if (providerId === 'journal_lab') {
    return { journal_text: 'Paper journal: followed setup, no FOMO, position size within plan.', max_daily_loss_pct: 1, max_rule_breaks: 2 }
  }
  if (providerId === 'backtest_lab') {
    return { start_date: '2023-01-01', end_date: '2025-12-31', initial_capital: 100000000 }
  }
  if (providerId === 'scenario_lab') {
    return { shock_label: 'fx_rate_stress', usd_vnd_rate: 25850, policy_rate_pct: 4.5 }
  }
  if (providerId === 'private_auto_copy_trading' && commandId === 'copy_trading_mapping_review') {
    return { source_style: 'quality momentum', personal_risk_budget_pct: 2, excluded_assets: [] }
  }
  if (providerId === 'private_auto_copy_trading') {
    return { strategy_brief: 'Paper-only automation plan for personal use.', max_daily_loss_pct: 1, max_position_pct: 10 }
  }
  return { memo_focus: 'Review research question, caveats and next validation steps.' }
}
