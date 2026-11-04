import { useEffect, useRef } from 'react'
import { useFinancialWorkflow } from '../context/FinancialWorkflowContext';

export default function TickerActionPopover() {
  const { popoverState, closeTickerMenu, navigateToSimulationLab, navigateToBctc, navigateToMarket } =
    useFinancialWorkflow();
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        closeTickerMenu();
      }
    }
    function handleKeyDown(e) {
      if (e.key === 'Escape') closeTickerMenu();
    }

    if (popoverState.isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [popoverState.isOpen, closeTickerMenu]);

  if (!popoverState.isOpen) return null;

  const { ticker, x, y } = popoverState;

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[220px] rounded-lg border border-slate-700/80 bg-slate-900/95 p-2 shadow-2xl backdrop-blur-md"
      style={{
        left: `${Math.max(12, Math.min(window.innerWidth - 240, x - 110))}px`,
        top: `${Math.min(window.innerHeight - 180, y)}px`,
      }}
    >
      <div className="mb-1.5 flex items-center justify-between border-b border-slate-800 px-2 pb-1.5">
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-xs font-bold text-cyan-400">{ticker}</span>
          <span className="text-[10px] text-slate-400">Thao tác nhanh</span>
        </div>
        <button
          type="button"
          onClick={closeTickerMenu}
          className="text-xs text-slate-400 hover:text-white"
        >
          ✕
        </button>
      </div>

      <div className="flex flex-col gap-1 text-xs">
        <button
          type="button"
          onClick={() => {
            closeTickerMenu();
            navigateToSimulationLab({ ticker });
          }}
          className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-slate-200 transition-colors hover:bg-cyan-500/15 hover:text-cyan-300"
        >
          <span>🔬</span>
          <span>Backtest trong Studio</span>
        </button>

        <button
          type="button"
          onClick={() => {
            closeTickerMenu();
            navigateToBctc(ticker);
          }}
          className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-slate-200 transition-colors hover:bg-emerald-500/15 hover:text-emerald-300"
        >
          <span>📊</span>
          <span>Soi Báo Cáo Tài Chính</span>
        </button>

        <button
          type="button"
          onClick={() => {
            closeTickerMenu();
            navigateToMarket(ticker);
          }}
          className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-slate-200 transition-colors hover:bg-amber-500/15 hover:text-amber-300"
        >
          <span>⚡</span>
          <span>Bảng điện & Giao dịch</span>
        </button>
      </div>
    </div>
  );
}
