import { finitePrice } from './sparklineModel.js'

export const COMMODITY_GROUPS = [
  ['all', 'Tất cả'], ['metals', 'Kim loại'], ['energy', 'Năng lượng'],
  ['grains', 'Ngũ cốc'], ['livestock', 'Chăn nuôi'], ['raw_materials', 'Nguyên liệu'],
]

export const COMMODITY_RANGES = ['1mo', '3mo', '6mo', '1y']
export const RANGE_LABELS = { '1mo': '1 tháng', '3mo': '3 tháng', '6mo': '6 tháng', '1y': '1 năm' }
export const groupLabel = category => COMMODITY_GROUPS.find(([key]) => key === category)?.[1] || 'Khác'
export const sourceLabel = source => source === 'yahoo_finance' ? 'Yahoo Finance' : source || 'Chưa rõ nguồn'
export const tone = value => finitePrice(value) === null ? 'unknown' : Number(value) > 0 ? 'up' : Number(value) < 0 ? 'down' : 'flat'

export function commodityNumber(value, digits = 2) {
  const number = finitePrice(value)
  return number === null ? '—' : number.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

// Keep the provider's quote unit: 450 US cents/bu is not $450/bu.
export function commodityPrice(value) {
  const number = finitePrice(value)
  return commodityNumber(number, number !== null && Math.abs(number) < 10 ? 4 : 2)
}

export function quoteTime(value) {
  if (!value || !Number.isFinite(Date.parse(value))) return 'Chưa có thời gian giá'
  return new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date(value))
}

const searchable = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').toLowerCase()
export function selectCommodities(items, { group = 'all', query = '', sort = 'volume' } = {}) {
  const search = searchable(query.trim())
  return items.filter(row => (group === 'all' || row.category === group) && searchable(`${row.symbol} ${row.name} ${groupLabel(row.category)}`).includes(search))
    .sort((a, b) => {
      if (sort === 'name') return a.symbol.localeCompare(b.symbol)
      const key = sort === 'volume' ? 'volume_24h' : 'change_pct'
      const left = finitePrice(a[key]), right = finitePrice(b[key])
      if (left === null || right === null) return left === right ? a.symbol.localeCompare(b.symbol) : left === null ? 1 : -1
      return (sort === 'losers' ? left - right : right - left) || a.symbol.localeCompare(b.symbol)
    })
}

export function normalizeCommodityHistory(rows) {
  const points = new Map()
  for (const row of Array.isArray(rows) ? rows : []) {
    const close = finitePrice(row?.close ?? row?.price)
    const time = Date.parse(row?.date)
    if (close === null || !Number.isFinite(time)) continue
    const open = finitePrice(row.open), high = finitePrice(row.high), low = finitePrice(row.low)
    const validOhlc = open !== null && high !== null && low !== null && high >= Math.max(open, close) && low <= Math.min(open, close)
    points.set(time, { date: new Date(time).toISOString(), close, ...(validOhlc ? { open, high, low } : {}), volume: finitePrice(row.volume) >= 0 ? finitePrice(row.volume) : null })
  }
  return [...points.values()].sort((a, b) => a.date.localeCompare(b.date))
}

export function historySummary(points) {
  const first = points[0], last = points.at(-1)
  if (!first) return { change: null, high: null, low: null, candles: false, volume: false }
  return {
    change: points.length > 1 && first.close !== 0 ? (last.close - first.close) / Math.abs(first.close) * 100 : null,
    high: Math.max(...points.map(point => point.high ?? point.close)),
    low: Math.min(...points.map(point => point.low ?? point.close)),
    candles: points.every(point => point.open !== undefined),
    volume: points.some(point => point.volume !== null && point.volume > 0),
  }
}
