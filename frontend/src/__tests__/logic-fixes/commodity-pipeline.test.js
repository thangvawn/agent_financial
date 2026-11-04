import { test } from 'node:test'
import assert from 'node:assert/strict'
import { fetchInstrumentHistory, clearDataHubClientCache } from '../../features/market-portfolio/services/dataHubApi.js'
import { createSparklineLoader } from '../../features/market-portfolio/services/sparklineHistory.js'

const points = [{ date: '2026-11-01', close: 100 }, { date: '2026-11-02', close: 102 }]

test('explicit history refresh reaches backend while normal requests use cache', async () => {
  clearDataHubClientCache()
  const original = globalThis.fetch, urls = []
  globalThis.fetch = async url => { urls.push(url); return new Response(JSON.stringify({ points })) }
  try {
    await fetchInstrumentHistory('XAU')
    await fetchInstrumentHistory('XAU')
    await fetchInstrumentHistory('XAU', { forceRefresh: true })
    assert.equal(urls.length, 2)
    assert.equal(new URL(urls[1], 'http://qa').searchParams.get('refresh'), 'true')
  } finally { globalThis.fetch = original; clearDataHubClientCache() }
})

test('aborting one history consumer does not poison another consumer', async () => {
  clearDataHubClientCache()
  const original = globalThis.fetch, owner = new AbortController()
  let release, transportSignal, calls = 0
  globalThis.fetch = async (_url, options) => {
    calls++; transportSignal = options.signal
    await new Promise(resolve => { release = resolve })
    return new Response(JSON.stringify({ points }))
  }
  try {
    const first = fetchInstrumentHistory('XAU', { signal: owner.signal })
    const abandoned = assert.rejects(first, { name: 'AbortError' })
    const second = fetchInstrumentHistory('XAU')
    owner.abort()
    assert.equal(transportSignal.aborted, false)
    release()
    await abandoned
    assert.deepEqual((await second).points, points)
    assert.equal(calls, 1)
  } finally { globalThis.fetch = original; clearDataHubClientCache() }
})

test('sparkline force refresh bypasses its cache and keeps history on provider errors', async () => {
  let calls = 0
  const loader = createSparklineLoader(async (_symbol, options) => {
    calls++
    if (calls > 1) { assert.equal(options.forceRefresh, true); throw Error('offline') }
    return { points, freshness: 'fresh' }
  })
  const first = await loader('XAU')
  const failed = await loader('XAU', { forceRefresh: true })
  assert.equal(calls, 2)
  assert.deepEqual(failed.points, first.points)
  assert.equal(failed.freshness, 'stale')
  assert.equal(failed.refreshFailed, true)
})
