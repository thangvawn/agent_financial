export function clampView(view, width, height, maxScale) {
  const scale = Math.max(1, Math.min(maxScale, view.scale))
  return { scale, x: Math.max(width * (1 - scale), Math.min(0, view.x)),
    y: Math.max(height * (1 - scale), Math.min(0, view.y)) }
}

export function zoomAt(view, factor, point, width, height, maxScale) {
  const scale = Math.max(1, Math.min(maxScale, view.scale * factor))
  return clampView({ scale, x: point.x - (point.x - view.x) * scale / view.scale,
    y: point.y - (point.y - view.y) * scale / view.scale }, width, height, maxScale)
}

export function focusBounds(bounds, width, height, maxScale) {
  const fit = Math.min((width - 40) / bounds.width, (height - 40) / bounds.height)
  const readable = bounds.columns ? Math.max(20 * bounds.columns * .62 / (bounds.width * .8), 20 * 2.4 / (bounds.height * .8)) : 1
  const scale = Math.max(1, Math.min(maxScale, Math.max(fit, readable)))
  return clampView({ scale, x: width / 2 - (bounds.x + bounds.width / 2) * scale,
    y: height / 2 - (bounds.y + bounds.height / 2) * scale }, width, height, maxScale)
}

export function reanchorView(view, previous, next, width, height, selectedId) {
  const identity = { scale: 1, x: 0, y: 0 }
  if (view.scale <= 1 || !previous?.cells.length || !next?.cells.length) return identity
  const world = { x: (width / 2 - view.x) / view.scale, y: (height / 2 - view.y) / view.scale }
  const old = selectedId ? previous.cells.find(c => c.id === selectedId)
    : previous.cells.find(c => world.x >= c.x && world.x <= c.x + c.width && world.y >= c.y && world.y <= c.y + c.height)
  const target = old && next.cells.find(c => c.id === old.id)
  if (!target) return selectedId ? identity : clampView(view, width, height, next.maxScale)
  // Keep the selected label (or the world point under the viewport center) in place.
  const box = projectBox(old, view, width, height)
  const screen = selectedId && box ? { x: box.x + box.width / 2, y: box.y + box.height / 2 } : { x: width / 2, y: height / 2 }
  if (selectedId && !box) return focusBounds(target, width, height, next.maxScale)
  const rx = Math.max(0, Math.min(1, ((screen.x - view.x) / view.scale - old.x) / old.width))
  const ry = Math.max(0, Math.min(1, ((screen.y - view.y) / view.scale - old.y) / old.height))
  const readable = selectedId && target.columns ? Math.max(16 * target.columns * .62 / (target.width * .8), 16 * 2.4 / (target.height * .8)) : 1
  const scale = Math.min(next.maxScale, Math.max(view.scale, readable))
  return clampView({ scale, x: screen.x - (target.x + rx * target.width) * scale,
    y: screen.y - (target.y + ry * target.height) * scale }, width, height, next.maxScale)
}

export function retainLiveView(view, previous, next, width, height, selectedId) {
  // Ordinary ticks must not translate the whole map to follow moving boundaries.
  // Recover only if a pinned stock disappears or is no longer readable onscreen.
  const retained = clampView(view, width, height, next.maxScale)
  if (!selectedId || view.scale <= 1) return retained
  const target = next.cells.find(c => c.id === selectedId)
  if (!target) return { scale: 1, x: 0, y: 0 }
  const visible = projectCells([target], retained, width, height)[0]
  return visible && visible.font >= 12 ? retained : reanchorView(view, previous, next, width, height, selectedId)
}

function projectBox(box, view, width, height) {
  const x = Math.max(0, box.x * view.scale + view.x), y = Math.max(0, box.y * view.scale + view.y)
  const right = Math.min(width, (box.x + box.width) * view.scale + view.x)
  const bottom = Math.min(height, (box.y + box.height) * view.scale + view.y)
  return right > x && bottom > y ? { x, y, width: right - x, height: bottom - y } : null
}

export function projectCells(cells, view, width, height, quotes) {
  return cells.flatMap(cell => {
    const box = projectBox(cell, view, width, height)
    if (!box) return []
    const inset = Math.min(6, Math.min(box.width, box.height) * .1)
    const label = quotes?.get(cell.id)?.changeLabel
    const columns = label ? Math.max(cell.id.length, label.length) : cell.columns
    const font = Math.min(30, (box.width - 2 * inset) / (columns * .62), (box.height - 2 * inset) / 2.4)
    return [{ ...cell, ...box, columns, font, center: [box.x + box.width / 2, box.y + box.height / 2] }]
  })
}

export function projectSectors(sectors, view, width, height) {
  return sectors.flatMap(sector => {
    const box = projectBox({ ...sector, height: sector.headerHeight }, view, width, height)
    return box && box.width >= 36 && box.height >= 12 ? [{ ...sector, ...box, height: Math.min(24, box.height) }] : []
  })
}
