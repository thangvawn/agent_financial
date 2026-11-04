export const METRICS = {
  value: { label: 'Giá trị giao dịch', unit: 'tỷ', divisor: 1e9 },
  volume: { label: 'Khối lượng', unit: 'triệu CP', divisor: 1e6 },
  market_cap: { label: 'Vốn hóa', unit: 'tỷ', divisor: 1 },
}
export const number = value => value === null || value === undefined || value === '' || typeof value === 'boolean' || !Number.isFinite(Number(value)) ? null : Number(value)
export const formatNumber = (value, digits = 2) => number(value) === null ? '—' : Number(value).toLocaleString('vi-VN', { maximumFractionDigits: digits })
export function formatChange(value) {
  const n = number(value)
  if (n === null) return '—'
  const text = Math.abs(n) > 0 && Math.abs(n) < .01 ? n.toLocaleString('vi-VN', { maximumSignificantDigits: 2 }) : formatNumber(n)
  return `${n > 0 ? '+' : ''}${text}%`
}
export function formatMetric(value, metric) {
  const n = number(value)
  if (n === null) return `— ${METRICS[metric].unit}`
  if (metric === 'volume') return Math.abs(n) >= 1e6 ? `${formatNumber(n / 1e6)} triệu CP` : `${formatNumber(n, 0)} CP`
  const dong = metric === 'market_cap' ? n * 1e9 : n
  if (Math.abs(dong) >= 1e9) return `${formatNumber(dong / 1e9)} tỷ`
  if (Math.abs(dong) >= 1e6) return `${formatNumber(dong / 1e6)} triệu đ`
  return `${formatNumber(dong, 0)} đ`
}

export function priceState(item) {
  const price = number(item.price), pct = number(item.change_pct), volume = number(item.volume)
  if (!item.aggregate && (price === null || price <= 0 || volume === 0)) return 'unknown'
  if (pct === null) return 'unknown'
  if (!item.aggregate) {
    const ceiling = number(item.ceiling), floor = number(item.floor), ref = number(item.ref_price)
    if (ceiling > ref && ref > 0 && Math.abs(price - ceiling) <= .5) return 'ceiling'
    if (floor < ref && floor > 0 && Math.abs(price - floor) <= .5) return 'floor'
  }
  return pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
}

export const STATE_LABEL = { ceiling: 'Trần', up: 'Tăng', flat: 'Tham chiếu', down: 'Giảm', floor: 'Sàn', unknown: 'Thiếu giá / chưa giao dịch' }
// Heatmap color expresses percentage change, including ceiling/floor quotes.
// Keep the actual exchange price state separately for the quote details.
const LOSS_START = [197, 123, 0], LOSS_END = [187, 0, 0]
const GAIN_START = [128, 204, 0], GAIN_END = [68, 187, 0]
const blend = (start, end, amount) => `#${start.map((v, i) => Math.round(v + (end[i] - v) * amount).toString(16).padStart(2, '0')).join('')}`
export function tileColor(item) {
  if (priceState(item) === 'unknown') return '#727b80'
  const pct = number(item.change_pct)
  if (pct < 0) return blend(LOSS_START, LOSS_END, Math.min(1, Math.abs(pct) / 7))
  if (pct > 0) return blend(GAIN_START, GAIN_END, Math.min(1, pct / 3))
  return '#cccc00'
}

export const HEATMAP_COLOR_LEGEND = [-7, -3, -1, 0, 1, 3].map(pct => ({
  label: pct === -7 ? '≤ −7%' : pct === 3 ? '≥ +3%' : formatChange(pct),
  color: tileColor({ price: 10000, volume: 1, change_pct: pct }),
}))

export function buildHeatmap(items, { metric = 'value', exchange = '', sector = '', query = '' } = {}) {
  const needle = query.trim().toLocaleLowerCase('vi-VN')
  const selected = items.filter(item => (!exchange || item.exchange === exchange) && (!sector || item.sector_id === sector)
    && (!needle || `${item.symbol} ${item.name}`.toLocaleLowerCase('vi-VN').includes(needle)))
  const eligible = selected.filter(item => number(item[metric]) !== null && item[metric] > 0)
    .sort((a, b) => b[metric] - a[metric] || a.symbol.localeCompare(b.symbol))
  const total = eligible.reduce((sum, item) => sum + item[metric], 0)
  const mapRows = eligible.filter(item => priceState(item) !== 'unknown')
  const grouped = new Map()
  for (const item of mapRows) {
    const id = item.sector_id || 'unknown'
    if (!grouped.has(id)) grouped.set(id, { id, name: item.sector || 'Chưa phân ngành', items: [] })
    grouped.get(id).items.push(item)
  }
  const groups = [...grouped.values()].sort((a, b) => a.id.localeCompare(b.id)).map(group => {
    const children = group.items.map(item => ({
      ...item, id: item.symbol, weight: item[metric], changeLabel: formatChange(item.change_pct),
    }))
    return { ...group, weight: group.items.reduce((sum, item) => sum + item[metric], 0),
      children }
  })
  return { groups, rows: eligible, mapRows, total, mapTotal: mapRows.reduce((sum, item) => sum + item[metric], 0), selected: selected.length, eligible: eligible.length,
    missingChange: eligible.length - mapRows.length,
    missing: selected.filter(item => number(item[metric]) === null).length,
    zero: selected.filter(item => number(item[metric]) !== null && item[metric] <= 0).length,
  }
}
