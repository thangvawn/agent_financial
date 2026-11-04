// QA-only: real app/auth on an isolated server, captured public quotes + controlled updates.
import { chromium } from 'playwright'
import { readFile, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'
const out = 'output/market-overview-live'
const session = JSON.parse(await readFile(`${out}/session.json`, 'utf8'))
const original = JSON.parse(await readFile(`${out}/live-snapshot.json`, 'utf8'))
const current = JSON.parse(await readFile(`${out}/current-session.json`, 'utf8'))
const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1600, height: 1080 } })
await context.addInitScript(s => {
  localStorage.setItem('public-beta.session_id', s.session_id)
  localStorage.setItem('public-beta.user_profile', JSON.stringify(s.profile))
  window.__mapQA = { workers: 0, requests: 0, delay: 0, fail: false }
  const NativeWorker = window.Worker
  window.Worker = class extends NativeWorker {
    constructor(...args) { super(...args); window.__mapQA.workers++ }
    postMessage(...args) {
      window.__mapQA.requests++
      if (window.__mapQA.fail) { setTimeout(() => this.onerror?.(new Event('error')), 10); return }
      if (window.__mapQA.delay) setTimeout(() => super.postMessage(...args), window.__mapQA.delay)
      else super.postMessage(...args)
    }
  }
}, session)
const page = await context.newPage(), checks = [], errors = [], evidence = {}
await page.clock.install()
page.on('pageerror', e => errors.push(e.message))
let payload = structuredClone(original), failNetwork = false
await page.route('**/api/v1/public/data-hub/instruments/**', r => r.fulfill({ json: { points: [] } }))
await page.route('**/api/v1/public/data-hub/vn-market/heatmap', r => r.fulfill(failNetwork ? { status: 503, json: { error: 'QA outage' } } : { json: payload }))
const panel = page.locator('.vn-heatmap'), svg = panel.locator('svg[data-scale]')
const waitReady = () => page.waitForFunction(() => {
  const p = document.querySelector('.vn-heatmap'), s = p?.querySelector('svg[data-scale]')
  return +s?.dataset.totalCells > 0 && !p.querySelector('.vn-heatmap__computing') && !p.querySelector('[aria-label="Tải lại bản đồ"]').disabled
})
const camera = () => svg.evaluate(e => ({ scale: +e.dataset.scale, x: +e.dataset.panX, y: +e.dataset.panY }))
const refresh = async () => {
  await Promise.all([page.waitForResponse(r => r.url().endsWith('/vn-market/heatmap')), panel.getByLabel('Tải lại bản đồ', { exact: true }).click()])
  await waitReady()
}
const observe = () => page.evaluate(() => {
  const svg = document.querySelector('.vn-heatmap svg[data-scale]')
  const cells = [...svg.querySelectorAll('[data-cell-id]')]
  window.__observation?.observer.disconnect()
  const o = window.__observation = { svg, cells, changed: new Set(), removed: 0, blankFrames: 0, frames: 0, transitions: new Set() }
  o.observer = new MutationObserver(records => {
    for (const record of records) {
      const cell = (record.target.nodeType === 1 ? record.target : record.target.parentElement)?.closest('[data-cell-id]')
      if (cell) o.changed.add(cell.dataset.cellId)
      for (const node of record.removedNodes) if (node.nodeType === 1) o.removed += Number(node.matches('[data-cell-id]')) + node.querySelectorAll('[data-cell-id]').length
    }
  })
  o.observer.observe(svg, { attributes: true, childList: true, subtree: true, characterData: true })
  svg.addEventListener('transitionrun', e => o.transitions.add(e.propertyName), { signal: (o.controller = new AbortController()).signal })
  const frame = () => { if (window.__observation !== o || o.done) return; o.frames++; if (!svg.isConnected || !svg.querySelector('[data-cell-id]')) o.blankFrames++; requestAnimationFrame(frame) }
  requestAnimationFrame(frame)
})
const observation = () => page.evaluate(() => {
  const o = window.__observation
  o.observer.disconnect(); o.controller.abort(); o.done = true
  return { changed: [...o.changed].sort(), removed: o.removed, blankFrames: o.blankFrames, frames: o.frames,
    retained: o.cells.filter(e => e.isConnected).length, cells: o.cells.length, sameSvg: o.svg === document.querySelector('.vn-heatmap svg[data-scale]'), transitions: [...o.transitions] }
})
try {
  await page.goto('http://127.0.0.1:5193/dashboard-static/global-terminal', { waitUntil: 'networkidle' }); await waitReady()
  assert.equal(await page.locator('.market-overview__header').count(), 0)
  assert.equal(await panel.locator('[data-cell-id]').count(), 874)
  evidence.headerHeight = await panel.evaluate(e => e.querySelector('.vn-heatmap__plot').getBoundingClientRect().top - e.getBoundingClientRect().top)
  assert.ok(evidence.headerHeight <= 110, `Compact controls height ${evidence.headerHeight}`)
  await page.screenshot({ path: `${out}/desktop-dark.png`, fullPage: true })
  await panel.screenshot({ path: `${out}/map-desktop-dark.png` })
  checks.push('Compact overview: redundant hero removed; controls ≤110px at desktop; all 874 eligible stocks remain')

  const workerBefore = await page.evaluate(() => ({ ...window.__mapQA }))
  await observe(); payload = { ...payload, last_success_at: new Date().toISOString() }; await refresh()
  evidence.identical = await observation()
  assert.deepEqual(evidence.identical.changed, []); assert.equal(evidence.identical.removed, 0)
  assert.equal(await page.evaluate(() => window.__mapQA.requests), workerBefore.requests)
  checks.push('Identical refresh: zero cell mutations, zero layout requests, same SVG/DOM nodes')

  await observe()
  payload = { ...payload, items: payload.items.map(r => r.symbol === 'VCB' ? { ...r, change_pct: 2.45, price: r.ref_price * 1.0245 } : r) }
  await refresh(); await panel.locator('[data-cell-id="VCB"]').filter({ hasText: '+2,45%' }).waitFor()
  evidence.priceOnly = await observation()
  assert.deepEqual(evidence.priceOnly.changed, ['VCB']); assert.equal(evidence.priceOnly.removed, 0)
  assert.equal(await page.evaluate(() => window.__mapQA.requests), workerBefore.requests)
  checks.push('Price-only update changes exactly VCB; no unrelated cell mutation or layout work')

  await panel.getByLabel('Phóng to', { exact: true }).click()
  const viewBefore = await camera()
  await observe(); await page.evaluate(() => { window.__mapQA.delay = 600 })
  payload = { ...payload, items: payload.items.map(r => r.symbol === 'VCB' ? { ...r, value: r.value * 1.01 } : r) }
  await refresh()
  assert.deepEqual(await camera(), viewBefore)
  assert.equal(await panel.locator('.vn-heatmap__computing').count(), 0)
  await page.waitForFunction(() => window.__observation.transitions.has('width') || window.__observation.transitions.has('height'))
  await page.waitForTimeout(300)
  evidence.weightUpdate = await observation()
  assert.equal(evidence.weightUpdate.blankFrames, 0); assert.equal(evidence.weightUpdate.removed, 0)
  assert.ok(evidence.weightUpdate.sameSvg); assert.equal(evidence.weightUpdate.retained, evidence.weightUpdate.cells)
  assert.deepEqual(await camera(), viewBefore)
  assert.equal(await page.evaluate(() => window.__mapQA.workers), workerBefore.workers)
  await page.evaluate(() => { window.__mapQA.delay = 0 })
  checks.push('Delayed size update: map stays visible every sampled frame, nodes/worker reused, local geometry transitions, exact zoom/pan retained')

  await observe(); failNetwork = true; await refresh()
  await panel.getByRole('alert').filter({ hasText: 'Không tải được' }).waitFor()
  evidence.networkFailure = await observation()
  assert.equal(evidence.networkFailure.removed, 0); assert.equal(evidence.networkFailure.blankFrames, 0)
  assert.deepEqual(await camera(), viewBefore)
  failNetwork = false; await refresh(); assert.equal(await panel.getByRole('alert').count(), 0)
  checks.push('Network failure retains chart/camera; retry restores service')

  await page.evaluate(() => { window.__mapQA.fail = true })
  payload = { ...payload, items: payload.items.map(r => r.symbol === 'VCB' ? { ...r, value: r.value * 1.01 } : r) }
  await observe(); await refresh()
  await panel.getByText('Chưa cập nhật được diện tích ô; đang giữ bố cục trước.').waitFor()
  evidence.workerFailure = await observation(); assert.equal(evidence.workerFailure.removed, 0)
  await page.evaluate(() => { window.__mapQA.fail = false })
  await panel.getByRole('button', { name: 'Thử dựng lại bản đồ' }).click()
  await page.waitForFunction(() => !document.querySelector('.vn-heatmap [role="alert"]'))
  checks.push('Worker failure retains last-good layout; explicit retry recovers')

  await panel.getByLabel('Về toàn cảnh', { exact: true }).click()
  await panel.getByLabel('Tìm mã trên bản đồ').fill('PFL'); await panel.getByLabel('Tìm mã trên bản đồ').press('Enter')
  await panel.getByRole('dialog', { name: 'Thông tin PFL' }).waitFor()
  const pinnedView = await camera()
  payload = { ...payload, items: payload.items.map(r => r.symbol === 'VCB' ? { ...r, value: r.value * 1.0001 } : r) }
  await refresh(); await page.waitForTimeout(400)
  assert.ok(await panel.getByRole('dialog', { name: 'Thông tin PFL' }).isVisible())
  assert.deepEqual(await camera(), pinnedView)
  await page.evaluate(() => { window.__mapQA.delay = 600 })
  payload = { ...payload, items: payload.items.filter(r => r.symbol !== 'PFL') }
  await refresh()
  assert.ok(await panel.getByRole('dialog', { name: 'Thông tin PFL' }).isVisible(), 'Keep the painted quote until the replacement layout is ready')
  await page.waitForFunction(() => document.querySelector('.vn-heatmap svg[data-scale]').dataset.totalCells === '873')
  assert.equal((await camera()).scale, 1); assert.equal(await panel.getByRole('dialog').count(), 0)
  await page.evaluate(() => { window.__mapQA.delay = 0 })
  checks.push('Pinned tiny quote remains on refresh; removal safely clears selection and returns to overview')

  await panel.getByLabel('Sàn giao dịch', { exact: true }).selectOption('HNX')
  await page.waitForFunction(() => document.querySelector('.vn-heatmap svg[data-scale]').dataset.totalCells === '194')
  assert.equal((await camera()).scale, 1)
  await panel.getByLabel('Xem dạng bảng', { exact: true }).click()
  assert.equal(await panel.locator('tbody tr').count(), 194)
  await panel.getByLabel('Xem bản đồ', { exact: true }).click(); await waitReady()
  await panel.getByLabel('Sàn giao dịch', { exact: true }).selectOption('')
  await page.waitForFunction(() => document.querySelector('.vn-heatmap svg[data-scale]').dataset.totalCells === '873')
  checks.push('Exchange filtering and table/map toggle preserve correct universe')

  payload = structuredClone(current); await refresh()
  await page.waitForFunction(() => document.querySelector('.vn-heatmap svg[data-scale]').dataset.totalCells !== '873')
  const expectedCurrent = current.items.filter(r => r.value > 0 && r.price > 0 && r.volume !== 0 && r.change_pct !== null).length
  assert.equal(await panel.locator('[data-cell-id]').count(), expectedCurrent)
  await page.screenshot({ path: `${out}/current-session.png`, fullPage: true })
  checks.push(`Captured current session: ${expectedCurrent}/${current.items.length} eligible quotes correctly mapped`)

  payload = structuredClone(original); await refresh(); await page.waitForFunction(() => document.querySelector('.vn-heatmap svg[data-scale]').dataset.totalCells === '874')
  await page.getByRole('switch', { name: 'Chế độ tối' }).click()
  await page.screenshot({ path: `${out}/desktop-light.png`, fullPage: true })
  for (const width of [768, 390, 320]) {
    await page.setViewportSize({ width, height: 960 }); await page.waitForTimeout(400)
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `Page overflow at ${width}`)
    const input = panel.getByLabel('Tìm mã trên bản đồ')
    await input.fill('VCB'); assert.ok(await panel.getByLabel('Kết quả tìm mã').isVisible()); await input.press('Enter')
    assert.ok(await panel.getByRole('dialog', { name: 'Thông tin VCB' }).isVisible())
    await panel.getByLabel('Đóng thông tin mã').click(); await panel.getByLabel('Về toàn cảnh', { exact: true }).click()
    await panel.screenshot({ path: `${out}/width-${width}.png` })
  }
  checks.push('Light/dark and 768/390/320px: no page overflow; search, quote and reset usable')
  const requestsBeforePoll = await page.evaluate(() => window.__mapQA.requests)
  payload = { ...payload, freshness: 'stale', items: payload.items.map(r => r.symbol === 'VCB' ? { ...r, change_pct: 1.23, price: r.ref_price * 1.0123 } : r) }
  await observe()
  await page.clock.fastForward(Math.max(30, payload.refresh_interval_seconds || 30) * 1000 + 1000)
  await panel.locator('[data-cell-id="VCB"]').filter({ hasText: '+1,23%' }).waitFor()
  evidence.polling = await observation()
  assert.equal(evidence.polling.removed, 0)
  assert.deepEqual(evidence.polling.changed, ['VCB'])
  assert.equal(await page.evaluate(() => window.__mapQA.requests), requestsBeforePoll)
  assert.ok(await panel.getByText('Dữ liệu lưu trước', { exact: true }).isVisible())
  checks.push('Automatic poll updates only changed ticker; stale-data warning remains visible')
  await page.emulateMedia({ reducedMotion: 'reduce' })
  assert.ok(await panel.locator('[data-cell-id] rect').first().evaluate(e => parseFloat(getComputedStyle(e).transitionDuration) <= .001))
  checks.push('Reduced motion disables tile animation')
  assert.deepEqual(errors, [])
  await writeFile(`${out}/checks.json`, JSON.stringify({ checks, errors, evidence }, null, 2))
  console.log(JSON.stringify({ checks, errors, evidence }, null, 2))
} catch (error) {
  await page.screenshot({ path: `${out}/failure-live.png`, fullPage: true })
  await writeFile(`${out}/failure-live.json`, JSON.stringify({ checks, errors, evidence, error: String(error) }, null, 2))
  throw error
} finally { await browser.close() }
