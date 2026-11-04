import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { readFile, writeFile } from 'node:fs/promises'

const session = JSON.parse(await readFile('output/social-qa/session.json', 'utf8'))
const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
await context.addInitScript(s => {
  localStorage.setItem('public-beta.session_id', s.session_id)
  localStorage.setItem('public-beta.user_profile', JSON.stringify(s.profile))
}, session)
const page = await context.newPage()
const errors = []
page.on('pageerror', e => errors.push(e.message))
try {
  await page.goto('http://127.0.0.1:5187/dashboard-static/news/social?scope=saved', { waitUntil: 'networkidle' })
  const probe = JSON.parse(await readFile('output/social-qa/import-probe.json', 'utf8'))
  assert.equal(await page.locator('.social-topic').count(), probe.saved.length)
  assert.ok(!await page.getByText("You've been blocked by network security", { exact: false }).count())
  assert.ok(await page.locator('.social-notice').filter({ hasText: 'Nguồn' }).count() > 0)
  await page.screenshot({ path: 'output/social-qa/import-status.png' })
  const mobile = await context.newPage({ viewport: { width: 390, height: 844 } })
  await mobile.setViewportSize({ width: 390, height: 844 })
  await mobile.goto('http://127.0.0.1:5187/dashboard-static/news/social', { waitUntil: 'networkidle' })
  await mobile.screenshot({ path: 'output/social-qa/mobile-390.png' })
  assert.deepEqual(errors, [])
  await writeFile('output/social-qa/imported-browser-report.json', JSON.stringify({
    checks: ['Saved count matches successful live jobs only', 'HTTP-200 Reddit access gate never appears as an article', 'Real upstream error displayed in UI', 'Fresh mobile capture with cached public feed'], errors,
  }, null, 2))
  console.log('PASS 4 live degradation/browser checks')
} finally { await browser.close() }
