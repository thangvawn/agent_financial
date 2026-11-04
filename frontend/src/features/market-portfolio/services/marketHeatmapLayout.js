import { hierarchy, treemap, treemapResquarify } from 'd3-hierarchy'

function tree(rows, previous) {
  const order = new Map(previous?.children?.map((node, index) => [node.data.id, index]))
  return hierarchy({ children: rows.map(row => ({ ...row })) })
    .sum(node => node.children ? 0 : node.weight)
    .sort((a, b) => {
      if (order.size) {
        const left = order.get(a.data.id) ?? Infinity, right = order.get(b.data.id) ?? Infinity
        if (left !== right) return left - right
      }
      return b.value - a.value || String(a.data.id || '').localeCompare(String(b.data.id || ''))
    })
}
const members = rows => JSON.stringify(rows.map(row => row.id).sort())
function updateWeights(root, rows) {
  const values = new Map(rows.map(row => [row.id, row]))
  root.each(node => { if (!node.children) node.data = { ...values.get(node.data.id) } })
  root.sum(node => node.children ? 0 : node.weight)
}

// Keep separate hierarchies for sectors and their stocks. Ordinary ticks retain
// every treemap row; a newly traded stock only rebuilds its own sector's rows.
export function createHeatmapLayoutEngine() {
  let sectorRoot, sectorMembers, frame
  const stocks = new Map()
  const tile = treemap().tile(treemapResquarify.ratio(1.3))
  return (groups, width, height, { focused = false } = {}) => {
    if (!groups.length) { sectorRoot = null; sectorMembers = null; stocks.clear(); return { cells: [], sectors: [], maxScale: 1 } }
    if (width < 120 || height < 100) throw new Error('Khung quá hẹp. Hãy mở rộng khung hoặc xem dạng bảng.')
    // An explicit viewport resize may choose better row shapes for the new aspect
    // ratio. Live quotes keep exactly the same viewport and never take this path.
    const nextFrame = `${width}:${height}`
    if (frame !== nextFrame) { sectorRoot = null; sectorMembers = null; stocks.clear(); frame = nextFrame }
    const sectors = groups.map(g => ({ id: g.id, name: g.name, weight: g.children.reduce((n, c) => n + c.weight, 0) }))
    const nextMembers = members(sectors)
    if (!sectorRoot || sectorMembers !== nextMembers) {
      sectorRoot = tree(sectors, sectorRoot); sectorMembers = nextMembers
    } else updateWeights(sectorRoot, sectors)
    tile.size([width, height])(sectorRoot)
    const groupsById = new Map(groups.map(group => [group.id, group]))
    for (const id of stocks.keys()) if (!groupsById.has(id)) stocks.delete(id)
    const cells = [], regions = []
    for (const sector of sectorRoot.leaves()) {
      const group = groupsById.get(sector.data.id)
      const topology = members(group.children), prior = stocks.get(group.id)
      const root = prior?.topology === topology ? prior.root : tree(group.children, prior?.root)
      if (prior?.topology === topology) updateWeights(root, group.children)
      stocks.set(group.id, { root, topology })
      const w = sector.x1 - sector.x0, h = sector.y1 - sector.y0
      const headerHeight = focused ? 0 : Math.min(24, h * .05)
      tile.size([w, h - headerHeight])(root)
      if (!focused) regions.push({ id: group.id, name: group.name, x: sector.x0, y: sector.y0, width: w, height: h, headerHeight })
      for (const node of root.leaves()) {
        const x = sector.x0 + node.x0, y = sector.y0 + headerHeight + node.y0
        const cellWidth = node.x1 - node.x0, cellHeight = node.y1 - node.y0
        cells.push({ id: node.data.id, sector_id: group.id, x, y, width: cellWidth, height: cellHeight,
          center: [x + cellWidth / 2, y + cellHeight / 2], columns: Math.max(node.data.id.length, 8) })
      }
    }
    if (cells.some(c => !(c.width > 0 && c.height > 0))) throw new Error('Chưa dựng được bản đồ đầy đủ. Hãy xem dữ liệu dạng bảng.')
    const maxScale = Math.max(16, ...cells.map(c => Math.max(
      Math.min((width - 40) / c.width, (height - 40) / c.height),
      24 * c.columns * .62 / (c.width * .8), 24 * 2.4 / (c.height * .8),
    )))
    return { cells, sectors: regions, maxScale, totalWeight: sectorRoot.value }
  }
}

export function createHeatmapLayout(groups, width, height, options) {
  return createHeatmapLayoutEngine()(groups, width, height, options)
}
