export const SENTIMENT_LABELS = { positive: 'Tích cực', negative: 'Tiêu cực', neutral: 'Trung tính', unknown: 'Chưa xác định' }
export const IMPORTANCE_LABELS = { critical: 'Khẩn cấp', high: 'Quan trọng', medium: 'Trung bình', low: 'Ít quan trọng', noise: 'Ít ảnh hưởng' }
const MARKET_LABELS = { FX: 'Ngoại hối', Rates: 'Lãi suất', 'VN Equity': 'Cổ phiếu VN', 'US Equity': 'Cổ phiếu Mỹ', Gold: 'Vàng', Oil: 'Dầu', Banking: 'Ngân hàng', 'Real Estate': 'Bất động sản', Crypto: 'Tài sản số', Technology: 'Công nghệ', Commodities: 'Hàng hóa', Bonds: 'Trái phiếu' }
export const marketLabel = value => MARKET_LABELS[value] || value
export function newsQuality(payload, now = Date.now()) {
  if (!payload) return { stale: false, label: 'Chưa có dữ liệu', updatedAt: null }
  const updatedAt = payload.data_updated_at || null
  const timestamp = Date.parse(updatedAt)
  const tooOld = !Number.isFinite(timestamp) || now - timestamp > 120000
  const partial = payload.source_count > 0 && payload.successful_source_count < payload.source_count
  const stale = tooOld || payload.freshness !== 'fresh' || Boolean(payload.stale_reason || payload.data_quality?.stale_reason) || partial
  return { stale, label: stale ? 'Dữ liệu cũ hoặc nguồn chưa đầy đủ' : 'Đã cập nhật', updatedAt }
}
