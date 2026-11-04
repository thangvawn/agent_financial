// Run against scripts/qa/market-heatmap-server.py, with its temporary auth DB.
import { chromium } from 'playwright'
import { readFile, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output = 'output/market-heatmap/fixes'
const session = JSON.parse(await readFile('output/market-heatmap/session.json', 'utf8'))
const snapshot = JSON.parse(await readFile('output/market-heatmap/live-snapshot.json', 'utf8'))
const browser = await chromium.launch()
const checks = [], errors = []
const context = await browser.newContext({ viewport: { width: 1600, height: 1100 } })
await context.addInitScript(s => {
  localStorage.setItem('public-beta.session_id', s.session_id)
  localStorage.setItem('public-beta.user_profile', JSON.stringify(s.profile))
}, session)
const page = await context.newPage()
page.on('pageerror', e => errors.push(e.message))
await page.route('**/api/v1/public/data-hub/instruments/**', r => r.fulfill({ json: { points: [] } }))
let payload = snapshot
await page.route('**/api/v1/public/data-hub/vn-market/heatmap', r => r.fulfill({ json: payload }))
const panel = page.locator('.vn-heatmap'), svg = panel.locator('svg[data-scale]')
const ready = () => page.waitForFunction(() => {
  const p = document.querySelector('.vn-heatmap'), s = p?.querySelector('svg[data-scale]')
  return s && +s.dataset.totalCells > 0 && !p.querySelector('.vn-heatmap__computing') && !p.querySelector('[aria-label="Tải lại bản đồ"]').disabled
})
const load = async () => { payload = snapshot; await page.goto('http://127.0.0.1:5188/dashboard-static/global-terminal', { waitUntil: 'networkidle' }); await ready() }
const camera = () => svg.evaluate(e => ({ scale: +e.dataset.scale, x: +e.dataset.panX, y: +e.dataset.panY }))
const focus = async id => { await panel.getByLabel('Tìm mã trên bản đồ').fill(id); await panel.getByLabel('Tìm mã trên bản đồ').press('Enter'); await panel.getByRole('dialog', { name: `Thông tin ${id}` }).waitFor() }
const refresh = async () => {
  await Promise.all([page.waitForResponse(r => r.url().endsWith('/vn-market/heatmap')), panel.getByLabel('Tải lại bản đồ').click()])
  await ready()
}
try {
  await load()
  await focus('PFL')
  assert.match(await panel.getByRole('dialog').innerText(), /150\.000 đ/)
  await panel.getByLabel('Diện tích ô', { exact: true }).selectOption('volume'); await ready(); await focus('ACE')
  assert.match(await panel.getByRole('dialog').innerText(), /100 CP/)
  checks.push('HM-02: real small GTGD/volume display as 150.000 đ and 100 CP')

  await panel.getByLabel('Diện tích ô', { exact: true }).selectOption('market_cap'); await ready()
  await panel.getByLabel('Diện tích ô', { exact: true }).selectOption('volume'); await ready()
  assert.equal((await camera()).scale, 1)
  assert.equal(await panel.locator('[data-cell-id]').count(), 874)
  checks.push('Switching metric away and back resets the viewport without reviving old zoom')

  await load(); await focus('PFL')
  payload = { ...snapshot, items: snapshot.items.map(r => r.symbol === 'VCB' ? { ...r, value: r.value * 1.01 } : r) }
  await refresh()
  await page.waitForFunction(() => {
    const p = document.querySelector('.vn-heatmap'); return p?.innerText.includes('17.171,35') && !p.querySelector('.vn-heatmap__computing')
  })
  const label = panel.locator('[data-cell-id="PFL"] text')
  assert.ok(await label.evaluate(e => parseFloat(getComputedStyle(e).fontSize) >= 16))
  assert.ok(await panel.getByRole('dialog', { name: 'Thông tin PFL' }).isVisible())
  await panel.screenshot({ path: `${output}/retained-focus-desktop.png` })
  checks.push('HM-03: changed weights preserve the selected tiny stock and pinned quote')

  payload = { ...payload, items: payload.items.filter(r => r.symbol !== 'PFL') }
  await refresh()
  await page.waitForFunction(() => document.querySelector('.vn-heatmap svg[data-scale]')?.dataset.totalCells === '873')
  assert.equal((await camera()).scale, 1)
  assert.equal(await panel.getByRole('dialog').count(), 0)
  checks.push('Removing the selected stock safely returns to the complete map')

  await load(); await panel.getByLabel('Phóng to', { exact: true }).click(); await svg.scrollIntoViewIfNeeded()
  let box = await svg.boundingBox()
  await page.mouse.move(box.x + box.width - 1, box.y + box.height / 2); await page.mouse.down()
  await page.mouse.move(box.x + box.width + 8, box.y + box.height / 2); await page.mouse.up()
  const released = await camera()
  await page.mouse.move(box.x + box.width - 90, box.y + box.height / 2)
  assert.deepEqual(await camera(), released)
  assert.equal(await panel.getByRole('dialog').count(), 0)
  await page.mouse.down(); await page.evaluate(() => window.dispatchEvent(new Event('blur'))); await page.mouse.up()
  const blurred = await camera(); await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  assert.deepEqual(await camera(), blurred)
  checks.push('HM-04: release outside and window blur end the drag without accidental quote clicks')

  await panel.getByLabel('Về toàn cảnh', { exact: true }).click()
  const heading = panel.getByRole('button', { name: 'Bất động sản', exact: true })
  await heading.focus(); await page.keyboard.press('Enter')
  assert.ok((await camera()).scale > 1)
  await panel.getByLabel('Về toàn cảnh', { exact: true }).click()
  await panel.locator('[data-cell-id="VCB"]').click()
  assert.ok(await panel.getByRole('dialog', { name: 'Thông tin VCB' }).isVisible())
  checks.push('HM-06: keyboard sector action after dragging and normal cell clicks both work')

  await load()
  await page.evaluate(() => {
    window.__workerCount = 0
    const Native = window.Worker
    window.Worker = class extends Native {
      constructor(...args) {
        super(...args); window.__workerCount++
        if (window.__workerCount === 1) setTimeout(() => { this.onerror?.(new Event('error')); this.terminate() }, 0)
      }
    }
  })
  await panel.getByLabel('Sàn giao dịch', { exact: true }).selectOption('HNX')
  await panel.getByText('Không khởi tạo được bản đồ. Bạn vẫn có thể xem dữ liệu dạng bảng.', { exact: true }).waitFor()
  await refresh()
  assert.equal(await page.evaluate(() => window.__workerCount), 2)
  assert.equal(await panel.locator('[data-cell-id]').count(), 194)
  checks.push('HM-05: top-level refresh restarts a failed worker even for an identical snapshot')

  await page.evaluate(() => { window.__workerCount = 0 })
  await panel.getByLabel('Sàn giao dịch', { exact: true }).selectOption('HOSE')
  await panel.getByRole('button', { name: 'Thử dựng lại bản đồ' }).waitFor()
  await panel.getByRole('button', { name: 'Thử dựng lại bản đồ' }).click(); await ready()
  assert.equal(await page.evaluate(() => window.__workerCount), 2)
  assert.equal(await panel.locator('[data-cell-id]').count(), 375)
  checks.push('Dedicated layout retry recovers independently of the network request')

  await load(); await page.setViewportSize({ width: 390, height: 900 })
  await page.waitForFunction(() => {
    const p = document.querySelector('.vn-heatmap__plot'), s = p?.querySelector('svg[data-scale]')
    return s && !p.querySelector('.vn-heatmap__computing') && Math.abs(p.clientWidth - s.viewBox.baseVal.width) < 1.1 && +s.dataset.totalCells === 874
  })
  await focus('PFL')
  payload = { ...snapshot, items: snapshot.items.map(r => r.symbol === 'VCB' ? { ...r, value: r.value * 1.01 } : r) }
  await refresh()
  await page.waitForFunction(() => document.querySelector('.vn-heatmap')?.innerText.includes('17.171,35') && !document.querySelector('.vn-heatmap__computing'))
  assert.ok(await panel.getByRole('dialog', { name: 'Thông tin PFL' }).isVisible())
  assert.ok(await panel.locator('[data-cell-id="PFL"] text').evaluate(e => parseFloat(getComputedStyle(e).fontSize) >= 16))
  await panel.screenshot({ path: `${output}/retained-focus-mobile.png` })
  checks.push('Mobile keeps the selected quote through refresh with correct small-value units')
  assert.deepEqual(errors, [])
  await writeFile(`${output}/browser-regressions.json`, JSON.stringify({ checks, errors }, null, 2))
  console.log(JSON.stringify({ checks, errors }))
} catch (error) {
  await page.screenshot({ path: `${output}/failure.png` })
  await writeFile(`${output}/failure.json`, JSON.stringify({ checks, errors, error: String(error) }, null, 2))
  throw error
} finally { await browser.close() }
