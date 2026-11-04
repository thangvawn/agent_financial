import { chromium } from 'playwright'
import { readFile, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const base = 'http://127.0.0.1:5192'
const out = 'output/playwright/commodities-fixed'
const session = JSON.parse(await readFile(`${out}/session.json`, 'utf8'))
const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1600, height: 1050 } })
await context.addInitScript(s => {
  localStorage.setItem('public-beta.session_id', s.session_id)
  localStorage.setItem('public-beta.user_profile', JSON.stringify(s.profile))
  localStorage.setItem('public-beta.theme', 'dark')
}, session)
const page = await context.newPage(), errors = [], checks = [], requests = []
let transportError = false
page.on('pageerror', error => errors.push(error.message))
await page.route('**/*', async route => {
  const url = new URL(route.request().url())
  if (url.origin !== base) return route.abort()
  if (url.pathname.includes('/instruments/') && url.pathname.endsWith('/history')) {
    requests.push(url.pathname + url.search)
    if (transportError && url.pathname.includes('/XAU/') && url.searchParams.has('refresh')) return route.fulfill({ status: 503, json: { detail: 'QA network error' } })
    return route.continue()
  }
  if (url.pathname.endsWith('/commodities/snapshot') || url.pathname.includes('/auth/') || !url.pathname.startsWith('/api/')) return route.continue()
  return route.fulfill({ status: 503, json: { detail: 'QA outside scope' } })
})
const control = async body => {
  const response = await context.request.post(`${base}/__qa/control`, { data: body })
  assert.ok(response.ok())
}
const ready = async () => {
  await page.locator('.commodity-chart [role=img]').waitFor()
  await page.waitForFunction(() => document.querySelector('.commodity-chart')?.getAttribute('aria-busy') === 'false')
}
const legend = () => page.locator('.gt-lwchart-legend').innerText()
const xauRequests = () => requests.filter(url => url.includes('/XAU/')).length
const refresh = async (name, period = '3mo') => {
  const response = page.waitForResponse(res => {
    const url = new URL(res.url())
    return url.pathname.includes('/instruments/XAU/history') && url.searchParams.get('period') === period && url.searchParams.has('refresh')
  })
  await page.getByRole('button', { name, exact: true }).click()
  await (await response).finished()
  // A retained chart is already visible during refresh. Wait for React's next
  // paint, instead of treating its old aria-busy=false frame as the new result.
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
  await ready()
}
try {
  await control({ version: 0, history_error: false, history_empty: false, partial: false, expire_history: true, reset_throttle: true })
  await page.clock.install()
  await page.goto(`${base}/dashboard-static/global-terminal`)
  await page.getByRole('tab', { name: 'Hàng hóa', exact: true }).click()
  await ready()
  await page.locator('.commodity-table .price-sparkline[data-state=ready]').first().waitFor()
  assert.equal(await page.locator('.commodity-table tbody tr').count(), 23)
  checks.push('Real snapshot/history API + SQLite/cache serve all 23 contracts')
  await page.getByRole('textbox', { name: 'Tìm hàng hoá', exact: true }).fill('XAU')
  assert.equal(await page.locator('.commodity-table tbody tr').count(), 1)
  const before = await legend(), beforeMini = await page.locator('.commodity-table .price-sparkline').getAttribute('aria-label')
  await page.locator('.commodity-chart [role=img]').evaluate(element => {
    let fiber = element[Object.keys(element).find(key => key.startsWith('__reactFiber$'))]
    while (fiber) {
      let hook = fiber.memoizedState
      while (hook && typeof hook === 'object') {
        const chart = hook.memoizedState?.current
        if (typeof chart?.timeScale === 'function') { window.__qaChart = chart; chart.timeScale().setVisibleLogicalRange({ from: 20, to: 45 }); return }
        hook = hook.next
      }
      fiber = fiber.return
    }
    throw Error('Chart API not found')
  })
  const countBefore = xauRequests()
  await control({ version: 1, expire_history: true })
  await page.clock.fastForward(11 * 60 * 1000)
  await page.waitForFunction(() => document.querySelector('.commodity-quote strong')?.textContent === '4,100.00')
  await ready()
  assert.notEqual(await legend(), before)
  assert.ok(xauRequests() >= countBefore + 2)
  assert.notEqual(await page.locator('.commodity-table .price-sparkline').getAttribute('aria-label'), beforeMini)
  assert.ok(await page.evaluate(() => { const range = window.__qaChart.timeScale().getVisibleLogicalRange(); return Math.abs(range.from - 20) < 1 && Math.abs(range.to - 45) < 1 }))
  checks.push('Quote, main chart and sparkline revalidate after 11 minutes; zoom preserved')
  const beforeManual = await legend(), countManual = xauRequests()
  await control({ version: 2, reset_throttle: true })
  await refresh('Làm mới bảng giá')
  assert.notEqual(await legend(), beforeManual)
  assert.ok(xauRequests() >= countManual + 2)
  assert.ok(requests.filter(url => url.includes('/XAU/')).slice(-2).every(url => url.includes('refresh=true')))
  checks.push('Whole-board manual refresh bypasses both browser and backend history caches')
  await page.screenshot({ path: `${out}/desktop-updated.png`, fullPage: true })

  const lastGood = await legend()
  await control({ history_error: true, reset_throttle: true })
  await refresh('Tải lại lịch sử giá')
  assert.equal(await legend(), lastGood)
  assert.ok((await page.locator('.commodity-detail .commodity-alert').innerText()).includes('giữ dữ liệu'))
  checks.push('Provider failure retains chart, statistics and quote with a stale notice')
  await control({ history_error: false, reset_throttle: true })
  transportError = true
  await refresh('Tải lại lịch sử giá')
  assert.equal(await legend(), lastGood)
  checks.push('HTTP503 also preserves last-good chart')
  transportError = false
  await control({ version: 3, reset_throttle: true })
  await refresh('Tải lại lịch sử giá')
  assert.notEqual(await legend(), lastGood)
  assert.equal(await page.locator('.commodity-detail .commodity-alert').count(), 0)
  checks.push('Retry recovers and clears stale warning')
  await refresh('Tải lại lịch sử giá')
  await page.getByText('Vừa yêu cầu cập nhật. Có thể thử lại sau vài giây.', { exact: true }).waitFor()
  checks.push('Server throttle is visible without clearing the chart')

  await control({ partial: true, reset_throttle: true })
  await refresh('Làm mới bảng giá')
  await page.getByText(/23\/23 hợp đồng có giá/).waitFor()
  assert.ok((await page.locator('.commodity-quote-meta').innerText()).includes('Giá lưu trước đó'))
  assert.ok((await page.locator('.commodity-table').innerText()).includes('XAU'))
  checks.push('Partial provider keeps selected contract and displays its stale status')
  await page.screenshot({ path: `${out}/stale-contract.png`, fullPage: true })

  await control({ partial: false, history_empty: true, reset_throttle: true })
  await page.getByRole('button', { name: '1 năm', exact: true }).click()
  await page.getByText('Chưa đủ lịch sử để vẽ biểu đồ', { exact: true }).waitFor()
  assert.equal(await page.locator('.commodity-chart canvas').count(), 0)
  await control({ history_empty: false, reset_throttle: true })
  await page.getByRole('button', { name: 'Thử lại lịch sử', exact: true }).click()
  await ready()
  checks.push('New uncached period with no data stays empty; retry loads the requested period')

  await page.getByRole('textbox', { name: 'Tìm hàng hoá', exact: true }).fill('')
  await page.getByRole('button', { name: 'Năng lượng', exact: false }).click()
  assert.equal(await page.locator('.commodity-table tbody tr').count(), 5)
  await page.getByRole('button', { name: 'Xem Crude Oil WTI (WTI)', exact: true }).click()
  await ready()
  await page.getByRole('button', { name: 'Tất cả', exact: false }).click()
  await page.getByRole('button', { name: 'Xem Gold (XAU)', exact: true }).click()
  await ready()
  checks.push('Filters and fast cross-contract selection keep the correct history')
  await page.getByRole('switch', { name: 'Chế độ tối', exact: true }).click()
  await page.screenshot({ path: `${out}/desktop-light.png`, fullPage: true })
  for (const width of [768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 })
    await ready()
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
    await page.screenshot({ path: `${out}/width-${width}.png`, fullPage: true })
  }
  checks.push('Both themes and 768/390/320 widths remain usable without page overflow')
  assert.deepEqual(errors, [])
} finally {
  await page.screenshot({ path: `${out}/last-state.png`, fullPage: true }).catch(() => {})
  await writeFile(`${out}/checks.json`, JSON.stringify({ checks, errors, requests }, null, 2))
  await browser.close()
}
console.log(JSON.stringify({ checks, errors }, null, 2))
