export const ASSET_LABELS = {
  vn_stocks: 'Cổ phiếu', indices: 'Chỉ số', fx: 'Ngoại hối',
  crypto: 'Tài sản số', commodities: 'Hàng hóa', derivatives: 'Phái sinh',
}

export function formatWatchlistNumber(value, item = {}, signed = false) {
  if (value == null || value === '' || !Number.isFinite(Number(value))) return '—'
  const number = Number(value), magnitude = Math.abs(number)
  const digits = item.asset_class === 'vn_stocks' ? 0
    : item.asset_class === 'fx' && item.symbol !== 'DXY' ? 5
    : magnitude > 0 && magnitude < 1 ? Math.min(12, Math.max(4, 3 - Math.floor(Math.log10(magnitude)))) : 2
  return `${signed && number > 0 ? '+' : ''}${number.toLocaleString('vi-VN', {
    minimumFractionDigits: Math.min(digits, 2), maximumFractionDigits: digits,
  })}`
}

export function formatWatchlistCap(item) {
  if (item.market_cap == null || !Number.isFinite(Number(item.market_cap))) return '—'
  const value = Number(item.market_cap)
  if (item.market_cap_unit === 'USD' && value >= 1e9) return `${(value / 1e9).toLocaleString('vi-VN', { maximumFractionDigits: 2 })} tỷ USD`
  if (item.market_cap_unit === 'USD' && value >= 1e6) return `${(value / 1e6).toLocaleString('vi-VN', { maximumFractionDigits: 2 })} triệu USD`
  return `${value.toLocaleString('vi-VN', { maximumFractionDigits: 2 })} ${item.market_cap_unit || ''}`.trim()
}

export function filterWatchlist(items, { search = '', assetClass = '', sort = 'saved' } = {}) {
  const needle = search.trim().toLocaleUpperCase('vi-VN')
  const rows = items.filter(item => (!assetClass || item.asset_class === assetClass)
    && (!needle || `${item.symbol} ${item.name || ''} ${item.label || ''}`.toLocaleUpperCase('vi-VN').includes(needle)))
  if (sort === 'symbol') return rows.sort((a, b) => a.symbol.localeCompare(b.symbol))
  if (sort === 'change_desc' || sort === 'change_asc') {
    const value = item => item.change_pct == null || !Number.isFinite(Number(item.change_pct)) ? null : Number(item.change_pct)
    return rows.sort((a, b) => {
      const left = value(a), right = value(b)
      if (left == null) return right == null ? 0 : 1
      if (right == null) return -1
      return sort === 'change_desc' ? right - left : left - right
    })
  }
  return rows
}
