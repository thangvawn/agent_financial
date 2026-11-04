import assert from 'node:assert/strict'
import { test } from 'node:test'
import { buildMarketOverview, selectOverviewMovers } from '../../features/market-portfolio/services/marketOverviewModel.js'
const quote = (symbol, extra = {}) => ({ symbol, price: 10000, change_pct: 1, value: 2e9, volume: 1000, exchange: 'HOSE', sector_id: '8', sector: 'Tài chính', ...extra })

test('breadth counts only traded valid quotes; missing change and unmatched reference are not flat', () => {
  const result = buildMarketOverview([
    quote('UP'), quote('DOWN', { change_pct: -2, exchange: 'HSX' }),
    quote('FLAT', { change_pct: 0, exchange: 'HNX' }),
    quote('UNTRADED', { volume: 0, value: 0, change_pct: 0 }),
    quote('NO_PCT', { change_pct: null }), quote('NO_PRICE', { price: null }),
    quote('NO_TRADE', { volume: null, value: null }), quote('BAD_PCT', { change_pct: true }),
  ])
  assert.deepEqual(result.totals, { up: 1, flat: 1, down: 1, known: 3, traded: 6, turnover: 12e9 })
  assert.equal(result.exchanges[0].down, 1)
  assert.equal(result.exchanges[1].flat, 1)
  assert.deepEqual(result.stocks.map(r => r.symbol), ['UP', 'DOWN', 'FLAT'])
})

test('missing turnover stays unknown; sector shares use actual values including quotes without change', () => {
  assert.equal(buildMarketOverview().totals.turnover, null)
  assert.equal(buildMarketOverview([quote('MISS', { value: null })]).totals.turnover, null)
  assert.equal(buildMarketOverview([quote('ZERO', { value: 0, volume: 0 })]).totals.turnover, 0)
  const result = buildMarketOverview([
    quote('A', { value: 3e9 }), quote('B', { value: 1e9, change_pct: null, sector_id: '9', sector: 'Công nghệ' }),
    quote('INVALID', { value: -5e9 }),
  ])
  assert.equal(result.totals.turnover, 4e9)
  assert.deepEqual(result.sectors.map(r => r.share), [75, 25])
})

test('movers filter by direction and liquidity before limiting across the complete universe', () => {
  const items = Array.from({ length: 105 }, (_, i) => quote(`T${i}`, { change_pct: 10 + i, value: 1000 }))
  items.push(quote('LIQUID', { change_pct: 2, value: 1e9 }), quote('DOWN', { change_pct: -5, value: 4e9 }), quote('FLAT', { change_pct: 0, value: 10e9 }))
  const { stocks } = buildMarketOverview(items)
  assert.deepEqual(selectOverviewMovers(stocks).map(r => r.symbol), ['LIQUID'])
  assert.deepEqual(selectOverviewMovers(stocks, { mode: 'losers' }).map(r => r.symbol), ['DOWN'])
  assert.deepEqual(selectOverviewMovers(stocks, { mode: 'liquidity' }).map(r => r.symbol), ['FLAT', 'DOWN', 'LIQUID'])
  assert.equal(selectOverviewMovers(stocks, { liquidOnly: false })[0].symbol, 'T104')
  assert.equal(selectOverviewMovers(stocks, { liquidOnly: false }).length, 6)
})

test('a quote tick updates breadth and rank together without modifying the input snapshot', () => {
  const items = [Object.freeze(quote('A')), Object.freeze(quote('B', { change_pct: -1, value: 3e9 }))]
  const before = buildMarketOverview(items)
  const after = buildMarketOverview(items.map(r => r.symbol === 'A' ? { ...r, change_pct: -3, value: 4e9 } : r))
  assert.equal(before.totals.up, 1)
  assert.equal(after.totals.up, 0)
  assert.equal(after.totals.down, 2)
  assert.equal(after.totals.turnover, 7e9)
  assert.equal(selectOverviewMovers(after.stocks, { mode: 'losers' })[0].symbol, 'A')
  assert.equal(items[0].change_pct, 1)
})
