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
    return <p className="text-xs text-[#88aab8]">Mở workspace Pro để chạy scenario hoặc backtest.</p>
  }
  const runActions = [
    {
      title: 'Scenario: FX / Rate Stress',
      summary: 'Xem blueprint nhạy với tỷ giá và lãi suất như thế nào.',
      button: 'Run scenario',
      onClick: () => onScenarioRun(selectedBlueprintId, 'fx_rate_stress', defaultPayloadFor('scenario_lab', 'fx_rate_stress')),
      disabled: !selectedBlueprintId,
      meta: 'macro sensitivity',
    },
    {
      title: 'Backtest: Benchmark Sandbox',
      summary: 'So sánh giả định với benchmark, có caveat về dữ liệu và execution.',
      button: 'Run backtest',
      onClick: () => onBacktestRun(selectedBlueprintId, '2023-01-01', '2025-12-31'),
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
    <div className="grid gap-6">
      <section className="flex justify-between items-start gap-4 flex-wrap pb-2">
        <div>
          <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Run Console</p>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider mt-1">Chọn run cần chạy</h2>
          <p className="text-xs text-[#88aab8]">Không cần đọc provider. Chọn mục tiêu nghiên cứu, hệ thống sẽ gọi command phù hợp.</p>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">{selectedBlueprintId ? 'Blueprint selected' : 'Create/select blueprint first'}</span>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {runActions.map((action) => (
          <article key={action.title} className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-3 justify-between">
            <div className="flex flex-col gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20 self-start">{action.meta}</span>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mt-1">{action.title}</h3>
              <p className="text-xs text-[#88aab8] leading-relaxed">{action.summary}</p>
            </div>
            <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] disabled:opacity-50 disabled:pointer-events-none w-full" type="button" onClick={action.onClick} disabled={action.disabled}>
              {action.button}
            </button>
          </article>
        ))}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Registry</p>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Commands</h3>
          <p className="text-xs text-[#5e7a72]">Advanced view cho provider/command thô.</p>
          {catalog ? (
            <div className="flex flex-col gap-3">
              {catalog.providers.map((provider) => (
                <article key={provider.provider_id} className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                  <div className="flex justify-between items-center text-xs pb-1 border-b border-[#88aab8]/10">
                    <strong className="text-white font-bold">{provider.label}</strong>
                    <span className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">{provider.category}</span>
                  </div>
                  <p className="text-xs text-[#88aab8] leading-relaxed">{provider.description}</p>
                  <div className="flex flex-col gap-1.5 mt-2">
                    {provider.commands.map((command) => (
                      <button
                        key={`${provider.provider_id}-${command.command_id}`}
                        type="button"
                        className="flex justify-between items-center text-left text-xs p-2 rounded-lg bg-[#0c1720]/60 border border-[#88aab8]/10 hover:border-[#4fd1b4]/20 transition cursor-pointer text-[#edf7f5]"
                        onClick={() => onRunCommand(provider.provider_id, command.command_id, defaultPayloadFor(provider.provider_id, command.command_id))}
                        disabled={!selectedBlueprintId && provider.provider_id !== 'report_builder'}
                      >
                        <span>{command.label}</span>
                        <small className="text-[9px] font-bold text-[#5e7a72] uppercase">{command.risk_level}</small>
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#88aab8]">Catalog chưa được tải.</p>
          )}
        </section>

        <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Latest Run</p>
          {lastRun ? (
            <>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">{lastRun.provider_id}:{lastRun.command_id}</h3>
              <div className="w-full h-1.5 bg-[#0c1720]/80 rounded-full overflow-hidden"><span className="block h-full bg-[#4fd1b4]" style={{ width: `${lastRun.progress_pct}%` }} /></div>
              <div className="flex flex-wrap gap-1.5">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/20 text-emerald-400 border border-emerald-900/30">{lastRun.status}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5]">{lastRun.progress_pct}%</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5]">stale: {String(lastRun.data_freshness?.stale)}</span>
              </div>
              <p className="text-xs text-[#5e7a72]">Safety flags: {lastRun.safety_flags.join(', ') || 'none'}</p>
              <div className="flex flex-col gap-1.5 max-h-[160px] overflow-y-auto bg-[#0c1720]/60 p-3 rounded-lg border border-[#88aab8]/10 font-mono text-[10px] [scrollbar-width:thin]">
                {lastRun.logs.map((log, index) => (
                  <div key={`${lastRun.run_id}-${index}`} className="flex gap-2">
                    <strong className="text-[#4fd1b4]">{log.level}</strong>
                    <span className="text-[#88aab8]">{log.message}</span>
                  </div>
                ))}
              </div>
              <pre className="p-3 rounded-lg bg-[#0c1720]/80 text-[#a8c4bb] font-mono text-[10px] overflow-x-auto border border-[#88aab8]/10 [scrollbar-width:thin]">{JSON.stringify(lastRun.output_payload, null, 2)}</pre>
            </>
          ) : (
            <p className="text-xs text-[#88aab8]">Chưa có run trong session hiện tại. Chọn command bên trái để chạy thử.</p>
          )}
        </section>
      </div>

      <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
        <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">History</p>
        <h3 className="text-xs font-bold text-white uppercase tracking-wider">Experiment History</h3>
        {workspace.experiments.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {workspace.experiments.map((item) => (
              <article key={item.experiment_id} className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
                <div className="flex justify-between items-center text-xs pb-1 border-b border-[#88aab8]/10">
                  <strong className="text-white font-bold">{item.experiment_type}</strong>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5]">{item.review_status}</span>
                </div>
                <p className="text-[10px] text-[#5e7a72] font-semibold">{item.created_at}</p>
                <div className="flex flex-col gap-3">
                  {item.notebook_sections.map((section, index) => (
                    <div key={`${item.experiment_id}-${index}`} className="flex flex-col gap-1">
                      <strong className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">{section.title}</strong>
                      <p className="text-xs text-[#88aab8] leading-relaxed">{section.body}</p>
                    </div>
                  ))}
                </div>
                {item.caveats.length ? <p className="text-xs text-[#5e7a72] font-semibold italic">{item.caveats.join(' | ')}</p> : null}
                {item.review_notes ? <p className="text-xs text-amber-400 font-semibold">Review notes: {item.review_notes}</p> : null}
                <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#3b82f6] hover:bg-[#60a5fa] text-white self-start mt-2" type="button" onClick={() => onExportReport(item.experiment_id)}>
                  Export report
                </button>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-xs text-[#88aab8]">Chưa có experiment nào. Workspace này sẽ lưu lại trail nghiên cứu để review sau.</p>
        )}
      </section>

      {reportExport ? (
        <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
          <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Export</p>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Report Export</h3>
          <p className="text-xs text-white font-bold">{reportExport.filename}</p>
          <p className="text-xs text-[#88aab8]">Confidence: {reportExport.confidence_label}</p>
          {reportExport.disclaimer_title ? <p className="text-xs text-rose-400 font-semibold"><strong>{reportExport.disclaimer_title}:</strong> {reportExport.disclaimer_text}</p> : null}
          {reportExport.risk_banner ? <p className="text-xs text-rose-400 font-semibold">{reportExport.risk_banner}</p> : null}
          <p className="text-xs text-[#88aab8]"><strong>Đây là gì:</strong> {reportExport.what_this_is}</p>
          <p className="text-xs text-[#88aab8]"><strong>Đây không phải:</strong> {reportExport.what_this_is_not}</p>
          <pre className="p-3 rounded-lg bg-[#0c1720]/80 text-[#a8c4bb] font-mono text-[10px] overflow-x-auto border border-[#88aab8]/10 [scrollbar-width:thin]">{reportExport.content}</pre>
        </section>
      ) : null}
    </div>
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
