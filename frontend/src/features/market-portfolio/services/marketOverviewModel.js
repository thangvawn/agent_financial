import { number } from './marketHeatmapModel.js'

const EXCHANGES = ['HOSE', 'HNX', 'UPCOM']
const emptyBreadth = () => ({ up: 0, flat: 0, down: 0, known: 0, traded: 0 })

// Use the same complete quote universe as the map. Missing quotes are not flat
// stocks; unmatched reference prices are not evidence that a stock has traded.
export function buildMarketOverview(items = []) {
  const totals = { ...emptyBreadth(), turnover: null }
  const exchanges = EXCHANGES.map(exchange => ({ exchange, ...emptyBreadth() }))
  const sectors = new Map()
  const stocks = []
  for (const item of items) {
    const rawValue = number(item.value)
    const value = rawValue !== null && rawValue >= 0 ? rawValue : null
    if (value !== null && value >= 0) {
      totals.turnover = (totals.turnover ?? 0) + value
      if (value > 0) {
        const id = item.sector_id || 'unknown'
        const sector = sectors.get(id) || { id, name: item.sector || 'Chưa phân ngành', value: 0, count: 0 }
        sector.value += value
        sector.count++
        sectors.set(id, sector)
      }
    }
    if (!(number(item.volume) > 0 || value > 0)) continue
    totals.traded++
    const exchange = exchanges.find(row => row.exchange === (item.exchange === 'HSX' ? 'HOSE' : item.exchange))
    if (exchange) exchange.traded++
    const change = number(item.change_pct)
    if (!(number(item.price) > 0) || change === null) continue
    const direction = change > 0 ? 'up' : change < 0 ? 'down' : 'flat'
    totals[direction]++
    totals.known++
    if (exchange) { exchange[direction]++; exchange.known++ }
    stocks.push({ ...item, change_pct: change, value })
  }
  return {
    totals, exchanges, stocks,
    sectors: [...sectors.values()].sort((a, b) => b.value - a.value || a.id.localeCompare(b.id))
      .map(row => ({ ...row, share: totals.turnover > 0 ? row.value / totals.turnover * 100 : 0 })),
  }
}

export function selectOverviewMovers(stocks, { mode = 'gainers', liquidOnly = true, limit = 6 } = {}) {
  return stocks.filter(row => (!liquidOnly || row.value >= 1e9)
    && (mode === 'gainers' ? row.change_pct > 0 : mode === 'losers' ? row.change_pct < 0 : row.value > 0))
    .sort((a, b) => (mode === 'liquidity' ? b.value - a.value
      : mode === 'losers' ? a.change_pct - b.change_pct : b.change_pct - a.change_pct)
      || (b.value ?? 0) - (a.value ?? 0) || a.symbol.localeCompare(b.symbol))
    .slice(0, limit)
}
