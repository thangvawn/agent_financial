export default function ProLabExperimentsPage({
  workspace,
  catalog,
  lastRun,
  selectedBlueprintId,
  onScenarioRun,
  onBacktestRun,
  onRunCommand,
  onExportReport,
  reportExport,
}) {
  if (!workspace) {
    return <p className="pro-lab-state">Mở workspace Pro để chạy scenario hoặc backtest.</p>
  }
  const runActions = [
    {
      title: 'Scenario: FX / Rate Stress',
      summary: 'Xem blueprint nhạy với tỷ giá và lãi suất như thế nào.',
      button: 'Run scenario',
      onClick: onScenarioRun,
      disabled: !selectedBlueprintId,
      meta: 'macro sensitivity',
    },
    {
      title: 'Backtest: Benchmark Sandbox',
      summary: 'So sánh giả định với benchmark, có caveat về dữ liệu và execution.',
      button: 'Run backtest',
      onClick: onBacktestRun,
      disabled: !selectedBlueprintId,
      meta: 'historical sandbox',
    },
    {
      title: 'Memo: Research Note',
      summary: 'Tạo memo có cấu trúc để ghi lại thesis, caveat và next review.',
      button: 'Create memo',
      onClick: () => onRunCommand('report_builder', 'research_memo', defaultPayloadFor('report_builder', 'research_memo')),
      disabled: false,
      meta: 'report builder',
    },
    {
      title: 'Private: Auto / Copy Paper Plan',
      summary: 'Tạo plan paper-only với limit, kill switch và manual review.',
      button: 'Create paper plan',
      onClick: () => onRunCommand('private_auto_copy_trading', 'paper_auto_trading_plan', defaultPayloadFor('private_auto_copy_trading', 'paper_auto_trading_plan')),
      disabled: false,
      meta: 'private controls',
    },
  ]

  return (
    <section className="pro-lab-section">
      <section className="pro-lab-run-console">
        <div>
          <p className="pro-lab-eyebrow">Run Console</p>
          <h2>Chọn run cần chạy</h2>
          <p>Không cần đọc provider. Chọn mục tiêu nghiên cứu, hệ thống sẽ gọi command phù hợp.</p>
        </div>
        <span className="pro-lab-badge">{selectedBlueprintId ? 'Blueprint selected' : 'Create/select blueprint first'}</span>
      </section>

      <section className="pro-lab-action-grid">
        {runActions.map((action) => (
          <article key={action.title} className="pro-lab-action-card">
            <span className="pro-lab-badge">{action.meta}</span>
            <h3>{action.title}</h3>
            <p>{action.summary}</p>
            <button type="button" onClick={action.onClick} disabled={action.disabled}>
              {action.button}
            </button>
          </article>
        ))}
      </section>

      <div className="pro-lab-runs-layout">
        <section className="pro-lab-card pro-lab-advanced-catalog">
          <p className="pro-lab-eyebrow">Registry</p>
          <h3>Commands</h3>
          <p className="pro-lab-muted">Advanced view cho provider/command thô.</p>
          {catalog ? (
            <div className="pro-lab-stack">
              {catalog.providers.map((provider) => (
                <article key={provider.provider_id} className="pro-lab-mini-card">
                  <div className="pro-lab-provider-card__header">
                    <strong>{provider.label}</strong>
                    <span>{provider.category}</span>
                  </div>
                  <p>{provider.description}</p>
                  <div className="pro-lab-command-list">
                    {provider.commands.map((command) => (
                      <button
                        key={`${provider.provider_id}-${command.command_id}`}
                        type="button"
                        onClick={() => onRunCommand(provider.provider_id, command.command_id, defaultPayloadFor(provider.provider_id, command.command_id))}
                        disabled={!selectedBlueprintId && provider.provider_id !== 'report_builder'}
                      >
                        <span>{command.label}</span>
                        <small>{command.risk_level}</small>
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p>Catalog chưa được tải.</p>
          )}
        </section>

        <section className="pro-lab-card">
          <p className="pro-lab-eyebrow">Latest Run</p>
          {lastRun ? (
            <>
              <h3>{lastRun.provider_id}:{lastRun.command_id}</h3>
              <div className="pro-lab-progress"><span style={{ width: `${lastRun.progress_pct}%` }} /></div>
              <div className="pro-lab-badges">
                <span className="pro-lab-badge pro-lab-badge--ok">{lastRun.status}</span>
                <span className="pro-lab-badge">{lastRun.progress_pct}%</span>
                <span className="pro-lab-badge">stale: {String(lastRun.data_freshness?.stale)}</span>
              </div>
              <p className="pro-lab-muted">Safety flags: {lastRun.safety_flags.join(', ') || 'none'}</p>
              <div className="pro-lab-log-list">
                {lastRun.logs.map((log, index) => (
                  <div key={`${lastRun.run_id}-${index}`}>
                    <strong>{log.level}</strong>
                    <span>{log.message}</span>
                  </div>
                ))}
              </div>
              <pre className="pro-lab-code-block">{JSON.stringify(lastRun.output_payload, null, 2)}</pre>
            </>
          ) : (
            <p>Chưa có run trong session hiện tại. Chọn command bên trái để chạy thử.</p>
          )}
        </section>
      </div>

      <section className="pro-lab-card">
        <p className="pro-lab-eyebrow">History</p>
        <h3>Experiment History</h3>
        {workspace.experiments.length ? (
          <div className="pro-lab-experiment-grid">
            {workspace.experiments.map((item) => (
              <article key={item.experiment_id} className="pro-lab-mini-card">
                <div className="pro-lab-provider-card__header">
                  <strong>{item.experiment_type}</strong>
                  <span>{item.review_status}</span>
                </div>
                <p>{item.created_at}</p>
                <div className="pro-lab-stack">
                  {item.notebook_sections.map((section, index) => (
                    <div key={`${item.experiment_id}-${index}`}>
                      <strong>{section.title}</strong>
                      <p>{section.body}</p>
                    </div>
                  ))}
                </div>
                {item.caveats.length ? <p>{item.caveats.join(' | ')}</p> : null}
                {item.review_notes ? <p>Review notes: {item.review_notes}</p> : null}
                <button type="button" onClick={() => onExportReport(item.experiment_id)}>
                  Export report
                </button>
              </article>
            ))}
          </div>
        ) : (
          <p>Chưa có experiment nào. Workspace này sẽ lưu lại trail nghiên cứu để review sau.</p>
        )}
      </section>

      {reportExport ? (
        <section className="pro-lab-card">
          <p className="pro-lab-eyebrow">Export</p>
          <h3>Report Export</h3>
          <p>{reportExport.filename}</p>
          <p>Confidence: {reportExport.confidence_label}</p>
          {reportExport.disclaimer_title ? <p><strong>{reportExport.disclaimer_title}:</strong> {reportExport.disclaimer_text}</p> : null}
          {reportExport.risk_banner ? <p>{reportExport.risk_banner}</p> : null}
          <p><strong>Đây là gì:</strong> {reportExport.what_this_is}</p>
          <p><strong>Đây không phải:</strong> {reportExport.what_this_is_not}</p>
          <pre className="pro-lab-code-block">{reportExport.content}</pre>
        </section>
      ) : null}
    </section>
  )
}

function defaultPayloadFor(providerId, commandId) {
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
  return { memo_focus: 'Build a caveat-first research memo from this blueprint.' }
}
