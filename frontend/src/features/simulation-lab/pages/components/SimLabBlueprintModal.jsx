import { useState } from 'react'
import { loadSavedBlueprints, saveBlueprint, deleteBlueprint } from '../../services/quantaBlueprintStorage';

export default function SimLabBlueprintModal({
  isOpen,
  onClose,
  currentConfig,
  onLoadBlueprint,
  owner,
}) {
  return isOpen ? <OpenBlueprintModal onClose={onClose} currentConfig={currentConfig} onLoadBlueprint={onLoadBlueprint} owner={owner} /> : null;
}

function OpenBlueprintModal({ onClose, currentConfig, onLoadBlueprint, owner }) {
  const [blueprints, setBlueprints] = useState(() => loadSavedBlueprints(owner));
  const [strategyName, setStrategyName] = useState(() => `Chiến lược ${currentConfig?.ticker || 'FPT'}`);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [error, setError] = useState('');

  const handleSave = (e) => {
    e.preventDefault();
    if (!strategyName.trim()) return;
    setError('');
    try { saveBlueprint({
      name: strategyName,
      ticker: currentConfig.ticker,
      period: currentConfig.period,
      interval: currentConfig.interval,
      code: currentConfig.code,
      params: currentConfig.params,
      metrics: currentConfig.metrics,
    }, owner); } catch (reason) { setError(reason.message); return; }
    setBlueprints(loadSavedBlueprints(owner));
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleDelete = (id) => {
    try { setBlueprints(deleteBlueprint(id, owner)); setError(''); }
    catch (reason) { setError(reason.message); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-xl border border-slate-700 bg-slate-900 p-5 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-slate-100">Quản Lý Bản Thiết Kế Chiến Lược</span>
            <span className="rounded bg-cyan-950 px-2 py-0.5 text-[11px] font-mono text-cyan-300 border border-cyan-800/40">
              {blueprints.length} bản lưu
            </span>
          </div>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-white">✕</button>
        </div>

        {error && <p role="alert">{error}</p>}
        <form onSubmit={handleSave} className="my-4 flex items-center gap-2">
          <input
            type="text"
            value={strategyName}
            onChange={(e) => setStrategyName(e.target.value)}
            placeholder="Tên chiến lược cần lưu..."
            className="flex-1 rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            className="rounded bg-cyan-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-cyan-500"
          >
            {saveSuccess ? '✓ Đã Lưu!' : 'Lưu Bản Hiện Tại'}
          </button>
        </form>

        <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
          {blueprints.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">
              Chưa có chiến lược nào được lưu. Lưu cấu hình hiện tại để sử dụng lại bất cứ lúc nào!
            </div>
          ) : (
            blueprints.map((bp) => (
              <div
                key={bp.id}
                className="flex items-center justify-between rounded border border-slate-800/80 bg-slate-800/40 p-2.5 hover:border-slate-700"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-slate-200">{bp.name}</span>
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-cyan-400">
                      {bp.ticker} • {bp.interval} • {bp.period}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-[11px] font-mono text-slate-400">
                    <span>Lợi nhuận: <b className="text-emerald-400">+{bp.metrics.totalReturn}%</b></span>
                    <span>Sharpe: <b className="text-cyan-300">{bp.metrics.sharpe ?? '—'}</b></span>
                    <span>MDD: <b className="text-rose-400">{bp.metrics.maxDrawdown}%</b></span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      onLoadBlueprint(bp);
                      onClose();
                    }}
                    className="rounded bg-slate-700 px-2.5 py-1 text-xs text-slate-200 hover:bg-cyan-600 hover:text-white"
                  >
                    Tải Vào Lab
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(bp.id)}
                    className="rounded px-2 py-1 text-xs text-slate-400 hover:bg-rose-950 hover:text-rose-400"
                    title="Xóa bản thiết kế"
                  >
                    🗑
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
