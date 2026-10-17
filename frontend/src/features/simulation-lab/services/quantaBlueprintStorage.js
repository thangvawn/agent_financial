/**
 * quantaBlueprintStorage.js
 * Local persistence and management for Quanta Strategy Blueprints.
 */

const STORAGE_KEY = 'quanta_saved_blueprints_v1';

export function loadSavedBlueprints() {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const list = JSON.parse(raw);
    return Array.isArray(list) ? list : [];
  } catch (err) {
    console.warn('[BlueprintStorage] Khong the doc localStorage:', err);
    return [];
  }
}

export function saveBlueprint({
  name = 'Chiến lược mới',
  ticker = 'FPT',
  period = '1y',
  interval = '1d',
  code = '',
  params = {},
  metrics = {},
}) {
  const existing = loadSavedBlueprints();
  const id = `bp_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
  const newBlueprint = {
    id,
    name: name.trim() || 'Chiến lược không tên',
    ticker: ticker.toUpperCase(),
    period,
    interval,
    code,
    params,
    metrics: {
      totalReturn: Number(metrics.total_return ?? metrics.totalReturnPct ?? 0),
      cagr: Number(metrics.cagr ?? 0),
      sharpe: Number(metrics.sharpe ?? metrics.sharpeRatio ?? 0),
      maxDrawdown: Number(metrics.max_drawdown ?? metrics.maxDrawdown ?? 0),
      winRate: Number(metrics.win_rate ?? metrics.winRate ?? 0),
    },
    savedAt: new Date().toISOString(),
  };

  const updated = [newBlueprint, ...existing.filter((b) => b.id !== id)].slice(0, 30);
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (err) {
    console.warn('[BlueprintStorage] Khong the ghi localStorage:', err);
  }
  return newBlueprint;
}

export function deleteBlueprint(id) {
  const existing = loadSavedBlueprints();
  const updated = existing.filter((b) => b.id !== id);
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (err) {
    console.warn('[BlueprintStorage] Khong the xoa blueprint:', err);
  }
  return updated;
}

export function exportBlueprintJson(blueprint) {
  return JSON.stringify(blueprint, null, 2);
}

export function importBlueprintJson(jsonString) {
  try {
    const parsed = JSON.parse(jsonString);
    if (parsed && parsed.code) {
      return saveBlueprint(parsed);
    }
  } catch (err) {
    console.warn('[BlueprintStorage] Import that bai:', err);
  }
  return null;
}
