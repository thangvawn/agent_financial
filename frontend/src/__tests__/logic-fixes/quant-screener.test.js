import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import { fetchVnScreener } from '../../features/market-portfolio/services/dataHubApi.js'
import { loadComponent, closeViteServer, React, renderToString } from '../test-helpers.js'

after(closeViteServer)

test('screener sends all criteria to server and keeps abort ownership per request', async () => {
  const saved = globalThis.fetch
  const calls = []
  globalThis.fetch = async (url, options) => { calls.push({ url, options }); return { ok: true, json: async () => ({ matched: 81, items: [] }) } }
  try {
    const first = new AbortController(), second = new AbortController()
    const a = await fetchVnScreener({ preset: 'breakout', sector: 'Ngân hàng', limit: 20, signal: first.signal })
    await fetchVnScreener({ preset: 'breakout', sector: 'Ngân hàng', limit: 100, signal: second.signal })
    assert.equal(a.matched, 81)
    assert.equal(new URL(calls[0].url, 'http://local').searchParams.get('sector'), 'Ngân hàng')
    assert.equal(calls[0].options.signal, first.signal)
    assert.equal(calls[1].options.signal, second.signal)
    assert.equal(calls.length, 2)
  } finally { globalThis.fetch = saved }
})

test('coverage distinguishes missing data and score disclosure is not probability', async () => {
  const { ScreenerResults, StockSignalDetails } = await loadComponent('./src/features/market-portfolio/components/ScreenerResults.jsx')
  const data = { evaluated: 0, scope_total: 1521, matched: 0, unknown: 1521, stale: 0, not_eligible: 0, missing_reasons: { adjustment_unverified: 1521 }, session_verified: false, freshness: 'stale' }
  const html = renderToString(React.createElement(ScreenerResults, { data, preset: 'breakout' })).replaceAll('<!-- -->', '')
  assert.ok(html.includes('1521 thiếu dữ liệu'))
  assert.ok(html.includes('Chưa xác minh điều chỉnh giá'))
  assert.ok(html.includes('không phải xác suất tăng giá'))
  assert.ok(html.includes('Chưa xác nhận phiên dữ liệu'))
  const signal = { score: 80, conditions: [], as_of: '2026-10-30', signals: { breakout: { conditions: [{ id: 'A', label: 'Vượt đỉnh', values: { close: 51200, high: 50000 }, passed: true }] } } }
  const detail = renderToString(React.createElement(StockSignalDetails, { signal }))
  assert.ok(detail.includes('80') && detail.includes('Vượt đỉnh') && detail.includes('30/10/2026'))
})
