import { accountStorageKey } from '../../../shared/auth/accountContext.js'
/**
 * quantaBlueprintStorage.js
 * Local persistence and management for Quanta Strategy Blueprints.
 */

const storageKey = owner => accountStorageKey(owner, 'blueprints:v2');

export function loadSavedBlueprints(owner) {
  if (typeof window === 'undefined' || !owner) return [];
  try {
    const raw = window.localStorage.getItem(storageKey(owner));
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
}, owner) {
  if (!owner) throw new Error('Vui lòng xác minh tài khoản trước khi lưu.');
  const existing = loadSavedBlueprints(owner);
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
      sharpe: (metrics.sharpe ?? metrics.sharpeRatio ?? null),
      maxDrawdown: Number(metrics.max_drawdown ?? metrics.maxDrawdown ?? 0),
      winRate: Number(metrics.win_rate ?? metrics.winRate ?? 0),
    },
    savedAt: new Date().toISOString(),
  };

  const updated = [newBlueprint, ...existing.filter((b) => b.id !== id)].slice(0, 30);
  try {
    window.localStorage.setItem(storageKey(owner), JSON.stringify(updated));
  } catch (err) {
    throw new Error(`Không lưu được bản thiết kế trên thiết bị: ${err.message}`);
  }
  return newBlueprint;
}

export function deleteBlueprint(id, owner) {
  if (!owner) throw new Error('Vui lòng xác minh tài khoản trước khi xóa.');
  const existing = loadSavedBlueprints(owner);
  const updated = existing.filter((b) => b.id !== id);
  try {
    window.localStorage.setItem(storageKey(owner), JSON.stringify(updated));
  } catch (err) {
    throw new Error(`Không xóa được bản thiết kế trên thiết bị: ${err.message}`);
  }
  return updated;
}

export function exportBlueprintJson(blueprint) {
  return JSON.stringify(blueprint, null, 2);
}

export function importBlueprintJson(jsonString, owner) {
  try {
    const parsed = JSON.parse(jsonString);
    if (parsed && parsed.code) {
      return saveBlueprint(parsed, owner);
    }
  } catch (err) {
    console.warn('[BlueprintStorage] Import that bai:', err);
  }
  return null;
}
