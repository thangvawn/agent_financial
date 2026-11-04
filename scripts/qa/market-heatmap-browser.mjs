import { chromium } from 'playwright'
import { readFile, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output = process.env.HEATMAP_QA_OUTPUT || 'output/market-heatmap/single-map'
const session = JSON.parse(await readFile('output/market-heatmap/session.json', 'utf8'))
const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1600, height: 1100 } })
await context.addInitScript(s => {
  localStorage.setItem('public-beta.session_id', s.session_id)
  localStorage.setItem('public-beta.user_profile', JSON.stringify(s.profile))
}, session)
const page = await context.newPage()
const errors = [], checks = [], labelChecks = []
page.on('pageerror', e => errors.push(e.message))
await page.route('**/api/v1/public/data-hub/instruments/**', route => route.fulfill({ json: { points: [] } }))
const endpoint = '**/api/v1/public/data-hub/vn-market/heatmap'
const panel = page.locator('.vn-heatmap')
const svg = panel.getByRole('group', { name: 'Bản đồ nhiệt cổ phiếu Việt Nam' })
const cell = id => panel.locator(`[data-cell-id="${id}"]`)
const ready = async () => {
  await panel.locator('[data-cell-id]').first().waitFor({ timeout: 15000 })
  await page.waitForFunction(() => {
    const p = document.querySelector('.vn-heatmap__plot'), s = p?.querySelector('svg')
    return !document.querySelector('.vn-heatmap__computing') && s && Math.abs(s.viewBox.baseVal.width - p.clientWidth) < 1.1
  })
  await page.evaluate(() => document.fonts.ready)
}
const resetView = async () => {
  await panel.getByLabel('Về toàn cảnh', { exact: true }).click()
  await ready()
  assert.equal(Number(await svg.getAttribute('data-scale')), 1)
}
const assertUniverse = async expected => {
  assert.equal(Number(await svg.getAttribute('data-total-cells')), expected.length)
  const ids = await panel.locator('[data-cell-id]').evaluateAll(es => es.map(e => {
    const lines = [...e.querySelectorAll('tspan')].map(t => t.textContent)
    if (lines.length !== 2 || lines[0] !== e.dataset.cellId || !/^[+-]?[0-9.,]+%$/.test(lines[1])) throw new Error(`Missing label: ${e.dataset.cellId}`)
    return e.dataset.cellId
  }))
  assert.deepEqual(ids.sort(), [...expected].sort())
  assert.equal(await panel.getByLabel('Lượt xem', { exact: true }).count(), 0)
  labelChecks.push({ viewport: page.viewportSize().width, completeMapStocks: ids.length })
}
const focus = async symbol => {
  await panel.getByLabel('Tìm mã trên bản đồ').fill(symbol)
  await panel.getByLabel('Tìm mã trên bản đồ').press('Enter')
  await cell(symbol).waitFor()
  const label = await cell(symbol).evaluate(e => {
    const r = e.querySelector('rect').getBBox(), text = e.querySelector('text'), b = text.getBBox()
    const labelBox = text.getBoundingClientRect(), infoBox = document.querySelector('.vn-heatmap__tooltip').getBoundingClientRect()
    return { font: parseFloat(getComputedStyle(text).fontSize), lines: [...text.querySelectorAll('tspan')].map(t => t.textContent),
      unobscured: labelBox.right <= infoBox.left || labelBox.left >= infoBox.right || labelBox.bottom <= infoBox.top || labelBox.top >= infoBox.bottom,
      fits: b.x >= r.x - .01 && b.y >= r.y - .01 && b.x + b.width <= r.x + r.width + .01 && b.y + b.height <= r.y + r.height + .01 }
  })
  assert.ok(label.font >= 16, JSON.stringify({ symbol, label }))
  assert.ok(label.fits, JSON.stringify({ symbol, label }))
  assert.ok(label.unobscured, JSON.stringify({ symbol, label }))
  assert.equal(label.lines[0], symbol)
  assert.match(label.lines[1], /%$/)
  return label
}
const pass = name => checks.push(name)
try {
  await page.goto('http://127.0.0.1:5188/dashboard-static/global-terminal', { waitUntil: 'networkidle' })
  await ready()
  const snapshot = await (await context.request.get('http://127.0.0.1:5188/api/v1/public/data-hub/vn-market/heatmap')).json()
  const validRows = metric => snapshot.items.filter(i => i[metric] > 0 && i.price > 0 && i.volume !== 0 && Number.isFinite(i.change_pct))
  const ids = metric => validRows(metric).map(i => i.symbol)
  await assertUniverse(ids('value'))
  assert.equal(ids('value').length, 874)
  await panel.screenshot({ path: `${output}/overview.png` })
  pass('All 874 eligible stocks and both labels are on one complete map; no pagination')

  await focus('FPT')
  assert.equal(Number(await svg.getAttribute('data-total-cells')), 874)
  await panel.screenshot({ path: `${output}/focus.png` })
  await panel.getByRole('button', { name: 'Mở chi tiết FPT', exact: true }).click()
  await panel.waitFor({ state: 'hidden' })
  assert.match(await page.locator('body').innerText(), /FPT/)
  await page.reload({ waitUntil: 'networkidle' }); await ready()
  await panel.getByRole('button', { name: 'Dạng bảng', exact: true }).click()
  await focus('FPT')
  await resetView()
  pass('Ticker search navigates within the original universe and opens existing stock details')

  for (const metric of ['market_cap', 'volume', 'value']) {
    await panel.getByLabel('Diện tích ô', { exact: true }).selectOption(metric); await ready()
    await assertUniverse(ids(metric))
    const smallest = [...validRows(metric)].sort((a, b) => a[metric] - b[metric]).slice(0, 3)
    for (const item of smallest) { await focus(item.symbol); assert.equal(Number(await svg.getAttribute('data-total-cells')), ids(metric).length) }
    await resetView()
  }
  pass('All three metrics retain complete universes; smallest real stocks magnify to readable labels')

  for (const exchange of ['HOSE', 'HNX', 'UPCOM']) {
    await panel.getByLabel('Sàn giao dịch', { exact: true }).selectOption(exchange); await ready()
    await assertUniverse(validRows('value').filter(i => i.exchange === exchange).map(i => i.symbol))
  }
  await panel.getByLabel('Sàn giao dịch', { exact: true }).selectOption(''); await ready()
  await panel.getByRole('button', { name: 'Bất động sản', exact: true }).click()
  assert.ok(Number(await svg.getAttribute('data-scale')) > 1)
  assert.equal(Number(await svg.getAttribute('data-total-cells')), 874)
  await resetView()
  await panel.getByLabel('Ngành trên bản đồ').selectOption('real_estate'); await ready()
  await assertUniverse(validRows('value').filter(i => i.sector_id === 'real_estate').map(i => i.symbol))
  await panel.getByRole('button', { name: 'Toàn thị trường', exact: true }).click(); await ready()
  pass('Exchange/industry filters work; clicking a sector header zooms without removing other stocks')

  await panel.getByLabel('Phóng to', { exact: true }).click()
  assert.equal(Number(await svg.getAttribute('data-scale')), 2)
  await svg.scrollIntoViewIfNeeded()
  let box = await svg.boundingBox()
  const beforeX = Number(await svg.getAttribute('data-pan-x'))
  await page.mouse.move(box.x + box.width * .5, box.y + box.height * .5)
  await page.mouse.down(); await page.mouse.move(box.x + box.width * .5 + 75, box.y + box.height * .5 + 30, { steps: 8 }); await page.mouse.up()
  assert.ok(Number(await svg.getAttribute('data-pan-x')) > beforeX + 50)
  assert.equal(await panel.getByRole('dialog').count(), 0)
  await resetView()
  await svg.scrollIntoViewIfNeeded(); box = await svg.boundingBox()
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await page.keyboard.down('Control'); await page.mouse.wheel(0, -180); await page.keyboard.up('Control')
  await page.waitForFunction(() => Number(document.querySelector('svg[data-scale]').dataset.scale) > 1)
  assert.equal(await page.evaluate(() => visualViewport.scale), 1)
  await resetView()
  pass('Zoom controls, drag pan, Ctrl-wheel and reset work; dragging never opens a quote')

  await panel.locator('[data-cell-id]').first().focus()
  await page.keyboard.press('ArrowRight'); await page.keyboard.press('Escape')
  assert.equal(await panel.getByRole('dialog').count(), 0)
  await panel.getByLabel('Phóng to bản đồ', { exact: true }).click()
  await page.waitForFunction(() => !!document.fullscreenElement); await ready(); await resetView()
  await assertUniverse(ids('value'))
  await panel.getByLabel('Thu nhỏ bản đồ', { exact: true }).click()
  await page.waitForFunction(() => !document.fullscreenElement); await ready()
  pass('Keyboard traversal and fullscreen preserve the complete map')

  const smallest = [...validRows('value')].sort((a, b) => a.value - b.value)[0].symbol
  for (const width of [1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 }); await ready(); await resetView()
    await assertUniverse(ids('value'))
    assert.ok(await panel.evaluate(e => e.getBoundingClientRect().right <= innerWidth + 1))
    await panel.screenshot({ path: `${output}/overview-${width}.png` })
    await focus(smallest)
    await panel.screenshot({ path: `${output}/smallest-${width}.png` })
    await resetView()
  }
  pass('1024/768/390/320px retain every stock, with readable navigation to the smallest quote')

  await page.setViewportSize({ width: 390, height: 900 }); await ready(); await resetView(); await svg.scrollIntoViewIfNeeded()
  box = await svg.boundingBox()
  const cx = box.x + box.width / 2, cy = box.y + box.height / 2
  const cdp = await context.newCDPSession(page)
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: cx - 35, y: cy, id: 1 }, { x: cx + 35, y: cy, id: 2 }] })
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: cx - 75, y: cy, id: 1 }, { x: cx + 75, y: cy, id: 2 }] })
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await page.waitForFunction(() => Number(document.querySelector('svg[data-scale]').dataset.scale) > 1.5)
  assert.equal(await page.evaluate(() => visualViewport.scale), 1)
  await resetView()
  pass('Two-finger pinch magnifies the map rather than the page in Chromium touch emulation')

  await panel.getByLabel('Tìm mã trên bản đồ').fill('NOTASYSTEMSYMBOL')
  await panel.getByText('Không có mã đủ dữ liệu trong bộ lọc hiện tại.', { exact: true }).waitFor()
  assert.equal(Number(await svg.getAttribute('data-total-cells')), 874)
  await panel.getByLabel('Tìm mã trên bản đồ').press('Escape')
  await page.route(endpoint, route => route.fulfill({ status: 503, json: { detail: 'QA unavailable' } }))
  await panel.getByLabel('Tải lại bản đồ').click(); await panel.getByRole('alert').waitFor()
  await assertUniverse(ids('value'))
  await page.unroute(endpoint); await panel.getByRole('button', { name: 'Thử lại', exact: true }).click()
  await panel.getByRole('alert').waitFor({ state: 'hidden' })
  pass('Search miss preserves context; refresh failure retains all quotes and retry recovers')

  await page.route(endpoint, route => route.fulfill({ json: { ...snapshot, items: snapshot.items.map(i => ({ ...i, change_pct: null })) } }))
  await panel.getByLabel('Tải lại bản đồ').click()
  await panel.getByText('Chưa có mã đủ giá và % biến động', { exact: true }).waitFor()
  await panel.getByRole('button', { name: 'Xem dạng bảng', exact: true }).click()
  assert.equal(await panel.locator('tbody tr').count(), 874)
  await page.unroute(endpoint)
  pass('Missing percent is explicit and rows remain in the table')
  assert.deepEqual(errors, [])
  await writeFile(`${output}/browser-results.json`, JSON.stringify({ checks, labelChecks, errors }, null, 2))
  console.log(JSON.stringify({ checks, labelChecks, errors }))
} catch (error) {
  await page.screenshot({ path: `${output}/failure.png` })
  await writeFile(`${output}/failure.json`, JSON.stringify({ checks, errors, error: String(error), text: await page.locator('body').innerText() }, null, 2))
  throw error
} finally { await browser.close() }
