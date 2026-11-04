import test from 'node:test'
import assert from 'node:assert/strict'
import { filterWatchlist, formatWatchlistNumber, formatWatchlistCap } from '../../features/market-portfolio/pages/watchlistModel.js'

test('prices preserve FX and tiny crypto precision, VND remains whole đồng', () => {
  assert.equal(formatWatchlistNumber(1.08234, { asset_class: 'fx', symbol: 'EURUSD' }), '1,08234')
  assert.equal(formatWatchlistNumber(0.00001234, { asset_class: 'crypto' }), '0,00001234')
  assert.equal(formatWatchlistNumber(-0.00000015, { asset_class: 'crypto' }, true), '-0,00000015')
  assert.equal(formatWatchlistNumber(96000, { asset_class: 'vn_stocks' }), '96.000')
  for (const value of [null, undefined, NaN, Infinity]) assert.equal(formatWatchlistNumber(value), '—')
})

test('market caps retain their currencies and scales', () => {
  assert.equal(formatWatchlistCap({ market_cap: 123.4, market_cap_unit: 'tỷ VND' }), '123,4 tỷ VND')
  assert.equal(formatWatchlistCap({ market_cap: 123400000000, market_cap_unit: 'USD' }), '123,4 tỷ USD')
  assert.equal(formatWatchlistCap({ market_cap: null }), '—')
})

test('asset filter and search intersect; missing changes sort last in both directions', () => {
  const items = [{ symbol: 'BTC', asset_class: 'crypto', change_pct: -2 }, { symbol: 'ETH', asset_class: 'crypto', change_pct: null }, { symbol: 'FPT', name: 'FPT Corporation', asset_class: 'vn_stocks', change_pct: 1 }]
  assert.deepEqual(filterWatchlist(items, { assetClass: 'crypto', search: 'bt' }).map(i => i.symbol), ['BTC'])
  assert.deepEqual(filterWatchlist(items, { search: 'corporation' }).map(i => i.symbol), ['FPT'])
  assert.deepEqual(filterWatchlist(items, { sort: 'change_desc' }).map(i => i.symbol), ['FPT', 'BTC', 'ETH'])
  assert.deepEqual(filterWatchlist(items, { sort: 'change_asc' }).map(i => i.symbol), ['BTC', 'FPT', 'ETH'])
  assert.deepEqual(items.map(i => i.symbol), ['BTC', 'ETH', 'FPT'])
})
