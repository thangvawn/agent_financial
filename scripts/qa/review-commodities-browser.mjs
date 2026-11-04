// Review observations against the isolated commodities QA server on 5191.
// Advances browser time; does not mutate the application DB or call providers.
import { chromium } from 'playwright'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output = 'output/playwright/commodities-review'
await mkdir(output, { recursive: true })
const fixtureDir = 'output/playwright/commodities'
const quotes = JSON.parse(await readFile(`${fixtureDir}/quotes.json`, 'utf8'))
const histories = JSON.parse(await readFile(`${fixtureDir}/histories.json`, 'utf8'))
const session = JSON.parse(await readFile(`${fixtureDir}/session.json`, 'utf8'))
const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } })
await context.addInitScript(s => {
  localStorage.setItem('public-beta.session_id', s.session_id)
  localStorage.setItem('public-beta.user_profile', JSON.stringify(s.profile))
  localStorage.setItem('public-beta.theme', 'dark')
}, session)
const page = await context.newPage()
const requests = [], errors = [], observations = []
let version = 0, failHistory = false
page.on('pageerror', error => errors.push(error.message))
await page.route('**/*', async route => {
  const url = new URL(route.request().url())
  if (url.hostname !== '127.0.0.1') return route.abort()
  if (url.pathname.endsWith('/commodities/snapshot')) {
    requests.push({ type: 'quote', version })
    const payload = structuredClone(quotes)
    payload.items = payload.items.filter(row => row.symbol === 'XAU')
    payload.items[0].price = 4000 + version * 100
    payload.items[0].updated_at = new Date().toISOString()
    return route.fulfill({ json: payload })
  }
  if (url.pathname.includes('/instruments/') && url.pathname.endsWith('/history')) {
    const symbol = decodeURIComponent(url.pathname.split('/').at(-2))
    requests.push({ type: symbol === 'XAU' ? 'history' : 'other-history', version, url: url.pathname + url.search })
    if (failHistory) return route.fulfill({ status: 503, json: { detail: 'QA provider unavailable' } })
    const period = url.searchParams.get('period')
    const payload = structuredClone(histories.XAU)
    payload.points = payload.points.slice(-({'1mo': 22, '3mo': 66, '6mo': 132, '1y': 260}[period] || 66))
    for (const point of payload.points) {
      for (const key of ['open', 'high', 'low', 'close']) point[key] += version * 100
    }
    return route.fulfill({ json: payload })
  }
  if (!url.pathname.startsWith('/api/') || url.pathname.includes('/auth/')) return route.continue()
  return route.fulfill({ status: 503, json: { detail: 'QA outside review scope' } })
})

try {
  await page.clock.install()
  await page.goto('http://127.0.0.1:5191/dashboard-static/global-terminal')
  await page.getByRole('tab', { name: 'Hàng hóa', exact: true }).click()
  await page.locator('.commodity-chart [role="img"]').waitFor()
  await page.locator('.price-sparkline[data-state="ready"]').first().waitFor()
  const initialLegend = await page.locator('.gt-lwchart-legend').innerText()
  const before = { quotes: requests.filter(x => x.type === 'quote').length, history: requests.filter(x => x.type === 'history').length }
  version = 1
  await page.clock.fastForward(11 * 60 * 1000)
  await page.locator('.commodity-quote strong').filter({ hasText: '4,100.00' }).waitFor()
  const after = { quotes: requests.filter(x => x.type === 'quote').length, history: requests.filter(x => x.type === 'history').length }
  assert.ok(after.quotes > before.quotes)
  assert.equal(after.history, before.history)
  assert.equal(await page.locator('.gt-lwchart-legend').innerText(), initialLegend)
  observations.push({ case: 'quotes_refresh_after_11_minutes_but_both_charts_do_not', before, after })

  version = 2
  await page.getByRole('button', { name: 'Làm mới bảng giá', exact: true }).click()
  await page.locator('.commodity-quote strong').filter({ hasText: '4,200.00' }).waitFor()
  assert.equal(requests.filter(x => x.type === 'history').length, after.history)
  observations.push({ case: 'quote_refresh_does_not_refresh_history_or_sparklines', historyRequests: after.history })
  await page.screenshot({ path: `${output}/quote-chart-desync.png`, fullPage: true })

  await page.getByRole('button', { name: 'Tải lại lịch sử giá', exact: true }).click()
  await page.locator('.commodity-chart [role="img"]').waitFor()
  assert.notEqual(await page.locator('.gt-lwchart-legend').innerText(), initialLegend)
  const refreshRequest = requests.filter(x => x.type === 'history').at(-1)
  assert.ok(!new URL(`http://localhost${refreshRequest.url}`).searchParams.has('refresh'))
  observations.push({ case: 'history_refresh_omits_backend_refresh_flag', request: refreshRequest })

  failHistory = true
  await page.getByRole('button', { name: 'Tải lại lịch sử giá', exact: true }).click()
  await page.getByText('Chưa tải được biểu đồ', { exact: true }).waitFor()
  assert.equal(await page.locator('.commodity-chart canvas').count(), 0)
  observations.push({ case: 'transient_history_error_removes_previous_chart', chartCanvasCount: 0, tablePreserved: await page.locator('.commodity-table tbody tr').count() === 1 })
  await page.screenshot({ path: `${output}/history-retry-discards-chart.png`, fullPage: true })
  assert.deepEqual(errors, [])
} finally {
  await writeFile(`${output}/observations.json`, JSON.stringify({ observations, errors, requests }, null, 2))
  await browser.close()
}
console.log(JSON.stringify({ observations, errors }, null, 2))
