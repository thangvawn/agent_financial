import React, { useState } from 'react';

export default function SimLabTodaySignalBanner({ todaySignal, ticker }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!todaySignal) return null;

  const {

    actionLabel,
    color,
    asOfDate,
    currentPrice,
    stopLossPrice,
    takeProfitPrice,
    confidenceScore,
    rationale,
    liquidity,
  } = todaySignal;

  const bgClasses = {
    emerald: 'border-emerald-500/30 bg-emerald-950/20 text-emerald-300',
    rose: 'border-rose-500/30 bg-rose-950/20 text-rose-300',
    amber: 'border-amber-500/30 bg-amber-950/20 text-amber-300',
    slate: 'border-slate-700 bg-slate-900/60 text-slate-300',
  }[color] || 'border-slate-700 bg-slate-900/60 text-slate-300';

  const badgeBg = {
    emerald: 'bg-emerald-500 text-slate-950 font-bold',
    rose: 'bg-rose-500 text-white font-bold',
    amber: 'bg-amber-400 text-slate-950 font-bold',
    slate: 'bg-slate-700 text-slate-200',
  }[color] || 'bg-slate-700 text-slate-200';

  return (
    <div className={`mb-3 rounded-lg border p-3 transition-all ${bgClasses}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className={`rounded px-2 py-0.5 text-xs font-mono tracking-wide ${badgeBg}`}>
            {actionLabel}
          </span>
          <span className="font-mono text-xs text-slate-200">
            {ticker} @ {currentPrice?.toLocaleString('vi-VN')} đ
          </span>
          {asOfDate && (
            <span className="text-[11px] text-slate-400">
              (Phiên {typeof asOfDate === 'number' ? new Date(asOfDate * 1000).toISOString().slice(0,16).replace('T',' ') : asOfDate})
            </span>
          )}
          {confidenceScore !== null && <span className="rounded bg-cyan-950/60 px-1.5 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-800/40">
            Độ tin cậy: {confidenceScore}%
          </span>}
          {!liquidity?.isSafe && (
            <span className="rounded bg-amber-950/60 px-1.5 py-0.5 text-[10px] text-amber-400 border border-amber-800/40">
              ⚠ Thanh khoản thấp ({liquidity?.avgVolume?.toLocaleString()} cp/phiên)
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-xs text-slate-400 hover:text-white"
        >
          {isCollapsed ? 'Mở rộng ▾' : 'Thu gọn ▴'}
        </button>
      </div>

      {!isCollapsed && (
        <div className="mt-2.5 grid grid-cols-1 gap-2 border-t border-slate-800/60 pt-2 text-xs text-slate-300 sm:grid-cols-3">
          <div className="flex items-center gap-1.5 font-mono">
            <span className="text-slate-400">Cắt lỗ (SL):</span>
            <span className="text-rose-400 font-bold">{stopLossPrice == null ? 'Chưa đặt' : `${stopLossPrice.toLocaleString('vi-VN')} đ`}</span>
          </div>
          <div className="flex items-center gap-1.5 font-mono">
            <span className="text-slate-400">Chốt lời (TP):</span>
            <span className="text-emerald-400 font-bold">{takeProfitPrice == null ? 'Chưa đặt' : `${takeProfitPrice.toLocaleString('vi-VN')} đ`}</span>
          </div>
          <div className="text-[11px] text-slate-300 italic sm:col-span-1">
            {rationale}
          </div>
        </div>
      )}
    </div>
  );
}
