import assert from 'node:assert/strict'
import { test, after } from 'node:test'
import { getViteServer, closeViteServer, React, renderToString } from './test-helpers.js'

after(closeViteServer)

test('social route and URL filters survive reload; unsupported values are normalized', async () => {
  const server = await getViteServer()
  const { resolveDomainRoute } = await server.ssrLoadModule('/src/app/domainRoutes.js')
  const { socialFilters } = await server.ssrLoadModule('/src/features/news/pages/hooks/useSocialFeed.js')
  assert.equal(resolveDomainRoute('/dashboard-static/news/social'), 'news_social')
  assert.deepEqual(socialFilters('?market=global&scope=saved&platform=reddit&hours=24&q=FPT'), {
    market: 'global', scope: 'saved', platform: 'reddit', hours: '24', q: 'FPT',
  })
  assert.equal(socialFilters('?platform=facebook&hours=-1').platform, 'all')
})

test('social URLs reject scripts and lookalike hosts; dates do not invent publication times', async () => {
  const server = await getViteServer()
  const { safeSocialUrl } = await server.ssrLoadModule('/src/features/news/services/socialApi.js')
  const { socialDate } = await server.ssrLoadModule('/src/features/news/pages/socialLabels.js')
  assert.equal(safeSocialUrl('javascript:alert(1)'), null)
  assert.equal(safeSocialUrl('https://www.youtube.com.evil.test/watch?v=1'), null)
  assert.equal(socialDate({ published_at: null, fetched_at: 1 }), 'Chưa rõ ngày đăng')
  assert.equal(socialDate({ published_at: '2026-11-02', time_precision: 'day' }), '02/11/2026')
})

test('reader escapes source markup and distinguishes unavailable subtitles', async () => {
  const server = await getViteServer()
  const { default: Reader } = await server.ssrLoadModule('/src/features/news/pages/components/SocialReader.jsx')
  const post = { id: 'one', platform: 'youtube', title: '<script>unsafe()</script>', text: '<img onerror="bad()">',
    url: 'https://www.youtube.com/watch?v=12345678901', saved: false, content_kind: 'description', transcript_status: 'unavailable' }
  const markup = renderToString(React.createElement(Reader, { topic: { title: post.title, posts: [post], evidence: [], related_news: [], post_count: 1, author_count: 0 } }))
  assert.ok(!markup.includes('<script>unsafe()'))
  assert.ok(markup.includes('&lt;script&gt;'))
  assert.ok(markup.includes('Chưa đọc được phụ đề'))
  assert.ok(markup.includes('Chưa xác minh độc lập'))
})
