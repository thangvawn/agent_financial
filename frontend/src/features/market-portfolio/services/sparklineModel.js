export function finitePrice(value) {
  if (value == null || typeof value === 'boolean' || String(value).trim() === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

export function normalizeSparklinePoints(rows = []) {
  const byTime = new Map()
  for (const row of Array.isArray(rows) ? rows : []) {
    const price = finitePrice(row?.close ?? row?.price)
    const rawTime = row?.date ?? row?.timestamp ?? row?.time
    const time = typeof rawTime === 'number' ? (rawTime < 1e12 ? rawTime * 1000 : rawTime) : Date.parse(rawTime)
    if (price !== null && price > 0 && Number.isFinite(time)) byTime.set(time, { time, price })
  }
  return [...byTime.values()].sort((a, b) => a.time - b.time)
}

export function sparklineGeometry(points, width = 240, height = 60) {
  if (points.length < 2) return null
  const prices = points.map(point => point.price)
  const reference = prices[0]
  const low = Math.min(...prices), high = Math.max(...prices)
  // Keep almost-flat series visually flat instead of magnifying a few ticks.
  const span = Math.max(high - low, reference * 0.004)
  const mid = (low + high) / 2
  const y = price => height - 7 - (price - (mid - span * 0.65)) / (span * 1.3) * (height - 14)
  const plotted = points.map((point, index) => ({ ...point, x: 4 + index / (points.length - 1) * (width - 8), y: y(point.price) }))
  const path = plotted.map((point, index) => `${index ? 'L' : 'M'}${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(' ')
  const last = plotted.at(-1)
  const changePct = (last.price / reference - 1) * 100
  return { points: plotted, path, area: `${path} L${last.x},${height} L4,${height} Z`, refY: y(reference), reference, changePct, tone: last.price > reference ? 'up' : last.price < reference ? 'down' : 'flat' }
}
