import test from 'node:test'
import assert from 'node:assert/strict'
import { setImmediate } from 'node:timers'
import { finitePrice, normalizeSparklinePoints, sparklineGeometry } from '../../features/market-portfolio/services/sparklineModel.js'
import { createSparklineLoader } from '../../features/market-portfolio/services/sparklineHistory.js'

const rows = [{ date: '2026-10-01', close: 100 }, { date: '2026-10-02', close: 101 }, { date: '2026-10-05', close: 98 }]
test('historical points are sorted and deduplicated without turning missing prices into zero', () => {
  const points = normalizeSparklinePoints([rows[2], rows[0], { ...rows[1], close: 5 }, rows[1], { date: '2026-10-06', close: null }, { date: '2026-10-07', close: '' }, { date: 'bad', price: 10 }, { date: '2026-10-08', close: Infinity }])
  assert.deepEqual(points.map(point => point.price), [100, 101, 98])
  assert.equal(finitePrice(null), null)
  assert.equal(finitePrice(''), null)
  assert.equal(finitePrice(0), 0)
})
test('missing or one-point history never produces a fictional price curve', () => {
  assert.equal(sparklineGeometry([]), null)
  assert.equal(sparklineGeometry(normalizeSparklinePoints(rows.slice(0, 1))), null)
})
test('flat histories stay level; tiny variations are not stretched into large moves', () => {
  const flat = sparklineGeometry(normalizeSparklinePoints(rows.map(row => ({ ...row, close: 100 }))))
  assert.equal(flat.tone, 'flat')
  assert.equal(flat.changePct, 0)
  assert.ok(flat.points.every(point => point.y === flat.refY))
  const tiny = sparklineGeometry(normalizeSparklinePoints([rows[0], { ...rows[1], close: 100.001 }]))
  assert.ok(Math.abs(tiny.points[0].y - tiny.points[1].y) < 1)
})
test('geometry preserves every supplied close and bases return on the first historical close', () => {
  const chart = sparklineGeometry(normalizeSparklinePoints(rows))
  assert.deepEqual(chart.points.map(point => point.price), [100, 101, 98])
  assert.equal(chart.tone, 'down')
  assert.ok(Math.abs(chart.changePct + 2) < 1e-10)
  assert.ok(chart.points.every(point => point.x >= 0 && point.x <= 240 && point.y > 0 && point.y < 60))
})
test('history loader deduplicates requests, limits concurrency and caches successful results', async () => {
  let active = 0, peak = 0, calls = 0
  const releases = []
  const load = createSparklineLoader(async (symbol, options) => {
    assert.equal(options.period, '1mo'); assert.equal(options.interval, '1d')
    calls++; active++; peak = Math.max(active, peak)
    await new Promise(resolve => releases.push(resolve))
    active--; return { symbol, points: rows, freshness: 'fresh' }
  }, { concurrency: 2 })
  const first = load('FPT'), duplicate = load('fpt'), second = load('VCB'), third = load('VIC')
  assert.equal(first, duplicate)
  await new Promise(resolve => setImmediate(resolve))
  assert.equal(calls, 2)
  releases.splice(0).forEach(release => release())
  await new Promise(resolve => setImmediate(resolve))
  releases.splice(0).forEach(release => release())
  const results = await Promise.all([first, second, third])
  assert.ok(results.every(result => result.status === 'ready'))
  assert.equal(peak, 2)
  await load('FPT'); assert.equal(calls, 3)
})
test('failures and empty history stay explicit and retry after the short TTL', async () => {
  let time = 0, calls = 0
  const load = createSparklineLoader(async () => { calls++; if (calls === 1) throw new Error('Offline'); return { points: [] } }, { now: () => time })
  assert.equal((await load('FPT')).status, 'error')
  assert.equal((await load('FPT')).status, 'error'); assert.equal(calls, 1)
  time = 30001
  assert.equal((await load('FPT')).status, 'empty'); assert.equal(calls, 2)
})
