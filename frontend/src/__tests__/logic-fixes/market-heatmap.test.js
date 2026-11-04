import assert from 'node:assert/strict'
import { test } from 'node:test'
import { buildHeatmap, priceState, formatMetric, formatChange } from '../../features/market-portfolio/services/marketHeatmapModel.js'
import { createHeatmapLayout, createHeatmapLayoutEngine } from '../../features/market-portfolio/services/marketHeatmapLayout.js'
import { clampView, zoomAt, focusBounds, projectCells, reanchorView, retainLiveView } from '../../features/market-portfolio/services/marketHeatmapViewport.js'

const quote = (symbol, value, extra = {}) => ({ symbol, value, price: 10000, ref_price: 10000, ceiling: 10700, floor: 9300,
  volume: 1000, change_pct: -1.23, exchange: 'HOSE', sector_id: '8', sector: 'Tài chính', name: symbol, ...extra })

test('filter before sizing; retain each stock instead of creating aggregate cells', () => {
  const rows = Array.from({ length: 30 }, (_, i) => quote(`T${i}`, i + 1))
  rows.push(quote('NONE', null), quote('ZERO', 0), quote('OTHER', 999, { exchange: 'HNX' }))
  const result = buildHeatmap(rows, { exchange: 'HOSE' })
  assert.equal(result.total, 465)
  assert.equal(result.eligible, 30)
  assert.equal(result.missing, 1)
  assert.equal(result.zero, 1)
  const children = result.groups.flatMap(g => g.children)
  assert.equal(children.length, 30)
  assert.ok(children.every(c => c.id === c.symbol && !c.aggregate))
  assert.equal(children.reduce((s, c) => s + c.weight, 0), 465)
  assert.equal(buildHeatmap(rows, { query: 'NONE' }).eligible, 0)
  assert.equal(buildHeatmap(rows, { metric: 'market_cap' }).eligible, 0)
})

test('a missing price/change is retained in the table but never rendered as an unlabeled stock', () => {
  const model = buildHeatmap([quote('AAA', 10), quote('BBB', 20, { change_pct: null }), quote('CCC', 20, { volume: 0 })])
  assert.equal(model.rows.length, 3)
  assert.equal(model.missingChange, 2)
  assert.equal(model.total, 50)
  assert.equal(model.mapTotal, 10)
  assert.deepEqual(model.mapRows.map(r => r.symbol), ['AAA'])
})

test('actual prices decide floor/ceiling; value units stay in billions of VND', () => {
  assert.equal(priceState(quote('A', 1, { price: 9300, change_pct: -6.99 })), 'floor')
  assert.equal(priceState(quote('A', 1, { price: 10700, change_pct: 6.99 })), 'ceiling')
  assert.equal(priceState(quote('A', 1, { price: 9350, change_pct: -7 })), 'down')
  assert.equal(priceState(quote('A', 1, { price: null })), 'unknown')
  assert.equal(formatMetric(1e9, 'value'), '1 tỷ')
})

test('small nonzero trades retain meaningful units instead of displaying zero', () => {
  assert.equal(formatMetric(150000, 'value'), '150.000 đ')
  assert.equal(formatMetric(2930000, 'value'), '2,93 triệu đ')
  assert.equal(formatMetric(1e9, 'value'), '1 tỷ')
  assert.equal(formatMetric(100, 'volume'), '100 CP')
  assert.equal(formatMetric(4800, 'volume'), '4.800 CP')
  assert.equal(formatMetric(2e6, 'volume'), '2 triệu CP')
  assert.equal(formatMetric(.00015, 'market_cap'), '150.000 đ')
  assert.match(formatMetric(null, 'value'), /—/)
  assert.equal(formatChange(.001), '+0,001%')
  assert.equal(formatChange(-.001), '-0,001%')
  assert.equal(formatChange(0), '0%')
})

test('a selected tiny stock stays visible and readable when another stock updates', () => {
  const rows = Array.from({ length: 180 }, (_, i) => quote(`X${i}`, (181 - i) ** 4, { sector_id: String(i % 9) }))
  const old = createHeatmapLayout(buildHeatmap(rows).groups, 1000, 650)
  const target = old.cells.find(c => c.id === 'X179')
  const view = focusBounds(target, 1000, 650, old.maxScale)
  const next = createHeatmapLayout(buildHeatmap(rows.map(r => r.symbol === 'X0' ? { ...r, value: r.value * 1.05 } : r)).groups, 1000, 650)
  const anchored = reanchorView(view, old, next, 1000, 650, target.id)
  const visible = projectCells(next.cells, anchored, 1000, 650).find(c => c.id === target.id)
  assert.ok(visible && visible.font >= 16)
  assert.equal(next.totalWeight, rows.reduce((s, r) => s + r.value * (r.symbol === 'X0' ? 1.05 : 1), 0))
})

