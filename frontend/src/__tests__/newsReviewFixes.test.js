import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { getViteServer, closeViteServer } from './test-helpers.js'
import { newsQuality } from '../features/news/pages/newsLabels.js'
import { fetchNewsFeed, fetchArticleDetail } from '../features/news/services/newsApi.js'

after(closeViteServer)

test('news freshness uses source update time, not response time', () => {
  const now = Date.parse('2026-11-01T12:00:00Z')
  const fresh = { data_updated_at: '2026-11-01T11:59:30Z', freshness: 'fresh', source_count: 3, successful_source_count: 3 }
  assert.equal(newsQuality(fresh, now).stale, false)
  assert.equal(newsQuality({ ...fresh, data_updated_at: '2026-11-01T11:00:00Z', as_of: new Date(now).toISOString() }, now).stale, true)
  assert.equal(newsQuality({ ...fresh, successful_source_count: 2 }, now).stale, true)
  assert.equal(newsQuality({ ...fresh, data_updated_at: null }, now).stale, true)
})

test('every supported news concept opens an existing lesson; invalid links are omitted', async () => {
  const server = await getViteServer()
  const { newsLessonLink, resolveLearningTarget } = await server.ssrLoadModule('/src/features/learn-hub/content/newsLessonLinks.js')
  const concepts = ['risk_on_off', 'fx_impact', 'rate_equity', 'oil_inflation', 'cpi_explained', 'bond_yield', 'crypto_liquidity', 'earnings_reading', 'geopolitics_market']
  for (const concept of concepts) {
    const link = newsLessonLink(concept)
    assert.ok(link?.label)
    const result = resolveLearningTarget(new URL(link.url, 'http://localhost').search)
    assert.equal(result.lesson.lesson_id, link.lesson.lesson_id)
    assert.equal(resolveLearningTarget(`?concept=${concept}`).lesson.lesson_id, link.lesson.lesson_id)
  }
  assert.equal(resolveLearningTarget('?course=missing&lesson=missing'), null)
  assert.equal(newsLessonLink('missing'), null)
})

test('news client sends cursor and cancellation, preserves expiry status for recovery', async t => {
  const controller = new AbortController()
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    const params = new URL(url, 'http://localhost').searchParams
    assert.equal(params.get('cursor'), 'snapshot:24')
    assert.equal(params.get('importance'), 'low')
    assert.equal(options.signal, controller.signal)
    return new Response(JSON.stringify({ detail: 'Expired' }), { status: 410 })
  })
  await assert.rejects(fetchNewsFeed({ cursor: 'snapshot:24', importance: 'low', signal: controller.signal }), error => error.status === 410)
})

test('article client encodes IDs and forwards abort signal', async t => {
  const controller = new AbortController()
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.ok(url.endsWith('/a%2Fb'))
    assert.equal(options.signal, controller.signal)
    return new Response(JSON.stringify({ article: { article_id: 'a/b' } }))
  })
  assert.equal((await fetchArticleDetail('a/b', { signal: controller.signal })).article.article_id, 'a/b')
})
