import test from 'node:test'
import assert from 'node:assert/strict'
import { fetchVnSnapshot, clearDataHubClientCache } from '../../features/market-portfolio/services/dataHubApi.js'

test('industry code and pagination are independent snapshot cache keys', async () => {
  const old = globalThis.fetch, calls = []
  clearDataHubClientCache()
  globalThis.fetch = async url => { calls.push(url); return { ok: true, json: async () => ({ items: [], total: 28 }) } }
  try {
    await fetchVnSnapshot({ industry: '8350', limit: 20 })
    await fetchVnSnapshot({ industry: '8350', limit: 20, offset: 20 })
    await fetchVnSnapshot({ industry: '8630', limit: 20 })
    await fetchVnSnapshot({ industry: '8350', limit: 20 })
    assert.equal(calls.length, 3)
    const params = calls.map(url => new URL(url, 'http://local').searchParams)
    assert.deepEqual(params.map(p => [p.get('industry'), p.get('offset')]), [['8350', '0'], ['8350', '20'], ['8630', '0']])
    assert.ok(calls.every(url => url.includes('/vn-market/snapshot?')))
  } finally { globalThis.fetch = old; clearDataHubClientCache() }
})

test('switching away and back cannot reuse an aborted snapshot promise', async () => {
  const old = globalThis.fetch, calls = []
  clearDataHubClientCache()
  globalThis.fetch = (url, { signal }) => new Promise((resolve, reject) => {
    calls.push({ signal, resolve })
    signal.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })))
  })
  try {
    const a = new AbortController(), b = new AbortController()
    const first = fetchVnSnapshot({ industry: '8350', signal: a.signal })
    const rejected = assert.rejects(first, { name: 'AbortError' })
    a.abort()
    const second = fetchVnSnapshot({ industry: '8350', signal: b.signal })
    assert.equal(calls.length, 2)
    calls[1].resolve({ ok: true, json: async () => ({ total: 28 }) })
    assert.equal((await second).total, 28)
    await rejected
  } finally { globalThis.fetch = old; clearDataHubClientCache() }
})