test('relayout retains the inspected point after manual pan, and resets a removed selection', () => {
  const old = { maxScale: 100, cells: [{ id: 'A', x: 0, y: 0, width: 500, height: 600 }, { id: 'B', x: 500, y: 0, width: 500, height: 600 }] }
  const next = { maxScale: 100, cells: [{ id: 'A', x: 0, y: 0, width: 300, height: 600 }, { id: 'B', x: 300, y: 0, width: 700, height: 600 }] }
  const view = { scale: 4, x: -2500, y: -900 }
  const anchored = reanchorView(view, old, next, 1000, 600)
  assert.equal((500 - anchored.x) / anchored.scale, 650)
  const identity = { scale: 1, x: 0, y: 0 }
  assert.deepEqual(reanchorView(identity, old, next, 1000, 600), identity)
  assert.deepEqual(reanchorView(view, old, { maxScale: 100, cells: [next.cells[0]] }, 1000, 600, 'B'), identity)
})

test('one map contains every stock with finite positive area, no overlap, and no pagination', () => {
  const model = buildHeatmap(Array.from({ length: 240 }, (_, i) => quote(`X${i}`, (241 - i) ** 3, {
    sector_id: String(i % 11), sector: `Ngành ${i % 11}`, change_pct: i % 2 ? -14.99 : 0.01,
  })))
  for (const width of [1530, 740, 366, 296]) {
    const layout = createHeatmapLayout(model.groups, width, 540)
    assert.equal(layout.pages, undefined)
    assert.equal(layout.cells.length, 240)
    assert.equal(new Set(layout.cells.map(c => c.id)).size, 240)
    assert.equal(layout.totalWeight, model.total)
    for (const [i, cell] of layout.cells.entries()) {
      assert.ok([cell.x, cell.y, cell.width, cell.height].every(Number.isFinite))
      assert.ok(cell.width > 0 && cell.height > 0)
      assert.ok(cell.x >= 0 && cell.y >= 0 && cell.x + cell.width <= width + .01 && cell.y + cell.height <= 540.01)
      for (const other of layout.cells.slice(i + 1)) assert.ok(cell.x + cell.width <= other.x + .0001 || other.x + other.width <= cell.x + .0001 || cell.y + cell.height <= other.y + .0001 || other.y + other.height <= cell.y + .0001)
      const focused = projectCells([cell], focusBounds(cell, width, 540, layout.maxScale), width, 540)[0]
      assert.ok(focused.font >= 16, cell.id)
    }
  }
})

test('relative area follows actual weights on the complete map', () => {
  const groups = buildHeatmap([quote('A', 60), quote('B', 30), quote('C', 10)]).groups
  const layout = createHeatmapLayout(groups, 1000, 600, { focused: true })
  const area = layout.cells.reduce((sum, c) => sum + c.width * c.height, 0)
  for (const cell of layout.cells) assert.ok(Math.abs(cell.width * cell.height / area - { A: .6, B: .3, C: .1 }[cell.id]) < .0001)
  assert.deepEqual(createHeatmapLayout(groups, 1000, 600, { focused: true }), layout)
})

test('extreme weight skew keeps tiny cells; navigation magnifies their labels without changing weights', () => {
  const groups = buildHeatmap([quote('VERYVERYLONG', 1e12), quote('TINY', 1, { change_pct: -99.99 })]).groups
  const layout = createHeatmapLayout(groups, 296, 540)
  assert.equal(layout.cells.length, 2)
  const tiny = layout.cells.find(c => c.id === 'TINY')
  const projection = projectCells(layout.cells, focusBounds(tiny, 296, 540, layout.maxScale), 296, 540)
  assert.ok(projection.find(c => c.id === 'TINY').font >= 16)
  assert.equal(layout.totalWeight, 1e12 + 1)
  assert.deepEqual(createHeatmapLayout([], 0, 540).cells, [])
  assert.throws(() => createHeatmapLayout(groups, 99, 540), /hẹp/)
})

test('zoom keeps pointer anchored and pan cannot expose space outside the map', () => {
  const view = { scale: 2, x: -200, y: -150 }, point = { x: 300, y: 200 }
  const next = zoomAt(view, 2, point, 1000, 600, 100)
  assert.equal((point.x - view.x) / view.scale, (point.x - next.x) / next.scale)
  assert.equal((point.y - view.y) / view.scale, (point.y - next.y) / next.scale)
  assert.deepEqual(clampView({ scale: 2, x: 200, y: -9000 }, 1000, 600, 100), { scale: 2, x: 0, y: -600 })
  assert.deepEqual(zoomAt(view, .01, point, 1000, 600, 100), { scale: 1, x: 0, y: 0 })
})

test('projection culls offscreen cells and clips huge geometry to bounded viewport coordinates', () => {
  const cells = [{ id: 'A', x: 0, y: 0, width: 500, height: 600, columns: 6 }, { id: 'B', x: 500, y: 0, width: 500, height: 600, columns: 6 }]
  const result = projectCells(cells, { scale: 10000, x: -8000000, y: -5000000 }, 1000, 600)
  assert.deepEqual(result.map(c => c.id), ['B'])
  assert.equal(result[0].width, 1000)
  assert.equal(result[0].height, 600)
  assert.equal(result[0].font, 30)
})

