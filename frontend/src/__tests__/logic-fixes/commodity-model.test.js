import { test } from 'node:test'
import assert from 'node:assert/strict'
import { commodityPrice, commodityNumber, selectCommodities, normalizeCommodityHistory, historySummary, tone } from '../../features/market-portfolio/services/commodityModel.js'

test('commodity prices retain quote values and distinguish zero, null and invalid numbers', () => {
  assert.equal(commodityPrice(447.25), '447.25')
  assert.equal(commodityPrice(2.909), '2.9090')
  for (const value of [null, undefined, '', false, Infinity, 'invalid']) assert.equal(commodityPrice(value), '—')
  assert.equal(commodityNumber(0, 0), '0')
  assert.equal(tone(0), 'flat')
  assert.equal(tone(null), 'unknown')
})
test('commodity filters combine group and unaccented search, with missing sort values last', () => {
  const items = [{ symbol: 'XAU', name: 'Gold', category: 'metals', change_pct: 2, volume_24h: 10 }, { symbol: 'SILVER', name: 'Silver', category: 'metals', change_pct: -1, volume_24h: 0 }, { symbol: 'WTI', name: 'Oil', category: 'energy', change_pct: null }]
  assert.deepEqual(selectCommodities(items, { query: 'kim loai', sort: 'losers' }).map(x => x.symbol), ['SILVER', 'XAU'])
  assert.deepEqual(selectCommodities(items, { group: 'energy', query: 'gold' }), [])
  assert.deepEqual(selectCommodities(items, { sort: 'losers' }).map(x => x.symbol), ['SILVER', 'XAU', 'WTI'])
  assert.equal(items[0].symbol, 'XAU')
})
test('history sorts, deduplicates and rejects missing prices without inventing candles or volume', () => {
  const points = normalizeCommodityHistory([{ date: '2026-10-02', close: 5 }, { date: '2026-10-01', close: 4, open: 3, high: 5, low: 2, volume: 0 }, { date: '2026-10-02', close: 6, open: 4, high: 3, low: 2 }, { date: 'bad', close: 7 }, { date: '2026-10-03', close: null }])
  assert.deepEqual(points.map(x => x.close), [4, 6])
  assert.equal(points[1].open, undefined)
  assert.equal(points[1].volume, null)
  assert.deepEqual(historySummary(points), { change: 50, high: 6, low: 2, candles: false, volume: false })
})
test('history supports negative futures prices and protects zero denominators', () => {
  assert.equal(historySummary(normalizeCommodityHistory([{ date: '2020-04-20', close: -10 }, { date: '2020-04-21', close: 5 }])).change, 150)
  assert.equal(historySummary([{ close: 0 }, { close: 2 }]).change, null)
  assert.equal(historySummary([]).change, null)
})
