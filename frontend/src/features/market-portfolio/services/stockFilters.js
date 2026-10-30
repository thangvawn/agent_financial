// Unknown fields stay unknown. Snapshot quotes cannot substitute for historical indicators.
const number = (item, ...keys) => {
  for (const key of keys) {
    const value = item[key]
    if (value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))) return Number(value)
  }
  return null
}
const check = (item, keys, predicate) => {
  const values = keys.map(key => number(item, ...key.split('|')))
  return values.some(v => v === null) ? null : predicate(...values)
}
const tests = {
  above_ma20: item => check(item, ['price|close','ma20'], (p,m) => p > m),
  above_ma50: item => check(item, ['price|close','ma50'], (p,m) => p > m),
  above_ma200: item => check(item, ['price|close','ma200'], (p,m) => p > m),
  rsi_overbought: item => check(item, ['rsi|rsi14'], r => r > 70),
  rsi_oversold: item => check(item, ['rsi|rsi14'], r => r < 35),
  vol_2x_ma20: item => check(item, ['volume','volume_ma20'], (v,m) => m > 0 && v > 2*m),
  high_volatility: item => check(item, ['high','low','ref_price|reference_price'], (h,l,r) => r > 0 && (h-l)/r > 0.03),
  breakout: item => check(item, ['price|close','prior_high_20','volume','volume_ma20'], (p,h,v,m) => p > h && m > 0 && v > 1.5*m),
  strong_trend: item => check(item, ['price|close','ma20','ma50','ma200'], (p,a,b,c) => p > a && a > b && b > c),
  money_inflow: item => tests.vol_2x_ma20(item),
  high_dividend: item => check(item, ['dividend_yield_pct|dividend_yield'], y => y > 8),
  regular_cash_div: item => check(item, ['consecutive_cash_dividend_years'], y => y >= 2),
  foreign_favorite: item => check(item, ['foreign_net_buy_streak'], n => n >= 3),
  value_investing: () => null, // Leverage definition and comparable fundamentals are not supplied yet.
  bottom_fishing: () => null,
  overbought_peak: () => null,
  bearish_reversal: () => null,
  dumping_signal: () => null,
  vcp_pattern: () => null,
}
export const UNSUPPORTED_PRESETS = new Set(['value_investing','bottom_fishing','overbought_peak','bearish_reversal','dumping_signal','vcp_pattern'])
export function filterStocks(items = [], { preset = '', sector = '', technical = 'all' } = {}) {
  let unavailable = 0
  const matches = items.filter(item => {
    if (sector && !(item.industry || item.sector || '').includes(sector)) return false
    const outcomes = [preset, technical === 'all' ? '' : technical].filter(Boolean).map(key => tests[key]?.(item) ?? null)
    if (outcomes.includes(null)) { unavailable++; return false }
    return outcomes.every(Boolean)
  })
  return { items: matches, unavailable }
}