test('live weights retain tile order and only resize inside the affected sector when its total is unchanged', () => {
  const update = createHeatmapLayoutEngine()
  const rows = [quote('A', 60), quote('B', 30), quote('C', 10), quote('D', 70, { sector_id: '9' }), quote('E', 30, { sector_id: '9' })]
  const initial = update(buildHeatmap(rows).groups, 1000, 650)
  const next = update(buildHeatmap(rows.map(r => ({ ...r, value: { A: 20, B: 70 }[r.symbol] || r.value }))).groups, 1000, 650)
  assert.deepEqual(next.cells.map(c => c.id), initial.cells.map(c => c.id))
  for (const id of ['D', 'E']) assert.deepEqual(next.cells.find(c => c.id === id), initial.cells.find(c => c.id === id))
  const sector = next.cells.filter(c => c.sector_id === '8')
  const totalArea = sector.reduce((n, c) => n + c.width * c.height, 0)
  for (const cell of sector) assert.ok(Math.abs(cell.width * cell.height / totalArea - { A: .2, B: .7, C: .1 }[cell.id]) < 1e-10)
  assert.notDeepEqual(next.cells[0], initial.cells[0])
})

test('successive small ticks move boundaries continuously without overlaps or lost stocks', () => {
  const update = createHeatmapLayoutEngine()
  const rows = Array.from({ length: 80 }, (_, i) => quote(`X${i}`, 100 - i, { sector_id: String(i % 8) }))
  let previous = update(buildHeatmap(rows).groups, 1000, 650)
  for (let tick = 1; tick <= 20; tick++) {
    const next = update(buildHeatmap(rows.map(r => ({ ...r, value: r.value + (r.symbol === 'X0' ? tick * .1 : 0) }))).groups, 1000, 650)
    assert.deepEqual(next.cells.map(c => c.id), previous.cells.map(c => c.id))
    for (const [i, cell] of next.cells.entries()) {
      assert.ok(Math.abs(cell.x - previous.cells[i].x) < 1 && Math.abs(cell.y - previous.cells[i].y) < 1)
      for (const other of next.cells.slice(i + 1)) assert.ok(cell.x + cell.width <= other.x + .0001 || other.x + other.width <= cell.x + .0001 || cell.y + cell.height <= other.y + .0001 || other.y + other.height <= cell.y + .0001)
    }
    previous = next
  }
})

test('stream handles membership changes, empty scope and resize without keeping removed cells', () => {
  const update = createHeatmapLayoutEngine()
  const rows = [quote('A', 60), quote('B', 30), quote('C', 10)]
  update(buildHeatmap(rows).groups, 1000, 650)
  const changed = update(buildHeatmap([rows[0], rows[2], quote('D', 50, { sector_id: '9' })]).groups, 390, 540)
  assert.deepEqual(changed.cells.map(c => c.id).sort(), ['A', 'C', 'D'])
  assert.ok(changed.cells.every(c => c.x + c.width <= 390.0001 && c.y + c.height <= 540.0001))
  assert.deepEqual(update([], 390, 540).cells, [])
  assert.equal(update(buildHeatmap(rows).groups, 1000, 650).cells.length, 3)
})

test('adding a stock only rebuilds rows within its own sector', () => {
  const update = createHeatmapLayoutEngine()
  const rows = [quote('A', 60), quote('B', 40), quote('C', 60, { sector_id: '9' }), quote('D', 40, { sector_id: '9' })]
  const old = update(buildHeatmap(rows).groups, 1000, 650)
  const next = update(buildHeatmap([...rows.map(r => r.symbol === 'A' ? { ...r, value: 50 } : r), quote('NEW', 10)]).groups, 1000, 650)
  assert.equal(next.cells.length, 5)
  for (const id of ['C', 'D']) assert.deepEqual(next.cells.find(c => c.id === id), old.cells.find(c => c.id === id))
  assert.deepEqual(next.sectors, old.sectors)
})

test('live refresh retains the exact camera unless a pinned stock is removed or leaves view', () => {
  const old = { maxScale: 100, cells: [{ id: 'A', x: 0, y: 0, width: 500, height: 600, columns: 8 }] }
  const next = { maxScale: 100, cells: [{ ...old.cells[0], width: 510 }] }
  const view = { scale: 2, x: -200, y: -150 }
  assert.deepEqual(retainLiveView(view, old, next, 1000, 600), view)
  assert.deepEqual(retainLiveView(view, old, next, 1000, 600, 'A'), view)
  assert.deepEqual(retainLiveView(view, old, { cells: [], maxScale: 100 }, 1000, 600, 'A'), { scale: 1, x: 0, y: 0 })
})
