import { chromium } from 'playwright'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import assert from 'node:assert/strict'
const output = 'output/market-heatmap/theme'
await mkdir(output, { recursive: true })
const session = JSON.parse(await readFile('output/market-heatmap/session.json', 'utf8'))
const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1600, height: 1100 } })
await context.addInitScript(s => {
  localStorage.setItem('public-beta.session_id', s.session_id)
  localStorage.setItem('public-beta.user_profile', JSON.stringify(s.profile))
}, session)
const page = await context.newPage(), checks = [], errors = []
page.on('pageerror', e => errors.push(e.message))
// Deterministic history only for theme/render testing; market quotes use the saved public snapshot.
const points = Array.from({ length: 120 }, (_, i) => ({ date: new Date(Date.UTC(2026, 5, i + 1)).toISOString(), open: 80 + i / 8, close: 81 + i / 8 + Math.sin(i), high: 83 + i / 8, low: 79 + i / 8, volume: 100000 + i * 200 }))
await page.route('**/api/v1/public/data-hub/instruments/**', route => route.fulfill({ json: { points, freshness: 'fresh', source: 'Theme QA fixture' } }))
await page.route('https://s3.tradingview.com/**', route => route.fulfill({ body: '', contentType: 'application/javascript' }))
const panel = page.locator('.vn-heatmap')
const toggle = page.getByRole('switch', { name: 'Chế độ tối', exact: true })
const ready = async () => {
  await panel.locator('[data-cell-id]').first().waitFor({ timeout: 20000 })
  await page.waitForFunction(() => {
    const plot = document.querySelector('.vn-heatmap__plot'), svg = plot?.querySelector('svg')
    return !document.querySelector('.vn-heatmap__computing') && svg && Math.abs(svg.viewBox.baseVal.width - plot.clientWidth) < 1.1
  })
  await page.evaluate(() => document.fonts.ready)
}
const theme = async expected => {
  await page.waitForFunction(t => {
    const shell = document.querySelector('.app-shell--global-terminal'), button = document.querySelector('.theme-toggle')
    return shell?.dataset.theme === t && button && (t === 'light' ? ['rgb(255, 255, 255)', 'rgb(237, 243, 248)'] : ['rgb(16, 22, 30)', 'rgb(24, 33, 43)']).includes(getComputedStyle(button).backgroundColor)
  }, expected)
}
// Inspect the live chart API to assert the user-visible time range, without adding production test hooks.
const chartState = async () => page.locator('.gt-lwchart').evaluate(element => {
  let fiber = element[Object.keys(element).find(k => k.startsWith('__reactFiber$'))]
  while (fiber) {
    let hook = fiber.memoizedState
    while (hook && typeof hook === 'object') {
      const current = hook.memoizedState?.current
      if (typeof current?.timeScale === 'function') {
        window.__qaChart ||= current
        return { range: current.timeScale().getVisibleLogicalRange(), sameChart: window.__qaChart === current }
      }
      hook = hook.next
    }
    fiber = fiber.return
  }
  throw new Error('Chart API not found')
})
const colors = async () => page.evaluate(() => {
  const selectors = ['.app-shell--global-terminal', '.connected-nav', '.mp-desk', '.global-terminal', '.vn-heatmap', '.vn-heatmap__tooltip']
  return Object.fromEntries(selectors.map(s => { const e = document.querySelector(s); return [s, e ? { bg: getComputedStyle(e).backgroundColor, ink: getComputedStyle(e).color, scheme: getComputedStyle(e).colorScheme } : null] }))
})
try {
  await page.goto('http://127.0.0.1:5188/dashboard-static/global-terminal')
  await ready(); await theme('dark')
  assert.equal(await toggle.getAttribute('aria-checked'), 'true')
  await page.screenshot({ animations: 'disabled', path: `${output}/dark-overview.png` })
  await panel.getByLabel('Tìm mã trên bản đồ').fill('FPT')
  await panel.getByLabel('Tìm mã trên bản đồ').press('Enter')
  await panel.locator('.vn-heatmap__tooltip[data-pinned="true"]').waitFor()
  const map = panel.locator('[data-total-cells]')
  const scale = await map.getAttribute('data-scale'), count = await map.getAttribute('data-total-cells')
  const before = await colors()
  await toggle.click(); await theme('light'); await ready()
  assert.equal(await toggle.getAttribute('aria-checked'), 'false')
  assert.equal(await map.getAttribute('data-scale'), scale)
  assert.equal(await map.getAttribute('data-total-cells'), count)
  assert.match(await panel.locator('.vn-heatmap__tooltip').innerText(), /FPT/)
  const after = await colors()
  for (const s of Object.keys(before)) { assert.notEqual(before[s].bg, after[s].bg, s); assert.equal(after[s].scheme, 'light') }
  assert.equal(after['.mp-desk'].bg, after['.global-terminal'].bg)
  assert.equal(after['.global-terminal'].bg, after['.vn-heatmap'].bg)
  await page.screenshot({ animations: 'disabled', path: `${output}/light-focus.png` })
  checks.push('Shared shell/map/tooltip palette changes; zoom, focused stock and all cells retained')
  await page.reload(); await ready(); await theme('light')
  assert.equal(await toggle.getAttribute('aria-checked'), 'false')
  await page.screenshot({ animations: 'disabled', path: `${output}/light-overview.png` })
  checks.push('Light preference persists after reload')
  await page.getByRole('tab', { name: 'Cổ phiếu', exact: true }).click()
  await page.locator('.gt-priceboard tbody tr').first().waitFor()
  await page.screenshot({ animations: 'disabled', path: `${output}/light-stocks.png` })
  const spark = page.locator('.gt-priceboard .price-sparkline[data-state="ready"]').first()
  await spark.waitFor(); await spark.focus()
  const tip = page.locator('.price-sparkline-tooltip')
  await tip.waitFor(); assert.equal(await tip.getAttribute('data-theme'), 'light')
  await toggle.click(); await theme('dark')
  await spark.focus(); await tip.waitFor(); assert.equal(await tip.getAttribute('data-theme'), 'dark')
  checks.push('Stock table and body-portalled sparkline tooltip follow both modes')
  await page.screenshot({ animations: 'disabled', path: `${output}/dark-stocks.png` })
  await page.getByRole('tab', { name: 'Tổng quan', exact: true }).click(); await ready()
  await page.setViewportSize({ width: 390, height: 844 }); await ready()
  await page.screenshot({ animations: 'disabled', path: `${output}/mobile-dark.png` })
  const bounds = await toggle.boundingBox()
  assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= 390)
  assert.ok(bounds.height >= 40)
  await toggle.focus(); await page.keyboard.press('Space'); await theme('light')
  await page.screenshot({ animations: 'disabled', path: `${output}/mobile-light.png` })
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
  checks.push('Visible 42px mobile toggle, keyboard Space works, no horizontal page overflow')
  await page.setViewportSize({ width: 1600, height: 1100 }); await ready()
  await panel.getByLabel('Tìm mã trên bản đồ').fill('FPT')
  await panel.getByLabel('Tìm mã trên bản đồ').press('Enter')
  await panel.getByRole('button', { name: 'Mở chi tiết FPT', exact: true }).click()
  const chart = page.locator('.gt-lwchart')
  await chart.waitFor()
  await chartState()
  // Deliberately zoom away from fitContent; a theme change must not reset this range.
  await page.evaluate(() => window.__qaChart.timeScale().setVisibleLogicalRange({ from: 45, to: 85 }))
  await page.waitForFunction(() => window.__qaChart.timeScale().getVisibleLogicalRange()?.from === 45)
  const range = (await chartState()).range
  await toggle.click(); await theme('dark')
  let result = await chartState()
  assert.deepEqual(result.range, range); assert.equal(result.sameChart, true)
  await page.screenshot({ animations: 'disabled', path: `${output}/dark-detail.png` })
  await toggle.click(); await theme('light')
  result = await chartState(); assert.deepEqual(result.range, range); assert.equal(result.sameChart, true)
  await page.screenshot({ animations: 'disabled', path: `${output}/light-detail.png` })
  checks.push('Live Lightweight Chart retains its instance and zoomed visible range through both theme changes')
  await page.getByRole('button', { name: 'TradingView Live', exact: true }).click()
  const widgetTheme = () => page.locator('.tradingview-widget-container script').evaluate(e => JSON.parse(e.textContent).theme)
  assert.equal(await widgetTheme(), 'light')
  await toggle.click(); await theme('dark'); assert.equal(await widgetTheme(), 'dark')
  checks.push('TradingView embed receives the current theme (external script stubbed; provider rendering not certified)')
  const other = await context.newPage()
  await other.goto('http://127.0.0.1:5188/dashboard-static/global-terminal')
  await other.evaluate(() => localStorage.setItem('public-beta.theme', 'light'))
  await theme('light'); assert.equal(await widgetTheme(), 'light')
  await other.close()
  checks.push('Preference syncs to an already-open tab, including the chart widget')
  await context.addInitScript(() => { const get = Storage.prototype.getItem; Storage.prototype.getItem = function(k) { if (k === 'public-beta.theme') throw new DOMException('Disabled', 'SecurityError'); return get.call(this, k) }; const set = Storage.prototype.setItem; Storage.prototype.setItem = function(k, v) { if (k === 'public-beta.theme') throw new DOMException('Disabled', 'SecurityError'); return set.call(this, k, v) } })
  await page.reload(); await ready(); await theme('dark'); await toggle.click(); await theme('light')
  checks.push('Theme remains usable when preference storage is blocked')
  assert.deepEqual(errors, [])
} finally {
  await writeFile(`${output}/checks.json`, JSON.stringify({ checks, errors }, null, 2))
  await browser.close()
}
console.log(JSON.stringify({ checks, errors }, null, 2))
