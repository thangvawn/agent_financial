import { chromium } from 'playwright'
import { readFile, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const base = 'http://127.0.0.1:5187'
const session = JSON.parse(await readFile('output/social-qa/session.json', 'utf8'))
const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
await context.addInitScript(({ session_id, profile }) => {
  localStorage.setItem('public-beta.session_id', session_id)
  localStorage.setItem('public-beta.user_profile', JSON.stringify(profile))
}, session)
const page = await context.newPage()
const errors = []
const checks = []
const api = async (path, method = 'GET', data) => {
  const response = await context.request.fetch(`${base}/api/v1/public/news/social${path}`, {
    method, headers: { Authorization: `Bearer ${session.session_id}` }, data,
  })
  assert.ok(response.ok(), `${method} ${path}: ${response.status()}`)
  return response.json()
}
const check = async (name, task) => {
  await task()
  checks.push(name)
  console.log(`PASS ${name}`)
}
const settle = async () => {
  await page.waitForFunction(() => !document.querySelector('.social-loading') &&
    !document.querySelector('.social-feed[aria-busy="true"]'))
}
const filter = async task => {
  await Promise.all([page.waitForResponse(r => r.url().includes('/news/social/feed')), task()])
  await settle()
}
page.on('pageerror', e => errors.push(e.message))
try {
// Reset only this temporary QA account, making this smoke script repeatable.
for (const source of (await api('/sources')).sources) {
  if (!source.id.startsWith('youtube-') && !source.id.startsWith('reddit-')) await api(`/subscriptions/${source.id}`, 'DELETE')
  else await api(`/subscriptions/${source.id}`, 'PATCH', { enabled: true })
}
for (const topic of (await api('/feed?scope=saved')).topics) await api(`/posts/${topic.lead.id}/save`, 'DELETE')
await page.goto(`${base}/dashboard-static/news/social`, { waitUntil: 'networkidle' })
await check('Authenticated live feed and attributed details', async () => {
  assert.ok(await page.locator('.social-topic').count() > 0)
  await page.getByRole('article', { name: 'Chi tiết thảo luận' }).waitFor()
  assert.ok(await page.locator('.social-evidence figcaption a').count() > 0)
})
await check('Vietnam / international / platform / search filters', async () => {
  for (const [label, value] of [['Việt Nam', 'vietnam'], ['Quốc tế', 'global']]) {
    await filter(() => page.getByRole('button', { name: label, exact: true }).click())
    assert.equal(new URL(page.url()).searchParams.get('market'), value)
    assert.ok((await api(`/feed?market=${value}`)).topics.every(t => t.market === value))
  }
  await filter(() => page.getByLabel('Lọc nền tảng', { exact: true }).selectOption('reddit'))
  // The public Reddit sample is old: the seven-day feed must remain honestly empty.
  await page.getByText('Chưa có thảo luận trong phạm vi này', { exact: true }).waitFor()
  await filter(() => page.getByLabel('Lọc nền tảng', { exact: true }).selectOption('all'))
  await filter(() => page.getByPlaceholder('Tìm mã hoặc chủ đề…').fill('no-match-qa-98765'))
  await page.getByText('Chưa có thảo luận trong phạm vi này', { exact: true }).waitFor()
  await filter(() => page.getByPlaceholder('Tìm mã hoặc chủ đề…').fill(''))
  await filter(() => page.getByRole('button', { name: 'Tất cả', exact: true }).click())
})
await check('Save persists through reload; unsave updates saved list', async () => {
  await page.locator('.social-original-top button').first().click()
  await page.getByText('Đã lưu bài vào tài khoản của bạn.', { exact: true }).waitFor()
  await filter(() => page.getByRole('button', { name: 'Đã lưu', exact: true }).first().click())
  await page.reload({ waitUntil: 'networkidle' })
  assert.equal(await page.locator('.social-topic').count(), 1)
  await page.locator('.social-original-top button').first().click()
  await page.getByText('Chưa có bài đã lưu', { exact: true }).waitFor()
  await filter(() => page.getByRole('button', { name: 'Khám phá', exact: true }).click())
})
await check('Watchlist empty state and URL state reload', async () => {
  await filter(() => page.getByRole('button', { name: 'Theo watchlist', exact: true }).click())
  await page.getByText('Chưa có thảo luận khớp watchlist', { exact: true }).waitFor()
  await page.reload({ waitUntil: 'networkidle' })
  assert.equal(await page.getByRole('button', { name: 'Theo watchlist' }).getAttribute('aria-pressed'), 'true')
  await filter(() => page.getByRole('button', { name: 'Khám phá', exact: true }).click())
})
await check('Create, disable, enable and remove a source', async () => {
  await page.getByRole('button', { name: 'Nguồn theo dõi', exact: true }).click()
  await page.getByRole('button', { name: 'Thêm nguồn', exact: true }).click()
  await page.getByLabel('Tên nguồn', { exact: true }).fill('QA nguồn công nghệ')
  await page.getByLabel('Chủ đề tìm kiếm', { exact: true }).fill('FPT kết quả kinh doanh')
  await page.getByRole('button', { name: 'Theo dõi nguồn', exact: true }).click()
  const row = page.locator('.social-source-row').filter({ hasText: 'QA nguồn công nghệ' })
  await row.waitFor()
  await row.getByRole('checkbox').uncheck()
  await page.waitForFunction(() => [...document.querySelectorAll('.social-source-row')].some(el => el.textContent.includes('QA nguồn công nghệ') && !el.querySelector('input').checked && !el.querySelector('input').disabled))
  await row.getByRole('checkbox').check()
  await page.waitForFunction(() => [...document.querySelectorAll('.social-source-row')].some(el => el.textContent.includes('QA nguồn công nghệ') && el.querySelector('input').checked && !el.querySelector('input').disabled))
  await row.getByRole('button', { name: 'Bỏ nguồn QA nguồn công nghệ' }).click()
  await row.waitFor({ state: 'detached' })
  await page.getByRole('button', { name: 'Nguồn theo dõi', exact: true }).click()
})
await check('Invalid URL rejected with recoverable message', async () => {
  await page.getByRole('button', { name: 'Thêm liên kết', exact: true }).click()
  await page.getByLabel('Liên kết công khai', { exact: true }).fill('https://127.0.0.1/private')
  await page.getByRole('button', { name: 'Thêm vào Đã lưu' }).click()
  await page.locator('.social-error').waitFor()
  assert.ok(await page.getByLabel('Liên kết công khai', { exact: true }).isVisible())
  await page.getByRole('button', { name: 'Thêm liên kết', exact: true }).click()
})
await check('Feed failure and retry recover without blank screen', async () => {
  await page.route('**/news/social/feed?**', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'QA nguồn tạm lỗi' }) }), { times: 1 })
  await filter(() => page.getByRole('button', { name: 'Quốc tế', exact: true }).click())
  await page.getByText('QA nguồn tạm lỗi', { exact: false }).waitFor()
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click()
  await page.locator('.social-topic').first().waitFor()
  await settle()
})
await check('Manual refresh queues once and reports stopped worker', async () => {
  await page.getByRole('button', { name: 'Cập nhật', exact: true }).click()
  await page.getByText('Lượt thu thập đã được lưu, đang chờ tiến trình thu thập hoạt động.').waitFor()
  const status = await api('/sources')
  assert.equal(status.jobs.filter(j => j.status === 'queued').length, 4)
  for (const source of status.sources) await api(`/subscriptions/${source.id}`, 'PATCH', { enabled: false })
})
await page.reload({ waitUntil: 'networkidle' })
await filter(() => page.getByRole('button', { name: 'Tất cả', exact: true }).click())
await check('Desktop + tablet + narrow mobile, source controls and keyboard', async () => {
  await page.screenshot({ path: 'output/social-qa/desktop.png', fullPage: false })
  for (const width of [768, 390, 320]) {
    await page.setViewportSize({ width, height: 844 })
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.locator('.social-topic').first().waitFor()
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
    const overflow = await page.locator('.social-desk button, .social-desk input, .social-desk select').evaluateAll(nodes => nodes.filter(n => { const r=n.getBoundingClientRect();return r.width && (r.right>innerWidth+1 || r.left<0) }).length)
    assert.equal(overflow, 0)
    await page.screenshot({ path: `output/social-qa/mobile-${width}.png`, fullPage: false })
    await page.locator('.social-topic').first().focus()
    await page.keyboard.press('Enter')
    await page.getByRole('button', { name: 'Trở lại danh sách' }).waitFor({ state: 'visible' })
    await page.screenshot({ path: `output/social-qa/reader-${width}.png`, fullPage: false })
    await page.getByRole('button', { name: 'Trở lại danh sách' }).click()
  }
})
await check('Public URL import enqueues an account-owned background job', async () => {
  const posts = JSON.parse(await readFile('output/social-qa/live-posts.json', 'utf8'))
  const video = posts.find(p => p.platform === 'youtube' && p.market === 'global')
  const reddit = posts.find(p => p.platform === 'reddit')
  await page.getByRole('button', { name: 'Thêm liên kết', exact: true }).click()
  await page.getByLabel('Liên kết công khai', { exact: true }).fill(video.url)
  await page.getByLabel('Phạm vi của liên kết', { exact: true }).selectOption('global')
  await page.getByRole('button', { name: 'Thêm vào Đã lưu' }).click()
  await page.getByText('Đã nhận liên kết. Bài đọc được sẽ xuất hiện trong Đã lưu.').waitFor()
  const extra = await api('/imports', 'POST', { url: reddit.url, market: 'global' })
  const status = await api('/sources')
  assert.equal(status.jobs.filter(j => j.status === 'queued').length, 2)
  await writeFile('output/social-qa/import-jobs.json', JSON.stringify({ ids: status.jobs.filter(j => j.status === 'queued').map(j => j.id), reddit: extra.id }, null, 2))
})
assert.deepEqual(errors, [])
} catch (error) {
  await page.screenshot({ path: 'output/social-qa/browser-failure.png', fullPage: true })
  throw error
} finally {
  await writeFile('output/social-qa/browser-report.json', JSON.stringify({ checks, errors }, null, 2))
  await browser.close()
}
