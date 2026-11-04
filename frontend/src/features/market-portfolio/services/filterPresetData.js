/**
 * Preset definitions and industry metadata for Student Stock Screener.
 * Strictly adheres to < 200 lines limit.
 */

export const PRESET_PACKS = [
  { id: 'breakout', label: 'Breakout có xác nhận', group: 'bullish', desc: 'Vượt đỉnh 60 phiên + 0,25 ATR; KL ≥1,5×; đóng gần đỉnh ngày; trên MA50 và cách MA20 ≤3 ATR.' },
  { id: 'strong_trend', label: 'Xu hướng tăng bền', group: 'bullish', desc: 'Giá > MA20 > MA50 > MA200; MA50/200 tăng; sức mạnh tương đối thuộc top 30%.' },
  { id: 'money_inflow', label: 'Áp lực mua', group: 'bullish', desc: 'Giá tăng; KL ≥1,5×; đóng ở ≥70% biên ngày; CMF20 ≥0,10.' },
  { id: 'bottom_fishing', label: 'Hồi phục từ quá bán', group: 'bullish', experimental: true, desc: 'RSI từng dưới 30, nay cắt lên 35; vượt đỉnh phiên trước; KL ≥1,2×.' },
  { id: 'vcp_pattern', label: 'Nền giá co hẹp', group: 'bullish', experimental: true, desc: 'Biến động và khối lượng co hẹp, giá gần đỉnh nền. Đây là proxy, chưa phải nhận diện VCP đầy đủ.' },
  { id: 'overbought_peak', label: 'Giá tăng quá xa nền', group: 'bearish', desc: 'Cao hơn MA20 ≥2,5 ATR và RSI ≥75; không khẳng định sắp đảo chiều.' },
  { id: 'bearish_reversal', label: 'Suy yếu xu hướng', group: 'bearish', desc: 'Cắt xuống MA20 hơn 0,25 ATR; KL ≥1,3×; đóng gần đáy ngày.' },
  { id: 'dumping_signal', label: 'Áp lực bán bất thường', group: 'bearish', desc: 'Giảm ≥1 ATR; KL ≥2×; đóng ở ≤25% biên ngày; CMF20 âm.' },
  { id: 'foreign_favorite', label: 'Khối ngoại mua ròng', group: 'bullish', desc: 'Ngoại ròng 5 phiên ≥2% GT khớp; mua ròng ≥3/5 phiên; tổng 20 phiên dương.' },
  { id: 'high_dividend', label: 'Cổ tức cao bền vững', group: 'dividend', desc: 'Yield tiền mặt ≥5%, top 25%; payout ≤80%; có lợi nhuận và dòng tiền chi trả.' },
  { id: 'regular_cash_div', label: 'Cổ tức tiền mặt đều', group: 'dividend', desc: 'Thực trả 3 năm liên tiếp; mức trả không giảm quá 20%; đủ dòng tiền chi trả.' },
  { id: 'value_investing', label: 'Chất lượng & định giá', group: 'value', desc: 'Chất lượng và định giá đều thuộc top 30% ngành; loại lợi nhuận/vốn chủ âm.' },
]

export const VN_SECTORS_31 = [
  { id: 'bank', name: 'Ngân hàng', code: '8300' },
  { id: 'real_estate', name: 'Bất động sản', code: '8600' },
  { id: 'securities', name: 'Chứng khoán', code: '8700' },
  { id: 'steel', name: 'Thép & Kim loại', code: '1750' },
  { id: 'retail', name: 'Bán lẻ', code: '5370' },
  { id: 'oil_gas', name: 'Dầu khí', code: '0500' },
  { id: 'technology', name: 'Công nghệ thông tin', code: '9500' },
  { id: 'food_beverage', name: 'Thực phẩm & Đồ uống', code: '3500' },
  { id: 'chemicals', name: 'Hóa chất & Phân bón', code: '1350' },
  { id: 'construction', name: 'Xây dựng & Vật liệu', code: '2350' },
  { id: 'logistics', name: 'Vận tải & Cảng biển', code: '2770' },
  { id: 'utilities', name: 'Điện, Nước & Tiện ích', code: '7500' },
  { id: 'textiles', name: 'Dệt may & Da giày', code: '3760' },
  { id: 'aquaculture', name: 'Thủy sản', code: '3570' },
  { id: 'pharmaceuticals', name: 'Dược phẩm & Y tế', code: '4500' },
  { id: 'industrial_park', name: 'Bất động sản KCN', code: '8650' },
  { id: 'telecom', name: 'Viễn thông', code: '6500' },
  { id: 'insurance', name: 'Bảo hiểm', code: '8500' },
  { id: 'rubber', name: 'Cao su', code: '1357' },
  { id: 'agriculture', name: 'Nông nghiệp & Chăn nuôi', code: '3530' },
  { id: 'sugar', name: 'Mía đường', code: '3535' },
  { id: 'aviation', name: 'Hàng không', code: '2775' },
  { id: 'automotive', name: 'Ô tô & Phụ tùng', code: '3350' },
  { id: 'plastics', name: 'Nhựa & Bao bì', code: '1353' },
  { id: 'wood', name: 'Gỗ & Sản phẩm gỗ', code: '2353' },
  { id: 'mining', name: 'Khai khoáng & Than', code: '1770' },
  { id: 'tourism', name: 'Du lịch & Giải trí', code: '5750' },
  { id: 'media', name: 'Truyền thông', code: '5550' },
  { id: 'water_supply', name: 'Cấp thoát nước', code: '7570' },
  { id: 'paper', name: 'Giấy & Bao bì giấy', code: '1730' },
  { id: 'other', name: 'Dịch vụ tài chính khác', code: '8770' }
]

export const EXCHANGES = [
  { id: '', label: 'Tất cả sàn' },
  { id: 'HOSE', label: 'HSX (HOSE)' },
  { id: 'HNX', label: 'HNX' },
  { id: 'UPCOM', label: 'UPCoM' }
]

export const TECHNICAL_FILTERS = [
  { id: 'all', label: 'Tất cả chỉ báo' },
  { id: 'above_ma20', label: 'Giá > MA20' },
  { id: 'above_ma50', label: 'Giá > MA50' },
  { id: 'above_ma200', label: 'Giá > MA200' },
  { id: 'vol_2x_ma20', label: 'Khối lượng > 2x MA20' },
  { id: 'rsi_oversold', label: 'RSI Quá bán (<35)' },
  { id: 'rsi_overbought', label: 'RSI Quá mua (>70)' },
  { id: 'high_volatility', label: 'Biên độ phiên > 3%' }
]
