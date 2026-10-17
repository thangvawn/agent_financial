import React from 'react';
import { useFinancialWorkflow } from '../../../shared/context/FinancialWorkflowContext';

export default function BctcActionBridge({ ticker = 'FPT', companyName = '' }) {
  const { navigateToSimulationLab, navigateToMarket } = useFinancialWorkflow();
  const cleanTicker = (ticker || 'FPT').toUpperCase();

  return (
    <div className="my-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-700/80 bg-slate-900/90 px-4 py-2.5 shadow-md backdrop-blur-sm">
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs font-bold text-cyan-400">{cleanTicker}</span>
        {companyName && (
          <span className="text-xs text-slate-400 font-medium">({companyName})</span>
        )}
        <span className="text-[11px] text-slate-500">• Chuyển đổi ngữ cảnh:</span>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => navigateToSimulationLab({ ticker: cleanTicker })}
          className="inline-flex items-center gap-1.5 rounded bg-cyan-950/80 border border-cyan-800/60 px-3 py-1.5 text-xs font-semibold text-cyan-300 transition-colors hover:bg-cyan-800/50 hover:text-white"
        >
          <span>🔬</span>
          <span>Backtest trong Studio</span>
        </button>

        <button
          type="button"
          onClick={() => navigateToMarket(cleanTicker)}
          className="inline-flex items-center gap-1.5 rounded bg-amber-950/80 border border-amber-800/60 px-3 py-1.5 text-xs font-semibold text-amber-300 transition-colors hover:bg-amber-800/50 hover:text-white"
        >
          <span>⚡</span>
          <span>Bảng điện & Giao dịch</span>
        </button>
      </div>
    </div>
  );
}
