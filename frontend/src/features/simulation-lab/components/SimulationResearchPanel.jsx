import React, { useState } from 'react';

/**
 * SimulationResearchPanel - Embedded studio panel for Simulation Agent (SIM6)
 * Features:
 * - Assumptions and constraints preview
 * - Data source & version badges
 * - Cost and slippage warnings
 * - Strict Paper / Research Only disclaimer badge
 * - Normalized run comparison matrix
 * - Methodology critique review cards
 * - Explicit ActionProposal confirmation dialog
 */
export default function SimulationResearchPanel({
  manifest,
  comparisonData,
  critiqueData,
  onProposeRun,
  onConfirmExecute,
  isExecuting = false,
}) {
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingProposal, setPendingProposal] = useState(null);
  const [confirmationTokenInput, setConfirmationTokenInput] = useState('');

  const handleCreateProposal = async () => {
    if (onProposeRun) {
      const proposal = await onProposeRun(manifest);
      setPendingProposal(proposal);
      setShowConfirmModal(true);
    }
  };

  const handleExecuteConfirmed = () => {
    if (onConfirmExecute && pendingProposal) {
      onConfirmExecute({
        proposalId: pendingProposal.proposal_id,
        confirmationToken: confirmationTokenInput,
        idempotencyKey: `idemp_${Date.now()}`,
      });
      setShowConfirmModal(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-200 shadow-xl space-y-6">
      {/* Header with Paper Research Boundary Badge */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <span className="text-indigo-400">⚡</span> Simulation Research Studio
            </h2>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
              PAPER / RESEARCH ONLY — NO LIVE TRADING
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Chuyển giả thuyết thành thí nghiệm tái lập, phân tích metrics và rà soát phương pháp luận.
          </p>
        </div>

        {/* Data Source and Version Badges */}
        <div className="flex items-center gap-2 text-xs">
          <span className="bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300">
            Source: <strong className="text-white">{manifest?.dataset_source || 'CafeF EOD'}</strong> ({manifest?.dataset_version || 'v2024.1'})
          </span>
          <span className="bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300">
            Engine: <strong className="text-white">{manifest?.engine_version || '1.0.0'}</strong>
          </span>
        </div>
      </div>

      {/* Assumptions and Warnings Box */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/60">
          <div className="text-xs text-slate-400 font-medium">Khoảng thời gian (Data Window)</div>
          <div className="text-sm font-semibold text-white mt-1">
            {manifest?.data_start || '2022-01-01'} → {manifest?.data_end || '2024-01-01'}
          </div>
          <div className="text-xs text-slate-400 mt-1">Benchmark: {manifest?.benchmark || 'VNINDEX'}</div>
        </div>

        <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/60">
          <div className="text-xs text-slate-400 font-medium">Phí & Trượt giá (Frictions)</div>
          <div className="text-sm font-semibold text-white mt-1">
            Fee: {manifest?.commission_pct || 0.15}% | Slippage: {manifest?.slippage_pct || 0.2}%
          </div>
          {(manifest?.commission_pct === 0 || manifest?.slippage_pct === 0) && (
            <div className="text-xs text-amber-400 font-medium mt-1">
              ⚠️ Cảnh báo: Chưa tính phí/trượt giá đầy đủ!
            </div>
          )}
        </div>

        <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/60 flex flex-col justify-between">
          <div>
            <div className="text-xs text-slate-400 font-medium">Hành động thực thi</div>
            <div className="text-xs text-slate-300 mt-1">2-phase confirmation required</div>
          </div>
          <button
            onClick={handleCreateProposal}
            disabled={isExecuting}
            className="mt-2 w-full py-1.5 px-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white font-medium text-xs rounded-md transition-colors"
          >
            {isExecuting ? 'Đang chạy...' : 'Propose Simulation Run'}
          </button>
        </div>
      </div>

      {/* Methodology Review & Critique Section */}
      {critiqueData && (
        <div className="bg-slate-800/40 border border-slate-700/80 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <span>🔍</span> Đánh giá Phương pháp luận (Methodology Critique)
            </h3>
            <span className="px-2 py-0.5 text-xs font-bold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
              Grade: {critiqueData.overall_grade || 'B+'}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {critiqueData.red_flags?.length > 0 && (
              <div className="bg-rose-950/20 border border-rose-900/40 p-3 rounded text-rose-300">
                <strong className="block text-rose-400 mb-1">Cảnh báo rủi ro (Red Flags):</strong>
                <ul className="list-disc list-inside space-y-1">
                  {critiqueData.red_flags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}
            {critiqueData.strengths?.length > 0 && (
              <div className="bg-emerald-950/20 border border-emerald-900/40 p-3 rounded text-emerald-300">
                <strong className="block text-emerald-400 mb-1">Điểm mạnh (Strengths):</strong>
                <ul className="list-disc list-inside space-y-1">
                  {critiqueData.strengths.map((str, idx) => (
                    <li key={idx}>{str}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {critiqueData.interpretation && (
            <p className="text-xs text-slate-300 italic pt-1">
              "{critiqueData.interpretation}"
            </p>
          )}
        </div>
      )}

      {/* Run Comparison Table */}
      {comparisonData?.runs?.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <span>📊</span> So sánh Kịch bản (Scenario Comparison)
          </h3>
          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="bg-slate-800 text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="px-4 py-2.5">Run ID</th>
                  <th className="px-4 py-2.5">Return</th>
                  <th className="px-4 py-2.5">Sharpe</th>
                  <th className="px-4 py-2.5">Max DD</th>
                  <th className="px-4 py-2.5">Win Rate</th>
                  <th className="px-4 py-2.5">Trades</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-900/60">
                {comparisonData.runs.map((r) => (
                  <tr key={r.run_id} className="hover:bg-slate-800/40">
                    <td className="px-4 py-2 font-mono text-indigo-300">{r.run_id}</td>
                    <td className="px-4 py-2 text-white font-medium">{r.total_return_pct}%</td>
                    <td className="px-4 py-2">{r.sharpe_ratio ?? 'N/A'}</td>
                    <td className="px-4 py-2 text-rose-400">{r.max_drawdown_pct}%</td>
                    <td className="px-4 py-2">{r.win_rate_pct}%</td>
                    <td className="px-4 py-2">{r.trade_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && pendingProposal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-base font-bold text-white">Xác nhận thực thi Simulation Run</h4>
              <button onClick={() => setShowConfirmModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <p className="text-xs text-slate-300">
              Bạn đang chuẩn bị chạy backtest cho chiến lược <strong>{pendingProposal.manifest.strategy_id}</strong>.
            </p>
            <div className="bg-slate-800 p-3 rounded text-xs space-y-1">
              <div>Ước tính chi phí tài nguyên: <strong className="text-amber-400">${pendingProposal.estimated_cost}</strong></div>
              <div>Thời hạn xác nhận (TTL): <strong className="text-slate-200">{pendingProposal.expires_at}</strong></div>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Mã xác nhận (Confirmation Token):</label>
              <input
                type="text"
                placeholder="Nhập hoặc dán confirmation token..."
                value={confirmationTokenInput}
                onChange={(e) => setConfirmationTokenInput(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded"
              >
                Huỷ bỏ
              </button>
              <button
                onClick={handleExecuteConfirmed}
                className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded"
              >
                Xác nhận chạy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

