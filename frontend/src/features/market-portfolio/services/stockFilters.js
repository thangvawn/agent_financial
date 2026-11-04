// Compatibility for callers holding server-evaluated rows. Financial rules live in the backend.
export const UNSUPPORTED_PRESETS = new Set()
export function filterStocks(items = [], { preset = '', sector = '', technical = 'all' } = {}) {
  let unavailable = 0
  const keys = [preset, technical === 'all' ? '' : technical].filter(Boolean)
  const matches = items.filter(item => {
    if (sector && (item.industry || item.sector || '') !== sector) return false
    const signals = keys.map(key => item.screening?.signals?.[key])
    if (signals.some(signal => !signal || signal.status !== 'evaluated')) { unavailable++; return false }
    return signals.every(signal => signal.matched)
  })
  return { items: matches, unavailable }
}
